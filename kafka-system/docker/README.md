# Local Kafka Docker

Kafka exposes these listeners:

- `localhost:9092`: external `PLAINTEXT` (existing)
- `localhost:9094`: external `SASL_PLAINTEXT` with `SCRAM-SHA-512`
- `kafka:29092`: Docker network internal `PLAINTEXT`, for Kafka UI and administration

`SASL_PLAINTEXT` authenticates clients but does not encrypt traffic. Use it only on a trusted network. For encrypted connections, configure `SASL_SSL` and TLS certificates.

## Create a SCRAM user

Start or recreate the broker after changing the compose file:

```powershell
docker compose up -d kafka
```

Create a user credential in the KRaft metadata using the internal admin listener:

```powershell
docker exec kafka kafka-configs --bootstrap-server localhost:29092 --alter --add-config "SCRAM-SHA-512=[password=ChangeThisPassword]" --entity-type users --entity-name app-user
```

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
