import speech_recognition as sr


def listen_for_phrase():
    recognizer = sr.Recognizer()

    # Use the microphone as the audio source
    with sr.Microphone() as source:
        print("Say something...")

        # Continuously listen for audio
        while True:
            try:
                # Adjust for ambient noise levels and listen for the phrase
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

                # Recognize the speech using Google's Web Speech API
                phrase = recognizer.recognize_google(audio)
                print(f"Recognized: {phrase}")

                # Check if the phrase matches "Ok Google"
                if "ok google" in phrase.lower():
                    print("Triggering action based on 'Ok Google' phrase!")
                    # You can add code to trigger any specific action here
                    break
            except sr.UnknownValueError:
                # If speech is unintelligible, continue listening
                pass
            except sr.RequestError:
                # API could not be reached
                print("Could not request results; check your internet connection.")
                break


# Run the function to start listening
listen_for_phrase()
