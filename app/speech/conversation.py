import asyncio
from fileinput import filename
import speech_recognition as sr
from dotenv import load_dotenv
import shutil
import subprocess
import requests
import time
import os
from asyncio import Queue
from pydub import AudioSegment
import simpleaudio as sa
from dataclasses import dataclass
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
    SpeakOptions,
)

load_dotenv()


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

        system_prompt = "You are a conversational assistant named Eliza. Use short, conversational responses as if you're having a live conversation. Your response should be under 20 words. Do not respond with any code, only conversation"

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{text}"),
            ]
        )

        self.conversation = LLMChain(
            llm=self.llm, prompt=self.prompt, memory=self.memory
        )

    def process(self, text):
        self.memory.chat_memory.add_user_message(text)
        start_time = time.time()
        response = self.conversation.invoke({"text": text})
        end_time = time.time()

        self.memory.chat_memory.add_ai_message(response["text"])

        elapsed_time = int((end_time - start_time) * 1000)
        print(f"LLM ({elapsed_time}ms): {response['text']}")
        return response["text"]


def text2speech(text):
    try:
        filename = "../output.wav"
        SPEAK_OPTIONS = {"text": text}
        deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

        options = SpeakOptions(
            model="aura-asteria-en", encoding="linear16", container="wav"
        )

        response = deepgram.speak.v("1").save(filename, SPEAK_OPTIONS, options)
        return filename

    except Exception as e:
        print(f"Exception: {e}")


class TranscriptCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.transcript_parts = []

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        return " ".join(self.transcript_parts)


transcript_collector = TranscriptCollector()


async def get_transcript(callback):
    transcription_complete = asyncio.Event()
    should_stop = False

    try:
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram: DeepgramClient = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"), config)

        dg_connection = deepgram.listen.asynclive.v("1")
        print("Listening...")

        async def on_message(self, result, **kwargs):
            nonlocal should_stop
            if should_stop:
                return

            sentence = result.channel.alternatives[0].transcript

            if not result.speech_final:
                transcript_collector.add_part(sentence)
            else:
                transcript_collector.add_part(sentence)
                full_sentence = transcript_collector.get_full_transcript()
                if len(full_sentence.strip()) > 0:
                    full_sentence = full_sentence.strip()
                    print(f"Human: {full_sentence}")
                    try:
                        await callback(full_sentence)
                    except asyncio.CancelledError:
                        should_stop = True
                        raise
                    transcript_collector.reset()

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            endpointing=300,
            smart_format=True,
        )

        await dg_connection.start(options)
        microphone = Microphone(dg_connection.send)
        microphone.start()

        try:
            # Keep the connection alive until explicitly stopped
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


@dataclass
class AudioPlayback:
    play_obj: Optional[sa.PlayObject] = None
    is_playing: bool = False

    def stop(self):
        if self.play_obj and self.is_playing:
            self.play_obj.stop()
            self.is_playing = False
            self.play_obj = None


class ConversationManager:
    def __init__(self):
        self.llm = LanguageModelProcessor()
        self.transcription_queue = Queue()
        self.is_listening = True
        self.audio_playback = AudioPlayback()
        self.current_transcription_task = None

    def play_wav(self, file_path):
        try:
            self.audio_playback.stop()
            audio = AudioSegment.from_wav(file_path)
            audio_data = audio.raw_data

            self.audio_playback.play_obj = sa.play_buffer(
                audio_data,
                num_channels=audio.channels,
                bytes_per_sample=audio.sample_width,
                sample_rate=audio.frame_rate,
            )
            self.audio_playback.is_playing = True
        except Exception as e:
            print(f"Error playing audio: {e}")

    async def handle_transcription(self, full_sentence):
        self.audio_playback.stop()
        await self.transcription_queue.put(full_sentence)

    async def start_listening(self):
        self.is_listening = True
        if (
            self.current_transcription_task is None
            or self.current_transcription_task.done()
        ):
            self.current_transcription_task = asyncio.create_task(
                get_transcript(self.handle_transcription)
            )

    async def stop_listening(self):
        self.is_listening = False
        if self.current_transcription_task:
            self.current_transcription_task.cancel()
            try:
                await self.current_transcription_task
            except asyncio.CancelledError:
                pass
            self.current_transcription_task = None

    async def main(self):
        try:
            await self.start_listening()
            print("Listening...")

            while True:
                try:
                    transcription = await self.transcription_queue.get()
                    print(f"Received transcription: {transcription}")

                    if "goodbye" in transcription.lower():
                        print("Detected 'goodbye'. Pausing conversation.")
                        await self.stop_listening()
                        break

                    llm_response = self.llm.process(transcription)
                    print(f"LLM Response: {llm_response}")

                    audio_response = text2speech(llm_response)
                    self.play_wav(audio_response)

                except asyncio.CancelledError:
                    print("Conversation cancelled")
                    break

        except Exception as e:
            print(f"Error in conversation: {e}")
        finally:
            await self.stop_listening()
            self.audio_playback.stop()
            print("Conversation ended. Waiting for next 'Ok Google' trigger phrase...")
