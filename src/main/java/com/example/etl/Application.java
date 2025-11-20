package com.example.etl;

import com.example.etl.consumer.EmployeeConsumer;
import com.example.etl.producer.CSVProducer;

public class Application {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            System.out.println("Usage: java -jar app.jar [producer|employee-consumer]");
            return;
        }
        switch (args[0]) {
            case "producer":
                CSVProducer.main(args);
                break;
            case "employee-consumer":
                EmployeeConsumer.main(args);
                break;
            case "order-consumer":
                com.example.etl.consumer.OrderConsumer.main(args);
                break;
            case "transform":
                com.example.etl.transform.TransformLoad.main(args);
                break;
            default:
                System.out.println("Unknown command: " + args[0]);
        }
    }
}
