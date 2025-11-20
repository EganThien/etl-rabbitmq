package com.example.etl.transform;

import com.example.etl.utils.DbUtil;
import com.example.etl.models.Employee;
import com.example.etl.models.OrderDetail;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class TransformLoad {

    public static void main(String[] args) throws Exception {
        TransformLoad tl = new TransformLoad();
        tl.transferEmployees();
        tl.transferOrders();
        System.out.println("Transform & load completed.");
    }

    public void transferEmployees() throws Exception {
        String selectSql = "SELECT id, employee_id, full_name, email FROM staging_employee";
        String upsertSql = "INSERT INTO main_employee (employee_id, full_name, email) VALUES (?, ?, ?) " +
                "ON DUPLICATE KEY UPDATE full_name = VALUES(full_name), email = VALUES(email)";
        String deleteSql = "DELETE FROM staging_employee WHERE id = ?";

        try (Connection conn = DbUtil.getConnection()) {
            conn.setAutoCommit(false);
            try (PreparedStatement sel = conn.prepareStatement(selectSql, ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY);
                 PreparedStatement upsert = conn.prepareStatement(upsertSql);
                 PreparedStatement delete = conn.prepareStatement(deleteSql)) {

                ResultSet rs = sel.executeQuery();
                List<Integer> processedIds = new ArrayList<>();
                while (rs.next()) {
                    int id = rs.getInt("id");
                    String employeeId = rs.getString("employee_id");
                    String fullName = rs.getString("full_name");
                    String email = rs.getString("email");

                    upsert.setString(1, employeeId);
                    upsert.setString(2, fullName);
                    upsert.setString(3, email);
                    upsert.executeUpdate();

                    processedIds.add(id);
                }

                for (Integer pid : processedIds) {
                    delete.setInt(1, pid);
                    delete.executeUpdate();
                }

                conn.commit();
                System.out.println("Transferred " + processedIds.size() + " employee(s) to main_employee");
            } catch (Exception ex) {
                conn.rollback();
                throw ex;
            } finally {
                conn.setAutoCommit(true);
            }
        }
    }

    public void transferOrders() throws Exception {
        String selectSql = "SELECT id, order_id, product_id, quantity, price FROM staging_order_detail";
        String upsertSql = "INSERT INTO main_order_detail (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?) " +
                "ON DUPLICATE KEY UPDATE product_id = VALUES(product_id), quantity = VALUES(quantity), price = VALUES(price)";
        String deleteSql = "DELETE FROM staging_order_detail WHERE id = ?";

        try (Connection conn = DbUtil.getConnection()) {
            conn.setAutoCommit(false);
            try (PreparedStatement sel = conn.prepareStatement(selectSql, ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY);
                 PreparedStatement upsert = conn.prepareStatement(upsertSql);
                 PreparedStatement delete = conn.prepareStatement(deleteSql)) {

                ResultSet rs = sel.executeQuery();
                List<Integer> processedIds = new ArrayList<>();
                while (rs.next()) {
                    int id = rs.getInt("id");
                    String orderId = rs.getString("order_id");
                    String productId = rs.getString("product_id");
                    int qty = rs.getInt("quantity");
                    double price = rs.getDouble("price");

                    upsert.setString(1, orderId);
                    upsert.setString(2, productId);
                    upsert.setInt(3, qty);
                    upsert.setDouble(4, price);
                    upsert.executeUpdate();

                    processedIds.add(id);
                }

                for (Integer pid : processedIds) {
                    delete.setInt(1, pid);
                    delete.executeUpdate();
                }

                conn.commit();
                System.out.println("Transferred " + processedIds.size() + " order(s) to main_order_detail");
            } catch (Exception ex) {
                conn.rollback();
                throw ex;
            } finally {
                conn.setAutoCommit(true);
            }
        }
    }
}
