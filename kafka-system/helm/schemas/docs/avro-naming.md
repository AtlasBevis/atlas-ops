# Avro auto-transform rules

Generator (`scripts/versions/`, `scripts/artifacts/`) áp dụng các quy tắc dưới đây
khi biến YAML cột / topic thành Avro + artifact Apicurio. **Không** sửa tay
`.avsc` — chỉ sửa YAML nguồn hoặc mapping.

## Spec Names (chuẩn)

Nguồn: [Apache Avro Specification — Names](https://avro.apache.org/docs/++version++/specification/#names)

Mỗi **name** (record / enum / fixed name, field name, enum symbol) phải:

- bắt đầu bằng `[A-Za-z_]`
- phần còn lại chỉ `[A-Za-z0-9_]`

Regex một name (spec / apache-avro):

```text
^[A-Za-z_][A-Za-z0-9_]*$
```

**Namespace** = chuỗi name nối bằng `.` (hoặc rỗng = null namespace):

```text
^([A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*)?$
```

Equality case-sensitive. Null namespace không được nằm giữa các đoạn có dấu chấm.

Code: `AVRO_NAME_RE`, `AVRO_NAMESPACE_RE`, `avro_name_segment`, `avro_namespace`
trong `scripts/versions/version.py`.

---

## 1. Topic Kafka → Avro namespace (auto replace)

| Khái niệm | Nguồn | Ví dụ (`topicPrefix: cdc.prod.card-bo`) |
| --- | --- | --- |
| Kafka topic | `{topicPrefix}.{schema}.{table}` | `cdc.prod.card-bo.MAIN.ACC_ACCOUNT` |
| Avro namespace | `avro_namespace(topic)` | `cdc.prod.card_bo.MAIN.ACC_ACCOUNT` |
| `connect.name` | `{namespace}.{Key\|Value\|Envelope}` | `cdc.prod.card_bo.MAIN.ACC_ACCOUNT.Value` |

### Thuật toán `avro_namespace`

1. `strip` / bỏ `.` đầu–cuối.
2. Split theo `.` → từng **segment**.
3. Mỗi segment qua `avro_name_segment`:
   - Regex thay thế: `[^A-Za-z0-9_]+` → `_`  
     (gom run ký tự lạ: `-`, `$`, khoảng trắng, …)
   - Segment rỗng sau replace → `_`
   - Ký tự đầu là digit → prefix `_` (spec cấm bắt đầu bằng số)
4. Join bằng `.`, validate bằng `AVRO_NAMESPACE_RE`.

Ví dụ:

| Topic segment | Avro name |
| --- | --- |
| `card-bo` | `card_bo` |
| `foo$bar` | `foo_bar` |
| `9table` | `_9table` |
| `__heartbeat` | `__heartbeat` (đã hợp lệ) |

Kafka / Apicurio **artifactId** `-key` / `-value` vẫn dùng **topic gốc** (được phép có `-`).
Chỉ **Avro `namespace`**, **`connect.name`**, và artifact **`.Value`** dùng form đã sanitize.

Nếu để nguyên `card-bo` trong namespace → Apicurio `VALIDITY=FULL` trả
`RuleViolationException` / *Syntax violation for Avro artifact* (HTTP 400).

---

## 2. ArtifactId (Apicurio)

Cùng một bảng tạo **ba** artifact trong group domain:

| ArtifactId | Dùng topic hay namespace? | Vai trò |
| --- | --- | --- |
| `{topic}-key` | **topic** (có `-`) | PK record `Key` |
| `{namespace}.Value` | **namespace** (đã sanitize) | Row payload `Value` |
| `{topic}-value` | **topic** (có `-`) | Envelope Debezium |

Ví dụ:

```text
cdc.prod.card-bo.MAIN.ACC_ACCOUNT-key
cdc.prod.card_bo.MAIN.ACC_ACCOUNT.Value
cdc.prod.card-bo.MAIN.ACC_ACCOUNT-value
```

Envelope `references[]` trỏ `artifactId` = `{namespace}.Value` (cùng FQN với
type trong field `before` / `after`).

Heartbeat (nếu bật): `{heartbeatPrefix}.{topicPrefix}-key` /
`-value` — schema dùng namespace Debezium cố định
(`io.debezium.connector.common`), không derive từ topic.

---

## 3. Nullability

| YAML | Avro field |
| --- | --- |
| `keys:` (mặc định) | không null (PK) |
| `values:` không ghi `nullable` | `["null", <type>]` + `"default": null` |
| `values:` `nullable: false` | `<type>` thuần |
| `values:` `nullable: true` | giống mặc định nullable |

---

## 4. DB type → Avro (tóm tắt)

Chi tiết rule: [core/types/README.md](../core/types/README.md) +
`core/types/<db>/mappings.yaml`.

Generator **không** yêu cầu viết Avro type trong YAML cột — chỉ DB type
(`NUMBER(12)`, `VARCHAR2(8)`, `DATE`, …).

Vài map hay gặp (Oracle, defaults Debezium 3.6):

| DB | Avro (rút gọn) |
| --- | --- |
| `VARCHAR2` / `CHAR` / … | `string` |
| `NUMBER(p)` scale 0, p≤2 | `int` |
| `NUMBER(p)` scale 0, p≤4 | `int` |
| `NUMBER(p)` scale 0, p≤9 | `int` |
| `NUMBER(p)` scale 0, p≤18 | `long` |
| `NUMBER(p,s)` s>0 | `bytes` + `decimal(p,s)` |
| `NUMBER` (không scale) | `VariableScaleDecimal` (ref group `debezium`) |
| `DATE` | `long` + `io.debezium.time.Timestamp` |
| `TIMESTAMP(6)` | `long` + `MicroTimestamp` |

---

## 5. Record names cố định

Trong mỗi namespace bảng:

| Record `name` | Artifact |
| --- | --- |
| `Key` | `{topic}-key` |
| `Value` | `{namespace}.Value` |
| `Envelope` | `{topic}-value` |

`Key` / `Value` / `Envelope` đã khớp `[A-Za-z_][A-Za-z0-9_]*`.
Không đổi tên record theo tên bảng — bảng nằm trong **namespace**.

---

## 6. Checklist khi thêm bảng

1. `topicPrefix` đúng môi trường (`cdc.prod.card-bo`, …) — **được phép có `-`**.
2. Không viết namespace Avro trong YAML; CI gọi `avro_namespace`.
3. 400 *Syntax violation* → kiểm tra còn đưa ký tự ngoài `[A-Za-z0-9_]` vào
   `namespace` / `.Value` artifactId không.
4. Đổi schema đã publish → **bump version** (`v2.yaml`).

---

## Tham chiếu

| | |
| --- | --- |
| Spec | https://avro.apache.org/docs/++version++/specification/#names |
| `avro_namespace` / regex | `scripts/versions/version.py` |
| empty artifactIds | `scripts/artifacts/artifact.py` → `debezium_artifact_ids` |
| DB → Avro | `scripts/versions/mapping.py` |
