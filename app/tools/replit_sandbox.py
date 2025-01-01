import os

import requests


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
        response = requests.post(self.api_url, json=data, headers=self.headers)
        if response.status_code == 201:
            repl_data = response.json()
            print(f"Repl created: {repl_data['url']}")
            return repl_data
        else:
            print("Failed to create Repl:", response.status_code, response.text)
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
        response = requests.post(upload_url, json=file_data, headers=self.headers)
        if response.status_code == 200:
            print(f"File '{file_path}' uploaded successfully.")
            return True
        else:
            print("Failed to upload file:", response.status_code, response.text)
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
        response = requests.post(run_url, headers=self.headers)
        if response.status_code == 200:
            print("Code executed successfully!")
            return response.json()
        else:
            print("Failed to execute code:", response.status_code, response.text)
            return None

    def get_repl_status(self, repl_id):
        """
        Get the status of the Repl.
        """
        status_url = f"{self.api_url}/{repl_id}/status"
        response = requests.get(status_url, headers=self.headers)
        if response.status_code == 200:
            status = response.json()
            return status
        else:
            print(
                "Failed to retrieve Repl status:", response.status_code, response.text
            )
            return None

    def upload_requirements(self, repl_id, requirements):
        """
        Upload a requirements.txt file for dependency management (Python).
        """
        if requirements:
            self.upload_file(repl_id, "../requirements.txt", requirements)
