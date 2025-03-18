from typing import List

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

load_dotenv()

import os
import time

import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

from src.logger import configured_logger

# Load environment variables from .env
load_dotenv()


class TextRact:
    """
    A class to interact with AWS Textract for text extraction from documents stored in S3.

    Attributes:
        textract (boto3.client): The AWS Textract client.
        bucket_name (str): The name of the S3 bucket containing documents.
    """

    def __init__(self):
        """
        Initialize the TextRact instance with AWS Textract client and S3 bucket information.
        """
        self.bucket_name = os.getenv("S3_DOCUMENT_BUCKET")
        self.textract = boto3.client(
            "textract",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )

    def start_async_text_detection(self, s3_file_name: str) -> str:
        """
        Start an asynchronous text detection job using AWS Textract.

        Args:
            s3_file_name (str): The name of the file in the S3 bucket.

        Returns:
            str: The Job ID of the asynchronous text detection.
        """
        try:
            response = self.textract.start_document_text_detection(
                DocumentLocation={
                    "S3Object": {"Bucket": self.bucket_name, "Name": s3_file_name}
                }
            )
            return response["JobId"]
        except (NoCredentialsError, ClientError) as e:
            raise Exception(f"Failed to start text detection -> {e}")

    def get_async_results(self, job_id: str) -> dict:
        """
        Retrieve the results of an asynchronous text detection job.

        Args:
            job_id (str): The Job ID of the text detection.

        Returns:
            dict: The text detection results.
        """
        try:
            while True:
                result = self.textract.get_document_text_detection(JobId=job_id)
                status = result["JobStatus"]

                if status == "SUCCEEDED":
                    configured_logger.info(f"Textract job {job_id} succeeded.")
                    return result
                elif status == "FAILED":
                    raise Exception(f"Textract job {job_id} failed.")

                configured_logger.info(
                    f"Textract job {job_id} is in progress. Waiting..."
                )
                time.sleep(5)
        except (NoCredentialsError, ClientError) as e:
            raise Exception(f"Error fetching Textract results -> {e}")

    def extract_text_by_type(self, response: dict, block_type: str = "LINE") -> list:
        """
        Extract text from the Textract response by block type.

        Args:
            response (dict): The Textract response.
            block_type (str): The block type to extract ("WORD" or "LINE").

        Returns:
            list: A list of extracted text blocks.
        """
        return [
            block["Text"]
            for block in response["Blocks"]
            if block["BlockType"] == block_type
        ]

    def process_async_document(self, s3_file_name: str) -> dict:
        """
        Process a document asynchronously using Textract.

        Args:
            s3_file_name (str): The name of the file in the S3 bucket.

        Returns:
            dict: Extracted text results by type.
        """
        job_id = self.start_async_text_detection(s3_file_name)
        response = self.get_async_results(job_id)
        return {
            "lines": self.extract_text_by_type(response, "LINE"),
            "words": self.extract_text_by_type(response, "WORD"),
        }

    def process_sync_document(self, s3_file_name: str) -> list:
        """
        Process a document synchronously using Textract.

        Args:
            s3_file_name (str): The name of the file in the S3 bucket.

        Returns:
            list: Extracted text lines.
        """
        try:
            response = self.textract.detect_document_text(
                Document={
                    "S3Object": {"Bucket": self.bucket_name, "Name": s3_file_name}
                }
            )
            return (
                self.extract_text_by_type(response, "LINE")
                if "Blocks" in response
                else []
            )
        except ClientError as e:
            raise Exception(f"Error in synchronous text detection -> {e}")

    def extract_text(self, file_names: list) -> str:
        """
        Process multiple files and extract text.

        Args:
            file_names (list): List of S3 file names.

        Returns:
            str: Concatenated extracted text.
        """
        extracted_text = ""
        for file_name in file_names:
            try:
                if file_name.lower().endswith(".pdf"):
                    result = self.process_async_document(file_name)
                    extracted_text += "\n".join(result["lines"]) + "\n"
                else:
                    lines = self.process_sync_document(file_name)
                    extracted_text += "\n".join(lines) + "\n"
            except Exception as e:
                configured_logger.error(f"Error processing file {file_name} -> {e}")
        return extracted_text


class TextractOCRQuery(BaseModel):
    file_names: List[str]


def textract_ocr(file_names: list) -> str:
    """
    Extract text from files in s3 object storage using AWS Textract.

    Args:
        file_names (list): List of S3 file names to extract text from.

    Returns:
        str: Concatenated extracted text from all files.
    """
    try:
        textract_client = TextRact()
        return textract_client.extract_text(file_names)
    except Exception as e:
        raise Exception(f"Text extraction failed -> {e}") from e


def textract_ocr_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="textract_ocr",
        func=textract_ocr,
        description=(
            "Extract text from files in s3 object storage using AWS Textract.\n"
            " - file_names: List of S3 file names to extract text from."
        ),
        input_schema=TextractOCRQuery,
    )
