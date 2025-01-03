import asyncio

import speech_recognition as sr

from conversation import ConversationManager


async def listen_for_phrase():
    recognizer = sr.Recognizer()
    manager = ConversationManager()

    with sr.Microphone() as source:
        print("Listening for 'Ok Google'...")

        while True:
            try:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

                phrase = recognizer.recognize_google(audio)
                print(f"Recognized: {phrase}")

                if "ok google" in phrase.lower():
                    print("Triggering conversation based on 'Ok Google' phrase!")
                    await manager.main()  # Start/resume conversation

            except sr.UnknownValueError:
                pass  # Continue listening if speech is unintelligible
            except sr.RequestError as e:
                print(f"Could not request results: {e}")
                break


if __name__ == "__main__":
    asyncio.run(listen_for_phrase())
