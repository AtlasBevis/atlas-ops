# Iceberg Maintenance

How to maintain Iceberg tables on the lakehouse (Lakekeeper REST catalog + MinIO S3).

References: [Iceberg Maintenance](https://iceberg.apache.org/docs/latest/maintenance/) · [Spark Procedures](https://iceberg.apache.org/docs/latest/spark-procedures/)

## 1. Why maintenance is needed

`raw.*` tables are written by the Kafka Connect Iceberg Sink ([kafka-connect/values.yaml](../kafka-connect/values.yaml)) with
`iceberg.control.commit.interval-ms: 60000` → **~1 commit/minute per table ≈ 1,440 snapshots/day**. Without maintenance:

| Problem              | Cause                                                           | Impact                                     |
| -------------------- | --------------------------------------------------------------- | ------------------------------------------ |
| Many small files     | Each commit writes new data files per `days(_cdc.ts)` partition | Slow Trino/Spark queries, more S3 requests |
| Metadata bloat       | Each snapshot adds a manifest list + manifests                  | Slow query planning, heavy catalog         |
| Delete files pile up | CDC (Debezium) produces equality/position deletes               | Merge-on-read gets slower over time        |
| Garbage on MinIO     | Files no longer referenced by any snapshot                      | Wasted storage                             |

## 2. Maintenance tasks

Recommended order: **rewrite_data_files → rewrite_position_delete_files → rewrite_manifests → expire_snapshots → remove_orphan_files**.

### 2.1 Compact data files

```sql
CALL lakehouse_uat.system.rewrite_data_files(
  table   => 'raw.card.bo.tbl1',
  strategy => 'binpack',                       -- or 'sort'
  where   => "_cdc.ts >= current_date - INTERVAL 2 DAYS", -- recent partitions only, avoid rewriting the whole table
  options => map(
    'target-file-size-bytes', '536870912',     -- 512MB
    'min-input-files', '5',
    'partial-progress.enabled', 'true',
    'partial-progress.max-commits', '10',
    'max-concurrent-file-group-rewrites', '5'
  )
);
```

- Compact only "cold" or recent partitions; partitions being actively written may cause commit conflicts with the sink (the sink will retry).
- `partial-progress.enabled` keeps completed work if the job fails midway.

### 2.2 Compact delete files (CDC tables)

```sql
CALL lakehouse_uat.system.rewrite_position_delete_files(
  table => 'raw.card.bo.tbl1',
  options => map('rewrite-all', 'true')
);
```

Alternatively, use `rewrite_data_files` with `'delete-file-threshold', '1'` to apply deletes into the data files.

### 2.3 Rewrite manifests

```sql
CALL lakehouse_uat.system.rewrite_manifests('raw.card.bo.tbl1');
```

### 2.4 Expire snapshots

```sql
CALL lakehouse_uat.system.expire_snapshots(
  table       => 'raw.card.bo.tbl1',
  older_than  => TIMESTAMP '2026-10-20 00:00:00',  -- now - retention
  retain_last => 100,
  max_concurrent_deletes => 8
);
```

Or set table defaults so the job does not need parameters:

```sql
ALTER TABLE lakehouse_uat.raw.card.bo.tbl1 SET TBLPROPERTIES (
  'history.expire.max-snapshot-age-ms' = '604800000',  -- 7 days
  'history.expire.min-snapshots-to-keep' = '100'
);
```

> ⚠️ Expired snapshots can **no longer be used for time travel / rollback**. Agree on retention with the team before reducing it.

### 2.5 Remove orphan files

```sql
CALL lakehouse_uat.system.remove_orphan_files(
  table      => 'raw.card.bo.tbl1',
  older_than => TIMESTAMP '2026-10-24 00:00:00',  -- at least now - 3 days
  dry_run    => true                               -- run dry_run first, review, then remove it
);
```

> ⚠️ **Never** set `older_than` close to the current time: files being written by a writer (Kafka Connect) but not yet committed will be deleted → data loss / corrupted table. Keep at least 3 days (Iceberg default).

### 2.6 Metadata file cleanup (one-time setup)

```sql
ALTER TABLE lakehouse_uat.raw.card.bo.tbl1 SET TBLPROPERTIES (
  'write.metadata.delete-after-commit.enabled' = 'true',
  'write.metadata.previous-versions-max' = '100'
);
```

## 3. Recommended schedule

| Task                                   | Frequency       | Notes                               |
| -------------------------------------- | --------------- | ----------------------------------- |
| rewrite_data_files (recent partitions) | Every 1–6 hours | CDC tables are written continuously |
| rewrite_position_delete_files          | Daily           | Tables with updates/deletes         |
| rewrite_manifests                      | Daily           |                                     |
| expire_snapshots                       | Daily           | 7-day retention                     |
| remove_orphan_files                    | Weekly          | Run off-peak, `older_than` ≥ 3 days |

## 4. Running maintenance jobs on Kubernetes

Jobs use the Spark Kubernetes Operator; sample manifest: [spark-system/SparkApplication.yaml](../spark-system/SparkApplication.yaml).

- Image: `registry.local/dwh/iceberg-maintenance:<version>`, entrypoint `/opt/spark/jobs/iceberg_maintenance_job.py`
- Arguments: `--catalog` (e.g. `lakehouse_uat`), `--zone` (e.g. `raw`), `--config` (JSON, e.g. `{"namespaces": ["raw.card.bo"]}`)
- Secret `lakekeeper-spark` provides `LAKEKEEPER_URI`

### Manual run

```bash
kubectl apply -f spark-system/SparkApplication.yaml
kubectl -n spark get sparkapplication lakehouse-raw-manual -w
kubectl -n spark logs -f -l maintenance-run=lakehouse-raw-manual,spark-role=driver
```

Normal lifecycle: `Submitted → DriverRequested → DriverStarted → RunningHealthy → Succeeded → ResourceReleased`.
Pods are kept on failure (`resourceRetainPolicy: OnFailure`); the CR is deleted automatically after 1 day (`ttlAfterStopMillis`).

### Re-run

```bash
kubectl -n spark delete sparkapplication lakehouse-raw-manual
kubectl apply -f spark-system/SparkApplication.yaml
```

### Scheduled runs

Use Airflow ([airflow/](../airflow/)) with `SparkKubernetesOperator`, or a CronJob that runs `kubectl apply` on the manifest; change `metadata.name` per run (e.g. a timestamp suffix) to avoid name collisions.

## 5. Table health checks

Run on Trino or Spark:

```sql
-- Number of snapshots
SELECT count(*) FROM lakehouse_uat.raw.card.bo."tbl1$snapshots";

-- File count and average file size per partition (small files = needs compaction)
SELECT partition, file_count, total_size / file_count / 1024 / 1024 AS avg_mb
FROM lakehouse_uat.raw.card.bo."tbl1$partitions"
ORDER BY file_count DESC LIMIT 20;

-- Number of manifests
SELECT count(*) FROM lakehouse_uat.raw.card.bo."tbl1$manifests";

-- Outstanding delete files (content: 1 = position, 2 = equality)
SELECT content, count(*) FROM lakehouse_uat.raw.card.bo."tbl1$files" GROUP BY content;
```

Suggested alert thresholds: avg file < 32MB, > 1,000 snapshots, > 500 manifests, delete files > 10% of data files.

> Trino also supports: `ALTER TABLE ... EXECUTE optimize(file_size_threshold => '128MB')`, `EXECUTE expire_snapshots(retention_threshold => '7d')`, `EXECUTE remove_orphan_files(retention_threshold => '7d')` — handy for quick fixes on a single table.

## 6. Troubleshooting

| Symptom                                     | Cause / Fix                                                                                                                                                               |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CommitFailedException` during compaction   | Conflict with Kafka Connect commits. Enable `partial-progress.enabled`, narrow `where` to older partitions, re-run.                                                       |
| Driver OOM                                  | Too many files/manifests. Increase `spark.driver.memory`, run `rewrite_manifests` first, compact partition by partition.                                                  |
| `DriverStartTimedOut` / `SchedulingFailure` | Insufficient node resources or image pull failure (`dockerhub-regcred`). Check `kubectl -n spark describe pod`.                                                           |
| 401/403 from Lakekeeper                     | OAuth2 token / `lakekeeper-spark` secret is wrong or expired.                                                                                                             |
| S3 error / `NoSuchKey` on read              | Possibly orphan cleanup with `older_than` too recent. Roll back with `CALL <catalog>.system.rollback_to_snapshot('<table>', <snapshot_id>)` if the snapshot still exists. |
| MinIO usage does not drop after expiring    | Files still referenced by retained snapshots, or MinIO versioning/lifecycle is enabled — check the bucket policy.                                                         |

## 7. Pre-PROD checklist

- [ ] Tested on UAT with the same image/version
- [ ] `remove_orphan_files` run with `dry_run => true` and the file list reviewed
- [ ] Snapshot retention approved by the data team
- [ ] Run off-peak and monitor Kafka Connect lag during compaction
- [ ] Record the current snapshot id of critical tables for rollback if needed
