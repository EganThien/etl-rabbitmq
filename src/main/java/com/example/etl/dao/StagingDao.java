package com.example.etl.dao;

import com.example.etl.models.Employee;
import com.example.etl.models.OrderDetail;
import com.example.etl.utils.DbUtil;

import java.sql.Connection;
import java.sql.PreparedStatement;

public class StagingDao {
    public void insertEmployee(Employee e, String rawPayload) throws Exception {
        String sql = "INSERT INTO staging_employee (employee_id, full_name, email, phone, raw_payload, validation_errors) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection c = DbUtil.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, e.getEmployeeId());
            ps.setString(2, e.getFullName());
            ps.setString(3, e.getEmail());
            ps.setString(4, e.getPhone());
            ps.setString(5, rawPayload);
            ps.setString(6, null);
            ps.executeUpdate();
        }
    }

    public void insertOrderDetail(OrderDetail od, String rawPayload) throws Exception {
        String sql = "INSERT INTO staging_order_detail (order_id, product_id, quantity, price, raw_payload, validation_errors) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection c = DbUtil.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, od.getOrderId());
            ps.setString(2, od.getProductId());
            ps.setInt(3, od.getQuantity());
            ps.setDouble(4, od.getPrice());
            ps.setString(5, rawPayload);
            ps.setString(6, null);
            ps.executeUpdate();
        }
    }

    public void insertEmployeeWithErrors(Employee e, String rawPayload, String validationErrors) throws Exception {
        String sql = "INSERT INTO staging_employee (employee_id, full_name, email, phone, raw_payload, validation_errors) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection c = DbUtil.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, e.getEmployeeId());
            ps.setString(2, e.getFullName());
            ps.setString(3, e.getEmail());
            ps.setString(4, e.getPhone());
            ps.setString(5, rawPayload);
            ps.setString(6, validationErrors);
            ps.executeUpdate();
        }
    }

    public void insertOrderDetailWithErrors(OrderDetail od, String rawPayload, String validationErrors) throws Exception {
        String sql = "INSERT INTO staging_order_detail (order_id, product_id, quantity, price, raw_payload, validation_errors) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection c = DbUtil.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, od.getOrderId());
            ps.setString(2, od.getProductId());
            ps.setInt(3, od.getQuantity());
            ps.setDouble(4, od.getPrice());
            ps.setString(5, rawPayload);
            ps.setString(6, validationErrors);
            ps.executeUpdate();
        }
    }
}
