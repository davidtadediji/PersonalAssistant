import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

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

    def list_buckets(self) -> list:
        try:
            response = self.s3.list_buckets()
            return [bucket["Name"] for bucket in response["Buckets"]]
        except ClientError as e:
            raise Exception(f"Error listing buckets -> {e}")

    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> str:
        try:
            create_args = {"Bucket": bucket_name}
            if region:
                create_args["CreateBucketConfiguration"] = {
                    "LocationConstraint": region
                }
            self.s3.create_bucket(**create_args)
            return f"Bucket '{bucket_name}' created successfully."
        except ClientError as e:
            raise Exception(f"Error creating bucket -> {e}")

    def delete_bucket(self, bucket_name: str) -> str:
        try:
            self.s3.delete_bucket(Bucket=bucket_name)
            return f"Bucket '{bucket_name}' deleted successfully."
        except ClientError as e:
            raise Exception(f"Error deleting bucket -> {e}")

    def upload_file(
        self, file_path: str, bucket_name: str, object_name: Optional[str] = None
    ) -> str:
        try:
            if not object_name:
                object_name = os.path.basename(file_path)
            self.s3.upload_file(file_path, bucket_name, object_name)
            return f"File '{file_path}' uploaded to '{bucket_name}/{object_name}'."
        except ClientError as e:
            raise Exception(f"Error uploading file -> {e}")

    def download_file(self, file_path: str, bucket_name: str, object_name: str) -> str:
        try:
            self.s3.download_file(bucket_name, object_name, file_path)
            return f"File '{object_name}' downloaded from '{bucket_name}' to '{file_path}'."
        except ClientError as e:
            raise Exception(f"Error downloading file -> {e}")

    def delete_object(self, bucket_name: str, object_name: str) -> str:
        try:
            self.s3.delete_object(Bucket=bucket_name, Key=object_name)
            return f"Object '{object_name}' deleted from '{bucket_name}'."
        except ClientError as e:
            raise Exception(f"Error deleting object -> {e}")

    def list_objects(self, bucket_name: str, prefix: Optional[str] = "") -> list:
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            return [content["Key"] for content in response.get("Contents", [])]
        except ClientError as e:
            raise Exception(f"Error listing objects -> {e}")
