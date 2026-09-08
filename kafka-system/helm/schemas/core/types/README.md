# Source data types → Schema Registry (Avro)

Tài liệu định nghĩa **kiểu dữ liệu nguồn** (Oracle / PostgreSQL / MySQL / SQL Server),
**mapping sang Kafka Connect / Debezium semantic types**, và cách generator
**tự tạo Avro schema** để đăng ký lên Apicurio Schema Registry.

## Mục tiêu

```text
Cột DB (type, precision, scale, nullability)
        │
        ▼
  mappings.yaml   (rule: source_types + when → avro_ref)
        │
        ▼
  shared/catalog.yaml   (avro_ref → Avro / Connect field type)
        │
        ▼
  .avsc + artifact YAML  (group / artifact / version [/ references])
        │
        ▼
  Schema Registry
```

Pipeline này **không** dựa vào `auto-register=true` trên connector.
Schema được generate từ metadata cột, commit vào Git, rồi CI sync lên registry
(`auto-register=false` + `find-latest=true` phía connector).

## Layout

```text
core/types/
  README.md                 ← file này
  shared/
    catalog.yaml            ← thư viện Avro/Connect dùng chung
  oracle.yaml               ← index connector Oracle
  oracle/mappings.yaml
  postgres.yaml
  postgres/mappings.yaml
  mysql.yaml
  mysql/mappings.yaml
  mssql.yaml
  mssql/mappings.yaml
```

Mỗi connector có **một file index** (`{connector}.yaml`) trỏ tới:

| Key | Ý nghĩa |
| --- | --- |
| `connector` | `oracle` \| `postgres` \| `mysql` \| `mssql` |
| `defaults` | Giá trị Debezium giả định khi generate (`decimal.handling.mode`, `time.precision.mode`, …) |
| `files.catalog` | Catalog Avro/Connect (thường là `shared/catalog.yaml`) |
| `files.mappings` | Rule map kiểu nguồn → `avro_ref` |

## Catalog (`shared/catalog.yaml`)

Mỗi key trong catalog là một `avro_ref`. Có hai nhóm:

### 1. Inline field types

Generator **inline** type vào field Avro (primitive hoặc logical type):

| `avro_ref` | Avro | `connect.name` (nếu có) |
| --- | --- | --- |
| `string` / `int` / `long` / `float` / `double` / `bytes` / `boolean` | primitive | — |
| `decimal` | `bytes` + `logicalType: decimal` | `org.apache.kafka.connect.data.Decimal` |
| `date_days` | `int` | `io.debezium.time.Date` |
| `time_ms` / `micro_time` / `nano_time` | `int`/`long` | `io.debezium.time.Time` / `MicroTime` / `NanoTime` |
| `timestamp_ms` / `timestamp_us` / `timestamp_ns` | `long` | `Timestamp` / `MicroTimestamp` / `NanoTimestamp` |
| `zoned_timestamp` / `zoned_time` | `string` | `ZonedTimestamp` / `ZonedTime` |
| `json` / `xml` / `uuid` / `enum` / `enum_set` / `bits` / … | xem catalog | Debezium semantic types |

Với `decimal`, generator gắn thêm `precision` / `scale` từ metadata cột.

### 2. Registered named records (`register: true`)

Một số type là **record đặt tên** (ví dụ `VariableScaleDecimal`, `Geometry`).
Chúng được đăng ký **một lần** trong group `debezium`, rồi table schema
**reference** tới artifact đó (Apicurio `references[]`).

| `avro_ref` | Group | Artifact |
| --- | --- | --- |
| `variable_scale_decimal` | `debezium` | `VariableScaleDecimal` |
| `point` | `debezium` | `Point` |
| `geometry` | `debezium` | `Geometry` |
| `geography` | `debezium` | `Geography` |
| `sparse_vector` | `debezium` | `SparseVector` |

## Mappings (`*/mappings.yaml`)

Rule list, **first match wins**.

```yaml
rules:
  - source_types: [VARCHAR, VARCHAR2]
    avro_ref: string

  - source_types: [NUMBER, NUMERIC, DECIMAL]
    when: { scale: { gt: 0 } }
    avro_ref: decimal

  - source_types: [XMLTYPE]
    avro_ref: xml
```

### Cột input (column metadata)

Generator nhận mỗi cột dưới dạng:

```yaml
name: CREATED_AT
type: TIMESTAMP          # so khớp source_types (uppercase)
precision: 6             # optional
scale: 0                 # optional; NUMERIC/NUMBER
fractional_seconds: 6    # optional; TIMESTAMP(n) / DATETIME2(n) / TIME(n)
length: 1                # optional; BIT(n)
nullable: true
```

### Điều kiện `when`

| Predicate | Ý nghĩa |
| --- | --- |
| `scale.gt` / `scale.lte` | So scale |
| `scale.defined` | Scale có trong DDL (Postgres `NUMERIC(p,s)` vs `NUMERIC`) |
| `p_minus_s.lt` / `gte` | `precision - scale` (Oracle `NUMBER`) |
| `fractional_seconds.lte` / `gte` | Precision phần thập phân thời gian |
| `length.lte` / `gte` | Độ dài (BIT, …) |
| `precision.lte` / `gte` | Precision số (MySQL `FLOAT(p)`) |

### `supported: false`

Cột match rule này → generator **fail rõ ràng** (không im lặng map sai).
Cần đổi kiểu DB, loại cột khỏi CDC, hoặc thêm custom converter.

## Defaults theo connector

| Connector | `decimal.handling.mode` | `time.precision.mode` | Ghi chú |
| --- | --- | --- | --- |
| Oracle | `precise` | `adaptive` | `NUMBER` không scale → `variable_scale_decimal` |
| PostgreSQL | `precise` | `adaptive` | `NUMERIC` không scale → `variable_scale_decimal` |
| MySQL | `precise` | `adaptive_time_microseconds` | `TIMESTAMP` → `zoned_timestamp` |
| SQL Server | `precise` | `adaptive` | `DATETIME2(7)` → `timestamp_ns` |

Nếu connector thực tế dùng mode khác (`connect`, `string`, `isostring`, …),
phải đổi `defaults` + mappings cho khớp — nếu không Avro generate sẽ ** lệch **
schema Debezium emit lúc runtime.

## Ví dụ generate (Oracle)

Input bảng:

```yaml
# domain/domain1/customers/table.yaml
connector: oracle
groupId: domain1
table:
  schema: CORE
  name: CUSTOMERS
columns:
  - name: ID
    type: NUMBER
    precision: 38
    scale: 0
    nullable: false
  - name: NAME
    type: VARCHAR2
    nullable: true
  - name: AMOUNT
    type: NUMBER
    precision: 18
    scale: 2
    nullable: true
  - name: CREATED_AT
    type: TIMESTAMP
    fractional_seconds: 6
    nullable: true
```

Resolve:

| Cột | Rule | `avro_ref` | Avro field (rút gọn) |
| --- | --- | --- | --- |
| `ID` | `NUMBER` + `scale≤0` + `p_minus_s≥19` | `decimal` | `bytes` + Decimal(38,0) |
| `NAME` | `VARCHAR2` | `string` | `["null","string"]` |
| `AMOUNT` | `NUMBER` + `scale>0` | `decimal` | `["null", Decimal(18,2)]` |
| `CREATED_AT` | `TIMESTAMP` + `fs≤6` | `timestamp_us` | `["null", long MicroTimestamp]` |

Output record (Value) đăng ký như artifact:

```text
groupId:    domain1
artifactId: cdc.oracle.CORE.CUSTOMERS.Value   # hoặc theo naming convention team
artifactType: AVRO
version: "1"
```

Envelope / key / shared Debezium types follow CI order:

1. Group `debezium` shared (`VariableScaleDecimal`, `event.block`, Source, …)
2. Record `.Value`
3. Key
4. Envelope `-value` (references → Value + Source + block)

## Nullable

Nếu `nullable: true` (hoặc không có `NOT NULL`):

```json
{ "name": "NAME", "type": ["null", "string"], "default": null }
```

Nếu `nullable: false`:

```json
{ "name": "ID", "type": { "type": "bytes", "logicalType": "decimal", "...": "..." } }
```

## References (Apicurio)

Khi field dùng `register: true` type:

```yaml
versions:
  - version: "1"
    content: ./customers-value-v1.avsc
    references:
      - name: io.debezium.data.VariableScaleDecimal
        groupId: debezium
        artifactId: VariableScaleDecimal
        version: "1"
```

CI validate: `groupId` ∈ `groups/spec.yaml`, target artifact/version tồn tại,
`topo_order()` đăng ký shared trước dependents.

## Thêm connector / type mới

1. Tạo `{connector}.yaml` + `{connector}/mappings.yaml`.
2. Thêm `avro_ref` mới vào `shared/catalog.yaml` nếu chưa có.
3. Ghi `defaults` **khớp** config Debezium production.
4. Cập nhật bảng trong README này + thêm test case cột mẫu.
5. Không sửa mapping “cho tiện consumer” nếu lệch Debezium — consumer phải
   đọc đúng semantic type connector emit.

## Nguồn Debezium

- [Oracle data type mappings](https://debezium.io/documentation/reference/3.6/connectors/oracle.html#oracle-data-type-mappings)
- [PostgreSQL data type mappings](https://debezium.io/documentation/reference/3.6/connectors/postgresql.html#postgresql-data-types)
- [MySQL data type mappings](https://debezium.io/documentation/reference/3.6/connectors/mysql.html#mysql-data-types)
- [SQL Server data type mappings](https://debezium.io/documentation/reference/3.6/connectors/sqlserver.html#sqlserver-data-types)
- [Avro serialization](https://debezium.io/documentation/reference/3.6/configuration/avro.html)
