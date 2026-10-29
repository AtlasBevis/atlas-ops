# SQL Server

## Create User for CDC

```sql
USE master
GO
-- create user debezium
CREATE LOGIN etl_user WITH PASSWORD = 'YourStrongPasswordHere!123';
CREATE USER etl_user FOR LOGIN etl_user;
GRANT VIEW DATABASE STATE TO [etl_user];
GRANT VIEW DATABASE PERFORMANCE STATE TO [etl_user];

USE [source_db]
GO

-- Enable CDC feature database
-- you are a member of sysadmin or db_owner
EXEC sys.sp_cdc_enable_db
GO

-- (optional) verify all databases are enabled cdc
SELECT name, is_cdc_enabled  FROM sys.databases

-- verify current db
SELECT is_cdc_enabled FROM sys.databases WHERE name = DB_NAME()

-- create schema etl
CREATE SCHEMA etl AUTHORIZATION [etl_user]
GO

-- grant select for user
GRANT SELECT ON SCHEMA::dbo TO [etl_user];
GRANT SELECT ON SCHEMA::cdc TO etl_user;
GRANT SELECT ON dbo.Loan TO etl_user;

-- create table signal
CREATE TABLE etl.Debezium_signal (
  id   varchar(42)  NOT NULL PRIMARY KEY,
  type varchar(32)  NOT NULL,
  data varchar(2048) NULL
);
GO

-- Enable CDC cho table source
EXEC sys.sp_cdc_enable_table
    @source_schema    = N'dbo',
    @source_name      = N'Loan',
    @role_name        = NULL
GO
```

> Note: Topics matches like <prefix>.<database>.<schema>.dbo.<table>
