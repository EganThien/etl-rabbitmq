package com.example.etl.utils;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DbUtil {
    private static final String DEFAULT_HOST = "localhost";
    private static final String DEFAULT_PORT = "3306";

    public static Connection getConnection() throws SQLException {
        String host = System.getenv().getOrDefault("MYSQL_HOST", DEFAULT_HOST);
        String port = System.getenv().getOrDefault("MYSQL_PORT", DEFAULT_PORT);
        String database = System.getenv().getOrDefault("MYSQL_DATABASE", "etl_db");
        String user = System.getenv().getOrDefault("MYSQL_USER", "etl");
        String password = System.getenv().getOrDefault("MYSQL_PASSWORD", "etlpass");

        String jdbcUrl = String.format("jdbc:mysql://%s:%s/%s?useSSL=false&allowPublicKeyRetrieval=true", host, port, database);
        return DriverManager.getConnection(jdbcUrl, user, password);
    }
}
