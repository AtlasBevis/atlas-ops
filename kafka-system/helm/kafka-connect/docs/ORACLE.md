# Oracle Golive with Debezium

We performs on `Oracle Database 12c Enterprise Edition Release 12.1.0.2.0 - 64bit Production`

## Requirements

```sql
-- to use LogMiner
GRANT LOGMINING TO ETL_USER;

-- read the data dictionary, is needed by Oracle LogMiner sessions
GRANT SELECT_CATALOG_ROLE TO ETL_USER;

-- write the data dictionary into the Oracle redo logs, is needed to track schema changes.
GRANT EXECUTE_CATALOG_ROLE TO ETL_USER;

-- performs the initial snapshot of data
GRANT FLASHBACK ANY TABLE TO ETL_USER;

-- flush table in its default tablespace
GRANT CREATE TABLE TO ETL_USER;
GRANT CREATE SEQUENCE TO ETL_USER;

-- if grant
GRANT SELECT ANY DICTIONARY TO ETL_USER;

-- if user has SELECT ANY DICTIONARY, no need privileges below
-- read information about the Oracle redo and archive logs, and the current transaction state, to prepare the Oracle LogMiner session
GRANT SELECT ON V_$DATABASE TO ETL_USER;
GRANT SELECT ON V_$LOG TO ETL_USER;
GRANT SELECT ON V_$LOG_HISTORY TO ETL_USER;
GRANT SELECT ON V_$LOGMNR_LOGS TO ETL_USER;
GRANT SELECT ON V_$LOGMNR_CONTENTS TO ETL_USER;
GRANT SELECT ON V_$LOGMNR_PARAMETERS TO ETL_USER;
GRANT SELECT ON V_$LOGFILE TO ETL_USER;
GRANT SELECT ON V_$ARCHIVED_LOG TO ETL_USER;
GRANT SELECT ON V_$ARCHIVE_DEST_STATUS TO ETL_USER;
GRANT SELECT ON V_$TRANSACTION TO ETL_USER;
GRANT SELECT ON V_$MYSTAT TO ETL_USER;
GRANT SELECT ON V_$STATNAME TO ETL_USER;

-- Change default tablespace avoid Oracle System (SYSTEM)
ALTER USER ETL_USER DEFAULT TABLESPACE USER_DATA_TBS;

-- Grant quota maximium 100M
ALTER USER ETL_USER QUOTA 100M ON USER_DATA_TBS;

-- table controls Debezium
CREATE TABLE ETL_USER.DEBEZIUM_SIGNAL (
  ID     VARCHAR2(42)  PRIMARY KEY,
  "TYPE" VARCHAR2(32)  NOT NULL,
  DATA   VARCHAR2(2048)
);

```

> Note: You must enable supplemental logging before generating log files that will be analyzed by LogMiner.

```sql
ALTER DATABASE ADD SUPPLEMENTAL LOG DATA;

-- To determine whether supplemental logging is enabled, query the V$DATABASE view, as the following SQL statement shows:
SELECT SUPPLEMENTAL_LOG_DATA_MIN FROM V$DATABASE;
```

### Refereces

- [Create User](https://debezium.io/documentation/reference/3.5/connectors/oracle.html?utm_source=chatgpt.com#creating-users-for-the-connector)
- [Using LogMiner to Analyze Red Log](https://docs.oracle.com/en/database/oracle/oracle-database/12.2/sutil/oracle-logminer-utility.html#GUID-3417B738-374C-4EE3-B15C-3A66E01AE2B5)