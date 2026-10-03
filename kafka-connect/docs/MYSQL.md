# MySQL Golive with Debezium

Debezium MySQL reads the **binary log** (`binlog`). The server must log in `ROW` format. **GTID** is strongly recommended (failover / replica switch).

Connector class: `io.debezium.connector.mysql.MySqlConnector`

Debezium **3.6** tested MySQL: **8.0.x**, **8.4.x**, **9.0**, **9.1**. MySQL **5.7** is not supported.

## 1. Verify binlog + GTID

```sql
SHOW VARIABLES WHERE Variable_name IN (
  'log_bin',
  'binlog_format',
  'binlog_row_image',
  'server_id',
  'gtid_mode',
  'enforce_gtid_consistency',
  'binlog_expire_logs_seconds'
);
```

Expected:

| Variable                     | Value                                                                  |
| ---------------------------- | ---------------------------------------------------------------------- |
| `log_bin`                    | `ON`                                                                   |
| `binlog_format`              | `ROW`                                                                  |
| `binlog_row_image`           | `FULL`                                                                 |
| `server_id`                  | unique in the MySQL topology (not `0`)                                 |
| `gtid_mode`                  | `ON`                                                                   |
| `enforce_gtid_consistency`   | `ON`                                                                   |
| `binlog_expire_logs_seconds` | retain long enough for connector downtime (example `864000` = 10 days) |

MySQL 8.x alternative:

```sql
SELECT variable_name, variable_value
FROM performance_schema.global_variables
WHERE variable_name IN (
  'log_bin',
  'binlog_format',
  'binlog_row_image',
  'server_id',
  'gtid_mode',
  'enforce_gtid_consistency',
  'binlog_expire_logs_seconds'
);
```

## 2. Enable binlog (if `log_bin` is OFF)

Add to MySQL config (`my.cnf` / `mysqld.cnf`) and restart:

```properties
server-id                   = 223344
log_bin                     = mysql-bin
binlog_format               = ROW
binlog_row_image            = FULL
binlog_expire_logs_seconds  = 864000
```

Notes:

- `server-id` must be unique vs every MySQL instance **and** vs Debezium `database.server.id`.

## 3. Enable GTID (recommended)

If you can restart from config:

```properties
gtid_mode                 = ON
enforce_gtid_consistency  = ON
```

Confirm:

```sql
SHOW GLOBAL VARIABLES LIKE '%GTID%';
```

```text
+--------------------------+-------+
| Variable_name            | Value |
+--------------------------+-------+
| enforce_gtid_consistency | ON    |
| gtid_mode                | ON    |
+--------------------------+-------+
```

> Enabling GTID on a live cluster is a staged DBA change (`OFF` → `OFF_PERMISSIVE` → `ON_PERMISSIVE` → `ON`). Do not flip `gtid_mode=ON` in one step on production without following MySQL [docs](https://dev.mysql.com/doc/refman/8.4/en/replication-options-gtids.html#option_mysqld_gtid-mode)

## 4. Create user CDC

```sql
CREATE USER 'etl_user'@'172.168.%' IDENTIFIED BY 'YourStrongPasswordHere!123';

-- snapshot + binlog
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'etl_user'@'172.168.%';

-- RDS / Aurora (no global read lock): snapshot uses table locks
-- GRANT LOCK TABLES ON *.* TO 'etl_user'@'%';

FLUSH PRIVILEGES;
```

| Privilege            | Why                                          |
| -------------------- | -------------------------------------------- |
| `SELECT`             | Initial / incremental snapshot               |
| `RELOAD`             | `FLUSH` / global read lock during snapshot   |
| `SHOW DATABASES`     | Snapshot discovery                           |
| `REPLICATION SLAVE`  | Read binlog as a replica                     |
| `REPLICATION CLIENT` | `SHOW MASTER STATUS` / `SHOW BINARY LOGS`    |
| `LOCK TABLES`        | Snapshot when global lock is forbidden (RDS) |

Tighten `SELECT` to captured DBs if policy requires it:

```sql
GRANT SELECT ON inventory.* TO 'etl_user'@'%';
FLUSH PRIVILEGES;
```

## 5. Signal table (ad-hoc / incremental snapshot)

Source channel needs a table Debezium can `INSERT`/`SELECT`. Put it in a dedicated database (not mixed with app tables if possible).

```sql
CREATE DATABASE IF NOT EXISTS etl;

CREATE TABLE etl.debezium_signal (
  id   VARCHAR(42)   NOT NULL PRIMARY KEY,
  type VARCHAR(32)   NOT NULL,
  data VARCHAR(2048) NULL
);

GRANT SELECT, INSERT, UPDATE, DELETE ON etl.debezium_signal TO 'etl_user'@'%';
FLUSH PRIVILEGES;
```

Connector:

```text
signal.enabled.channels: source,kafka
signal.data.collection: etl.debezium_signal
```

Example incremental snapshot:

```sql
INSERT INTO etl.debezium_signal (id, type, data)
VALUES (
  'ad-hoc-1',
  'execute-snapshot',
  '{"data-collections": ["inventory.customers"], "type": "incremental"}'
);
```

`data-collections` uses `database.table` (MySQL has no Oracle-style schema). Names are **case-sensitive**.

> MySQL **read-only** connection: source signal table is not required; use Kafka / other channels instead.

## 6. Optional: session timeout (large snapshot)

```sql
SET GLOBAL interactive_timeout = 28800;
SET GLOBAL wait_timeout = 28800;
```

Or set the same in `my.cnf` / parameter group.

## Notes

- Topics: `<topic.prefix>.<database>.<table>`  
  Example: `cdc.mysql.inventory.customers`
- `database.server.id` on the connector must be unique in the replication topology.
- `binlog_format` must stay `ROW`. `STATEMENT` / `MIXED` cannot be used for CDC.
- If binlog is purged before the connector catches up, the connector fails and needs a new snapshot / `set-binlog-position` signal.

### References

- [Creating a user](https://debezium.io/documentation/reference/3.6/connectors/mysql.html#mysql-creating-a-user)
- [Enabling the binlog](https://debezium.io/documentation/reference/3.6/connectors/mysql.html#mysql-enabling-the-binlog)
- [Enabling GTIDs](https://debezium.io/documentation/reference/3.6/connectors/mysql.html#mysql-enabling-gtids)
- [Signalling](https://debezium.io/documentation/reference/3.6/configuration/signalling.html)
