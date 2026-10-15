# Local Kafka Docker

Kafka exposes these listeners:

- `localhost:9092`: external `PLAINTEXT` (existing)
- `localhost:9094`: external `SASL_PLAINTEXT` with `SCRAM-SHA-512`
- `kafka:29092`: Docker network internal `PLAINTEXT`, for Kafka UI and administration

The Confluent image requires `KAFKA_OPTS` to point to a JAAS config file when an advertised listener uses SASL. Compose mounts `config/kafka_server_jaas.conf`; it defines the required `KafkaServer` SCRAM login context. SCRAM users are created in KRaft metadata with `kafka-configs` below.

`SASL_PLAINTEXT` authenticates clients but does not encrypt traffic. Use it only on a trusted network. For encrypted connections, configure `SASL_SSL` and TLS certificates.

## Create a SCRAM user

After changing the compose file, run these commands from `kafka-system/docker` (the directory containing `docker-compose.yml`). `down` stops and removes the containers; the broker data is bind-mounted at `./data` and remains in place:

```powershell
docker compose down
docker compose up -d kafka
docker compose ps
```

Wait until the `kafka` service is healthy before creating the user. If you normally start Kafka UI too, use `docker compose up -d` instead of `docker compose up -d kafka`.

Create a user credential in the KRaft metadata using the internal admin listener:

```powershell
docker exec kafka kafka-configs --bootstrap-server localhost:29092 --alter --add-config "SCRAM-SHA-512=[password=ChangeThisPassword]" --entity-type users --entity-name app-user
```

You can run that command again with a different password to update the user's SCRAM credential. The first user command is run after the broker starts; it does not need a pre-created admin user because it connects through the internal Docker-only listener.

Replace the sample username and password. Run the command again with `--delete-config SCRAM-SHA-512` to remove that user's SCRAM credential:

```powershell
docker exec kafka kafka-configs --bootstrap-server localhost:29092 --alter --delete-config SCRAM-SHA-512 --entity-type users --entity-name app-user
```

The user can authenticate on port `9094`. Example `client.properties`:

```properties
security.protocol=SASL_PLAINTEXT
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username="app-user" password="ChangeThisPassword";
```

Use the properties file with Kafka CLI tools via `--command-config client.properties`. Creating a user only sets authentication credentials; grant Kafka ACLs separately if authorization is enabled.
