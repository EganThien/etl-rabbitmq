package com.example.etl.producer;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
import com.example.etl.models.Employee;
import com.example.etl.models.OrderDetail;
import com.example.etl.utils.RabbitMqUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.opencsv.CSVReader;
import com.opencsv.exceptions.CsvValidationException;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.MessageProperties;

import java.io.FileReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class Producer {
    // CSV -> RabbitMQ publisher
    public static void main(String[] args) throws Exception {
        System.out.println("Producer started: publishing CSV files to RabbitMQ queues");
        ObjectMapper mapper = new ObjectMapper();

        // publish employee.csv -> employee_queue
        Path empPath = Path.of("src/main/resources/data/employee.csv");
        if (Files.exists(empPath)) {
            publishEmployees(empPath, mapper);
        } else {
            System.out.println("employee.csv not found at " + empPath.toAbsolutePath());
        }

        // publish order_detail.csv -> order_queue
        Path odPath = Path.of("src/main/resources/data/order_detail.csv");
        if (Files.exists(odPath)) {
            publishOrderDetails(odPath, mapper);
        } else {
            System.out.println("order_detail.csv not found at " + odPath.toAbsolutePath());
        }

        System.out.println("Producer finished.");
    }

    private static void publishEmployees(Path csvPath, ObjectMapper mapper) throws Exception {
        try (Connection conn = RabbitMqUtil.newConnection(); Channel ch = conn.createChannel()) {
            String q = "employee_queue";
            ch.queueDeclare(q, true, false, false, null);
            try (Reader r = new FileReader(csvPath.toFile()); CSVReader cr = new CSVReader(r)) {
                String[] header = cr.readNext();
                String[] row;
                int sent = 0;
                while ((row = cr.readNext()) != null) {
                    Employee e = new Employee();
                    // Assume columns: employeeId,fullName,email
                    if (row.length > 0) e.setEmployeeId(row[0]);
                    if (row.length > 1) e.setFullName(row[1]);
                    if (row.length > 2) e.setEmail(row[2]);
                    byte[] body = mapper.writeValueAsString(e).getBytes(StandardCharsets.UTF_8);
                    ch.basicPublish("", q, MessageProperties.PERSISTENT_TEXT_PLAIN, body);
                    sent++;
                }
                System.out.println("Published " + sent + " employee messages to " + q);
            }
        }
    }

    private static void publishOrderDetails(Path csvPath, ObjectMapper mapper) throws Exception {
        try (Connection conn = RabbitMqUtil.newConnection(); Channel ch = conn.createChannel()) {
            String q = "order_queue";
            ch.queueDeclare(q, true, false, false, null);
            try (Reader r = new FileReader(csvPath.toFile()); CSVReader cr = new CSVReader(r)) {
                String[] header = cr.readNext();
                String[] row;
                int sent = 0;
                while ((row = cr.readNext()) != null) {
                    OrderDetail od = new OrderDetail();
                    // Assume columns: orderId,productId,quantity,price
                    if (row.length > 0) od.setOrderId(row[0]);
                    if (row.length > 1) od.setProductId(row[1]);
                    if (row.length > 2) {
                        try { od.setQuantity(Integer.parseInt(row[2])); } catch (NumberFormatException ex) { od.setQuantity(0); }
                    }
                    if (row.length > 3) {
                        try { od.setPrice(Double.parseDouble(row[3])); } catch (NumberFormatException ex) { od.setPrice(0.0); }
                    }
                    byte[] body = mapper.writeValueAsString(od).getBytes(StandardCharsets.UTF_8);
                    ch.basicPublish("", q, MessageProperties.PERSISTENT_TEXT_PLAIN, body);
                    sent++;
                }
                System.out.println("Published " + sent + " order_detail messages to " + q);
            }
        }
    }
}
