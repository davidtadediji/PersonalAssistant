import asyncio
import os
import time
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from queue import Queue as ThreadQueue
from typing import Optional

import simpleaudio as sa
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
    SpeakOptions,
)
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydub import AudioSegment

load_dotenv()


@dataclass
class AudioPlayback:
    play_obj: Optional[sa.PlayObject] = None
    is_playing: bool = False

    def stop(self):
        if self.play_obj and self.is_playing:
            self.play_obj.stop()
            self.is_playing = False
            self.play_obj = None


class LanguageModelProcessor:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="mixtral-8x7b-32768",
            groq_api_key=os.getenv("GROQ_API_KEY"),
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        # Pre-compiled system message
        self.system_prompt = "You are a conversational assistant named Eliza. Use short, conversational responses as if you're having a live conversation. Your response should be under 20 words. Do not respond with any code, only conversation"

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{text}"),
            ]
        )

        self.conversation = LLMChain(
            llm=self.llm, prompt=self.prompt, memory=self.memory
        )

    def process(self, text):
        response = self.conversation.invoke({"text": text})
        return response["text"]


class ConversationManager:
    def __init__(self):
        self.llm = LanguageModelProcessor()
        self.transcription_queue = Queue(maxsize=1)
        self.audio_queue = ThreadQueue(maxsize=1)
        self.is_listening = True
        self.audio_playback = AudioPlayback()
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.start_time = None

        config = DeepgramClientOptions(options={"keepalive": "true"})
        self.deepgram = DeepgramClient(
            api_key=os.getenv("DEEPGRAM_API_KEY"), config=config
        )

    def play_audio(self, audio):
        """Run audio playback in thread pool"""
        try:
            start_time = time.time()
            self.audio_playback.stop()

            play_obj = sa.play_buffer(
                audio.raw_data,
                num_channels=audio.channels,
                bytes_per_sample=audio.sample_width,
                sample_rate=audio.frame_rate,
            )

            end_time = time.time()
            playback_latency = int((end_time - start_time) * 1000)
            print(f"Audio playback latency: {playback_latency}ms")
            total_latency = int((end_time - self.start_time))
            print(f"Total latency: {total_latency}ms")

            self.audio_playback.play_obj = play_obj
            self.audio_playback.is_playing = True
            play_obj.wait_done()
        except Exception as e:
            print(f"Audio playback error: {e}")

    async def text_to_speech(self, text: str):
        """Process TTS in parallel with other operations"""
        try:
            start_time = time.time()

            options = SpeakOptions(
                model="aura-asteria-en", encoding="linear16", container="wav"
            )

            filename = "../output.wav"
            audio_future = self.thread_pool.submit(
                self.deepgram.speak.v("1").save, filename, {"text": text}, options
            )

            await asyncio.wrap_future(audio_future)
            tts_latency = int((time.time() - start_time) * 1000)
            print(f"TTS generation latency: {tts_latency}ms")

            audio_start = time.time()
            audio = AudioSegment.from_wav(filename)
            audio_load_latency = int((time.time() - audio_start) * 1000)
            print(f"Audio loading latency: {audio_load_latency}ms")

            self.audio_queue.put(audio)
            self.thread_pool.submit(self.play_audio, audio)

        except Exception as e:
            print(f"Audio processing error: {e}")

    async def handle_transcription(self, full_sentence):
        self.audio_playback.stop()
        await self.transcription_queue.put(full_sentence)

    async def get_transcript(self, callback):
        should_stop = False

        try:
            dg_connection = self.deepgram.listen.asynclive.v("1")
            print("Listening...")

            async def on_message(self, result, **kwargs):
                nonlocal should_stop
                if should_stop:
                    return

                sentence = result.channel.alternatives[0].transcript

                if result.speech_final and len(sentence.strip()) > 0:
                    print(f"Human: {sentence}")
                    try:
                        await callback(sentence)
                    except asyncio.CancelledError:
                        should_stop = True
                        raise

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            options = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                endpointing=1000,
                smart_format=True,
            )

            await dg_connection.start(options)
            microphone = Microphone(dg_connection.send)
            microphone.start()

            try:
                while not should_stop:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                should_stop = True
                raise
            finally:
                microphone.finish()
                await dg_connection.finish()

        except Exception as e:
            print(f"Could not open socket: {e}")
            raise

    async def main(self):
        try:
            transcription_task = asyncio.create_task(
                self.get_transcript(self.handle_transcription)
            )
            print("Listening...")

            while True:
                try:
                    self.start_time = time.time()
                    transcription = await self.transcription_queue.get()
                    transcription_latency = int((time.time() - self.start_time) * 1000)
                    print(f"Transcription latency: {transcription_latency}ms")
                    print(f"Received transcription: {transcription}")

                    if "goodbye" in transcription.lower():
                        print("Detected 'goodbye'. Pausing conversation.")
                        break

                    llm_start = time.time()
                    llm_response = self.llm.process(transcription)
                    llm_latency = int((time.time() - llm_start) * 1000)
                    print(f"LLM processing latency: {llm_latency}ms")
                    print(f"LLM Response: {llm_response}")

                    await self.text_to_speech(llm_response)

                except asyncio.CancelledError:
                    print("Conversation cancelled")
                    break

        except Exception as e:
            print(f"Error in conversation: {e}")
        finally:
            if transcription_task:
                transcription_task.cancel()
                try:
                    await transcription_task
                except asyncio.CancelledError:
                    pass
            self.audio_playback.stop()
            self.thread_pool.shutdown()
            print("Conversation ended. Waiting for next 'Ok Google' trigger phrase...")
