package com.example.etl.rules.impl;

import com.example.etl.rules.Rule;
import com.example.etl.rules.RuleResult;

import java.util.function.Function;

public class QuantityRule<T> implements Rule<T> {
    private final Function<T, Integer> extractor;
    private final String fieldName;

    public QuantityRule(Function<T, Integer> extractor, String fieldName) {
        this.extractor = extractor;
        this.fieldName = fieldName;
    }

    @Override
    public RuleResult validate(T value) {
        Integer v = extractor.apply(value);
        if (v == null) {
            return new RuleResult(false, fieldName + " must not be null");
        }
        if (v <= 0) {
            return new RuleResult(false, fieldName + " must be greater than 0");
        }
        return new RuleResult(true, "");
    }
}
