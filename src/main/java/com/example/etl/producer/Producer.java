package com.example.etl.producer;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;

public class Producer {
    // Placeholder: implement CSV reader and RabbitMQ publisher
    public static void main(String[] args) throws Exception {
        System.out.println("Producer started (placeholder). Implement CSV -> RabbitMQ publish logic here.");
        Path p = Path.of("src/main/resources/data/employee.csv");
        if (Files.exists(p)){
            try (Stream<String> lines = Files.lines(p)){
                lines.limit(5).forEach(System.out::println);
            }
        }
    }
}
