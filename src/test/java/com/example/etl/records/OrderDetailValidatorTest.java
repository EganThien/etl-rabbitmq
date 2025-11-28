package com.example.etl.records;

import com.example.etl.models.OrderDetail;
import com.example.etl.rules.RecordValidator;
import com.example.etl.rules.RuleResult;
import com.example.etl.rules.impl.NotEmptyRule;
import com.example.etl.rules.impl.QuantityRule;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

public class OrderDetailValidatorTest {

    @Test
    public void testValidOrderDetail() {
        OrderDetail od = new OrderDetail();
        od.setOrderId("O1");
        od.setProductId("P1");
        od.setQuantity(5);
        od.setPrice(10.0);

        RecordValidator<OrderDetail> v = new RecordValidator<>();
        v.addRule(new NotEmptyRule<>((OrderDetail x) -> x.getOrderId(), "orderId"));
        v.addRule(new NotEmptyRule<>((OrderDetail x) -> x.getProductId(), "productId"));
        v.addRule(new QuantityRule<>((OrderDetail x) -> x.getQuantity(), "quantity"));

        List<RuleResult> results = v.validateAll(od);
        assertTrue(results.stream().allMatch(RuleResult::isOk));
    }

    @Test
    public void testInvalidQuantity() {
        OrderDetail od = new OrderDetail();
        od.setOrderId("O2");
        od.setProductId("P2");
        od.setQuantity(0);

        RecordValidator<OrderDetail> v = new RecordValidator<>();
        v.addRule(new QuantityRule<>((OrderDetail x) -> x.getQuantity(), "quantity"));

        List<RuleResult> results = v.validateAll(od);
        assertFalse(results.stream().allMatch(RuleResult::isOk));
    }
}
