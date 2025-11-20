package com.example.etl.rules;

public interface Rule<T> {
    RuleResult validate(T value);
}

