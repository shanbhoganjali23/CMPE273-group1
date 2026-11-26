package com.agentmesh.order;

import java.sql.Connection;
import java.sql.SQLException;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(HealthController.class)
class HealthControllerTest {
    @Autowired MockMvc mvc;
    @MockitoBean DataSource source;

    @Test void liveDoesNotRequireDatabase() throws Exception {
        mvc.perform(get("/health/live")).andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
        verifyNoInteractions(source);
    }

    @Test void readinessChecksDatabaseAndClosesConnection() throws Exception {
        Connection connection = mock(Connection.class);
        when(source.getConnection()).thenReturn(connection);
        when(connection.isValid(1)).thenReturn(true);
        mvc.perform(get("/health/ready")).andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
        verify(connection).close();
    }

    @Test void unavailableDatabaseReturnsSafeContractError() throws Exception {
        when(source.getConnection()).thenThrow(new SQLException("secret-password"));
        mvc.perform(get("/health/ready")).andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.code").value("DATABASE_UNAVAILABLE"))
                .andExpect(jsonPath("$.retryable").value(true))
                .andExpect(jsonPath("$.correlationId").isString())
                .andExpect(content().string(org.hamcrest.Matchers.not(org.hamcrest.Matchers.containsString("secret-password"))));
    }

    @Test void invalidConnectionIsNotReady() throws Exception {
        Connection connection = mock(Connection.class);
        when(source.getConnection()).thenReturn(connection);
        when(connection.isValid(1)).thenReturn(false);
        mvc.perform(get("/health/ready")).andExpect(status().isServiceUnavailable());
        verify(connection).close();
    }
}
