package com.example.etl.rules.impl;

import com.example.etl.rules.RuleResult;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class NotEmptyRuleTest {

    static class Dummy {
        String val;
        Dummy(String v){ this.val = v; }
        String getVal(){ return val; }
    }

    @Test
    void testNotEmptyPass() {
        NotEmptyRule<Dummy> rule = new NotEmptyRule<>(d -> d.getVal(), "val");
        RuleResult r = rule.validate(new Dummy("hello"));
        assertTrue(r.isOk());
    }

    @Test
    void testNotEmptyFail() {
        NotEmptyRule<Dummy> rule = new NotEmptyRule<>(d -> d.getVal(), "val");
        RuleResult r = rule.validate(new Dummy(""));
        assertFalse(r.isOk());
        assertTrue(r.getMessage().contains("must not be empty"));
    }
}
