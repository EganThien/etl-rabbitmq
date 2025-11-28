package com.example.etl.consumer;

import com.example.etl.dao.StagingDao;
import com.example.etl.models.Employee;
import com.example.etl.rules.RecordValidator;
import com.example.etl.rules.Rule;
import com.example.etl.rules.RuleResult;
import com.example.etl.rules.impl.EmailRule;
import com.example.etl.rules.impl.NotEmptyRule;
import com.example.etl.utils.RabbitMqUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rabbitmq.client.*;

import java.nio.charset.StandardCharsets;
import java.util.List;

public class EmployeeConsumer {
    private static final String EMPLOYEE_QUEUE = "employee_queue";

    public static void main(String[] args) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        StagingDao dao = new StagingDao();

        RecordValidator<Employee> validator = new RecordValidator<>();
        validator.addRule(new NotEmptyRule<Employee>((Employee e) -> e.getEmployeeId(), "employeeId"));
        validator.addRule(new NotEmptyRule<Employee>((Employee e) -> e.getFullName(), "fullName"));
        validator.addRule(new EmailRule<Employee>((Employee e) -> e.getEmail(), "email"));

        try (Connection conn = RabbitMqUtil.newConnection(); Channel ch = conn.createChannel()) {
            ch.queueDeclare(EMPLOYEE_QUEUE, true, false, false, null);
            System.out.println("Waiting for messages on " + EMPLOYEE_QUEUE);

            DeliverCallback deliverCallback = (consumerTag, delivery) -> {
                byte[] body = delivery.getBody();
                try {
                    Employee e = mapper.readValue(body, Employee.class);
                    List<RuleResult> results = validator.validateAll(e);
                    boolean ok = results.stream().allMatch(RuleResult::isOk);
                    String raw = new String(body, StandardCharsets.UTF_8);
                    if (ok) {
                        dao.insertEmployee(e, raw);
                        System.out.println("Inserted into staging: " + e.getEmployeeId());
                        ch.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
                    } else {
                        System.err.println("Validation failed for " + e.getEmployeeId());
                        // build structured errors as JSON array of {field, message}
                        java.util.List<java.util.Map<String, String>> errs = new java.util.ArrayList<>();
                        results.stream().filter(r -> !r.isOk()).forEach(r -> {
                            System.err.println(r.getMessage());
                            java.util.Map<String, String> m = new java.util.HashMap<>();
                            m.put("field", r.getField() != null ? r.getField() : "");
                            m.put("message", r.getMessage());
                            errs.add(m);
                        });
                        String errsJson = mapper.writeValueAsString(errs);
                        // persist into staging with structured validation errors
                        dao.insertEmployeeWithErrors(e, raw, errsJson);
                        ch.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
                    }
                } catch (Exception ex) {
                    ex.printStackTrace();
                    ch.basicNack(delivery.getEnvelope().getDeliveryTag(), false, true);
                }
            };

            ch.basicConsume(EMPLOYEE_QUEUE, false, deliverCallback, consumerTag -> {});

            // keep main thread alive
            Thread.currentThread().join();
        }
    }
}
