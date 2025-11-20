package com.example.etl.models;

public class Employee {
    private String employeeId;
    private String fullName;
    private String email;

    public String getEmployeeId() { return employeeId; }
    public void setEmployeeId(String employeeId) { this.employeeId = employeeId; }

    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    @Override
    public String toString() {
        return "Employee{" + "employeeId='" + employeeId + '\'' + ", fullName='" + fullName + '\'' + ", email='" + email + '\'' + '}';
    }
}
