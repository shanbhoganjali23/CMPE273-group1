package com.agentmesh.order;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertTimeout;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = {
                "server.address=127.0.0.1",
                "agentmesh.database.enabled=true",
                "agentmesh.database.url=jdbc:postgresql://127.0.0.1:1/agentmesh_test",
                "agentmesh.database.username=test",
                "agentmesh.database.password="
        })
class DatabaseUnavailableTest {
    @LocalServerPort int port;
    @Autowired TestRestTemplate client;

    @Test void configuredButUnreachableDatabaseDoesNotKillProcess() {
        var live = client.getForEntity("http://127.0.0.1:" + port + "/health/live", String.class);
        assertThat(live.getStatusCode().value()).isEqualTo(200);
        assertTimeout(Duration.ofSeconds(5), () -> {
            var ready = client.getForEntity("http://127.0.0.1:" + port + "/health/ready", String.class);
            assertThat(ready.getStatusCode().value()).isEqualTo(503);
            assertThat(ready.getBody()).contains("DATABASE_UNAVAILABLE");
        });
    }
}
