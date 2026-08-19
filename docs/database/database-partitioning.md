---
icon: material/view-split-vertical
---

# Database Partitioning

<a class="watch-video" href="https://www.youtube.com/watch?v=oJj-pltxBUM">&#9654;&nbsp;Watch Video</a>

Database partitioning is a technique used to divide a large database table into smaller, more manageable pieces, called partitions. Each partition holds a subset of the data, which can improve performance, simplify maintenance, and enhance scalability by allowing operations to run on smaller data sets. Partitioning is especially useful for very large databases where query performance can degrade over time due to the sheer volume of data.

### Types of Partitioning Methods

1. **Range Partitioning**:

    - **Description**: Data is divided into partitions based on a range of values in a specified column. For example, a table with a `date` column can be partitioned by year or month.

    - **Use Case**: Useful when data naturally falls into continuous ranges, such as dates or numbers.

1. **List Partitioning**:

    - **Description**: Data is divided based on a list of discrete values. Each partition holds rows that match one of the specified values.

    - **Use Case**: Suitable when the data can be categorized into a small number of distinct groups, such as regions or departments.

1. **Hash Partitioning**:

    - **Description**: Data is distributed across partitions based on a hash function applied to a column's value. The result of the hash determines the partition.

    - **Use Case**: Useful for distributing data evenly across partitions when there is no natural grouping or ordering.

1. **Composite Partitioning**:

    - **Description**: A combination of multiple partitioning methods, such as range and hash partitioning. This allows for more complex partitioning schemes.

    - **Use Case**: Used when there are multiple dimensions along which data can be partitioned.

### Implementing Partitioning in PostgreSQL

In PostgreSQL, you can implement partitioning using declarative partitioning (introduced in PostgreSQL 10). Here's how you can implement different types of partitioning:

### Range Partitioning Example

```sql
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    amount DECIMAL(10, 2)
) PARTITION BY RANGE (sale_date);

CREATE TABLE sales_2023 PARTITION OF sales
    FOR VALUES FROM ('2023-01-01') TO ('2023-12-31');

CREATE TABLE sales_2024 PARTITION OF sales
    FOR VALUES FROM ('2024-01-01') TO ('2024-12-31');
```

### List Partitioning Example

```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    department TEXT NOT NULL,
    name TEXT
) PARTITION BY LIST (department);

CREATE TABLE sales_department PARTITION OF employees
    FOR VALUES IN ('Sales');

CREATE TABLE hr_department PARTITION OF employees
    FOR VALUES IN ('HR');
```

### Hash Partitioning Example

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATE
) PARTITION BY HASH (customer_id);

CREATE TABLE orders_p0 PARTITION OF orders
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE orders_p1 PARTITION OF orders
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
```

### Implementing Partitioning in Django

In Django, implementing partitioning is not natively supported out of the box, but it can be achieved using custom database operations or by manually creating the partitions in PostgreSQL and using Django's ORM to interact with them.

Here's how you can manage partitioned tables in Django:

1. **Manually Create Partitions**: As shown above, create partitions in PostgreSQL. Django will treat them as regular tables.

1. **Custom Model Manager**: Create a custom manager to handle operations on specific partitions. You can define methods that target specific partitions based on your logic.

```python
from django.db import models

class SalesManager(models.Manager):
    def for_year(self, year):
        table_name = f'sales_{year}'
        return self.raw(f'SELECT * FROM {table_name}')

class Sales(models.Model):
    sale_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    objects = SalesManager()

    class Meta:
        managed = False  # Do not create a table for this model
```

1. **Use Raw SQL for Partitioned Queries**: Sometimes, it's easier to use raw SQL queries to interact with partitioned tables, especially when dealing with complex partitioning schemes.

### Summary

Database partitioning is a powerful tool for managing large datasets. In PostgreSQL, it's relatively straightforward to implement using declarative partitioning methods like range, list, and hash. In Django, partitioning requires more manual work but can be managed with custom managers, raw SQL, or direct interaction with PostgreSQL partitions.
