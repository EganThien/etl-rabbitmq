package com.example.etl.rules.impl;

import com.example.etl.rules.Rule;
import com.example.etl.rules.RuleResult;

import java.util.function.Function;
import java.util.regex.Pattern;

public class EmailRule<T> implements Rule<T> {
    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$");
    private final Function<T, String> extractor;
    private final String fieldName;

    public EmailRule(Function<T, String> extractor, String fieldName) {
        this.extractor = extractor;
        this.fieldName = fieldName;
    }

    @Override
    public RuleResult validate(T value) {
        String v = extractor.apply(value);
        if (v == null || v.trim().isEmpty()) {
            return new RuleResult(false, fieldName + " must not be empty", fieldName);
        }
        if (!EMAIL_PATTERN.matcher(v).matches()) {
            return new RuleResult(false, fieldName + " is not a valid email", fieldName);
        }
        return new RuleResult(true, "");
    }
}
