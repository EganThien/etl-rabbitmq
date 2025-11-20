package com.example.etl.rules;

import com.example.etl.rules.impl.EmailRule;
import com.example.etl.rules.impl.NotEmptyRule;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class RecordValidatorTest {
    static class Emp { String id; String email; Emp(String i, String e){id=i;email=e;} String getId(){return id;} String getEmail(){return email;} }

    @Test
    void testValidatorAllPass() {
        RecordValidator<Emp> v = new RecordValidator<>();
        v.addRule(new NotEmptyRule<>(e -> e.getId(), "id"));
        v.addRule(new EmailRule<>(e -> e.getEmail(), "email"));

        List<RuleResult> results = v.validateAll(new Emp("E1", "a@b.com"));
        assertTrue(results.stream().allMatch(RuleResult::isOk));
    }

    @Test
    void testValidatorFail() {
        RecordValidator<Emp> v = new RecordValidator<>();
        v.addRule(new NotEmptyRule<>(e -> e.getId(), "id"));
        v.addRule(new EmailRule<>(e -> e.getEmail(), "email"));

        List<RuleResult> results = v.validateAll(new Emp("", "bademail"));
        assertTrue(results.stream().anyMatch(r -> !r.isOk()));
    }
}
