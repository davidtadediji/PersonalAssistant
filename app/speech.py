import os
import wave
import pyaudio
import torch
import whisper
from openvoice import se_extractor
from openvoice.api import BaseSpeakerTTS, ToneColorConverter


def play_audio(file_path):
    try:
        wf = wave.open(file_path, "rb")
    except Exception as e:
        print(f"Error opening audio file: {e}")
        return

    p = pyaudio.PyAudio()

    stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True,
    )

    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()


def setup_models():
    # Define the project root and checkpoint paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    en_ckpt_base = os.path.join(project_root, "checkpoints", "base_speakers", "EN")
    ckpt_converter = os.path.join(project_root, "checkpoints", "converter")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    output_dir = os.path.join(
        project_root, "outputs"
    )  # Outputs directory within project root
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

    try:
        # Initialize the BaseSpeakerTTS model
        en_base_speaker_tts = BaseSpeakerTTS(
            os.path.join(en_ckpt_base, "config.json"), device=device
        )
        en_base_speaker_tts.load_ckpt(os.path.join(en_ckpt_base, "checkpoint.pth"))

        # Initialize the ToneColorConverter model
        tone_color_converter = ToneColorConverter(
            os.path.join(ckpt_converter, "config.json"), device=device
        )
        tone_color_converter.load_ckpt(os.path.join(ckpt_converter, "checkpoint.pth"))

        # Load speaker embedding files
        en_source_default_se = torch.load(
            os.path.join(en_ckpt_base, "en_default_se.pth")
        ).to(device)
        en_source_style_se = torch.load(
            os.path.join(en_ckpt_base, "en_style_se.pth")
        ).to(device)

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        raise
    except Exception as e:
        print(f"An error occurred while setting up models: {e}")
        raise

    return (
        en_base_speaker_tts,
        tone_color_converter,
        en_source_default_se,
        en_source_style_se,
    )


en_base_speaker_tts, tone_color_converter, en_source_default_se, en_source_style_se = (
    setup_models()
)


def process_and_play(prompt, style, audio_file_pth):
    tts_model = en_base_speaker_tts
    source_se = en_source_default_se if style == "default" else en_source_style_se

    try:
        target_se, audio_name = se_extractor.get_se(
            audio_file_pth, tone_color_converter, target_dir="processed", vad=True
        )

        src_path = "output_dir/tmp.wav"
        tts_model.tss(prompt, src_path, speaker=style, language="English")

        save_path = "output_dir/output.wav"

        encode_message = "@MyShell"
        tone_color_converter.convert(
            src_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=save_path,
            message=encode_message,
        )

        print("Audio generated successfully.")
        play_audio(save_path)
    except Exception as e:
        print(f"Error during audio generation: {e}")


def transcribe_with_whisper(audio_file_path):
    model = whisper.load_model("base.en")
    result = model.transcribe(audio_file_path)
    return result["text"]


def record_audio(file_path):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024,
    )
    frames = []

    print("Recording...")

    try:
        while True:
            data = stream.read(1024)
            frames.append(data)

    except KeyboardInterrupt:
        pass

    print("Recording stopped.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(file_path, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b"".join(frames))
    wf.close()


import asyncio
import websockets
import json
import pyaudio

deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
deepgram_ws_url = os.getenv("DEEPGRAM_WS_URL")


async def deepgram_transcription():
    async with websockets.connect(
        deepgram_ws_url,
        extra_headers={
            "Authorization": f"Token {deepgram_api_key}",
            "Sec-WebSocket-Protocol": "token",
        },
    ) as ws:
        # Audio streaming setup
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
        )

        print("Streaming audio to Deepgram... Press Ctrl+C to stop.")

        try:

            async def send_audio():
                while True:
                    data = stream.read(1024, exception_on_overflow=False)
                    await ws.send(data)

            async def receive_transcriptions():
                async for message in ws:
                    response = json.loads(message)
                    if "channel" in response:
                        transcript = response["channel"]["alternatives"][0][
                            "transcript"
                        ]
                        if transcript:
                            print(f"Transcript: {transcript}")

            await asyncio.gather(send_audio(), receive_transcriptions())

        except KeyboardInterrupt:
            print("Stopping audio streaming...")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()


def user_chatbot_conversation():
    while True:
        mode = input(
            "Select mode (1: Deepgram Live, 2: Whisper Recorded, exit to quit): "
        ).strip()
        if mode == "1":
            asyncio.run(deepgram_transcription())
        elif mode == "2":
            audio_file = "temp_recording.wav"
            record_audio(audio_file)
            transcription = transcribe_with_whisper(audio_file)
            print(f"Whisper transcription: {transcription}")
            os.remove(audio_file)
        elif mode.lower() == "exit":
            break
        else:
            print("Invalid mode. Please try again.")


user_chatbot_conversation()
