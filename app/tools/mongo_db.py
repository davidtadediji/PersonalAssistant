from typing import Optional, Any, Dict

from pymongo import MongoClient


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

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a document into the MongoDB collection."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        result = self.collection.insert_one(data)
        return {
            "status": "success",
            "message": f"Data inserted with ID {result.inserted_id}",
        }

    def read(self, filter_condition: Optional[Dict[str, Any]] = None) -> Any:
        """Find documents in the MongoDB collection based on a filter."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        results = list(
            self.collection.find(filter_condition or {})
        )  # Default to empty filter if none provided
        return results if results else []

    def update(
        self, filter_condition: Dict[str, Any], update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a document in the MongoDB collection based on a filter."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        result = self.collection.update_one(filter_condition, {"$set": update_data})
        if result.modified_count > 0:
            return {"status": "success", "message": "Data updated successfully"}
        return {"status": "success", "message": "No documents matched the filter"}

    def delete(self, filter_condition: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a document from the MongoDB collection based on a filter."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        result = self.collection.delete_one(filter_condition)
        if result.deleted_count > 0:
            return {"status": "success", "message": "Data deleted successfully"}
        return {"status": "success", "message": "No documents matched the filter"}

    def execute(self, query: Dict[str, Any]) -> Any:
        """Execute a custom query on the MongoDB collection."""
        if not self.collection:
            raise ValueError("Collection not specified.")
        result = self.collection.find(query)
        results = list(result)
        return results if results else []

    def close(self):
        """Close the MongoDB client connection."""
        self.client.close()
