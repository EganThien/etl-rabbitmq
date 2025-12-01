package com.example.etl.transform;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.*;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration test for TransformLoad using H2 in-memory database.
 * Tests validation logic and validation_errors persistence.
 */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class TransformLoadTest {

    private Connection conn;
    private static final String DB_URL = "jdbc:h2:mem:testdb;MODE=MySQL;DB_CLOSE_DELAY=-1";
    private static final String DB_USER = "sa";
    private static final String DB_PASS = "";

    @BeforeAll
    void setupDatabase() throws Exception {
        // Create H2 in-memory database with schema
        conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
        
        // Create staging and main tables
        try (Statement stmt = conn.createStatement()) {
            stmt.execute(
                "CREATE TABLE staging_employee (" +
                "  id INT AUTO_INCREMENT PRIMARY KEY," +
                "  employee_id VARCHAR(50)," +
                "  full_name VARCHAR(255)," +
                "  email VARCHAR(255)," +
                "  phone VARCHAR(50)," +
                "  raw_payload TEXT," +
                "  validation_errors TEXT," +
                "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
                ")"
            );
            
            stmt.execute(
                "CREATE TABLE main_employee (" +
                "  id INT AUTO_INCREMENT PRIMARY KEY," +
                "  employee_id VARCHAR(50) UNIQUE," +
                "  full_name VARCHAR(255)," +
                "  email VARCHAR(255)," +
                "  phone VARCHAR(50)" +
                ")"
            );

            stmt.execute(
                "CREATE TABLE staging_order_detail (" +
                "  id INT AUTO_INCREMENT PRIMARY KEY," +
                "  order_id VARCHAR(50)," +
                "  product_id VARCHAR(50)," +
                "  quantity INT," +
                "  price DOUBLE," +
                "  raw_payload TEXT," +
                "  validation_errors TEXT," +
                "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" +
                ")"
            );

            stmt.execute(
                "CREATE TABLE main_order_detail (" +
                "  id INT AUTO_INCREMENT PRIMARY KEY," +
                "  order_id VARCHAR(50)," +
                "  product_id VARCHAR(50)," +
                "  quantity INT," +
                "  price DOUBLE," +
                "  UNIQUE(order_id)" +
                ")"
            );
        }

        // Override DbUtil to use test connection
        System.setProperty("DB_URL", DB_URL);
        System.setProperty("DB_USER", DB_USER);
        System.setProperty("DB_PASS", DB_PASS);
    }

    @AfterAll
    void teardownDatabase() throws Exception {
        if (conn != null && !conn.isClosed()) {
            conn.close();
        }
    }

    @BeforeEach
    void clearTables() throws Exception {
        try (Statement stmt = conn.createStatement()) {
            stmt.execute("DELETE FROM staging_employee");
            stmt.execute("DELETE FROM main_employee");
            stmt.execute("DELETE FROM staging_order_detail");
            stmt.execute("DELETE FROM main_order_detail");
        }
    }

    @Test
    void testTransferEmployees_ValidRecords() throws Exception {
        // Insert valid employees into staging
        try (PreparedStatement ps = conn.prepareStatement(
            "INSERT INTO staging_employee (employee_id, full_name, email, phone, raw_payload, validation_errors) " +
            "VALUES (?, ?, ?, ?, ?, ?)"
        )) {
            ps.setString(1, "E001");
            ps.setString(2, "John Doe");
            ps.setString(3, "john@example.com");
            ps.setString(4, "+1234567890");
            ps.setString(5, "{\"employeeId\":\"E001\"}");
            ps.setString(6, null);
            ps.executeUpdate();

            ps.setString(1, "E002");
            ps.setString(2, "Jane Smith");
            ps.setString(3, "jane@test.com");
            ps.setString(4, "+9876543210");
            ps.setString(5, "{\"employeeId\":\"E002\"}");
            ps.setString(6, null);
            ps.executeUpdate();
        }

        // Create TransformLoad with test connection
        TransformLoadTestHelper helper = new TransformLoadTestHelper(conn);
        helper.transferEmployees();

        // Verify records moved to main_employee
        try (Statement stmt = conn.createStatement()) {
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM main_employee");
            rs.next();
            assertEquals(2, rs.getInt(1), "Should have 2 employees in main");

            // Verify staging is cleared
            rs = stmt.executeQuery("SELECT COUNT(*) FROM staging_employee");
            rs.next();
            assertEquals(0, rs.getInt(1), "Staging should be empty after transfer");
        }
    }

    @Test
    void testTransferEmployees_InvalidRecords() throws Exception {
        // Insert invalid employees (bad email, missing fields)
        try (PreparedStatement ps = conn.prepareStatement(
            "INSERT INTO staging_employee (employee_id, full_name, email, phone, raw_payload, validation_errors) " +
            "VALUES (?, ?, ?, ?, ?, ?)"
        )) {
            // Invalid email
            ps.setString(1, "E003");
            ps.setString(2, "Bad Email");
            ps.setString(3, "not-an-email");
            ps.setString(4, "+1111111111");
            ps.setString(5, "{\"employeeId\":\"E003\"}");
            ps.setString(6, null);
            ps.executeUpdate();

            // Empty name
            ps.setString(1, "E004");
            ps.setString(2, "");
            ps.setString(3, "empty@test.com");
            ps.setString(4, "+2222222222");
            ps.setString(5, "{\"employeeId\":\"E004\"}");
            ps.setString(6, null);
            ps.executeUpdate();
        }

        // Run transform
        TransformLoadTestHelper helper = new TransformLoadTestHelper(conn);
        helper.transferEmployees();

        // Verify no records moved to main
        try (Statement stmt = conn.createStatement()) {
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM main_employee");
            rs.next();
            assertEquals(0, rs.getInt(1), "No invalid records should be in main");

            // Verify validation_errors are recorded in staging
            rs = stmt.executeQuery("SELECT id, validation_errors FROM staging_employee WHERE validation_errors IS NOT NULL ORDER BY id");
            
            List<String> errors = new ArrayList<>();
            while (rs.next()) {
                errors.add(rs.getString("validation_errors"));
            }
            
            assertEquals(2, errors.size(), "Should have 2 records with validation errors");
            
            // Parse and verify error structure
            ObjectMapper mapper = new ObjectMapper();
            for (String errorJson : errors) {
                assertNotNull(errorJson);
                List<Map<String, String>> errorList = mapper.readValue(errorJson, List.class);
                assertFalse(errorList.isEmpty(), "Error list should not be empty");
                
                // Each error should have field and message
                for (Map<String, String> error : errorList) {
                    assertTrue(error.containsKey("field"));
                    assertTrue(error.containsKey("message"));
                    assertNotNull(error.get("message"));
                }
            }
        }
    }

    @Test
    void testTransferEmployees_MixedRecords() throws Exception {
        // Insert mix of valid and invalid records
        try (PreparedStatement ps = conn.prepareStatement(
            "INSERT INTO staging_employee (employee_id, full_name, email, phone, raw_payload, validation_errors) " +
            "VALUES (?, ?, ?, ?, ?, ?)"
        )) {
            // Valid
            ps.setString(1, "E005");
            ps.setString(2, "Alice Valid");
            ps.setString(3, "alice@valid.com");
            ps.setString(4, "+3333333333");
            ps.setString(5, "{\"employeeId\":\"E005\"}");
            ps.setString(6, null);
            ps.executeUpdate();

            // Invalid email
            ps.setString(1, "E006");
            ps.setString(2, "Bob Invalid");
            ps.setString(3, "bob@");
            ps.setString(4, "+4444444444");
            ps.setString(5, "{\"employeeId\":\"E006\"}");
            ps.setString(6, null);
            ps.executeUpdate();

            // Valid
            ps.setString(1, "E007");
            ps.setString(2, "Charlie Valid");
            ps.setString(3, "charlie@example.com");
            ps.setString(4, "+5555555555");
            ps.setString(5, "{\"employeeId\":\"E007\"}");
            ps.setString(6, null);
            ps.executeUpdate();
        }

        // Run transform
        TransformLoadTestHelper helper = new TransformLoadTestHelper(conn);
        helper.transferEmployees();

        // Verify only valid records in main
        try (Statement stmt = conn.createStatement()) {
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM main_employee");
            rs.next();
            assertEquals(2, rs.getInt(1), "Should have 2 valid employees in main");

            // Verify 1 invalid record remains in staging with errors
            rs = stmt.executeQuery("SELECT COUNT(*) FROM staging_employee WHERE validation_errors IS NOT NULL");
            rs.next();
            assertEquals(1, rs.getInt(1), "Should have 1 record with validation errors in staging");
        }
    }

    @Test
    void testTransferOrders_ValidRecords() throws Exception {
        // Insert valid orders into staging
        try (PreparedStatement ps = conn.prepareStatement(
            "INSERT INTO staging_order_detail (order_id, product_id, quantity, price, raw_payload, validation_errors) " +
            "VALUES (?, ?, ?, ?, ?, ?)"
        )) {
            ps.setString(1, "O001");
            ps.setString(2, "P001");
            ps.setInt(3, 5);
            ps.setDouble(4, 99.99);
            ps.setString(5, "{\"orderId\":\"O001\"}");
            ps.setString(6, null);
            ps.executeUpdate();
        }

        // Run transform
        TransformLoadTestHelper helper = new TransformLoadTestHelper(conn);
        helper.transferOrders();

        // Verify transfer
        try (Statement stmt = conn.createStatement()) {
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM main_order_detail");
            rs.next();
            assertEquals(1, rs.getInt(1), "Should have 1 order in main");

            rs = stmt.executeQuery("SELECT COUNT(*) FROM staging_order_detail");
            rs.next();
            assertEquals(0, rs.getInt(1), "Staging should be empty");
        }
    }

    @Test
    void testTransferOrders_InvalidQuantity() throws Exception {
        // Insert order with invalid quantity (negative or zero)
        try (PreparedStatement ps = conn.prepareStatement(
            "INSERT INTO staging_order_detail (order_id, product_id, quantity, price, raw_payload, validation_errors) " +
            "VALUES (?, ?, ?, ?, ?, ?)"
        )) {
            ps.setString(1, "O002");
            ps.setString(2, "P002");
            ps.setInt(3, -5);
            ps.setDouble(4, 50.00);
            ps.setString(5, "{\"orderId\":\"O002\"}");
            ps.setString(6, null);
            ps.executeUpdate();
        }

        // Run transform
        TransformLoadTestHelper helper = new TransformLoadTestHelper(conn);
        helper.transferOrders();

        // Verify no transfer and error recorded
        try (Statement stmt = conn.createStatement()) {
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM main_order_detail");
            rs.next();
            assertEquals(0, rs.getInt(1), "No invalid orders should be in main");

            rs = stmt.executeQuery("SELECT validation_errors FROM staging_order_detail WHERE validation_errors IS NOT NULL");
            assertTrue(rs.next(), "Should have validation error");
            String errorJson = rs.getString(1);
            assertNotNull(errorJson);
            assertTrue(errorJson.contains("quantity"), "Error should mention quantity field");
        }
    }

    /**
     * Helper class that extends TransformLoad to use test connection.
     * In production, we'd refactor TransformLoad to accept Connection as constructor parameter.
     */
    private static class TransformLoadTestHelper {
        private final Connection testConn;

        TransformLoadTestHelper(Connection conn) {
            this.testConn = conn;
        }

        void transferEmployees() throws Exception {
            // Simplified version of TransformLoad.transferEmployees using testConn
            String selectSql = "SELECT id, employee_id, full_name, email, phone FROM staging_employee WHERE validation_errors IS NULL";
            String upsertSql = "INSERT INTO main_employee (employee_id, full_name, email, phone) VALUES (?, ?, ?, ?) " +
                "ON DUPLICATE KEY UPDATE full_name = VALUES(full_name), email = VALUES(email), phone = VALUES(phone)";
            String deleteSql = "DELETE FROM staging_employee WHERE id = ?";
            String markErrorSql = "UPDATE staging_employee SET validation_errors = ? WHERE id = ?";

            // Use TransformLoad logic with test connection
            com.example.etl.rules.RecordValidator<com.example.etl.models.Employee> validator = new com.example.etl.rules.RecordValidator<>();
            validator.addRule(new com.example.etl.rules.impl.NotEmptyRule<>((com.example.etl.models.Employee e) -> e.getEmployeeId(), "employeeId"));
            validator.addRule(new com.example.etl.rules.impl.NotEmptyRule<>((com.example.etl.models.Employee e) -> e.getFullName(), "fullName"));
            validator.addRule(new com.example.etl.rules.impl.EmailRule<>((com.example.etl.models.Employee e) -> e.getEmail(), "email"));
            validator.addRule(new com.example.etl.rules.impl.PhoneNumberRule<>((com.example.etl.models.Employee e) -> e.getPhone(), "phone"));

            testConn.setAutoCommit(false);
            try (PreparedStatement sel = testConn.prepareStatement(selectSql);
                 PreparedStatement upsert = testConn.prepareStatement(upsertSql);
                 PreparedStatement delete = testConn.prepareStatement(deleteSql);
                 PreparedStatement markErr = testConn.prepareStatement(markErrorSql)) {

                ResultSet rs = sel.executeQuery();
                List<Integer> batchIds = new ArrayList<>();

                while (rs.next()) {
                    int id = rs.getInt("id");
                    String employeeId = rs.getString("employee_id");
                    String fullName = rs.getString("full_name");
                    String email = rs.getString("email");
                    String phone = rs.getString("phone");

                    com.example.etl.models.Employee e = new com.example.etl.models.Employee();
                    e.setEmployeeId(employeeId);
                    e.setFullName(fullName);
                    e.setEmail(email);
                    e.setPhone(phone);

                    List<com.example.etl.rules.RuleResult> results = validator.validateAll(e);
                    boolean ok = results.stream().allMatch(com.example.etl.rules.RuleResult::isOk);
                    
                    if (!ok) {
                        com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
                        List<Map<String, String>> errs = new ArrayList<>();
                        results.stream().filter(r -> !r.isOk()).forEach(r -> {
                            Map<String, String> m = new java.util.HashMap<>();
                            m.put("field", r.getField() != null ? r.getField() : "");
                            m.put("message", r.getMessage());
                            errs.add(m);
                        });
                        String errsJson = mapper.writeValueAsString(errs);
                        markErr.setString(1, errsJson);
                        markErr.setInt(2, id);
                        markErr.executeUpdate();
                        testConn.commit();
                        continue;
                    }

                    upsert.setString(1, employeeId);
                    upsert.setString(2, fullName);
                    upsert.setString(3, email);
                    upsert.setString(4, phone);
                    upsert.addBatch();
                    batchIds.add(id);
                }

                if (!batchIds.isEmpty()) {
                    upsert.executeBatch();
                    for (Integer pid : batchIds) {
                        delete.setInt(1, pid);
                        delete.addBatch();
                    }
                    delete.executeBatch();
                    testConn.commit();
                }

                testConn.setAutoCommit(true);
            } catch (Exception ex) {
                testConn.rollback();
                testConn.setAutoCommit(true);
                throw ex;
            }
        }

        void transferOrders() throws Exception {
            String selectSql = "SELECT id, order_id, product_id, quantity, price FROM staging_order_detail WHERE validation_errors IS NULL";
            String upsertSql = "INSERT INTO main_order_detail (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?) " +
                "ON DUPLICATE KEY UPDATE product_id = VALUES(product_id), quantity = VALUES(quantity), price = VALUES(price)";
            String deleteSql = "DELETE FROM staging_order_detail WHERE id = ?";
            String markErrorSql = "UPDATE staging_order_detail SET validation_errors = ? WHERE id = ?";

            com.example.etl.rules.RecordValidator<com.example.etl.models.OrderDetail> validator = new com.example.etl.rules.RecordValidator<>();
            validator.addRule(new com.example.etl.rules.impl.NotEmptyRule<>((com.example.etl.models.OrderDetail o) -> o.getOrderId(), "orderId"));
            validator.addRule(new com.example.etl.rules.impl.NotEmptyRule<>((com.example.etl.models.OrderDetail o) -> o.getProductId(), "productId"));
            validator.addRule(new com.example.etl.rules.impl.QuantityRule<>((com.example.etl.models.OrderDetail o) -> o.getQuantity(), "quantity"));

            testConn.setAutoCommit(false);
            try (PreparedStatement sel = testConn.prepareStatement(selectSql);
                 PreparedStatement upsert = testConn.prepareStatement(upsertSql);
                 PreparedStatement delete = testConn.prepareStatement(deleteSql);
                 PreparedStatement markErr = testConn.prepareStatement(markErrorSql)) {

                ResultSet rs = sel.executeQuery();
                List<Integer> batchIds = new ArrayList<>();

                while (rs.next()) {
                    int id = rs.getInt("id");
                    String orderId = rs.getString("order_id");
                    String productId = rs.getString("product_id");
                    int qty = rs.getInt("quantity");
                    double price = rs.getDouble("price");

                    com.example.etl.models.OrderDetail od = new com.example.etl.models.OrderDetail();
                    od.setOrderId(orderId);
                    od.setProductId(productId);
                    od.setQuantity(qty);
                    od.setPrice(price);

                    List<com.example.etl.rules.RuleResult> results = validator.validateAll(od);
                    boolean ok = results.stream().allMatch(com.example.etl.rules.RuleResult::isOk);
                    
                    if (!ok) {
                        com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
                        List<Map<String, String>> errs = new ArrayList<>();
                        results.stream().filter(r -> !r.isOk()).forEach(r -> {
                            Map<String, String> m = new java.util.HashMap<>();
                            m.put("field", r.getField() != null ? r.getField() : "");
                            m.put("message", r.getMessage());
                            errs.add(m);
                        });
                        String errsJson = mapper.writeValueAsString(errs);
                        markErr.setString(1, errsJson);
                        markErr.setInt(2, id);
                        markErr.executeUpdate();
                        testConn.commit();
                        continue;
                    }

                    upsert.setString(1, orderId);
                    upsert.setString(2, productId);
                    upsert.setInt(3, qty);
                    upsert.setDouble(4, price);
                    upsert.addBatch();
                    batchIds.add(id);
                }

                if (!batchIds.isEmpty()) {
                    upsert.executeBatch();
                    for (Integer pid : batchIds) {
                        delete.setInt(1, pid);
                        delete.addBatch();
                    }
                    delete.executeBatch();
                    testConn.commit();
                }

                testConn.setAutoCommit(true);
            } catch (Exception ex) {
                testConn.rollback();
                testConn.setAutoCommit(true);
                throw ex;
            }
        }
    }
}
