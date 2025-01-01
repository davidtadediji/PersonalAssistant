import json
import os
import sqlite3
import time
from datetime import datetime
from typing import List, Optional, Any, Dict

import aiohttp
import cv2
import geocoder
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from app.tools.mongo_db import MongoDB
from app.tools.openweather import OpenWeather
from app.tools.replit_sandbox import ReplitSandbox
from app.tools.s3_storage import S3
from app.tools.textract_ocr import TextRact

# Load environment variables from .env file
load_dotenv()


@tool
def wolfram_alpha_computing(
    input_query: Optional[str] = None, max_chars: int = 6800
) -> str:
    """
    Query Wolfram Alpha LLM API with better handling of partial inputs.
    If the input_query is missing or incomplete, provide guidance for the user.

    Args:
        input_query (Optional[str]): The query for Wolfram Alpha. If not provided, a prompt will guide the user.
        max_chars (int): The maximum number of characters in the response (default is 6800).

    Returns:
        str: The result from the Wolfram Alpha LLM API or an error message with guidance.
    """
    try:
        # Retrieve the app_id from the environment variable
        app_id = os.getenv(
            "WOLFRAM_ALPHA_APP_ID", "DEMO"
        )  # Default to "DEMO" if the environment variable is not set

        if not input_query:
            return "Error: No query provided. Please provide a valid query to proceed."

        base_url = "https://www.wolframalpha.com/api/v1/llm-api"
        params = {"input": input_query, "appid": app_id, "maxchars": max_chars}

        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses

        if response.status_code == 200:
            result = response.json()
            query_result = result.get("queryresult", {})
            if query_result:
                pods = query_result.get("pods", [])
                if pods:
                    return f"Query result:\n{pods}"
                else:
                    return "No relevant data found for the query."
            else:
                return "Error: No valid query result returned by Wolfram Alpha."
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error occurred during Wolfram Alpha API call -> {e}") from e


@tool
def geocode_location(api_key, location_name=None, zip_code=None, limit=5):
    """
    Query the OpenWeather Geocoding API to get geographical coordinates by either city name or zip code.
    Supports direct geocoding (from location name or zip code). The API allows searching for multiple
    locations with the same name and can limit the number of results returned.

    Args:
        api_key (str): Your unique OpenWeather API key (can be found under the "API key" tab in your account page).
        location_name (Optional[str]): The name of the location (city name, state code, country code) for direct geocoding.
                                       The format should be "city name, state code (only for US), country code" (e.g., "London,GB").
        zip_code (Optional[str]): The zip/postal code and country code for direct geocoding (e.g., "90210,US").
                                  Either this or `location_name` should be provided.
        limit (Optional[int]): The number of locations to return in the response (up to 5 results can be returned, default is 5).

    Returns:
        dict: The result of the geocoding query, which may include:
            - A list of matching locations with names, coordinates, and other relevant details for city name geocoding.
            - An error message if no results are found or if there is an issue with the query.
            Example:
                [
                    {
                        "name": "London",
                        "lat": 51.5073219,
                        "lon": -0.1276474,
                        "country": "GB",
                        "state": "England"
                    }
                ]
    """
    # Define base URL for the API
    if location_name:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={location_name}&limit={limit}&appid={api_key}"
    elif zip_code:
        url = (
            f"http://api.openweathermap.org/geo/1.0/zip?zip={zip_code}&appid={api_key}"
        )
    else:
        raise ValueError(
            "You must provide either a location name or zip code for geocoding."
        )

    # Make the request to the API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        if not data:
            return {"error": "No matching locations found."}

        return data
    else:
        return {"error": f"Request failed with status code {response.status_code}."}


@tool
def reverse_geocode(api_key, lat, lon, limit=5):
    """
    Perform reverse geocoding to get location names from geographical coordinates (latitude, longitude).
    The API allows multiple results if locations share similar coordinates.

    Args:
        api_key (str): Your unique OpenWeather API key (can be found under the "API key" tab in your account page).
        lat (float): The latitude coordinate of the location.
        lon (float): The longitude coordinate of the location.
        limit (int, optional): The number of location names to return in the response (default is 5, maximum is 5).

    Returns:
        dict: The result of the reverse geocoding query, which may include:
            - A list of matching locations with names, coordinates, and other relevant details.
            - An error message if no results are found or if there is an issue with the query.
            Example:
                [
                    {
                        "name": "City of London",
                        "lat": 51.5128,
                        "lon": -0.0918,
                        "country": "GB"
                    }
                ]
    """
    # Define the reverse geocoding URL
    url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit={limit}&appid={api_key}"

    # Make the request to the API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        if not data:
            return {"error": "No matching locations found."}

        return data
    else:
        return {"error": f"Request failed with status code {response.status_code}."}


@tool
def get_current_location():
    """
    This function returns the current location based on the IP address.

    Returns:
        dict: A dictionary containing location details like city, country, latitude, longitude, etc.
    """
    g = geocoder.ip("me")  # Uses your IP address to find your location
    current_location = g.json
    return current_location


@tool
def sql_database(
    operation,
    db_name,
    table_name=None,
    data=None,
    columns=None,
    condition=None,
    query=None,
):
    """
    Perform CRUD operations and custom queries on the database.

    Args:
        operation (str): The type of operation ('create', 'read', 'update', 'delete', 'execute').
        db_name (str): The name of the database file.
        table_name (str, optional): The name of the table to operate on (required for 'create', 'update', 'delete').
        data (dict, optional): The data to insert or update (required for 'create', 'update').
        columns (list, optional): List of column names (required for 'create').
        condition (str, optional): The condition for 'update' or 'delete' (optional).
        query (str, optional): A custom SQL query for 'execute' operation (optional).

    Returns:
        dict: A dictionary containing the status and message of the operation.
            For 'read' and 'execute' operations, it returns the result of the query.
    """
    connection = None
    try:
        connection = sqlite3.connect(db_name)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        if operation == "create" and data and table_name and columns:
            placeholders = ", ".join("?" * len(data))
            column_names = ", ".join(columns)
            sql_query = (
                f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            )
            cursor.execute(sql_query, tuple(data.values()))
            connection.commit()
            return {"status": "success", "message": "Data inserted successfully"}

        elif operation == "read" and query:
            cursor.execute(query)
            results = cursor.fetchall()
            return [dict(row) for row in results] if results else []

        elif operation == "update" and data and table_name and condition:
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            sql_query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
            cursor.execute(sql_query, tuple(data.values()))
            connection.commit()
            return {"status": "success", "message": "Data updated successfully"}

        elif operation == "delete" and table_name and condition:
            sql_query = f"DELETE FROM {table_name} WHERE {condition}"
            cursor.execute(sql_query)
            connection.commit()
            return {"status": "success", "message": "Data deleted successfully"}

        elif operation == "execute" and query:
            cursor.execute(query)
            if query.strip().lower().startswith(("insert", "update", "delete")):
                connection.commit()
            if query.strip().lower().startswith("select"):
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []

        else:
            raise ValueError("Invalid parameters or operation")

    except sqlite3.Error as e:
        raise Exception(f"Database operation failed -> {e}") from e

    finally:
        if connection:
            connection.close()


@tool
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
        raise Exception(f"MongoDB operation failed -> {e}") from e


@tool
async def tavily_extract(urls: List[str]) -> Dict:
    """Retrieve raw web content from specified URLs using the Tavily API.

    Args:
        urls (List[str]): The list of URLs to extract content from.

    Returns:
        Dict: A dictionary containing the extraction results, including raw content and any errors.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    base_url = os.getenv("TAVILY_API_URL")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        payload = {"urls": urls}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/extract", headers=headers, json=payload
            ) as response:
                if response.status == 200:
                    results = await response.json()

                    formatted_results = {
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                        "results": [],
                        "failed_results": [],
                        "response_time": results.get("response_time", "N/A"),
                    }

                    if "results" in results:
                        formatted_results["results"] = [
                            {"url": r["url"], "raw_content": r["raw_content"]}
                            for r in results["results"]
                        ]

                    if "failed_results" in results:
                        formatted_results["failed_results"] = [
                            {"url": r["url"], "error": r["error"]}
                            for r in results["failed_results"]
                        ]

                    return formatted_results
                else:
                    error_msg = await response.text()
                    raise Exception(f"Extraction failed -> {error_msg}") from Exception(
                        error_msg
                    )

    except Exception as e:
        raise Exception(f"Tavily extract failed -> {e}") from e

@tool
def tavily_search(
        query: str,
        search_depth: str = "basic",
        topic: str = "general",
        max_results: int = 5,
        include_images: bool = False,
        include_image_descriptions: bool = False,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        days: int = 3,  # Only relevant for 'news' topic
) -> Dict:
    """Search function that can be used to perform web searches using the Tavily search engine.

    Args:
        query (str): The search query
        search_depth (str): Level of search depth ('basic' or 'advanced')
        topic (str): Type of search ('general' or 'news')
        max_results (int): Maximum number of results to return
        include_images (bool): Whether to include image results
        include_image_descriptions (bool): Whether to include descriptions for images
        include_answer (bool): Whether to include AI-generated answer
        include_raw_content (bool): Whether to include raw search results
        include_domains (List[str], optional): List of domains to specifically include
        exclude_domains (List[str], optional): List of domains to exclude
        days (int, optional): Number of days back for "news" topic, default is 3

    Returns:
        Dict: Search results including metadata and formatted content
    """
    import requests
    from typing import Dict, List, Optional
    import os

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError(
            "API key for Tavily is missing. Please set the TAVILY_API_KEY environment variable."
        )

    base_url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}

    try:
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "max_results": max_results,
            "include_images": include_images,
            "include_image_descriptions": include_image_descriptions,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_domains": include_domains or [],
            "exclude_domains": exclude_domains or []
        }

        # Only add days parameter if topic is news
        if topic == "news":
            payload["days"] = days

        response = requests.post(base_url, json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = response.text
            raise Exception(f"Search failed -> {error_msg}")

    except Exception as e:
        raise Exception(f"Tavily search failed -> {e}") from e

@tool
def perplexity_search(
    query,
    model="llama-3.1-sonar-small-128k-online",
    max_tokens=None,
    temperature=0.2,
    top_p=0.9,
    search_domain_filter=None,
    return_images=False,
    return_related_questions=False,
    search_recency_filter="month",
    top_k=0,
    presence_penalty=0,
    frequency_penalty=1,
):
    """
    Queries the Perplexity API with the provided parameters.

    Args:
        query (str): The user's query.
        model (str): The language model to use.
        max_tokens (int or None): Maximum number of tokens in the response.
        temperature (float): Sampling temperature for response generation.
        top_p (float): Nucleus sampling parameter.
        search_domain_filter (list or None): Domains to restrict search results to.
        return_images (bool): Whether to include images in the response.
        return_related_questions (bool): Whether to return related questions.
        search_recency_filter (str): Recency filter for the search (e.g., "month").
        top_k (int): Number of top results to return.
        presence_penalty (float): Presence penalty for token generation.
        frequency_penalty (float): Frequency penalty for token generation.

    Returns:
        dict: The API response as a JSON object.
    """
    if not query:
        return {"error": "Query cannot be empty."}

    token = os.getenv("PERPLEXITY_TOKEN")

    if not token:
        return {"error": "API token is required."}

    url = os.getenv("PERPLEXITY_API_URL")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "search_domain_filter": search_domain_filter or ["perplexity.ai"],
        "return_images": return_images,
        "return_related_questions": return_related_questions,
        "search_recency_filter": search_recency_filter,
        "top_k": top_k,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@tool
def replit_sandbox(api_key, repl_title, program_structure, requirements=None):
    """
    Interact with a code execution sandbox. Create a Replit sandbox, upload an entire program (multi-file),
    execute it, and retrieve results.
    """
    try:
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
            return "The Repl is still running. Please try again later."

        return execution_result.get("output", "No output returned.")
    except Exception as e:
        raise Exception(f"Replit sandbox creation failed -> {e}") from e


@tool
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


@tool
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

        return method(
            bucket_name=bucket_name,
            file_path=file_path,
            object_name=object_name,
            prefix=prefix,
            region=region,
        )
    except Exception as e:
        raise Exception(f"S3 operation failed -> {e}") from e


@tool
def capture_image(save_path="captured_image.jpg"):
    """
    Captures an image from the default camera (usually the first webcam) and saves it to the specified file.

    Args:
        save_path (str): The path where the captured image will be saved. Default is 'captured_image.jpg'.

    Returns:
        str: The file path of the saved image.
    """
    # Initialize the webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None

    # Capture a single frame
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture image.")
        cap.release()
        return None

    # Save the captured image to the specified path
    cv2.imwrite(save_path, frame)
    print(f"Image captured and saved to {save_path}")

    # Release the camera and close any OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

    return save_path


@tool
def weather_forecast(
    operation: str,
    lat: float,
    lon: float,
    units: str = "standard",
    lang: str = "en",
    exclude: Optional[List[str]] = None,
    timestamp: Optional[int] = None,
    date: Optional[str] = None,
    timezone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get weather information from OpenWeather One Call API 3.0

    Args:
        operation: Type of weather data to retrieve:
            - "current_forecast": Current weather and forecast data
            - "historical": Historical weather data
            - "daily_aggregate": Daily aggregated weather data
            - "overview": Weather overview with AI summary
        lat: Latitude between -90 and 90
        lon: Longitude between -180 and 180
        units: Units of measurement ("standard", "metric", or "imperial")
        lang: Language code (e.g., "en", "es", "fr")
        exclude: List of data to exclude for current_forecast (optional)
        timestamp: Unix timestamp for historical data (required for historical operation)
        date: Date in YYYY-MM-DD format (required for daily_aggregate, optional for overview)
        timezone: Timezone in ±XX:XX format (optional, for daily_aggregate only)

    Returns:
        Dict containing requested weather information

    Example:
        # Get current weather
        result = weather_information(
            operation="current_forecast",
            lat=33.44,
            lon=-94.04,
            api_key="your_api_key",
            units="metric"
        )

        # Get historical weather
        result = weather_information(
            operation="historical",
            lat=33.44,
            lon=-94.04,
            api_key="your_api_key",
            timestamp=1643803200
        )
    """
    client = OpenWeather(os.getenv("OPENWEATHER_API_KEY"))

    if operation == "current_forecast":
        return client.get_current_forecast(lat, lon, units, lang, exclude)
    elif operation == "historical":
        if timestamp is None:
            raise ValueError("Timestamp is required for historical operation")
        return client.get_historical(lat, lon, timestamp, units, lang)
    elif operation == "daily_aggregate":
        if date is None:
            raise ValueError("Date is required for daily_aggregate operation")
        return client.get_daily_aggregate(lat, lon, date, timezone, units, lang)
    elif operation == "overview":
        return client.get_overview(lat, lon, date, units)
    else:
        raise ValueError(f"Unknown operation: {operation}")


@tool
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


@tool
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


@tool
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

#
# # New York City coordinates
# lat = 40.7128
# lon = -74.0060
#
# try:
#     # Get current weather and forecast
#     current_weather = weather_forecast(
#         operation="current_forecast",
#         lat=lat,
#         lon=lon,
#         units="metric",  # Use Celsius and m/s
#         lang="en",  # English language
#         exclude=["minutely"],  # Exclude minute-by-minute forecast
#     )
#
#     print(f"Temperature: {current_weather['current']['temp']}°C")
#     print(f"Weather: {current_weather['current']['weather'][0]['description']}")
#     print(f"Humidity: {current_weather['current']['humidity']}%")
#
# except Exception as e:
#     print(f"Error: {str(e)}")
