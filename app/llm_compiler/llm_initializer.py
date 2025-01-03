# app/llm_compiler/llm_initializer.py
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

load_dotenv()


def initialize_llm():
    provider = os.getenv("LLM_PROVIDER", "groq")
    if provider.lower() == "groq":
        model = os.getenv("GROQ_PLANNING_MODEL")
        return ChatGroq(model=model), ChatGroq(model=os.getenv("GROQ_CHAT_MODEL"), temperature="0"), ChatGroq(model=os.getenv("GROQ_EXECUTION_MODEL"))
    elif provider.lower() == "openai":
        model = os.getenv("OPENAI_PLANNING_MODEL")
        return ChatOpenAI(model=model), ChatOpenAI(model=os.getenv("OPENAI_EXECUTION_MODEL")), ChatOpenAI(model=os.getenv("OPENAI_EXECUTION_MODEL"))
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


llm, chat_llm, execution_llm = initialize_llm()

