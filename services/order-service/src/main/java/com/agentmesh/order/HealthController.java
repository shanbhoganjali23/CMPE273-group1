package com.agentmesh.order;

import java.sql.SQLException;
import java.util.Map;
import java.util.UUID;
import javax.sql.DataSource;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {
    private final ObjectProvider<DataSource> dataSources;

    public HealthController(ObjectProvider<DataSource> dataSources) {
        this.dataSources = dataSources;
    }

    @GetMapping("/health/live")
    public Map<String, String> live() {
        return Map.of("status", "UP");
    }

    @GetMapping("/health/ready")
    public ResponseEntity<?> ready() {
        DataSource source = dataSources.getIfAvailable();
        if (source == null) {
            return unavailable("DATABASE_NOT_CONFIGURED", "Order database configuration is required.");
        }
        try (var connection = source.getConnection()) {
            if (connection.isValid(1)) {
                return ResponseEntity.ok(Map.of("status", "UP"));
            }
        } catch (SQLException ignored) {
            // Driver errors may contain credentials/URLs; return only a safe summary.
        }
        return unavailable("DATABASE_UNAVAILABLE", "Order database is unavailable; check configuration and connectivity.");
    }

    private ResponseEntity<?> unavailable(String code, String message) {
        return ResponseEntity.status(503).body(Map.of(
                "code", code, "message", message, "retryable", true,
                "correlationId", UUID.randomUUID().toString()));
    }
}
