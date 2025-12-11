FROM eclipse-temurin:11-jre
WORKDIR /app
# The build is performed on the host (mvn package) so Dockerfile only needs the runtime image.
# The shaded jar replaces the original, so we just copy etl-rabbitmq-0.2.0.jar
COPY target/etl-rabbitmq-0.2.0.jar /app/app.jar
ENTRYPOINT ["java","-jar","/app/app.jar"]
