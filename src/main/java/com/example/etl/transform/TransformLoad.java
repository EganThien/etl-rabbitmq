package com.example.etl.transform;

import com.example.etl.utils.DbUtil;
import com.example.etl.models.Employee;
import com.example.etl.models.OrderDetail;
import com.example.etl.rules.RecordValidator;
import com.example.etl.rules.RuleResult;
import com.example.etl.rules.impl.EmailRule;
import com.example.etl.rules.impl.NotEmptyRule;
import com.example.etl.rules.impl.PhoneNumberRule;
import com.example.etl.rules.impl.QuantityRule;

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
        // Only select records without validation errors
        String selectSql = "SELECT id, employee_id, full_name, email, phone FROM staging_employee WHERE validation_errors IS NULL";
        String upsertSql = "INSERT INTO main_employee (employee_id, full_name, email, phone) VALUES (?, ?, ?, ?) " +
            "ON DUPLICATE KEY UPDATE full_name = VALUES(full_name), email = VALUES(email), phone = VALUES(phone)";
        String deleteSql = "DELETE FROM staging_employee WHERE id = ?";
        String markErrorSql = "UPDATE staging_employee SET validation_errors = ? WHERE id = ?";

        final int BATCH_SIZE = 500;

        // prepare validators (same as used by consumer)
        RecordValidator<Employee> validator = new RecordValidator<>();
        validator.addRule(new NotEmptyRule<Employee>((Employee e) -> e.getEmployeeId(), "employeeId"));
        validator.addRule(new NotEmptyRule<Employee>((Employee e) -> e.getFullName(), "fullName"));
        validator.addRule(new EmailRule<Employee>((Employee e) -> e.getEmail(), "email"));
        validator.addRule(new PhoneNumberRule<Employee>((Employee e) -> e.getPhone(), "phone"));

        try (Connection conn = DbUtil.getConnection()) {
            conn.setAutoCommit(false);
            try (PreparedStatement sel = conn.prepareStatement(selectSql, ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY);
                 PreparedStatement upsert = conn.prepareStatement(upsertSql);
                 PreparedStatement delete = conn.prepareStatement(deleteSql);
                 PreparedStatement markErr = conn.prepareStatement(markErrorSql)) {

                ResultSet rs = sel.executeQuery();
                List<Integer> batchIds = new ArrayList<>(BATCH_SIZE);
                int processedTotal = 0;

                while (rs.next()) {
                    int id = rs.getInt("id");
                    String employeeId = rs.getString("employee_id");
                    String fullName = rs.getString("full_name");
                    String email = rs.getString("email");
                    String phone = rs.getString("phone");

                    Employee e = new Employee();
                    e.setEmployeeId(employeeId);
                    e.setFullName(fullName);
                    e.setEmail(email);
                    e.setPhone(phone);

                    List<RuleResult> results = validator.validateAll(e);
                    boolean ok = results.stream().allMatch(RuleResult::isOk);
                    if (!ok) {
                        // build JSON errors and mark staging
                        com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
                        java.util.List<java.util.Map<String, String>> errs = new java.util.ArrayList<>();
                        results.stream().filter(r -> !r.isOk()).forEach(r -> {
                            java.util.Map<String, String> m = new java.util.HashMap<>();
                            m.put("field", r.getField() != null ? r.getField() : "");
                            m.put("message", r.getMessage());
                            errs.add(m);
                        });
                        String errsJson = mapper.writeValueAsString(errs);
                        markErr.setString(1, errsJson);
                        markErr.setInt(2, id);
                        markErr.executeUpdate();
                        // commit the validation_errors update immediately so errors are persisted
                        conn.commit();
                        // continue to next record without adding to upsert batch
                        continue;
                    }

                    upsert.setString(1, employeeId);
                    upsert.setString(2, fullName);
                    upsert.setString(3, email);
                    upsert.setString(4, phone);
                    upsert.addBatch();

                    batchIds.add(id);

                    if (batchIds.size() >= BATCH_SIZE) {
                        upsert.executeBatch();
                        // delete processed ids in batch
                        for (Integer pid : batchIds) {
                            delete.setInt(1, pid);
                            delete.addBatch();
                        }
                        delete.executeBatch();
                        conn.commit();
                        processedTotal += batchIds.size();
                        batchIds.clear();
                    }
                }

                // flush remaining
                if (!batchIds.isEmpty()) {
                    upsert.executeBatch();
                    for (Integer pid : batchIds) {
                        delete.setInt(1, pid);
                        delete.addBatch();
                    }
                    delete.executeBatch();
                    conn.commit();
                    processedTotal += batchIds.size();
                    batchIds.clear();
                }

                conn.setAutoCommit(true);
                System.out.println("Transferred " + processedTotal + " employee(s) to main_employee");
            } catch (Exception ex) {
                conn.rollback();
                conn.setAutoCommit(true);
                throw ex;
            }
        }
    }

    public void transferOrders() throws Exception {
        // Only select records without validation errors
        String selectSql = "SELECT id, order_id, product_id, quantity, price FROM staging_order_detail WHERE validation_errors IS NULL";
        String upsertSql = "INSERT INTO main_order_detail (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?) " +
                "ON DUPLICATE KEY UPDATE product_id = VALUES(product_id), quantity = VALUES(quantity), price = VALUES(price)";
        String deleteSql = "DELETE FROM staging_order_detail WHERE id = ?";
        String markErrorSql = "UPDATE staging_order_detail SET validation_errors = ? WHERE id = ?";

        final int BATCH_SIZE = 500;

        // prepare order validators
        RecordValidator<OrderDetail> validator = new RecordValidator<>();
        validator.addRule(new NotEmptyRule<>((OrderDetail o) -> o.getOrderId(), "orderId"));
        validator.addRule(new NotEmptyRule<>((OrderDetail o) -> o.getProductId(), "productId"));
        validator.addRule(new QuantityRule<>((OrderDetail o) -> o.getQuantity(), "quantity"));

        try (Connection conn = DbUtil.getConnection()) {
            conn.setAutoCommit(false);
            try (PreparedStatement sel = conn.prepareStatement(selectSql, ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY);
                 PreparedStatement upsert = conn.prepareStatement(upsertSql);
                 PreparedStatement delete = conn.prepareStatement(deleteSql);
                 PreparedStatement markErr = conn.prepareStatement(markErrorSql)) {

                ResultSet rs = sel.executeQuery();
                List<Integer> batchIds = new ArrayList<>(BATCH_SIZE);
                int processedTotal = 0;

                while (rs.next()) {
                    int id = rs.getInt("id");
                    String orderId = rs.getString("order_id");
                    String productId = rs.getString("product_id");
                    int qty = rs.getInt("quantity");
                    double price = rs.getDouble("price");

                    OrderDetail od = new OrderDetail();
                    od.setOrderId(orderId);
                    od.setProductId(productId);
                    od.setQuantity(qty);
                    od.setPrice(price);

                    List<RuleResult> results = validator.validateAll(od);
                    boolean ok = results.stream().allMatch(RuleResult::isOk);
                    if (!ok) {
                        com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
                        java.util.List<java.util.Map<String, String>> errs = new java.util.ArrayList<>();
                        results.stream().filter(r -> !r.isOk()).forEach(r -> {
                            java.util.Map<String, String> m = new java.util.HashMap<>();
                            m.put("field", r.getField() != null ? r.getField() : "");
                            m.put("message", r.getMessage());
                            errs.add(m);
                        });
                        String errsJson = mapper.writeValueAsString(errs);
                        markErr.setString(1, errsJson);
                        markErr.setInt(2, id);
                        markErr.executeUpdate();
                        // persist validation error immediately
                        conn.commit();
                        continue;
                    }

                    upsert.setString(1, orderId);
                    upsert.setString(2, productId);
                    upsert.setInt(3, qty);
                    upsert.setDouble(4, price);
                    upsert.addBatch();

                    batchIds.add(id);

                    if (batchIds.size() >= BATCH_SIZE) {
                        upsert.executeBatch();
                        for (Integer pid : batchIds) {
                            delete.setInt(1, pid);
                            delete.addBatch();
                        }
                        delete.executeBatch();
                        conn.commit();
                        processedTotal += batchIds.size();
                        batchIds.clear();
                    }
                }

                // flush remaining
                if (!batchIds.isEmpty()) {
                    upsert.executeBatch();
                    for (Integer pid : batchIds) {
                        delete.setInt(1, pid);
                        delete.addBatch();
                    }
                    delete.executeBatch();
                    conn.commit();
                    processedTotal += batchIds.size();
                    batchIds.clear();
                }

                conn.setAutoCommit(true);
                System.out.println("Transferred " + processedTotal + " order(s) to main_order_detail");
            } catch (Exception ex) {
                conn.rollback();
                conn.setAutoCommit(true);
                throw ex;
            }
        }
    }
}
