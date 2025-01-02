from typing import Optional

import cv2
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

load_dotenv()


class CaptureImageQuery(BaseModel):
    save_path: Optional[str] = "captured_image.jpg"


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


def get_capture_image_tool():
    return StructuredTool.from_function(
        name="capture_image",
        func=capture_image,
        description=(
            "capture_image(save_path='captured_image.jpg') -> str:\n"
            " - Captures an image from the default camera and saves it to the specified file.\n"
        ),
        input_schema=CaptureImageQuery,
    )
