import os
from typing import Any
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.logger import configured_logger

# Load environment variables from .env
load_dotenv()


class S3:
    """
    A class to interact with AWS S3, providing methods for common operations.
    """

    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        configured_logger.info("S3 client initialized.")

    def list_buckets(self) -> list:
        try:
            response = self.s3.list_buckets()
            configured_logger.info("Buckets listed successfully.")
            return [bucket["Name"] for bucket in response["Buckets"]]
        except ClientError as e:
            configured_logger.error(f"Error listing buckets: {e}")
            raise Exception(f"Error listing buckets -> {e}")

    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> str:
        try:
            create_args = {"Bucket": bucket_name}
            if region:
                create_args["CreateBucketConfiguration"] = {
                    "LocationConstraint": region
                }
            self.s3.create_bucket(**create_args)
            configured_logger.info(f"Bucket '{bucket_name}' created successfully.")
            return f"Bucket '{bucket_name}' created successfully."
        except ClientError as e:
            configured_logger.error(f"Error creating bucket: {e}")
            raise Exception(f"Error creating bucket -> {e}")

    def delete_bucket(self, bucket_name: str) -> str:
        try:
            self.s3.delete_bucket(Bucket=bucket_name)
            configured_logger.info(f"Bucket '{bucket_name}' deleted successfully.")
            return f"Bucket '{bucket_name}' deleted successfully."
        except ClientError as e:
            configured_logger.error(f"Error deleting bucket: {e}")
            raise Exception(f"Error deleting bucket -> {e}")

    def upload_file(
            self, file_path: str, bucket_name: str, object_name: Optional[str] = None
    ) -> str:
        try:
            if not object_name:
                object_name = os.path.basename(file_path)
            self.s3.upload_file(file_path, bucket_name, object_name)
            configured_logger.info(f"File '{file_path}' uploaded to '{bucket_name}/{object_name}'.")
            return f"File '{file_path}' uploaded to '{bucket_name}/{object_name}'."
        except ClientError as e:
            configured_logger.error(f"Error uploading file: {e}")
            raise Exception(f"Error uploading file -> {e}")

    def download_file(self, file_path: str, bucket_name: str, object_name: str) -> str:
        try:
            self.s3.download_file(bucket_name, object_name, file_path)
            configured_logger.info(f"File '{object_name}' downloaded from '{bucket_name}' to '{file_path}'.")
            return f"File '{object_name}' downloaded from '{bucket_name}' to '{file_path}'."
        except ClientError as e:
            configured_logger.error(f"Error downloading file: {e}")
            raise Exception(f"Error downloading file -> {e}")

    def delete_object(self, bucket_name: str, object_name: str) -> str:
        try:
            self.s3.delete_object(Bucket=bucket_name, Key=object_name)
            configured_logger.info(f"Object '{object_name}' deleted from '{bucket_name}'.")
            return f"Object '{object_name}' deleted from '{bucket_name}'."
        except ClientError as e:
            configured_logger.error(f"Error deleting object: {e}")
            raise Exception(f"Error deleting object -> {e}")

    def list_objects(self, bucket_name: str, prefix: Optional[str] = "") -> list:
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            configured_logger.info(f"Objects listed in bucket '{bucket_name}'.")
            return [content["Key"] for content in response.get("Contents", [])]
        except ClientError as e:
            configured_logger.error(f"Error listing objects: {e}")
            raise Exception(f"Error listing objects -> {e}")


class S3ObjectStorageQuery(BaseModel):
    operation: str
    bucket_name: Optional[str] = None
    file_path: Optional[str] = None
    object_name: Optional[str] = None
    prefix: Optional[str] = None
    region: Optional[str] = None


def s3_object_storage(
        operation: str,
        bucket_name: Optional[str] = None,
        file_path: Optional[str] = None,
        object_name: Optional[str] = None,
        prefix: Optional[str] = None,
        region: Optional[str] = None,
) -> Any:
    """
    Perform an S3 storage operation.

    Args:
        operation (str): The S3 operation to perform. Supported operations are:
            - "list_buckets": Lists all buckets.
            - "create_bucket": Creates a new bucket. Requires `bucket_name` and optionally `region`.
            - "delete_bucket": Deletes a bucket. Requires `bucket_name`.
            - "upload_file": Uploads a file. Requires `file_path`, `bucket_name`, and optionally `object_name`.
            - "download_file": Downloads a file. Requires `file_path`, `bucket_name` and `object_name`.
            - "delete_object": Deletes an object. Requires `bucket_name` and `object_name`.
            - "list_objects": Lists objects in a bucket. Requires `bucket_name` and optionally `prefix`.

        bucket_name (str, optional): The name of the bucket. Required for most operations.
        file_path (str, optional): The name of the file to upload or download.
        object_name (str, optional): The key (object name) in the bucket.
        prefix (str, optional): The prefix to filter objects in `list_objects`.
        region (str, optional): The region for `create_bucket`.

    Returns:
        Any: The result of the operation.

    Raises:
        ValueError: If required arguments for the operation are missing.
        Exception: If the operation encounters an error.
    """
    try:
        configured_logger.info(f"Performing S3 operation: {operation}")
        s3_api_instance = S3()

        if not hasattr(s3_api_instance, operation):
            raise ValueError(f"Operation '{operation}' is not supported.")

        if operation == "create_bucket" and not bucket_name:
            raise ValueError("Operation 'create_bucket' requires 'bucket_name'.")
        if operation == "delete_bucket" and not bucket_name:
            raise ValueError("Operation 'delete_bucket' requires 'bucket_name'.")
        if operation == "upload_file" and not file_path or not bucket_name:
            raise ValueError(
                "Operation 'upload_file' requires 'file_path' and 'bucket_name'."
            )
        if (
                operation == "download_file"
                and not file_path
                or not bucket_name
                or not object_name
        ):
            raise ValueError(
                "Operation 'download_file' requires 'file_path', 'bucket_name', and 'object_name'."
            )
        if operation == "delete_object" and not bucket_name or not object_name:
            raise ValueError(
                "Operation 'delete_object' requires 'bucket_name' and 'object_name'."
            )
        if operation == "list_objects" and not bucket_name:
            raise ValueError("Operation 'list_objects' requires 'bucket_name'.")

        method = getattr(s3_api_instance, operation)

        result = method(
            bucket_name=bucket_name,
            file_path=file_path,
            object_name=object_name,
            prefix=prefix,
            region=region,
        )
        configured_logger.info(f"Operation '{operation}' completed successfully.")
        return result
    except Exception as e:
        configured_logger.error(f"S3 operation failed: {e}")
        raise Exception(f"S3 operation failed -> {e}") from e


def get_s3_object_storage_tool():
    return StructuredTool.from_function(
        name="s3_object_storage",
        func=s3_object_storage,
        description=(
            "s3_object_storage(operation, bucket_name=None, file_path=None, object_name=None, prefix=None, region=None) -> Any:\n"
            " - Perform an S3 storage operation (list, create, delete, upload, download, delete object, etc.).\n"
        ),
        input_schema=S3ObjectStorageQuery,
    )
