
### Create Data Stream

1. Create Policy retention 30d

```sh
PUT _plugins/_ism/policies/logs-kafka-connect-policy
{
  "policy": {
    "description": "Kafka Connect logs retention policy",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [
          { "rollover": { "min_index_age": "1d" } }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": { "min_index_age": "30d" }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          { "delete": {} }
        ],
        "transitions": []
      }
    ],
    "ism_template": {
      "index_patterns": ["logs-kafka-connect-*"],
      "priority": 200
    }
  }
}
```
2. Create Index Template

```sh
PUT _index_template/logs-kafka-connect-template
{
  "index_patterns": ["logs-kafka-connect-*"],
  "priority": 200,
  "data_stream": {},
  "template": {
    "settings": {
      "number_of_shards": "1",
      "number_of_replicas": "1",
      "plugins.index_state_management.policy_id": "logs-kafka-connect-policy"
    },
    "mappings": {
      "dynamic": true,
      "properties": {
        "@timestamp": { "type": "date" },
        "ecs.version": { "type": "keyword" },
        "log.level": { "type": "keyword" },
        "log.logger": { "type": "keyword" },
        "process.thread.name": { "type": "keyword" },
        "message": { "type": "match_only_text" }
      }
    }
  }
}
```

3. Create Data Stream

```sh
PUT _data_stream/logs-kafka-connect-uat
```

4. Verify Data Stream

```sh
GET _data_stream/logs-kafka-connect-uat
GET _plugins/_ism/explain/.ds-logs-kafka-connect-uat-*
```