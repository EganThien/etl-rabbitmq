package com.example.etl.rules.impl;

import com.example.etl.rules.RuleResult;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class EmailRuleTest {
    static class Dummy { String email; Dummy(String e){this.email=e;} String getEmail(){return email;} }

    @Test
    void testValidEmail() {
        EmailRule<Dummy> rule = new EmailRule<>(d -> d.getEmail(), "email");
        RuleResult r = rule.validate(new Dummy("user@example.com"));
        assertTrue(r.isOk());
    }

    @Test
    void testInvalidEmail() {
        EmailRule<Dummy> rule = new EmailRule<>(d -> d.getEmail(), "email");
        RuleResult r = rule.validate(new Dummy("not-an-email"));
        assertFalse(r.isOk());
        assertTrue(r.getMessage().contains("not a valid email") || r.getMessage().length() > 0);
    }
}
