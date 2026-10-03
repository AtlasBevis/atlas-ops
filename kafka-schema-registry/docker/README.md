# Apicurio Docker

## Back End Server (REST API)

1. Pull the Apicurio Registry image

```sh
docker pull apicurio/apicurio-registry:3.3.3
```

2. Run the Apicurio Registry image


```sh
docker run -it -p 8080:8080 apicurio/apicurio-registry:3.3.3
```

## UI

1. Pull the Apicurio Registry UI image

```sh
docker pull apicurio/apicurio-registry-ui:3.3.3
```

2. Run the Apicurio Registry UI image

```sh
docker run -it -p 8888:8080 apicurio/apicurio-registry-ui:3.3.3
```

## References

- [Docker](https://www.apicur.io/registry/getting-started/)