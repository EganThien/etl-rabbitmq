package com.example.etl.rules.impl;

import com.example.etl.rules.Rule;
import com.example.etl.rules.RuleResult;

import java.util.function.Function;

public class NotEmptyRule<T> implements Rule<T> {
    private final Function<T, String> extractor;
    private final String fieldName;

    public NotEmptyRule(Function<T, String> extractor, String fieldName) {
        this.extractor = extractor;
        this.fieldName = fieldName;
    }

    @Override
    public RuleResult validate(T value) {
        String v = extractor.apply(value);
        if (v == null || v.trim().isEmpty()) {
            return new RuleResult(false, fieldName + " must not be empty", fieldName);
        }
        return new RuleResult(true, "");
    }
}
