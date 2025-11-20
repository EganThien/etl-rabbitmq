# etl-rabbitmq
ETL pipeline sá»­ dá»¥ng RabbitMQ Ä‘á»ƒ ingest, transform vÃ  validate dá»¯ liá»‡u staging â†’ main.

ETL-RabbitMQ-Integration-System

Má»¥c tiÃªu: MÃ´ phá»ng pipeline ETL Ä‘á»c CSV -> publish lÃªn RabbitMQ -> consumer validate -> lÆ°u Staging DB -> transform -> load Main DB.

YÃªu cáº§u trÆ°á»›c khi cháº¡y:
- Java 11+
- Maven
- Docker Desktop (Ä‘Ã£ cÃ i) vÃ  docker compose

Cháº¡y stack (RabbitMQ + MySQL):

```powershell
cd etl-rabbitmq
docker compose up -d
```

Kiá»ƒm tra RabbitMQ Management UI: http://localhost:15672 (user/pass tá»« `.env`)

CÃ i dependencies & build:

```powershell
mvn -v
mvn clean package -DskipTests
```

Cháº¡y á»©ng dá»¥ng (vÃ­ dá»¥ cháº¡y Producer/Consumer tá»« IDE hoáº·c jar):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application"
```

VÃ­ dá»¥ cháº¡y Producer (publish CSV -> queues):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="producer"
```

VÃ­ dá»¥ cháº¡y Employee Consumer (consume employee messages -> staging DB):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="employee-consumer"
```

VÃ­ dá»¥ cháº¡y Order Consumer (consume order messages -> staging DB):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="order-consumer"
```

VÃ­ dá»¥ cháº¡y Transform & Load (staging -> main):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="transform"
```

Run full pipeline with Docker Compose
-----------------------------------
You can build the application image and run the whole pipeline (RabbitMQ, MySQL, producer, consumers, transform) using docker compose. This will build the Java app image (multi-stage) and start the services.

Start full stack (build image and run all services):
```powershell
docker compose up --build -d
```

Notes:
- `app-producer` will run once (command `producer`) and exit; consumers (`app-employee-consumer`, `app-order-consumer`) run continuously.
- To run only the producer (one-off):
```powershell
docker compose run --rm app-producer
```
- To view logs for consumers:
```powershell
docker compose logs -f app-employee-consumer
docker compose logs -f app-order-consumer
```
- To run transform container once:
```powershell
docker compose run --rm app-transform
```

Dashboard (optional)
-------------------
I added a small read-only dashboard service that shows RabbitMQ queue sizes and table counts. After starting the stack, open:

http://localhost:8080

To run the dashboard with the rest of the stack (it is included in `docker compose up --build -d`), or start it separately:

```powershell
docker compose up --build -d etl-dashboard
```

File quan trá»ng:
- `docker-compose.yml` : khá»Ÿi RabbitMQ vÃ  MySQL
- `src/main/resources/data` : sample CSV
- `src/main/resources/sql/create_tables.sql` : script táº¡o báº£ng

Tiáº¿p theo: TÃ´i sáº½ táº¡o skeleton Maven project vÃ  cÃ¡c class Java cÆ¡ báº£n.
 f231e4a (ETL demo: add project files, scripts and docs)
