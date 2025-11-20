FROM eclipse-temurin:11-jre
WORKDIR /app
# The build is performed on the host (mvn package) so Dockerfile only needs the runtime image.
# Ensure `target/etl-rabbitmq-0.1.0.jar` exists before running `docker compose up --build`.
## Prefer the shaded jar produced by the Shade plugin to guarantee a Main-Class in the manifest
COPY target/etl-rabbitmq-0.1.0-shaded.jar /app/app.jar
ENTRYPOINT ["java","-jar","/app/app.jar"]
