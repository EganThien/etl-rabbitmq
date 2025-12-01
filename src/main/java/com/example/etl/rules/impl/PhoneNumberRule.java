package com.example.etl.rules.impl;

import com.example.etl.rules.Rule;
import com.example.etl.rules.RuleResult;

import java.util.function.Function;

public class PhoneNumberRule<T> implements Rule<T> {
    // Accept international numbers with optional +, digits, spaces, dashes and parentheses
    private static final String PHONE_REGEX = "^\\+?[0-9\\-() ]{7,20}$";
    private final Function<T, String> extractor;
    private final String fieldName;

    public PhoneNumberRule(Function<T, String> extractor, String fieldName) {
        this.extractor = extractor;
        this.fieldName = fieldName;
    }

    @Override
    public RuleResult validate(T value) {
        String v = extractor.apply(value);
        if (v == null || v.trim().isEmpty()) {
            return new RuleResult(false, fieldName + " must not be empty", fieldName);
        }
        if (!v.matches(PHONE_REGEX)) {
            return new RuleResult(false, fieldName + " is not a valid phone number", fieldName);
        }
        return new RuleResult(true, "");
    }
}
