package com.example.etl.rules;

public class RuleResult {
    private final boolean ok;
    private final String message;
    private final String field; // optional field name related to the rule

    public RuleResult(boolean ok, String message) {
        this(ok, message, null);
    }

    public RuleResult(boolean ok, String message, String field) {
        this.ok = ok;
        this.message = message;
        this.field = field;
    }

    public boolean isOk() {
        return ok;
    }

    public String getMessage() {
        return message;
    }

    public String getField() {
        return field;
    }
}
