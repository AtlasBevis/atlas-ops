# Oracle Docker


## List Database Images

1. Download Oracle Software Delivery Cloud

```sh
# after you downloaded 
V46095-01_1of2.zip
V46095-01_2of2.zip

# then rename its
linuxamd64_12102_database_1of2.zip
linuxamd64_12102_database_2of2.zip
```

1. Clone repo

```sh
git clone github.com/oracle/docker-images
```

2. Copy database images

```sh
# copy buildContainerImage.sh
# https://github.com/oracle/docker-images/blob/main/OracleDatabase/SingleInstance/dockerfiles/buildContainerImage.sh
# Copy original 
cd OracleDatabase/SingleInstance/dockerfiles/<version>

```
## Refereces

- [Repo Images](https://github.com/oracle/docker-images)