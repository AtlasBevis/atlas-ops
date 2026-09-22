# Opensearch Stack


## Install

1. Add opensearch helm-charts repository to Helm:

```shell
helm repo add opensearch https://opensearch-project.github.io/helm-charts/
```

2. Update the available charts locally from charts repositories:

```shell
helm repo update
```

3. To search for the OpenSearch-related Helm charts:

```shell
helm search repo opensearch
```

## Opensearch

```shell
helm pull opensearch/opensearch --version 3.7.0 --untar
```

## Opensearch Dashboard

```shell
helm pull opensearch/opensearch-dashboards --version 3.7.0 --untar
```

## Setup

### Create Index Template

```sh
PUT _index_template/app-prod-data-api-gw-tpl
{
  "index_patterns": ["app-prod-data-api-gw*"],
  "data_stream": {
    "timestamp_field": {
      "name": "timestamp"
    }
  },
  "priority": 200,
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "refresh_interval": "30s"
    },
    "mappings": {
      "properties": {
        "timestamp": {
          "type": "date"
        }
      }
    }
  }
}
```

### Create Data Stream

```sh
PUT _data_stream/app-prod-data-api-gw
# Expect: { "acknowledged": true }.
```

### Verify 

```sh
GET _data_stream/app-prod-data-api-gw
GET _cat/indices/.ds-app-prod-data-api-gw*?v
GET _cluster/health?pretty
```

## Document

- [Home](https://docs.opensearch.org/latest/)
- [Github](https://github.com/opensearch-project/OpenSearch)
- [Install](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/helm/#install-opensearch-using-helm)
