#

### Enable Logical Replication

```sql
---default: replica
SHOW wal_level;
```

```sh
2026-10-29T14:50:58,242 ERROR  Postgres||lifecycle  Failed testing connection for jdbc:postgresql://postgres:5432/de with user 'etl'   [io.debezium.connector.postgresql.PostgresConnectorTask]
java.sql.SQLException: Postgres server wal_level property must be 'logical' but is: 'replica'
        at io.debezium.connector.postgresql.PostgresConnectorTask.checkWalLevel(PostgresConnectorTask.java:527)
        at io.debezium.connector.postgresql.PostgresConnectorTask.start(PostgresConnectorTask.java:174)
        at io.debezium.connector.common.BaseSourceTask.start(BaseSourceTask.java:286)
        at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.initializeAndStart(AbstractWorkerSourc
```

Enabled logical replication

```sh
# find config file
SHOW config_file;

sudo vi /var/lib/postgresql/18/docker/postgresql.conf
wal_level = logical
max_wal_senders = 10
max_replication_slots = 10
```

2. Miss role REPLICATE

```sh
2026-10-29T15:14:00,091 ERROR  Postgres||lifecycle  WorkerSourceTask{id=postgres-cdc-0} Task threw an uncaught and unrecoverable exception. Task is being killed and will not recover until manually restarted   [org.apache.kafka.connect.runtime.WorkerTask]
io.debezium.DebeziumException: Creation of replication slot failed
        at io.debezium.connector.postgresql.PostgresConnectorTask.tryToCreateSlot(PostgresConnectorTask.java:329)
        at io.debezium.connector.postgresql.PostgresConnectorTask.start(PostgresConnectorTask.java:197)
        at io.debezium.connector.common.BaseSourceTask.start(BaseSourceTask.java:286)
        at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.initializeAndStart(AbstractWorkerSourceTask.java:288)
        at org.apache.kafka.connect.runtime.WorkerTask.doStart(WorkerTask.java:191)
        at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:242)
        at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:298)
        at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.run(AbstractWorkerSourceTask.java:83)
        at org.apache.kafka.connect.runtime.isolation.Plugins.lambda$withClassLoader$0(Plugins.java:252)
        at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:545)
        at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:328)
        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1090)
        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:614)
        at java.base/java.lang.Thread.run(Thread.java:1474)
Caused by: org.postgresql.util.PSQLException: FATAL: permission denied to start WAL sender
  Detail: Only roles with the REPLICATION attribute may start a WAL sender process.
        at org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(QueryExecutorImpl.java:2993)
        at org.postgresql.core.v3.QueryExecutorImpl.readStartupMessages(QueryExecutorImpl.java:3118)
        at org.postgresql.core.v3.QueryExecutorImpl.<init>(QueryExecutorImpl.java:251)
        at org.postgresql.core.v3.ConnectionFactoryImpl.openConnectionImpl(ConnectionFactoryImpl.java:398)
        at org.postgresql.core.ConnectionFactory.openConnection(ConnectionFactory.java:52)
        at org.postgresql.jdbc.PgConnection.<init>(PgConnection.java:295)
        at org.postgresql.Driver.makeConnection(Driver.java:437)
        at org.postgresql.Driver.connect(Driver.java:305)
        at io.debezium.jdbc.JdbcConnection.lambda$patternBasedFactory$1(JdbcConnection.java:252)
        at io.debezium.jdbc.JdbcConnection$ConnectionFactoryDecorator.connect(JdbcConnection.java:138)
        at io.debezium.jdbc.JdbcConnection.establishConnection(JdbcConnection.java:942)
        at io.debezium.jdbc.JdbcConnection.connection(JdbcConnection.java:926)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.pgConnection(PostgresReplicationConnection.java:922)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.createReplicationSlot(PostgresReplicationConnection.java:846)
        at io.debezium.connector.postgresql.PostgresConnectorTask.tryToCreateSlot(PostgresConnectorTask.java:322)
        ... 13 more
```

### Add REPLICATE role to etl

```sql
ALTER ROLE etl WITH REPLICATION;

-- verify
SELECT
    rolname,
    rolreplication,
    rolsuper
FROM pg_roles
WHERE rolname = 'etl';
```

### Add plugin into connector

```sh
ERROR: could not access file "decoderbufs": No such file or directory
```

```json
{
  "plugin.name": "pgoutput"
}
```

### Failed to create publication

```sh
onnection.PostgresReplicationConnection]
2026-10-29T15:21:40,976 INFO   Postgres||postgres-connector-task  Creating new publication 'dbz_publication' for plugin 'PGOUTPUT'   [io.debezium.connector.postgresql.connection.PostgresReplicationConnection]
2026-10-29T15:21:40,976 INFO   Postgres||postgres-connector-task  Creating Publication with statement 'CREATE PUBLICATION dbz_publication FOR ALL TABLES;'   [io.debezium.connector.postgresql.connection.PostgresReplicationConnection]
2026-10-29T15:21:40,977 WARN   Postgres||postgres-connector-task  Failed to reset statement_timeout to original value: 0   [io.debezium.connector.postgresql.connection.PostgresReplicationConnection]
org.postgresql.util.PSQLException: ERROR: current transaction is aborted, commands ignored until end of transaction block
        at org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(QueryExecutorImpl.java:2993)
        at org.postgresql.core.v3.QueryExecutorImpl.processResults(QueryExecutorImpl.java:2656)
        at org.postgresql.core.v3.QueryExecutorImpl.execute(QueryExecutorImpl.java:446)
        at org.postgresql.jdbc.PgStatement.executeInternal(PgStatement.java:533)
        at org.postgresql.jdbc.PgStatement.execute(PgStatement.java:449)
        at org.postgresql.jdbc.PgStatement.executeWithFlags(PgStatement.java:371)
        at org.postgresql.jdbc.PgStatement.executeCachedSql(PgStatement.java:356)
        at org.postgresql.jdbc.PgStatement.executeWithFlags(PgStatement.java:332)
        at org.postgresql.jdbc.PgStatement.execute(PgStatement.java:327)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.resetStatementTimeout(PostgresReplicationConnection.java:191)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.executeWithTimeout(PostgresReplicationConnection.java:217)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.initPublication(PostgresReplicationConnection.java:250)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.createReplicationSlot(PostgresReplicationConnection.java:865)
        at io.debezium.connector.postgresql.PostgresConnectorTask.tryToCreateSlot(PostgresConnectorTask.java:322)
        at io.debezium.connector.postgresql.PostgresConnectorTask.start(PostgresConnectorTask.java:197)
        at io.debezium.connector.common.BaseSourceTask.start(BaseSourceTask.java:286)
        at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.initializeAndStart(AbstractWorkerSourceTask.java:288)
        at org.apache.kafka.connect.runtime.WorkerTask.doStart(WorkerTask.java:191)
        at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:242)
        at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:298)
        at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.run(AbstractWorkerSourceTask.java:83)
        at org.apache.kafka.connect.runtime.isolation.Plugins.lambda$withClassLoader$0(Plugins.java:252)
        at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:545)
        at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:328)
        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1090)
        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:614)
        at java.base/java.lang.Thread.run(Thread.java:1474)
Caused by: org.postgresql.util.PSQLException: ERROR: permission denied for database de
        at org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(QueryExecutorImpl.java:2993)
        at org.postgresql.core.v3.QueryExecutorImpl.processResults(QueryExecutorImpl.java:2656)
        at org.postgresql.core.v3.QueryExecutorImpl.execute(QueryExecutorImpl.java:446)
        at org.postgresql.jdbc.PgStatement.executeInternal(PgStatement.java:533)
        at org.postgresql.jdbc.PgStatement.execute(PgStatement.java:449)
        at org.postgresql.jdbc.PgStatement.executeWithFlags(PgStatement.java:371)
        at org.postgresql.jdbc.PgStatement.executeCachedSql(PgStatement.java:356)
        at org.postgresql.jdbc.PgStatement.executeWithFlags(PgStatement.java:332)
        at org.postgresql.jdbc.PgStatement.execute(PgStatement.java:327)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.executeWithTimeout(PostgresReplicationConnection.java:214)
        ... 16 more
2026-10-29T15:21:40,978 ERROR  Postgres||lifecycle  WorkerSourceTask{id=postgres-cdc-0} Task threw an uncaught and unrecoverable exception. Task is being killed and will not recover until manually restarted   [org.apache.kafka.connect.runtime.WorkerTask]
io.debezium.jdbc.JdbcConnectionException: ERROR: permission denied for database de
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.initPublication(PostgresReplicationConnection.java:331)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.createReplicationSlot(PostgresReplicationConnection.java:865)
        at io.debezium.connector.postgresql.PostgresConnectorTask.tryToCreateSlot(PostgresConnectorTask.java:322)
        at io.debezium.connector.postgresql.PostgresConnectorTask.start(PostgresConnectorTask.java:197)
        at io.debezium.connector.common.BaseSourceTask.start(BaseSourceTask.java:286)
        at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.initializeAndStart(AbstractWorkerSourceTask.java:288)
        at org.apache.kafka.connect.runtime.WorkerTask.doStart(WorkerTask.java:191)
        at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:242)
        at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:298)
        at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.run(AbstractWorkerSourceTask.java:83)
        at org.apache.kafka.connect.runtime.isolation.Plugins.lambda$withClassLoader$0(Plugins.java:252)
        at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:545)
        at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:328)
        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1090)
        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:614)
        at java.base/java.lang.Thread.run(Thread.java:1474)
Caused by: org.postgresql.util.PSQLException: ERROR: permission denied for database de
        at org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(QueryExecutorImpl.java:2993)
        at org.postgresql.core.v3.QueryExecutorImpl.processResults(QueryExecutorImpl.java:2656)
        at org.postgresql.core.v3.QueryExecutorImpl.execute(QueryExecutorImpl.java:446)
        at org.postgresql.jdbc.PgStatement.executeInternal(PgStatement.java:533)
        at org.postgresql.jdbc.PgStatement.execute(PgStatement.java:449)
        at org.postgresql.jdbc.PgStatement.executeWithFlags(PgStatement.java:371)
        at org.postgresql.jdbc.PgStatement.executeCachedSql(PgStatement.java:356)
        at org.postgresql.jdbc.PgStatement.executeWithFlags(PgStatement.java:332)
        at org.postgresql.jdbc.PgStatement.execute(PgStatement.java:327)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.executeWithTimeout(PostgresReplicationConnection.java:214)
        at io.debezium.connector.postgresql.connection.PostgresReplicationConnection.initPublication(PostgresReplicationConnection.java:250)
        ... 15 more
```

```sql
CREATE PUBLICATION dbz_publication FOR ALL TABLES;
```

add to connector

```json
{
  "publication.name": "dbz_publication",
  "publication.autocreate.mode": "disabled"
}
```
