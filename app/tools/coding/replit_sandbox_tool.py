import os
import time
from typing import Dict, Optional, Any
import requests
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from app.logger import configured_logger

load_dotenv()


class ReplitSandbox:
    def __init__(self, api_key):
        self.api_url = "https://replit.com/api/v0/repls"
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def create_repl(self, title, language="python3", template="python3"):
        """
        Create a new Repl instance.
        """
        data = {
            "title": title,
            "language": language,
            "template": template,
        }
        configured_logger.info(f"Creating a Repl with title: {title}, language: {language}, template: {template}")
        response = requests.post(self.api_url, json=data, headers=self.headers)
        if response.status_code == 201:
            repl_data = response.json()
            configured_logger.info(f"Repl created successfully: {repl_data['url']}")
            return repl_data
        else:
            configured_logger.error(f"Failed to create Repl: {response.status_code} - {response.text}")
            return None

    def upload_file(self, repl_id, file_path, content):
        """
        Upload a file to the Repl.
        """
        upload_url = f"{self.api_url}/{repl_id}/files"
        file_data = {
            "path": file_path,
            "content": content,
        }
        configured_logger.info(f"Uploading file '{file_path}' to Repl {repl_id}")
        response = requests.post(upload_url, json=file_data, headers=self.headers)
        if response.status_code == 200:
            configured_logger.info(f"File '{file_path}' uploaded successfully.")
            return True
        else:
            configured_logger.error(f"Failed to upload file '{file_path}': {response.status_code} - {response.text}")
            return False

    def upload_directory(self, repl_id, directory_path, local_directory):
        """
        Upload a directory of files to the Repl.
        """
        for root, _, files in os.walk(local_directory):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, local_directory)
                with open(file_path, "r") as f:
                    content = f.read()
                self.upload_file(repl_id, relative_path, content)

    def execute_code(self, repl_id):
        """
        Execute the code in the Repl.
        """
        run_url = f"{self.api_url}/{repl_id}/run"
        configured_logger.info(f"Executing code in Repl {repl_id}")
        response = requests.post(run_url, headers=self.headers)
        if response.status_code == 200:
            configured_logger.info(f"Code executed successfully in Repl {repl_id}.")
            return response.json()
        else:
            configured_logger.error(
                f"Failed to execute code in Repl {repl_id}: {response.status_code} - {response.text}")
            return None

    def get_repl_status(self, repl_id):
        """
        Get the status of the Repl.
        """
        status_url = f"{self.api_url}/{repl_id}/status"
        configured_logger.info(f"Retrieving status for Repl {repl_id}")
        response = requests.get(status_url, headers=self.headers)
        if response.status_code == 200:
            status = response.json()
            configured_logger.info(f"Repl {repl_id} status: {status}")
            return status
        else:
            configured_logger.error(
                f"Failed to retrieve status for Repl {repl_id}: {response.status_code} - {response.text}")
            return None

    def upload_requirements(self, repl_id, requirements):
        """
        Upload a requirements.txt file for dependency management (Python).
        """
        if requirements:
            configured_logger.info(f"Uploading requirements.txt to Repl {repl_id}")
            self.upload_file(repl_id, "../../requirements.txt", requirements)


class ReplitSandboxQuery(BaseModel):
    api_key: str
    repl_title: str
    program_structure: Dict[str, Any]
    requirements: Optional[Dict[str, Any]] = None


def replit_sandbox(api_key, repl_title, program_structure, requirements=None):
    """
    Interact with a code execution sandbox. Create a Replit sandbox, upload an entire program (multi-file),
    execute it, and retrieve results.
    """
    try:
        configured_logger.info(f"Starting Replit sandbox creation with title: {repl_title}")
        replit_api = ReplitSandbox(api_key)
        repl_data = replit_api.create_repl(repl_title)
        if not repl_data:
            raise Exception("Failed to create Repl.")

        repl_id = repl_data["id"]

        program_files = program_structure.get("files", {})
        for file_path, content in program_files.items():
            if not replit_api.upload_file(repl_id, file_path, content):
                raise Exception(f"Failed to upload file {file_path}.")

        if requirements:
            replit_api.upload_requirements(repl_id, requirements)

        directories = program_structure.get("directories", {})
        for dir_name, local_directory in directories.items():
            replit_api.upload_directory(repl_id, dir_name, local_directory)

        execution_result = replit_api.execute_code(repl_id)
        if not execution_result:
            raise Exception("Failed to execute code in Repl.")

        time.sleep(2)

        status = replit_api.get_repl_status(repl_id)
        if status and status.get("status") == "running":
            configured_logger.info("Repl is still running.")
            return "The Repl is still running. Please try again later."

        configured_logger.info(f"Repl execution result: {execution_result.get('output', 'No output returned.')}")
        return execution_result.get("output", "No output returned.")
    except Exception as e:
        configured_logger.error(f"Replit sandbox creation failed: {e}")
        raise Exception(f"Replit sandbox creation failed -> {e}") from e


def replit_sandbox_tool() -> StructuredTool:
    return StructuredTool.from_function(
        name="replit_sandbox",
        func=replit_sandbox,
        description=(
            "Interact with a code execution sandbox. Create a Replit sandbox, upload an entire program (multi-file), "
            "execute it, and retrieve results."
        ),
        input_schema=ReplitSandboxQuery,
    )
