import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")


def get_chat_model(model: str | None = None, temperature: float = 0, max_retries: int = 3) -> ChatGroq:
    return ChatGroq(
        model=model or GROQ_MODEL_NAME,
        temperature=temperature,
        max_retries=max_retries,
    )
