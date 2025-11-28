package com.example.etl.producer;

public class CSVProducer {
    public static void main(String[] args) throws Exception {
        Producer.main(args);
    }
}
package com.example.etl.producer;

import com.example.etl.models.Employee;
import com.example.etl.models.OrderDetail;
import com.example.etl.utils.RabbitMqUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.opencsv.CSVReader;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;

import java.io.FileReader;
import java.nio.file.Files;
import java.nio.file.Path;

public class CSVProducer {
    private static final String EMPLOYEE_QUEUE = "employee_queue";
    private static final String ORDER_QUEUE = "order_queue";

    public static void main(String[] args) throws Exception {
        ObjectMapper mapper = new ObjectMapper();

        try (Connection conn = RabbitMqUtil.newConnection(); Channel ch = conn.createChannel()) {
            ch.queueDeclare(EMPLOYEE_QUEUE, true, false, false, null);
            ch.queueDeclare(ORDER_QUEUE, true, false, false, null);

            Path empPath = Path.of("src/main/resources/data/employee.csv");
            if (Files.exists(empPath)) {
                try (CSVReader reader = new CSVReader(new FileReader(empPath.toFile()))) {
                    String[] header = reader.readNext();
                    String[] line;
                    while ((line = reader.readNext()) != null) {
                        Employee e = new Employee();
                        e.setEmployeeId(line[0]);
                        e.setFullName(line[1]);
                        e.setEmail(line[2]);
                        byte[] payload = mapper.writeValueAsBytes(e);
                        ch.basicPublish("", EMPLOYEE_QUEUE, null, payload);
                        System.out.println("Published employee: " + e.getEmployeeId());
                    }
                }
            }

            Path orderPath = Path.of("src/main/resources/data/order_detail.csv");
            if (Files.exists(orderPath)) {
                try (CSVReader reader = new CSVReader(new FileReader(orderPath.toFile()))) {
                    String[] header = reader.readNext();
                    String[] line;
                    while ((line = reader.readNext()) != null) {
                        OrderDetail od = new OrderDetail();
                        od.setOrderId(line[0]);
                        od.setProductId(line[1]);
                        od.setQuantity(Integer.parseInt(line[2]));
                        od.setPrice(Double.parseDouble(line[3]));
                        byte[] payload = mapper.writeValueAsBytes(od);
                        ch.basicPublish("", ORDER_QUEUE, null, payload);
                        System.out.println("Published order: " + od.getOrderId());
                    }
                }
            }
        }
    }
}
