package com.example.etl.rules.impl;

import com.example.etl.rules.RuleResult;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PhoneNumberRuleTest {
    static class Dummy { String phone; Dummy(String p){this.phone=p;} String getPhone(){return phone;} }

    @Test
    void testValidPhone() {
        PhoneNumberRule<Dummy> rule = new PhoneNumberRule<>(d -> d.getPhone(), "phone");
        RuleResult r1 = rule.validate(new Dummy("+1-202-555-0183"));
        RuleResult r2 = rule.validate(new Dummy("(202) 555 0183"));
        RuleResult r3 = rule.validate(new Dummy("2025550183"));
        assertTrue(r1.isOk());
        assertTrue(r2.isOk());
        assertTrue(r3.isOk());
    }

    @Test
    void testInvalidPhone() {
        PhoneNumberRule<Dummy> rule = new PhoneNumberRule<>(d -> d.getPhone(), "phone");
        RuleResult r = rule.validate(new Dummy("abc-123"));
        assertFalse(r.isOk());
        assertTrue(r.getMessage().contains("not a valid phone") || r.getMessage().length() > 0);
    }
}
