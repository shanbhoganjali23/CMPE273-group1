package com.agentmesh.order;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DatabaseConfiguration {
    @Bean(destroyMethod = "close")
    @ConditionalOnProperty(name = "agentmesh.database.enabled", havingValue = "true")
    HikariDataSource dataSource(
            @Value("${agentmesh.database.url}") String url,
            @Value("${agentmesh.database.username}") String username,
            @Value("${agentmesh.database.password}") String password) {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(url);
        config.setUsername(username);
        config.setPassword(password);
        config.setMaximumPoolSize(2);
        config.setMinimumIdle(0);
        config.setConnectionTimeout(2000);
        config.setValidationTimeout(1000);
        config.setInitializationFailTimeout(-1);
        config.addDataSourceProperty("connectTimeout", "2");
        config.addDataSourceProperty("socketTimeout", "2");
        return new HikariDataSource(config);
    }
}
