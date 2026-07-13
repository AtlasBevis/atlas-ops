# OpenSearch


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

4. (optional) pull chart 

```shell
helm pull opensearch/opensearch --version 3.7.0 --untar
```
### Document

- [Github](https://github.com/opensearch-project/OpenSearch)
- [Install](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/helm/#install-opensearch-using-helm)
