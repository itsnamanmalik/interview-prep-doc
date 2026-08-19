---
icon: material/help-circle-outline
---

![](../assets/images/database-general-questions-cover.jpg){ .cover-photo }

# General Questions

### What is Difference Betweet MySQL & PostgreSQL?

1. **Data Integrity and Concurrency**:

    - **PostgreSQL**: Strong emphasis on data integrity with features like MVCC (Multi-Version Concurrency Control) and support for advanced data types (JSON, XML, etc.).

    - **MySQL**: It Prioritizes speed and performance which sometimes compromising strict **data integrity**. It has optional transactional support with **InnoDB**.

1. **Extensibility and Standards Compliance**:

    - **PostgreSQL**: Highly extensible and compliant with SQL standards. It supports custom data types, operators, and full-text search.

    - **MySQL**: Less extensible but simpler to use. It offers support for a variety of storage engines, which can be switched depending on the use case.

1. **Performance and Scalability**:

    - **PostgreSQL**: Performs well with complex queries and large datasets, supporting horizontal scaling through sharding and replication.

    - **MySQL**: Known for its read-heavy workload efficiency and high-speed read operations. MySQL’s replication can be challenging in terms of **consistency**.

### What is MVCC (Multi-Version Concurrency Control)?

- **Multiple Versions**: MVCC keeps multiple versions of each data item to allow multiple transactions to read and write without interfering with each other.

- **Read Consistency**: Readers can access a snapshot of the database at a particular time without being blocked by ongoing write operations, ensuring a consistent view of the data.

- **No Locks for Reads**: MVCC allows readers to work with a snapshot of data, so they don’t need to wait for write operations to complete, reducing the need for read locks.

- **Write Operations**: Writers create new versions of data items rather than overwriting existing ones, ensuring that readers can still access the previous versions until the transaction is complete.

- **Transaction Timestamps**: Each transaction is assigned a timestamp or transaction ID, which is used to determine which version of the data a transaction should see.

- **Garbage Collection**: Older, obsolete versions of data are eventually cleaned up (garbage collected) after they are no longer needed by any transactions.

- **Increased Concurrency**: MVCC enhances database concurrency by allowing more transactions to run in parallel without conflicts, compared to traditional locking mechanisms.

- **Common in Databases**: MVCC is widely used in databases like PostgreSQL, MySQL (InnoDB), and Oracle to provide high-performance concurrency control.

### **What is a composite key?**

A composite key is a type of key used in the database that consists of two or more columns in a table that can uniquely identify each row. The combination of columns guarantees uniqueness, whereas individual columns do not. Composite keys are used when no single column can uniquely identify each row.

In Simple Words: Django Unique Together Constraint use Composite Key under the hood.

### **Key features of Database Normalization and Denormalization.**

>> Normalization:

- Reduces data redundancy.

- Improves data integrity.

- Involves organizing data into separate tables to minimize duplication.

>> Denormalization:

- Adds some redundancy back to the database.

- Aims to improve the performance of read operations.

- Reduces the number of joins needed between tables.

- Prioritizes query performance over strict data integrity.

- Used in specific scenarios where performance needs outweigh the benefits of normalization.

- Might increase the risk of data anomalies.

### **How can you optimize a slow-running SQL query?**

To optimize a slow-running SQL query, consider the following strategies:

- Use indexes: Ensure that indexes are used on columns frequently in WHERE clauses or as join keys to speed up data retrieval.

- Optimize Joins: If possible, reduce the number of joins and ensure you only join necessary tables. Consider the order of joins in complex queries.

- Limit data: Use WHERE clauses to filter rows early and limit the data the query returns with the LIMIT or TOP clause.

- Use subqueries wisely: Subqueries can sometimes slow down a query; consider using JOINs where appropriate.

- Avoid SELECT: Specify only the necessary columns instead of using SELECT * to retrieve all columns.

- Query optimization tools: Use built-in database tools and explain plans to analyze and optimize your queries.

### **What is a subquery, and when would you use one?**

A subquery is a SQL query nested inside a larger query. It can be used in SELECT, INSERT, UPDATE, or DELETE statements or in the WHERE clause of another SQL query. Subqueries often perform operations requiring multiple steps in a single query, such as filtering results based on an aggregate value or checking for records in a related table.

### **Describe the difference between the HAVING and WHERE clause.**

- WHERE Clause: This clause filters rows before groupings are made. It applies conditions to individual records in the table(s) involved in the SQL statement. The WHERE clause cannot be used with aggregate functions.

- HAVING Clause: This clause filters groups after applying the GROUP BY clause. It is often used with aggregate functions (COUNT, MAX, MIN, SUM, AVG) to filter the results of a GROUP BY operation.

### **How do you implement pagination in SQL queries?**

Pagination in SQL queries can be implemented using the LIMIT and OFFSET clauses (in MySQL, PostgreSQL) or the FETCH NEXT and OFFSET clauses (in SQL Server, Oracle 12c+). For example, to retrieve the second set of 10 records:

**Query:**

```sql
SELECT * FROM table_name LIMIT 10 OFFSET 10;
```

### **What are stored procedures, and what are their advantages?**

Stored procedures are precompiled SQL statements stored in the database. They can be executed with a single call, allowing complex operations to be encapsulated as public functions on the database server. The advantages of stored procedures include:

- Performance: Stored procedures are precompiled, running faster than dynamic SQL queries.

- Reduced Network Traffic: Only the call to the procedure is sent across the network, not the procedure code itself.

- Security: Stored procedures can provide an additional layer of security, allowing users to execute complex operations without granting them direct access to the underlying tables.

- Reusability and Maintainability: Stored procedures allow you to centralize logic in the database, making the code more reusable and easier to maintain.

### **How do database triggers work?**

Database triggers are special stored procedures automatically executed in response to certain events or actions in a database. Triggers are used to enforce business rules, maintain data integrity, and automate database tasks. Database triggers are commonly used with constraints, stored procedures, and other objects to enforce complex business logic and ensure data consistency.
