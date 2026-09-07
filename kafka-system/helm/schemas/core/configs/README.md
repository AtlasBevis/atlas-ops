# Config

## Admin Rules

string (RuleType)

Enum: `VALIDITY`, `COMPATIBILITY`, `INTEGRITY`

- VALIDITY: Ensure that content is valid when creating an artifact or artifact version. (Kiểm tra tính hợp lệ)
- COMPATIBILITY: Enforce a compatibility level when creating a new artifact version. (Kiểm tra tính tương thích)
- INTEGRITY: Enforce artifact reference integrity when creating an artifact or artifact version. (Kiểm tra tính toàn vẹn)

common config:

- Validity: Full
- COMPATIBILITY: Backward (new schema must be compatible with old schema)
- INTEGRITY: None

1. List current global rules

```sh
curl --location 'https://domain.com.vn/apis/registry/v3/admin/rules'
```

2. List global rules configuration

```sh
# Rule Type get from list global rules
curl --location 'https://domain.com.vn/apis/registry/v3/admin/rules/{{ruleType}}'
```

## References

- [API Specs](https://www.apicur.io/registry/docs/apicurio-registry/3.0.x/assets-attachments/registry-rest-api.htm#tag/Admin)
