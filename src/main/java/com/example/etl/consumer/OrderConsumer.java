package com.example.etl.consumer;

import com.example.etl.dao.StagingDao;
import com.example.etl.models.OrderDetail;
import com.example.etl.rules.RecordValidator;
import com.example.etl.rules.RuleResult;
import com.example.etl.rules.impl.NotEmptyRule;
import com.example.etl.rules.impl.QuantityRule;
import com.example.etl.utils.RabbitMqUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.DeliverCallback;

import java.nio.charset.StandardCharsets;
import java.util.List;

public class OrderConsumer {
    private static final String ORDER_QUEUE = "order_queue";

    public static void main(String[] args) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        StagingDao dao = new StagingDao();

        RecordValidator<OrderDetail> validator = new RecordValidator<>();
        validator.addRule(new NotEmptyRule<>((OrderDetail o) -> o.getOrderId(), "orderId"));
        validator.addRule(new NotEmptyRule<>((OrderDetail o) -> o.getProductId(), "productId"));
        validator.addRule(new QuantityRule<>((OrderDetail o) -> o.getQuantity(), "quantity"));

        try (Connection conn = RabbitMqUtil.newConnection(); Channel ch = conn.createChannel()) {
            ch.queueDeclare(ORDER_QUEUE, true, false, false, null);
            System.out.println("Waiting for messages on " + ORDER_QUEUE);

            DeliverCallback deliverCallback = (consumerTag, delivery) -> {
                byte[] body = delivery.getBody();
                try {
                    OrderDetail od = mapper.readValue(body, OrderDetail.class);
                    List<RuleResult> results = validator.validateAll(od);
                    boolean ok = results.stream().allMatch(RuleResult::isOk);
                    String raw = new String(body, StandardCharsets.UTF_8);
                    if (ok) {
                        dao.insertOrderDetail(od, raw);
                        System.out.println("Inserted order into staging: " + od.getOrderId());
                        ch.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
                    } else {
                        System.err.println("Validation failed for order " + od.getOrderId());
                        java.util.List<java.util.Map<String, String>> errs = new java.util.ArrayList<>();
                        results.stream().filter(r -> !r.isOk()).forEach(r -> {
                            System.err.println(r.getMessage());
                            java.util.Map<String, String> m = new java.util.HashMap<>();
                            m.put("field", r.getField() != null ? r.getField() : "");
                            m.put("message", r.getMessage());
                            errs.add(m);
                        });
                        String errsJson = mapper.writeValueAsString(errs);
                        dao.insertOrderDetailWithErrors(od, raw, errsJson);
                        ch.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
                    }
                } catch (Exception ex) {
                    ex.printStackTrace();
                    ch.basicNack(delivery.getEnvelope().getDeliveryTag(), false, true);
                }
            };

            ch.basicConsume(ORDER_QUEUE, false, deliverCallback, consumerTag -> {});

            Thread.currentThread().join();
        }
    }
}
