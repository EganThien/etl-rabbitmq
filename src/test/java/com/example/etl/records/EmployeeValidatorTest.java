package com.example.etl.records;

import com.example.etl.models.Employee;
import com.example.etl.rules.RecordValidator;
import com.example.etl.rules.RuleResult;
import com.example.etl.rules.impl.EmailRule;
import com.example.etl.rules.impl.NotEmptyRule;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

public class EmployeeValidatorTest {

    @Test
    public void testValidEmployee() {
        Employee e = new Employee();
        e.setEmployeeId("E1");
        e.setFullName("Nguyen Van A");
        e.setEmail("a@example.com");

        RecordValidator<Employee> v = new RecordValidator<>();
        v.addRule(new NotEmptyRule<>((Employee x) -> x.getEmployeeId(), "employeeId"));
        v.addRule(new NotEmptyRule<>((Employee x) -> x.getFullName(), "fullName"));
        v.addRule(new EmailRule<>((Employee x) -> x.getEmail(), "email"));

        List<RuleResult> results = v.validateAll(e);
        assertTrue(results.stream().allMatch(RuleResult::isOk));
    }

    @Test
    public void testInvalidEmail() {
        Employee e = new Employee();
        e.setEmployeeId("E2");
        e.setFullName("Nguyen Van B");
        e.setEmail("invalid-email");

        RecordValidator<Employee> v = new RecordValidator<>();
        v.addRule(new EmailRule<>((Employee x) -> x.getEmail(), "email"));

        List<RuleResult> results = v.validateAll(e);
        assertFalse(results.stream().allMatch(RuleResult::isOk));
    }
}
