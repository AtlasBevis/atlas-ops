# Config

## Admin Rules

string (RuleType)

Enum: `VALIDITY`, `COMPATIBILITY`, `INTEGRITY`

- VALIDITY: Ensure that content is valid when creating an artifact or artifact version. (Kiểm tra tính hợp lệ)
- COMPATIBILITY: Enforce a compatibility level when creating a new artifact version. (Kiểm tra tính tương thích)
- INTEGRITY: Enforce artifact reference integrity when creating an artifact or artifact version. (Kiểm tra tính toàn vẹn)

common config:

- VALIDITY: Full
- COMPATIBILITY: Backward_Transitive (new version must be compatible with **every** prior
  version, not just the latest — safe when consumers lag producers by more than one
  version). Never use `NONE` in production.
- INTEGRITY: None (kept `NONE` — `ALL_REFS_MAPPED` would break the heartbeat's inlined
  fields; see `docs/CLAUDE.md`)

1. List current global rules

```sh
curl --location 'https://domain.com.vn/apis/registry/v3/admin/rules'
```

2. List global rules configuration

```sh
# Rule Type get from list global rules
curl --location 'https://domain.com.vn/apis/registry/v3/admin/rules/{{ruleType}}'
```

## Version states (per-version, not a global rule)

`ENABLED` / `DEPRECATED` / `DISABLED` control whether **consumers** can fetch one
version — separate from the compatibility/validity rules above, and separate
from content (state changes never touch the registered schema bytes).
Set via `table.key.versions[].state` / `table.value.versions[].state` in the
table index YAML; CI reconciles it every run (`core/versions/state.py`).
See [../docs/CLAUDE.md](../docs/CLAUDE.md) → "Version lifecycle".

## References

- [API Specs](https://www.apicur.io/registry/docs/apicurio-registry/3.0.x/assets-attachments/registry-rest-api.htm#tag/Admin)
- [Schema lifecycle best practices](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html)
