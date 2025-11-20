package com.example.etl.rules;

public class RuleResult {
    private final boolean ok;
    private final String message;

    public RuleResult(boolean ok, String message) {
        this.ok = ok;
        this.message = message;
    }

    public boolean isOk() {
        return ok;
    }

    public String getMessage() {
        return message;
    }
}
