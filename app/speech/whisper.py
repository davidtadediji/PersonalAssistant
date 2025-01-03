import wave
import pyaudio
import os
from faster_whisper import WhisperModel
from time import time

from app.llm_compiler.agent import query_agent

# Configuration for audio recording
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
SILENCE_THRESHOLD = 500  # RMS threshold to detect silence
SILENCE_DURATION = 2  # Seconds of silence to consider as end of speech


def is_silent(data):
    """Check if the audio chunk is silent."""
    rms = (sum(int(sample) ** 2 for sample in data) / len(data)) ** 0.5
    return rms < SILENCE_THRESHOLD


def record_audio(filename):
    """Record audio until silence is detected."""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []
    silence_counter = 0

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        data_int = list(data)
        frames.append(data)

        if is_silent(data_int):
            silence_counter += CHUNK / RATE
        else:
            silence_counter = 0

        if silence_counter > SILENCE_DURATION:
            break

    print("Recording stopped.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save audio to file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return filename


def transcribe_audio(file_path, model):
    """Transcribe audio using the Faster Whisper model."""
    segments, info = model.transcribe(file_path, vad_filter=True)
    transcription = ""

    print(f"Detected language: {info.language} with probability {info.language_probability:.2f}")
    print("Transcription:")

    # Combine all segments into a single string
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        transcription += segment.text + " "

    return transcription.strip()



def main():
    # Initialize the Faster Whisper model
    model_size = "large-v2"
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    while True:
        timestamp = int(time())
        filename = f"audio_{timestamp}.wav"
        try:
            # Record and save audio
            audio_file = record_audio(filename)

            # Transcribe audio and get the text
            transcription = transcribe_audio(audio_file, model)

            # Query the agent with transcribed text
            if transcription:
                llm_response = query_agent(transcription)
                print(f"Agent response: {llm_response}")
            else:
                print("No transcription available to query")

            # Delete the audio file after transcription
            os.remove(audio_file)
        except KeyboardInterrupt:
            print("Stopping...")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            if os.path.exists(filename):
                os.remove(filename)


if __name__ == "__main__":
    main()