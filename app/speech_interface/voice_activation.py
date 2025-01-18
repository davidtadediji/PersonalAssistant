import asyncio
import os
from groq import Groq
import speech_recognition as sr
from sts import ConversationManager
import keyboard
import time
import threading

# Initialize the Groq client
client = Groq()
assistant_name = os.getenv("ASSISTANT_NAME")

def listen_for_abort(manager):
    """Listen for Ctrl+Space and set the should_abort flag."""
    while True:
        if keyboard.is_pressed('ctrl+space'):
            manager.should_abort = True
            print("Ctrl+Space pressed. Aborting current stage...")
        time.sleep(0.1)


async def listen_for_phrase():
    recognizer = sr.Recognizer()
    manager = ConversationManager()

    threading.Thread(target=listen_for_abort, args=(manager,), daemon=True)

    with sr.Microphone() as source:
        phrase = f"Hey {assistant_name}"
        print(f"Listening for '{phrase}'...")

        while True:
            try:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

                # Save the audio to a temporary file
                temp_audio_file = "temp_audio.wav"
                with open(temp_audio_file, "wb") as f:
                    f.write(audio.get_wav_data())

                # Transcribe the audio using Groq API
                with open(temp_audio_file, "rb") as file:
                    transcription = client.audio.transcriptions.create(
                        file=(temp_audio_file, file.read()),
                        model="whisper-large-v3-turbo",
                        response_format="text",
                        language="en"
                    )

                print(f"Recognized: {transcription}")
                if all(word in transcription.lower() for word in phrase.lower().split()):
                    print("Triggering conversation based on 'Ok Google' phrase!")
                    try:
                        await manager.main()  # Start/resume conversation
                    except Exception as e:
                        print(f"Error during conversation: {e}")
                    finally:
                        print("Returning to listening for trigger phrase...")


                # Clean up the temporary audio file
                os.remove(temp_audio_file)

            except sr.UnknownValueError:
                pass  # Continue listening if speech is unintelligible
            except sr.RequestError as e:
                print(f"Could not request results: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

if __name__ == "__main__":
    asyncio.run(listen_for_phrase())