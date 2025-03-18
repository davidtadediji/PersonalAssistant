from typing import Optional, Any, Dict

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from pymongo import MongoClient

from src.logger import configured_logger

load_dotenv()


class MongoDB:
    def __init__(self, db_name: str, collection_name: Optional[str] = None):
        """
        Initialize the MongoDB connection.

        Args:
            db_name (str): The name of the MongoDB database.
            collection_name (str, optional): The name of the MongoDB collection. Defaults to None.
        """
        self.client = MongoClient()  # Connect to the default MongoDB server
        self.db = self.client[db_name]
        self.collection_name = collection_name
        self.collection = self.db[collection_name] if collection_name else None
        configured_logger.info(f"MongoDB connection established to database: {db_name}")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a document into the MongoDB collection."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        result = self.collection.insert_one(data)
        configured_logger.info(f"Data inserted with ID {result.inserted_id}")
        return {
            "status": "success",
            "message": f"Data inserted with ID {result.inserted_id}",
        }

    def read(self, filter_condition: Optional[Dict[str, Any]] = None) -> Any:
        """Find documents in the MongoDB collection based on a filter."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        results = list(self.collection.find(filter_condition or {}))  # Default to empty filter if none provided
        if results:
            configured_logger.info(f"Read {len(results)} document(s) from collection.")
        else:
            configured_logger.warn("No documents found for the given filter.")
        return results if results else []

    def update(self, filter_condition: Dict[str, Any], update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a document in the MongoDB collection based on a filter."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        result = self.collection.update_one(filter_condition, {"$set": update_data})
        if result.modified_count > 0:
            configured_logger.info("Data updated successfully.")
            return {"status": "success", "message": "Data updated successfully"}
        configured_logger.warn("No documents matched the filter for update.")
        return {"status": "success", "message": "No documents matched the filter"}

    def delete(self, filter_condition: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a document from the MongoDB collection based on a filter."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        result = self.collection.delete_one(filter_condition)
        if result.deleted_count > 0:
            configured_logger.info("Data deleted successfully.")
            return {"status": "success", "message": "Data deleted successfully"}
        configured_logger.warn("No documents matched the filter for deletion.")
        return {"status": "success", "message": "No documents matched the filter"}

    def execute(self, query: Dict[str, Any]) -> Any:
        """Execute a custom query on the MongoDB collection."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        result = self.collection.find(query)
        results = list(result)
        if results:
            configured_logger.info(f"Executed query and found {len(results)} result(s).")
        else:
            configured_logger.warn("Query returned no results.")
        return results if results else []

    def close(self):
        """Close the MongoDB client connection."""
        self.client.close()
        configured_logger.info("MongoDB client connection closed.")


class MongoDatabaseQuery(BaseModel):
    operation: str
    db_name: str
    collection_name: Optional[str] = None
    data: Optional[Dict] = None
    filter_condition: Optional[Dict] = None
    update_data: Optional[Dict] = None
    query: Optional[Dict] = None


def mongo_database(
        operation: str,
        db_name: str,
        collection_name: Optional[str] = None,
        data: Optional[dict] = None,
        filter_condition: Optional[dict] = None,
        update_data: Optional[dict] = None,
        query: Optional[dict] = None,
) -> Any:
    """
    Perform operations on the MongoDB database using the MongoDB class.

    Args:
        operation (str): The type of operation ('create', 'read', 'update', 'delete', 'execute').
        db_name (str): The name of the database.
        collection_name (str, optional): The name of the collection (required for 'create', 'update', 'delete').
        data (dict, optional): The data for 'create' and 'update' operations.
        filter_condition (dict, optional): The filter condition for 'read', 'update', or 'delete' operations.
        update_data (dict, optional): The data to update in 'update' operation.
        query (dict, optional): A custom query for 'execute' operation.

    Returns:
        dict or list: The result of the operation.
    """
    try:
        # Create MongoDB object instance
        db_obj = MongoDB(db_name, collection_name)

        # Perform the appropriate operation based on the input
        if operation == "create" and data:
            return db_obj.create(data)
        elif operation == "read":
            return db_obj.read(filter_condition)
        elif operation == "update" and filter_condition and update_data:
            return db_obj.update(filter_condition, update_data)
        elif operation == "delete" and filter_condition:
            return db_obj.delete(filter_condition)
        elif operation == "execute" and query:
            return db_obj.execute(query)
        else:
            raise ValueError("Invalid operation or missing parameters")

    except Exception as e:
        configured_logger.error(f"MongoDB operation failed -> {e}")
        raise Exception(f"MongoDB operation failed -> {e}") from e


def mongo_database_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="mongo_database",
        func=mongo_database,
        description=(
            "Perform operations on the MongoDB database using the MongoDB class.\n"
            " - operation: The type of operation ('create', 'read', 'update', 'delete', 'execute').\n"
            " - db_name: The name of the database.\n"
            " - collection_name, data, filter_condition, update_data, query: Optional arguments."
        ),
        input_schema=MongoDatabaseQuery,
    )
