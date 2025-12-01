package com.example.etl.dao;

import com.example.etl.models.Employee;
import com.example.etl.models.OrderDetail;
import com.example.etl.utils.DbUtil;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

public class StagingDao {
    
    /**
     * Insert employee into staging with null-safe field handling.
     * Logs errors and throws exception for caller to handle.
     */
    public void insertEmployee(Employee e, String rawPayload) throws Exception {
        if (e == null) {
            throw new IllegalArgumentException("Employee cannot be null");
        }
        String sql = "INSERT INTO staging_employee (employee_id, full_name, email, phone, raw_payload, validation_errors) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection c = DbUtil.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, nullSafe(e.getEmployeeId()));
            ps.setString(2, nullSafe(e.getFullName()));
            ps.setString(3, nullSafe(e.getEmail()));
            ps.setString(4, nullSafe(e.getPhone()));
            ps.setString(5, nullSafe(rawPayload));
            ps.setString(6, null);
            ps.executeUpdate();
        } catch (SQLException ex) {
            System.err.println("Failed to insert employee: " + e.getEmployeeId() + " - " + ex.getMessage());
            throw ex;
        }
    }

    public void insertOrderDetail(OrderDetail od, String rawPayload) throws Exception {
        if (od == null) {
            throw new IllegalArgumentException("OrderDetail cannot be null");
        }
        String sql = "INSERT INTO staging_order_detail (order_id, product_id, quantity, price, raw_payload, validation_errors) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection c = DbUtil.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, nullSafe(od.getOrderId()));
            ps.setString(2, nullSafe(od.getProductId()));
            ps.setInt(3, od.getQuantity());
            ps.setDouble(4, od.getPrice());
            ps.setString(5, nullSafe(rawPayload));
            ps.setString(6, null);
            ps.executeUpdate();
        } catch (SQLException ex) {
            System.err.println("Failed to insert order: " + od.getOrderId() + " - " + ex.getMessage());
            throw ex;
        }
    }

    /**
     * Insert employee with validation errors into staging.
     */
    public void insertEmployeeWithErrors(Employee e, String rawPayload, String validationErrors) throws Exception {
        if (e == null) {
            throw new IllegalArgumentException("Employee cannot be null");
        }
        String sql = "INSERT INTO staging_employee (employee_id, full_name, email, phone, raw_payload, validation_errors) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection c = DbUtil.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, nullSafe(e.getEmployeeId()));
            ps.setString(2, nullSafe(e.getFullName()));
            ps.setString(3, nullSafe(e.getEmail()));
            ps.setString(4, nullSafe(e.getPhone()));
            ps.setString(5, nullSafe(rawPayload));
            ps.setString(6, nullSafe(validationErrors));
            ps.executeUpdate();
        } catch (SQLException ex) {
            System.err.println("Failed to insert employee with errors: " + e.getEmployeeId() + " - " + ex.getMessage());
            throw ex;
        }
    }

    public void insertOrderDetailWithErrors(OrderDetail od, String rawPayload, String validationErrors) throws Exception {
        if (od == null) {
            throw new IllegalArgumentException("OrderDetail cannot be null");
        }
        String sql = "INSERT INTO staging_order_detail (order_id, product_id, quantity, price, raw_payload, validation_errors) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection c = DbUtil.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, nullSafe(od.getOrderId()));
            ps.setString(2, nullSafe(od.getProductId()));
            ps.setInt(3, od.getQuantity());
            ps.setDouble(4, od.getPrice());
            ps.setString(5, nullSafe(rawPayload));
            ps.setString(6, nullSafe(validationErrors));
            ps.executeUpdate();
        } catch (SQLException ex) {
            System.err.println("Failed to insert order with errors: " + od.getOrderId() + " - " + ex.getMessage());
            throw ex;
        }
    }

    /**
     * Helper to handle null strings safely.
     */
    private String nullSafe(String value) {
        return value != null ? value : "";
    }
}
