---
type: reference
---

# SQL Development

Guidelines for generating SQL statements and stored procedures [source: instructions/sql-sp-generation.instructions.md]

## Database schema generation
- all table names should be in singular form (e.g., `customers`)
- all column names should be in singular form (e.g., `customer_id`)
- all tables should have a primary key column named `id`
- all tables should have a column named `created_at` to store the creation timestamp
- all tables should have a column named `updated_at` to store the last update timestamp

## Database schema design
- all tables should have a primary key constraint
- all foreign key constraints should have a name (e.g., `fk_orders_customers`)
- all foreign key constraints should be defined inline
- all foreign key constraints should have `ON DELETE CASCADE` option
- all foreign key constraints should have `ON UPDATE CASCADE` option
- all foreign key constraints should reference the primary key of the parent table (e.g., `orders.customer_id`)

## SQL Coding Style
- use uppercase for SQL keywords (SELECT, FROM, WHERE)
- use consistent indentation for nested queries and conditions
- include comments to explain complex logic (e.g., `-- Retrieve all orders for a specific customer`)
- break long queries into multiple lines for readability
- organize clauses consistently (SELECT, FROM, JOIN, WHERE, GROUP BY, HAVING, ORDER BY)

## SQL Query Structure
- use explicit column names in SELECT statements instead of SELECT * (e.g., `SELECT customer_id, order_date`)
- qualify column names with table name or alias when using multiple tables (e.g., `orders.order_date`)
- limit the use of subqueries when joins can be used instead
- include LIMIT/TOP clauses to restrict result sets (e.g., `SELECT TOP 10 orders.id FROM orders`)
- use appropriate indexing for frequently queried columns
- avoid using functions on indexed columns in WHERE clauses (e.g., `WHERE orders.order_date >= '2022-01-01'`)

## Stored Procedure Naming Conventions
- prefix stored procedure names with 'usp_' (e.g., `usp_GetCustomerOrders`)
- use PascalCase for stored procedure names (e.g., `uspGetProducts`)
- use descriptive names that indicate purpose (e.g., `usp_GetCustomerOrders`)
- include plural noun when returning multiple records (e.g., `usp_GetProducts`)
- include singular noun when returning single record (e.g., `usp_GetProduct`)

## Parameter Handling
- prefix parameters with '@' (e.g., `@customer_id INT`)
- use camelCase for parameter names (e.g., `@customerId INT`)
- provide default values for optional parameters (e.g., `@customer_id INT = NULL`)
- validate parameter values before use
- document parameters with comments (e.g., `-- @customer_id: ID of the customer to retrieve orders for`)
- arrange parameters consistently (required first, optional later)

## Stored Procedure Structure
- include header comment block with description, parameters, and return values
- return standardized error codes/messages (e.g., `RAISERROR('Invalid customer ID', 16, 1)`)
- return result sets with consistent column order
- use OUTPUT parameters for returning status information (e.g., `@status INT OUTPUT`)
- prefix temporary tables with 'tmp_' (e.g., `CREATE TABLE #tmpOrders (...)`)

## SQL Security Best Practices
- parameterize all queries to prevent SQL injection (e.g., using prepared statements or parameterized queries)
- use prepared statements when executing dynamic SQL
- avoid embedding credentials in SQL scripts
- implement proper error handling without exposing system details (e.g., `THROW;`)
- avoid using dynamic SQL within stored procedures

## Transaction Management
- explicitly begin and commit transactions (e.g., `BEGIN TRANSACTION; COMMIT;`)
- use appropriate isolation levels based on requirements (e.g., READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE)
- avoid long-running transactions that lock tables
- use batch processing for large data operations
- include SET NOCOUNT ON for stored procedures that modify data (e.g., `SET NOCOUNT ON;`)