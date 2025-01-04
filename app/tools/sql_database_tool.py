import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from app.logger import configured_logger

def get_resource_path(resource_name: str) -> Path:
    """
    Get the path to a resource file in the 'resources' directory.

    Args:
        resource_name (str): The name of the resource file (e.g., 'test_database.db').

    Returns:
        Path: The full path to the resource file.
    """
    project_root = Path(__file__).resolve().parent
    resources_dir = project_root / "../../resources"

    # Ensure the resources directory exists
    resources_dir.mkdir(parents=True, exist_ok=True)

    # Return the full path to the requested resource
    return resources_dir / resource_name


class SQLDatabaseQuery(BaseModel):
    operation: str
    db_name: str
    table_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    columns: Optional[List[str]] = None
    condition: Optional[str] = None
    query: Optional[str] = None


def sql_database(
        operation,
        db_name,
        table_name=None,
        data=None,
        columns=None,
        condition=None,
        query=None,
):
    """
    Perform CRUD operations and custom queries on the database.

    Args:
        operation (str): The type of operation ('create', 'read', 'update', 'delete', 'execute').
        db_name (str): The name of the database file.
        table_name (str, optional): The name of the table to operate on (required for 'create', 'update', 'delete').
        data (dict, optional): The data to insert or update (required for 'create', 'update').
        columns (list, optional): List of column names (required for 'create').
        condition (str, optional): The condition for 'update' or 'delete' (optional).
        query (str, optional): A custom SQL query for 'execute' operation (optional).

    Returns:
        dict: A dictionary containing the status and message of the operation.
            For 'read' and 'execute' operations, it returns the result of the query.
    """
    connection = None
    try:
        configured_logger.info(f"Attempting operation '{operation}' on database '{db_name}'")
        db_path = get_resource_path(db_name)  # Get the full path to the database
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        if operation == "create" and data and table_name and columns:
            placeholders = ", ".join("?" * len(data))
            column_names = ", ".join(columns)
            sql_query = (
                f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            )
            cursor.execute(sql_query, tuple(data.values()))
            connection.commit()
            configured_logger.info(f"Data inserted into '{table_name}' successfully.")
            return {"status": "success", "message": "Data inserted successfully"}

        elif operation == "read" and query:
            cursor.execute(query)
            results = cursor.fetchall()
            configured_logger.info(f"Data read successfully from the database.")
            return [dict(row) for row in results] if results else []

        elif operation == "update" and data and table_name and condition:
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            sql_query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
            cursor.execute(sql_query, tuple(data.values()))
            connection.commit()
            configured_logger.info(f"Data in '{table_name}' updated successfully.")
            return {"status": "success", "message": "Data updated successfully"}

        elif operation == "delete" and table_name and condition:
            sql_query = f"DELETE FROM {table_name} WHERE {condition}"
            cursor.execute(sql_query)
            connection.commit()
            configured_logger.info(f"Data from '{table_name}' deleted successfully.")
            return {"status": "success", "message": "Data deleted successfully"}

        elif operation == "execute" and query:
            cursor.execute(query)
            if query.strip().lower().startswith(("insert", "update", "delete")):
                connection.commit()
            if query.strip().lower().startswith("select"):
                results = cursor.fetchall()
                configured_logger.info(f"Custom query executed successfully.")
                return [dict(row) for row in results] if results else []

        else:
            error_message = "Invalid parameters or operation"
            configured_logger.error(error_message)
            raise ValueError(error_message)

    except sqlite3.Error as e:
        error_message = f"Database operation failed -> {e}"
        configured_logger.error(error_message)
        raise Exception(error_message) from e

    finally:
        if connection:
            connection.close()
            configured_logger.info("Database connection closed.")


def sql_database_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="sql_database",
        func=sql_database,
        description=(
            "Perform CRUD operations and custom queries on the database.\n"
            "\n"
            "### Operations and Parameters:\n"
            "- **operation** (str): Specifies the type of operation to perform:\n"
            "    - 'create': Inserts new data into a table. Requires `table_name`, `data`, and `columns`.\n"
            "    - 'read': Retrieves data from the database. Requires a custom `query`.\n"
            "    - 'update': Updates existing data in a table. Requires `table_name`, `data`, and `condition`.\n"
            "    - 'delete': Removes data from a table. Requires `table_name` and `condition`.\n"
            "    - 'execute': Executes a custom SQL query. Requires `query`.\n"
            "\n"
            "- **db_name** (str): The name of the SQLite database file to connect to.\n"
            "- **table_name** (str, optional): The name of the table for 'create', 'update', or 'delete' operations.\n"
            "- **data** (dict, optional): The data to be inserted or updated. Required for 'create' and 'update' operations.\n"
            "- **columns** (list, optional): List of column names for the 'create' operation.\n"
            "- **condition** (str, optional): A condition clause for 'update' or 'delete' operations (e.g., 'id=1').\n"
            "- **query** (str, optional): A custom SQL query for the 'execute' operation. Can handle SELECT, INSERT, UPDATE, or DELETE statements.\n"
            "\n"
            "### Returns:\n"
            "- A dictionary with the status and a message about the operation's success or failure.\n"
            "- For 'read' and 'execute' operations, it returns the query results if applicable.\n"
            "\n"
            "### Usage Notes:\n"
            "- Ensure the database file exists and is accessible.\n"
            "- The `table_name`, `data`, `columns`, and `condition` parameters are contextually required for certain operations.\n"
            "- Custom queries (e.g., for 'execute') should be valid SQL statements.\n"
        ),
        input_schema=SQLDatabaseQuery,
    )


def test_sql_database():
    # Define sample data for testing
    db_name = "test_database.db"
    table_name = "test_table"

    # Create a table (for testing)
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL
    );
    """

    # Create a sample data for insertion
    sample_data = {
        "name": "John Doe",
        "age": 30
    }

    # Define columns for the insert
    columns = ["name", "age"]

    try:
        # Step 1: Create a test table (execute query)
        result = sql_database(
            operation="execute",
            db_name=db_name,
            query=create_table_query
        )
        print("Table created:", result)

        # Step 2: Insert sample data (create operation)
        result = sql_database(
            operation="create",
            db_name=db_name,
            table_name=table_name,
            data=sample_data,
            columns=columns
        )
        print("Data inserted:", result)

        # Step 3: Read the inserted data (read operation)
        read_query = f"SELECT * FROM {table_name} WHERE name='John Doe';"
        result = sql_database(
            operation="read",
            db_name=db_name,
            query=read_query
        )
        print("Read data:", result)

    except Exception as e:
        print(f"Error occurred: {e}")


# Call the test function
test_sql_database()
