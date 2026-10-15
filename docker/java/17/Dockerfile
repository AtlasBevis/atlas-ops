FROM maven:3.8.4-openjdk-17 as build

LABEL maintainer="dev.binhtt@gmail.com"

WORKDIR /build

COPY . .

RUN mvn install -DskipTests=true

FROM eclipse-temurin:17-jre-alpine

RUN unlink /etc/localtime;ln -s  /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime

WORKDIR /run

COPY --from=build /build/src/target/*.jar ./app.jar

EXPOSE 8888

ENV JAVA_OPTIONS="-Xmx2048m -Xms256m"

ENTRYPOINT java -jar $JAVA_OPTIONS /run/app.jar