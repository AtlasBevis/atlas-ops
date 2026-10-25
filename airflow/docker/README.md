# Airflow Docker

## Fetching docker-compose.yaml

```sh
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.3.2/docker-compose.yaml'
```

## Installments

Single VM setup with `LocalExecutor` and an external PostgreSQL (no redis/celery worker).

### 1. Prepare PostgreSQL

```sql
CREATE DATABASE airflow;
CREATE USER airflow WITH PASSWORD 'xxx';
ALTER DATABASE airflow OWNER TO airflow;
-- PostgreSQL 15+
\c airflow
GRANT ALL ON SCHEMA public TO airflow;
```

Make sure the VM can reach the DB on port `5432` (firewall, `pg_hba.conf`).

### 2. Configure environment

```sh
mkdir -p dags logs plugins config
cp .env.example .env
echo "AIRFLOW_UID=$(id -u)" >> .env
```

Edit `.env`:

| Variable                                                    | Description                                                                                                                                                                      |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AIRFLOW_DB_CONN`                                           | `postgresql+psycopg2://<user>:<password>@<host>:5432/<db>` (URL-encode special chars in password, e.g. `@` -> `%40`)                                                             |
| `FERNET_KEY`                                                | Encrypts connections/variables in DB. Generate: `docker run --rm apache/airflow:3.3.2 python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `AIRFLOW__API_AUTH__JWT_SECRET`                             | Random secret, e.g. `openssl rand -hex 32`                                                                                                                                       |
| `AIRFLOW_BASE_URL`                                          | Public URL of the UI                                                                                                                                                             |
| `AIRFLOW_PARALLELISM`                                       | Max tasks running at the same time on the VM                                                                                                                                     |
| `_AIRFLOW_WWW_USER_USERNAME` / `_AIRFLOW_WWW_USER_PASSWORD` | Admin account created by `airflow-init`                                                                                                                                          |
| `AIRFLOW_REMOTE_LOGGING`                                    | Set `True` after creating connection `minio_conn`                                                                                                                                |

### 3. Initialize and start

```sh
docker compose config -q          # validate
docker compose up airflow-init    # migrate DB + create admin user
docker compose up -d
docker compose ps
```

UI: `http://<VM-IP>:8080`

### 4. Operations

```sh
docker compose logs -f airflow-scheduler
docker compose run --rm airflow-cli airflow dags list   # airflow CLI
docker compose down                                      # stop (DB is external, data kept)
```

Upgrade Airflow: change `AIRFLOW_IMAGE_NAME` in `.env`, then `docker compose up airflow-init && docker compose up -d`.

> Do not share the database with the K8s (Helm) deployment unless both use the same Airflow version — `airflow-init` migrates the schema.

## References

- [docker-compose](https://airflow.apache.org/docs/apache-airflow/3.3.2/howto/docker-compose/index.html#fetching-docker-compose-yaml)
