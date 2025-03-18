import os
from pathlib import Path

from src.assistant.tools.create_file import create_file
from src.assistant.tools.database_storage.sql_database import sql_database
from src.assistant.tools.web_browsing.browser_use import execute_browser_task


def test_create_file():
    # Sample data for testing
    content = [
        {"text": "Hello, this is a test text.", "size": 12, "align": "L", "new_line": True},
        {"text": "This is another line in the PDF.", "size": 14, "align": "C", "new_line": True},
    ]

    # Test PDF creation
    pdf_filename = "test_output.pdf"
    pdf_result = create_file(pdf_filename, "pdf", content)
    assert pdf_result == f"PDF created successfully at: {pdf_filename}", "PDF creation failed"
    assert Path(pdf_filename).exists(), "PDF file does not exist"
    print(f"Test passed for PDF: {pdf_result}")

    # Test Text file creation
    txt_filename = "test_output.txt"
    txt_result = create_file(txt_filename, "txt", content)
    assert txt_result == f"Text file created successfully at: {txt_filename}", "Text file creation failed"
    assert Path(txt_filename).exists(), "Text file does not exist"
    print(f"Test passed for Text file: {txt_result}")

    # Cleanup: Remove created test files
    os.remove(pdf_filename)
    os.remove(txt_filename)
    print("Test files cleaned up.")

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


def test_browser_task_tool():
    test_task = (
        "Go to Reddit, search for 'browser-use' in the search bar, "
        "click on the first post and return the first comment."
    )

    try:
        # Using the tool to execute the browser task
        task_result = execute_browser_task(test_task)

        # Log the result of the task
        print(f"Task result: {task_result}")

    except Exception as e:
        # Log any error that occurs during task execution
        print(f"Error during browser task execution: {e}")

test_browser_task_tool()

# Call the test function
test_sql_database()

# Run the test
test_create_file()
