package com.example.etl.rules;

import java.util.ArrayList;
import java.util.List;

public class RecordValidator<T> {
    private final List<Rule<T>> rules = new ArrayList<>();

    public void addRule(Rule<T> r){ rules.add(r); }

    public List<RuleResult> validateAll(T value){
        List<RuleResult> results = new ArrayList<>();
        for (Rule<T> r: rules){
            results.add(r.validate(value));
        }
        return results;
    }
}
