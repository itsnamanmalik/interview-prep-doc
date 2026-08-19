---
icon: simple/mysql
---

# SQL Queries Questions

### Find Second Highest Salary of the employee from data table.

```sql
SELECT salary FROM employee ORDER BY salary DESC LIMIT 1 OFFSET 1
```

### Find Nth Highest Salary of the employee from data table.

```sql
SELECT salary FROM employee ORDER BY salary DESC LIMIT 1 OFFSET N-1;
```

### Show Department wise highest salary.

```sql
SELECT MAX(salary), deptno FROM employee GROUP BY deptno;
```

### Show Department wise minimum salary.

```sql
SELECT MIN(salary), deptno FROM employee GROUP BY deptno;
```

### Show Department wise employee count.

```sql
SELECT COUNT(*), deptno FROM employee GROUP BY deptno;
```

### Fetch unique values of major Subjects from students table.

```sql
SELECT DISTINCT major from student;
```

### Print the first 3 characters of FIRST_NAME from Student table.

```sql
SELECT SUBSTRING(FIRST_NAME, 1, 3) FROM Student;
```

### Display the details of students who have received scholarships, including their names, scholarship amounts, and scholarship dates.

```sql
SELECT
    student.first_name,
    student.last_name,
    scholarship.scholarship_name,
    scholarship.scholarship_date
FROM
    student
INNER JOIN
    scholarship ON student.student_id = scholarship.student_ref_id;
```
