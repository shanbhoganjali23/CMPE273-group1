package com.agentmesh.order;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = {"agentmesh.database.enabled=false", "agentmesh.database.url=", "server.address=127.0.0.1"})
class ApplicationTest {
    @LocalServerPort int port;
    @Autowired TestRestTemplate client;

    @Test void startsWithoutInfrastructureButReportsNotReady() {
        var live = client.getForEntity("http://127.0.0.1:" + port + "/health/live", String.class);
        assertThat(live.getStatusCode().value()).isEqualTo(200);
        var ready = client.getForEntity("http://127.0.0.1:" + port + "/health/ready", String.class);
        assertThat(ready.getStatusCode().value()).isEqualTo(503);
        assertThat(ready.getBody()).contains("DATABASE_NOT_CONFIGURED");
    }

    @Test void businessEndpointsAreNotImplemented() {
        var result = client.getForEntity("http://127.0.0.1:" + port + "/orders/00000000-0000-4000-8000-000000000001", String.class);
        assertThat(result.getStatusCode().value()).isEqualTo(404);
    }
}
