package com.example.etl.utils;

import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;

public class RabbitMqUtil {
    public static Connection newConnection() throws Exception {
        ConnectionFactory factory = new ConnectionFactory();
        String host = System.getenv().getOrDefault("RABBITMQ_HOST", "localhost");
        String user = System.getenv().getOrDefault("RABBITMQ_DEFAULT_USER", "guest");
        String pass = System.getenv().getOrDefault("RABBITMQ_DEFAULT_PASS", "guest");
        factory.setHost(host);
        factory.setUsername(user);
        factory.setPassword(pass);
        return factory.newConnection();
    }
}
