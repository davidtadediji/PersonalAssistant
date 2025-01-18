import os
import queue
import threading
import time
import pyaudio
import websocket
import json
from dotenv import load_dotenv
from typing import Optional, Dict, Any


class DeepgramTranscriber:
    """A class to handle real-time speech-to-text transcription using Deepgram's WebSocket API."""

    def __init__(
            self,
            api_key: str,
            url: str,
            endpointing_duration: int = 1000,
            sample_rate: int = 16000,
            channels: int = 1,
            chunk_size: int = 1024
    ):
        """
        Initialize the transcriber with the given configuration.

        Args:
            api_key: Deepgram API key
            url: Deepgram WebSocket URL
            endpointing_duration: Duration in ms to wait before considering speech ended
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            chunk_size: Size of audio chunks to process
        """
        self.api_key = api_key
        self.url = url
        self.endpointing_duration = endpointing_duration

        # Audio configuration
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16

        # Internal state
        self.audio_queue = queue.Queue()
        self.audio = pyaudio.PyAudio()
        self.ws: Optional[websocket.WebSocketApp] = None
        self.transcription = ""
        self.is_recording = False
        self.capture_thread: Optional[threading.Thread] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.speech_started = False

        # Callback for client code
        self.on_transcription_update = None
        self.on_final_transcription = None

    def _get_deepgram_options(self) -> Dict[str, Any]:
        """Generate options for Deepgram WebSocket connection."""
        return {
            "model": "nova-2",
            "language": "en-US",
            "smart_format": True,
            "encoding": "linear16",
            "channels": self.channels,
            "sample_rate": self.sample_rate,
            "interim_results": True,
            "endpointing": self.endpointing_duration,
            "vad_events": True,
            "utterance_end_ms": str(self.endpointing_duration)
        }

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)

            # Handle VAD (Voice Activity Detection) events
            if 'vad_events' in data:
                vad_event = data['vad_events'].get('type')
                if vad_event == 'speech_start':
                    self.speech_started = True
                elif vad_event == 'speech_end' and self.speech_started:
                    # Only consider speech_end if we've detected speech_start
                    time.sleep(self.endpointing_duration / 1000)  # Wait for the endpointing duration
                    if self.on_final_transcription:
                        self.on_final_transcription(self.transcription.strip())
                    self.stop()
                    return

            if 'channel' in data:
                alternatives = data['channel'].get('alternatives', [{}])
                if alternatives:
                    transcript = alternatives[0].get('transcript', '')
                    confidence = alternatives[0].get('confidence', 0)

                    if transcript:
                        self.transcription += transcript + " "
                        if self.on_transcription_update:
                            self.on_transcription_update(transcript, confidence)

        except json.JSONDecodeError:
            print(f"Error decoding message: {message}")
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """Handle WebSocket errors."""
        print(f"WebSocket error: {str(error)}")

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        """Handle WebSocket connection closure."""
        print(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.is_recording = False

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        """Handle WebSocket connection opening."""
        print("WebSocket connection established")
        # Send configuration options when connection opens
        options = self._get_deepgram_options()
        ws.send(json.dumps(options))

        def send_audio():
            while self.is_recording:
                try:
                    audio_chunk = self.audio_queue.get(timeout=1)
                    if audio_chunk is None:
                        break
                    ws.send(audio_chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Error sending audio: {str(e)}")
                    break
            ws.close()

        threading.Thread(target=send_audio, daemon=True).start()

    def _capture_audio(self) -> None:
        """Capture audio from microphone and add to queue."""
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

        print("Recording started... Press Ctrl+C to stop.")

        while self.is_recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.audio_queue.put(data)
            except Exception as e:
                print(f"Error capturing audio: {str(e)}")
                break

        self.stream.stop_stream()
        self.stream.close()
        self.audio_queue.put(None)

    def start(self) -> None:
        """Start the transcription process."""
        if self.is_recording:
            print("Already recording!")
            return

        self.is_recording = True
        self.transcription = ""
        self.speech_started = False

        # Initialize WebSocket
        headers = {"Sec-WebSocket-Protocol": f"token, {self.api_key}"}
        self.ws = websocket.WebSocketApp(
            self.url,
            header=headers,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.on_open = self._on_open

        # Start WebSocket connection
        ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        ws_thread.start()

        # Start audio capture
        self.capture_thread = threading.Thread(target=self._capture_audio, daemon=True)
        self.capture_thread.start()

    def stop(self) -> None:
        """Stop the transcription process."""
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.ws:
            self.ws.close()

        if self.capture_thread:
            self.capture_thread.join(timeout=1)

    def get_transcription(self) -> str:
        """Get the current transcription text."""
        return self.transcription.strip()


def main():
    """Example usage of the DeepgramTranscriber class."""
    load_dotenv()

    api_key = os.getenv("DEEPGRAM_API_KEY")
    url = os.getenv("DEEPGRAM_WS_URL")

    if not api_key or not url:
        print("Error: Missing required environment variables")
        return

    def on_update(transcript: str, confidence: float):
        print(f"Transcript update: {transcript} (confidence: {confidence:.2f})")

    def on_final(transcript: str):
        print(f"\nFinal transcription: {transcript}")

    transcriber = DeepgramTranscriber(api_key, url)
    transcriber.on_transcription_update = on_update
    transcriber.on_final_transcription = on_final

    try:
        transcriber.start()
        # Keep the main thread running
        while transcriber.is_recording:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping transcription...")
        transcriber.stop()


if __name__ == "__main__":
    main()