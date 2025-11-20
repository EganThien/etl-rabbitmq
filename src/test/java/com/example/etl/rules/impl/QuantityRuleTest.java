package com.example.etl.rules.impl;

import com.example.etl.rules.RuleResult;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class QuantityRuleTest {
    static class Dummy { Integer q; Dummy(Integer q){this.q=q;} Integer getQ(){return q;} }

    @Test
    void testPositive() {
        QuantityRule<Dummy> rule = new QuantityRule<>(d -> d.getQ(), "quantity");
        RuleResult r = rule.validate(new Dummy(5));
        assertTrue(r.isOk());
    }

    @Test
    void testZeroOrNegative() {
        QuantityRule<Dummy> rule = new QuantityRule<>(d -> d.getQ(), "quantity");
        RuleResult r1 = rule.validate(new Dummy(0));
        RuleResult r2 = rule.validate(new Dummy(-1));
        assertFalse(r1.isOk());
        assertFalse(r2.isOk());
    }
}
