import json
import os
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from src.logger import configured_logger


def store_user_personal_info(key, value):
    """
    This function stores personal information by adding a new key-value pair
    to a JSON file. If the key exists, it updates the value; otherwise, it adds a new key-value pair.

    Example usage:
    - store_user_personal_information('name', 'Jane Doe')
    - store_user_personal_information('hobbies', ['reading', 'painting'])

    Args:
    - key (str): The key of the information to store.
    - value (str or list): The value of the information to store.

    Returns:
    - str: A message confirming the update or addition of the information.
    """

    directory = "resources"  # Directory where the file should be stored
    filename = "resources/personal_info.json"  # Full path to the file

    # Check if the directory exists, if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)
        configured_logger.info(f"Created directory: {directory}")

    # Check if the file exists
    if os.path.exists(filename):
        # Load existing personal information from the file
        with open(filename, "r") as file:
            personal_info = json.load(file)
            configured_logger.info(f"Loaded existing personal info from {filename}.")
    else:
        # If the file doesn't exist, create an empty dictionary
        personal_info = {}
        configured_logger.info(f"File {filename} not found, starting with an empty dictionary.")

    # Check if the key already exists
    if key in personal_info:
        # Update the value if the key exists
        personal_info[key] = value
        result = f"Updated {key} to {value}."
        configured_logger.info(f"Updated {key} with new value: {value}")
    else:
        # Add the new key-value pair
        personal_info[key] = value
        result = f"Added {key}: {value}."
        configured_logger.info(f"Added new key-value pair: {key} -> {value}")

    # Save the updated personal information back to the file
    try:
        with open(filename, "w") as file:
            json.dump(personal_info, file, indent=4)
            configured_logger.info(f"Successfully saved updated personal information to {filename}.")
    except Exception as e:
        configured_logger.error(f"Failed to save personal information: {e}")
        result = f"Error: Failed to save personal information - {e}"

    return result


def get_available_user_personal_information_keys():
    """
    Retrieves the available keys from the personal_info.json file. These keys are important to know before
    calling the 'retrieve_user_personal_information' function in order to know what values can be retrieved.

    The function returns the keys as a list.

    Returns:
    - list: A list of available keys that can be used to retrieve personal information.
    """
    filename = "resources/personal_info.json"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            personal_info = json.load(file)

        configured_logger.info(f"Retrieved available keys from {filename}: {list(personal_info.keys())}")
        return list(personal_info.keys())  # Return the keys as a list
    configured_logger.warn(f"Personal information file {filename} not found.")
    return []  # Return an empty list if the file doesn't exist


def retrieve_user_personal_info(key):
    """
    This function retrieves personal information from the JSON file based on the provided key.

    Args:
    - key (str): The key corresponding to the information you want to retrieve.

    Returns:
    - str or list: The value corresponding to the key, or "Information not found" if the key doesn't exist.
    """

    filename = "resources/personal_info.json"  # Fixed storage location

    # Load personal information from the file
    if os.path.exists(filename):
        with open(filename, "r") as file:
            personal_info = json.load(file)

        value = personal_info.get(key, "Information not found.")
        if value == "Information not found.":
            configured_logger.warn(f"Key '{key}' not found in the personal information file.")
        else:
            configured_logger.info(f"Retrieved value for key '{key}': {value}")
        return value
    else:
        configured_logger.error(f"File {filename} not found.")
        return "No personal information file found."


class StoreUserPersonalInfoQuery(BaseModel):
    key: str
    value: Any


def get_store_user_personal_info_tool():
    return StructuredTool.from_function(
        name="store_user_personal_info",
        func=store_user_personal_info,
        description=(
            " - Stores personal information by adding or updating key-value pairs in a JSON file.\n"
            "store_user_personal_info(key, value) -> str:\n"
        ),
        input_schema=StoreUserPersonalInfoQuery,
    )


def get_available_user_personal_information_keys_tool():
    return StructuredTool.from_function(
        name="get_available_user_personal_information_keys",
        func=get_available_user_personal_information_keys,
        description=(
            "get_available_user_personal_information_keys() -> list:\n"
            " - Retrieves available keys from the personal information file.\n"
        ),
        input_schema=None,
    )


class RetrieveUserPersonalInfoQuery(BaseModel):
    key: str


def get_retrieve_user_personal_info_tool():
    return StructuredTool.from_function(
        name="retrieve_user_personal_info",
        func=retrieve_user_personal_info,
        description=(
            " - Retrieves personal information based on the provided key from the JSON file.\n"
            "retrieve_user_personal_info(key) -> str:\n"
        ),
        input_schema=RetrieveUserPersonalInfoQuery,
    )
