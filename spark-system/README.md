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

## Example 

1. SparkApplication

```sh
apiVersion: spark.apache.org/v1
kind: SparkApplication
metadata:
  name: pi
spec:
  # Entry point for the app
  mainClass: "org.apache.spark.examples.SparkPi"
  jars: "local:///opt/spark/examples/jars/spark-examples.jar"
  sparkConf:
    spark.dynamicAllocation.enabled: "true"
    spark.dynamicAllocation.maxExecutors: "3"
    spark.kubernetes.authenticate.driver.serviceAccountName: "spark"
    spark.kubernetes.container.image: "apache/spark:4.2.0-scala"
  applicationTolerations:
    resourceRetainPolicy: OnFailure
    ttlAfterStopMillis: 10000
  runtimeVersions:
    sparkVersion: "4.2.0"
```

### Document

- [Spark](https://sparkingscala.com/)
- [Github](https://github.com/apache/spark-kubernetes-operator)
- [Docs](https://github.com/apache/spark-kubernetes-operator/tree/main/docs)
- [Architecture](https://github.com/apache/spark-kubernetes-operator/blob/main/docs/architecture.md)
- [SparkApplication](https://github.com/apache/spark-kubernetes-operator/blob/main/docs/spark_custom_resources.md)