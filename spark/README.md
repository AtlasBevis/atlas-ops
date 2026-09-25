# Apache Spark Operator

## Installment

1. Add Chart repo

```sh
helm repo add spark https://apache.github.io/spark-kubernetes-operator
helm repo update
```

2. Install 

```sh
helm install spark spark/spark-kubernetes-operator   --namespace spark-operator   --create-namespace
```

or pull chart

```sh
helm pull spark/spark-kubernetes-operator --version 1.8.0 --untar
```


### Document

- [Spark](https://sparkingscala.com/)