# app/llm_compiler/llm_initializer.py
import os

from dotenv import load_dotenv
from huggingface_hub import login
from langchain_groq import ChatGroq
from langchain_huggingface import ChatHuggingFace
from langchain_huggingface import HuggingFaceEndpoint
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

load_dotenv()


def initialize_llm():
    provider = os.getenv("LLM_PROVIDER", "groq")
    if provider.lower() == "groq":
        model = os.getenv("GROQ_PLANNING_MODEL")
        return (
            ChatGroq(model=model),
            ChatGroq(model=os.getenv("GROQ_CHAT_MODEL"), temperature="0"),
            ChatGroq(model=os.getenv("GROQ_EXECUTION_MODEL")),
        )
    if provider.lower() == "deepseek":
        login(os.getenv("hf_token"))
        endpoint = HuggingFaceEndpoint(repo_id="microsoft/Phi-3-mini-4k-instruct",
                                       task="text-generation", )

        return (
            ChatHuggingFace(llm=endpoint),
            ChatHuggingFace(llm=endpoint),
            ChatHuggingFace(llm=endpoint)
        )

        # from langchain_huggingface import HuggingFaceTextGenInference
        #
        # ENDPOINT_URL = "https://huggingface.co/deepseek-ai/DeepSeek-V3"
        # HF_TOKEN = os.getenv("HF_TOKEN")
        #
        # llm = HuggingFaceTextGenInference(
        #     inference_server_url=ENDPOINT_URL,
        #     max_new_tokens=512,
        #     top_k=50,
        #     temperature=0.1,
        #     repetition_penalty=1.03,
        #     server_kwargs={
        #         "headers": {
        #             "Authorization": f"Bearer {HF_TOKEN}",
        #             "Content-Type": "application/json",
        #         }
        #     },
        # )
        # return (
        #     ChatHuggingFace(llm=llm),
        #     ChatHuggingFace(llm=llm),
        #     ChatHuggingFace(llm=llm)
        # )

    elif provider.lower() == "openai":
        model = os.getenv("OPENAI_PLANNING_MODEL")
        return (
            ChatOpenAI(model=model),
            ChatOpenAI(model=os.getenv("OPENAI_EXECUTION_MODEL")),
            ChatOpenAI(model=os.getenv("OPENAI_EXECUTION_MODEL")),
        )
    elif provider.lower() == "ollama":
        model = os.getenv("OLLAMA_PLANNING_MODEL")
        return (
            ChatOllama(model=model),
            ChatOllama(model=os.getenv("OLLAMA_CHAT_MODEL")),
            ChatOllama(model=os.getenv("OLLAMA_EXECUTION_MODEL")),
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


llm, chat_llm, execution_llm = initialize_llm()
