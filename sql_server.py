from mcp.server.fastmcp import FastMCP
import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

mcp = FastMCP("sqlite-db")

# Database configuration
DB_PATH = os.getenv("SQLITE_DB_PATH", "./business_data.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row  # Return rows as dictionaries

# Business insights memo storage
insights_memo = []

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a query and return results"""
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    if query.strip().upper().startswith("SELECT"):
        results = cursor.fetchall()
        return [dict(row) for row in results]
    else:
        conn.commit()
        return [{"affected_rows": cursor.rowcount}]


@mcp.tool()
def read_query(query: str) -> Dict[str, Any]:
    """
    Execute SELECT queries to read data from the database.
    
    Args:
        query: The SELECT SQL query to execute
    
    Returns:
        Dictionary containing query results
    
    Example:
        read_query("SELECT * FROM customers WHERE age > 25")
    """
    try:
        if not query.strip().upper().startswith("SELECT"):
            return {"error": "Only SELECT queries are allowed. Use write_query for modifications."}
        
        results = execute_query(query)
        return {
            "success": True,
            "row_count": len(results),
            "data": results
        }
    except sqlite3.Error as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
def write_query(query: str) -> Dict[str, Any]:
    """
    Execute INSERT, UPDATE, or DELETE queries to modify data.
    
    Args:
        query: The SQL modification query (INSERT/UPDATE/DELETE)
    
    Returns:
        Dictionary with affected rows count
    
    Example:
        write_query("INSERT INTO customers (name, age) VALUES ('John', 30)")
    """
    try:
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return {"error": "Use read_query for SELECT statements"}
        
        if not any(query_upper.startswith(cmd) for cmd in ["INSERT", "UPDATE", "DELETE"]):
            return {"error": "Only INSERT, UPDATE, or DELETE queries allowed"}
        
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        
        return {
            "success": True,
            "affected_rows": cursor.rowcount,
            "message": f"Successfully modified {cursor.rowcount} row(s)"
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        conn.rollback()
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
def create_table(query: str) -> Dict[str, Any]:
    """
    Create new tables in the database.
    
    Args:
        query: CREATE TABLE SQL statement
    
    Returns:
        Confirmation of table creation
    
    Example:
        create_table("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
    """
    try:
        if not query.strip().upper().startswith("CREATE TABLE"):
            return {"error": "Only CREATE TABLE statements allowed"}
        
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        
        return {
            "success": True,
            "message": "Table created successfully"
        }
    except sqlite3.Error as e:
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
def list_tables() -> Dict[str, Any]:
    """
    Get a list of all tables in the database.
    
    Returns:
        Dictionary containing array of table names
    
    Example:
        list_tables()
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        return {
            "success": True,
            "count": len(tables),
            "tables": tables
        }
    except sqlite3.Error as e:
        return {"error": f"Database error: {str(e)}"}


@mcp.tool()
def describe_table(table_name: str) -> Dict[str, Any]:
    """
    View schema information for a specific table.
    
    Args:
        table_name: Name of the table to describe
    
    Returns:
        Dictionary containing column definitions with names and types
    
    Example:
        describe_table("customers")
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            return {"error": f"Table '{table_name}' does not exist"}
        
        schema = []
        for col in columns:
            schema.append({
                "column_id": col[0],
                "name": col[1],
                "type": col[2],
                "not_null": bool(col[3]),
                "default_value": col[4],
                "primary_key": bool(col[5])
            })
        
        return {
            "success": True,
            "table_name": table_name,
            "columns": schema
        }
    except sqlite3.Error as e:
        return {"error": f"Database error: {str(e)}"}


@mcp.tool()
def append_insight(insight: str) -> Dict[str, Any]:
    """
    Add new business insights to the memo resource.
    
    Args:
        insight: Business insight discovered from data analysis
    
    Returns:
        Confirmation of insight addition
    
    Example:
        append_insight("Sales increased 25% in Q4 compared to Q3")
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        insight_entry = {
            "timestamp": timestamp,
            "insight": insight
        }
        insights_memo.append(insight_entry)
        
        return {
            "success": True,
            "message": "Insight added successfully",
            "total_insights": len(insights_memo),
            "insight": insight_entry
        }
    except Exception as e:
        return {"error": f"Error adding insight: {str(e)}"}


@mcp.tool()
def get_insights_memo() -> Dict[str, Any]:
    """
    Retrieve all business insights from the memo.
    
    Returns:
        Dictionary containing all stored insights
    
    Example:
        get_insights_memo()
    """
    try:
        if not insights_memo:
            return {
                "success": True,
                "message": "No insights recorded yet",
                "insights": []
            }
        
        memo_text = "BUSINESS INSIGHTS MEMO\n"
        memo_text += "=" * 50 + "\n\n"
        
        for idx, entry in enumerate(insights_memo, 1):
            memo_text += f"{idx}. [{entry['timestamp']}]\n"
            memo_text += f"   {entry['insight']}\n\n"
        
        return {
            "success": True,
            "total_insights": len(insights_memo),
            "memo": memo_text,
            "insights": insights_memo
        }
    except Exception as e:
        return {"error": f"Error retrieving memo: {str(e)}"}


@mcp.tool()
def create_sample_database(topic: str = "sales") -> Dict[str, Any]:
    """
    Create a sample database with demo data for learning purposes.
    
    Args:
        topic: Business domain (sales, customers, inventory, employees)
    
    Returns:
        Confirmation with details of created tables
    
    Example:
        create_sample_database("sales")
    """
    try:
        cursor = conn.cursor()
        
        if topic.lower() == "sales":
            # Create sales table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    sale_date DATE NOT NULL,
                    region TEXT NOT NULL
                )
            """)
            
            # Insert sample data
            sample_sales = [
                ("Laptop", 5, 1200.00, "2024-01-15", "North"),
                ("Mouse", 20, 25.00, "2024-01-16", "South"),
                ("Keyboard", 15, 75.00, "2024-01-17", "East"),
                ("Monitor", 8, 300.00, "2024-01-18", "West"),
                ("Laptop", 3, 1200.00, "2024-02-10", "North"),
                ("Mouse", 25, 25.00, "2024-02-11", "South"),
                ("Headphones", 12, 50.00, "2024-02-12", "East")
            ]
            
            cursor.executemany(
                "INSERT INTO sales (product, quantity, price, sale_date, region) VALUES (?, ?, ?, ?, ?)",
                sample_sales
            )
            
        elif topic.lower() == "customers":
            # Create customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    city TEXT,
                    signup_date DATE NOT NULL
                )
            """)
            
            sample_customers = [
                ("Alice Smith", "alice@email.com", 28, "New York", "2023-06-15"),
                ("Bob Johnson", "bob@email.com", 35, "Los Angeles", "2023-07-20"),
                ("Carol White", "carol@email.com", 42, "Chicago", "2023-08-10"),
                ("David Brown", "david@email.com", 31, "Houston", "2023-09-05"),
                ("Eve Davis", "eve@email.com", 26, "Phoenix", "2023-10-12")
            ]
            
            cursor.executemany(
                "INSERT INTO customers (name, email, age, city, signup_date) VALUES (?, ?, ?, ?, ?)",
                sample_customers
            )
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Sample {topic} database created successfully!",
            "topic": topic,
            "next_steps": [
                f"Use list_tables() to see all tables",
                f"Use describe_table('{topic}') to see table structure",
                f"Use read_query('SELECT * FROM {topic}') to view data"
            ]
        }
    except sqlite3.Error as e:
        conn.rollback()
        return {"error": f"Database error: {str(e)}"}


@mcp.tool()
def analyze_sales_data() -> Dict[str, Any]:
    """
    Perform automatic analysis on sales data and generate insights.
    
    Returns:
        Dictionary with analysis results and auto-generated insights
    
    Example:
        analyze_sales_data()
    """
    try:
        cursor = conn.cursor()
        
        # Check if sales table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales'")
        if not cursor.fetchone():
            return {"error": "Sales table not found. Create sample database first using create_sample_database('sales')"}
        
        insights = []
        
        # Analysis 1: Total revenue
        cursor.execute("SELECT SUM(quantity * price) as total_revenue FROM sales")
        total_revenue = cursor.fetchone()[0]
        insights.append(f"Total revenue across all sales: ${total_revenue:,.2f}")
        
        # Analysis 2: Best selling product
        cursor.execute("""
            SELECT product, SUM(quantity) as total_qty, SUM(quantity * price) as revenue
            FROM sales 
            GROUP BY product 
            ORDER BY revenue DESC 
            LIMIT 1
        """)
        best_product = cursor.fetchone()
        insights.append(f"Best selling product: {best_product[0]} with {best_product[1]} units sold (${best_product[2]:,.2f} revenue)")
        
        # Analysis 3: Top region
        cursor.execute("""
            SELECT region, SUM(quantity * price) as revenue
            FROM sales 
            GROUP BY region 
            ORDER BY revenue DESC 
            LIMIT 1
        """)
        top_region = cursor.fetchone()
        insights.append(f"Highest revenue region: {top_region[0]} with ${top_region[1]:,.2f}")
        
        # Auto-append insights to memo
        for insight in insights:
            append_insight(insight)
        
        return {
            "success": True,
            "analysis_complete": True,
            "insights_generated": len(insights),
            "insights": insights,
            "message": "Analysis complete! Insights have been added to the memo."
        }
    except sqlite3.Error as e:
        return {"error": f"Database error: {str(e)}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")