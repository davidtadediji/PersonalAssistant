import base64
import io  # Add this import
import os
import subprocess

import cv2  # Install with: !pip install opencv-python
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image as PILImage
from openai import OpenAI
from playsound import playsound  # Install with: !pip install playsound

from src.logger import configured_logger  # Import your configured logger
from src.utils import get_resource_path

# Initialize logger
logger = configured_logger

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>"))

# Step 1: Extract frames from the video using OpenCV
video_path = get_resource_path("test.mp4")  # Ensure this path is correct
logger.info(f"Attempting to open video file at: {video_path}")

video = cv2.VideoCapture(video_path)

# Check if the video was opened successfully
if not video.isOpened():
    logger.error(f"Could not open video file at {video_path}")
    exit(1)

base64Frames = []
while video.isOpened():
    success, frame = video.read()
    if not success:
        break
    _, buffer = cv2.imencode(".jpg", frame)
    base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

video.release()
logger.info(f"{len(base64Frames)} frames read.")

# Check if frames were read
if len(base64Frames) == 0:
    logger.error("No frames were read from the video.")
    exit(1)


# Step 2: Create a photo grid from the frames
def create_photo_grid(frames, grid_size=(3, 3)):
    """Create a photo grid from a list of frames."""
    logger.info("Creating photo grid from frames.")
    images = [PILImage.open(io.BytesIO(base64.b64decode(frame.encode("utf-8")))) for frame in frames]
    grid_width = grid_size[0] * images[0].width
    grid_height = grid_size[1] * images[0].height
    grid_image = PILImage.new("RGB", (grid_width, grid_height))

    for i, img in enumerate(images):
        row = i // grid_size[0]
        col = i % grid_size[0]
        grid_image.paste(img, (col * img.width, row * img.height))

    return grid_image


# Select a subset of frames (e.g., 9 frames for a 3x3 grid)
num_frames = len(base64Frames)
if num_frames < 9:
    logger.warning(f"Only {num_frames} frames available. Using all frames.")
    selected_frames = base64Frames
else:
    selected_frames = base64Frames[::num_frames // 9][:9]  # Adjust for more or fewer frames

grid_image = create_photo_grid(selected_frames)

# Convert the grid image to base64
grid_buffer = np.array(grid_image)
_, grid_buffer = cv2.imencode(".jpg", grid_buffer)
grid_base64 = base64.b64encode(grid_buffer).decode("utf-8")

# Display the grid image using matplotlib
logger.info("Displaying photo grid.")
plt.imshow(grid_image)
plt.axis("off")  # Hide axes
plt.show(block=False)  # Non-blocking display

# Step 3: Extract audio using FFMPEG and transcribe with Whisper
# Install FFMPEG if not already installed: !apt install ffmpeg

# Extract audio from the video
audio_file = "audio.mp3"
logger.info(f"Extracting audio from video to {audio_file}.")
subprocess.run(["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_file, "-y"])

# Transcribe audio using Whisper
logger.info("Transcribing audio using Whisper.")
with open(audio_file, "rb") as audio:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
        response_format="text"
    )
logger.info(f"Audio Transcript: {transcript}")

# Step 4: Use GPT-4 Vision to describe the video with the photo grid and audio transcript
PROMPT_MESSAGES = [
    {
        "role": "user",
        "content": [
            "The image shows video frames in sequence. Describe what’s likely going on in each frame.",
            f"You can hear the following in the audio track: {transcript}. Also mention what you can hear in the audio.",
            {"image": grid_base64, "resize": 768},
        ],
    },
]
params = {
    "model": "gpt-4-vision-preview",
    "messages": PROMPT_MESSAGES,
    "max_tokens": 500,
}

logger.info("Sending request to GPT-4 Vision.")
result = client.chat.completions.create(**params)
logger.info(f"GPT-4 Vision Description: {result.choices[0].message.content}")

# Step 5: Summarize the description using GPT-4
PROMPT_MESSAGES = [
    {
        "role": "user",
        "content": [
            "Explain what’s happening in the text, but this time refer to it as a short clip, not individual frames.",
            result.choices[0].message.content,
        ],
    },
]
params = {
    "model": "gpt-4",
    "messages": PROMPT_MESSAGES,
    "max_tokens": 300,
}

logger.info("Summarizing description using GPT-4.")
result = client.chat.completions.create(**params)
logger.info(f"Summarized Description: {result.choices[0].message.content}")

# Step 6: Generate a voiceover using OpenAI's TTS API
logger.info("Generating voiceover using OpenAI's TTS API.")
response = requests.post(
    "https://api.openai.com/v1/audio/speech",
    headers={
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
    },
    json={
        "model": "tts-1-1106",
        "input": result.choices[0].message.content,
        "voice": "onyx",
    },
)

# Save the audio to a file
audio_file = "voiceover.mp3"
logger.info(f"Saving voiceover to {audio_file}.")
with open(audio_file, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        f.write(chunk)

# Play the audio using playsound
logger.info("Playing voiceover.")
playsound(audio_file)
