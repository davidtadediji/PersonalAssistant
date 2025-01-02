import json
import os
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel


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

    # Check if the file exists
    if os.path.exists(filename):
        # Load existing personal information from the file
        with open(filename, "r") as file:
            personal_info = json.load(file)
    else:
        # If the file doesn't exist, create an empty dictionary
        personal_info = {}

    # Check if the key already exists
    if key in personal_info:
        # Update the value if the key exists
        personal_info[key] = value
        result = f"Updated {key} to {value}."
    else:
        # Add the new key-value pair
        personal_info[key] = value
        result = f"Added {key}: {value}."

    # Save the updated personal information back to the file
    with open(filename, "w") as file:
        json.dump(personal_info, file, indent=4)

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

        return list(personal_info.keys())  # Return the keys as a list
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

        return personal_info.get(key, "Information not found.")
    else:
        return "No personal information file found."


class StoreUserPersonalInfoQuery(BaseModel):
    key: str
    value: Any


def get_store_user_personal_info_tool():
    return StructuredTool.from_function(
        name="store_user_personal_info",
        func=store_user_personal_info,
        description=(
            "store_user_personal_info(key, value) -> str:\n"
            " - Stores personal information by adding or updating key-value pairs in a JSON file.\n"
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
            "retrieve_user_personal_info(key) -> str:\n"
            " - Retrieves personal information based on the provided key from the JSON file.\n"
        ),
        input_schema=RetrieveUserPersonalInfoQuery,
    )
