# Build from repository root: docker build -f services/order-service/Dockerfile .
FROM eclipse-temurin:21.0.13_9-jdk-jammy@sha256:a8b6e4da662e2ff710459e76be515a14746045c7a7493531d0901ca10a231501 AS build
# Keep the wrapper on its checksum-pinned ZIP distribution (no tar.gz fallback).
RUN apt-get update && apt-get install -y --no-install-recommends unzip && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY .mvn .mvn
COPY mvnw pom.xml ./
COPY libs/trace-context/pom.xml libs/trace-context/pom.xml
COPY services/order-service services/order-service
RUN ./mvnw -B -pl services/order-service -am package -DskipTests

FROM eclipse-temurin:21.0.13_9-jre-jammy@sha256:f1ad2fff1437cbcf7be96408f264ad5d2128fad9cf262f88f1827a84e60d246e
WORKDIR /app
COPY --from=build /workspace/services/order-service/target/order-service-0.1.0-SNAPSHOT.jar app.jar
ENV ORDER_BIND_HOST=0.0.0.0
USER 10001:10001
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
