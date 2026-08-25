import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from src.log_utils import logger

load_dotenv()

# Model Identifiers
PRIMARY_MODEL_NAME = os.getenv("PRIMARY_MODEL_NAME", "gemini-2.5-flash")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b")
OPENROUTER_MODEL_NAME = os.getenv("OPENROUTER_MODEL_NAME", "google/gemma-4-31b-it:free")

# Langfuse Observability
try:
    from langfuse.callback import CallbackHandler
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        _langfuse_handler = CallbackHandler()
    else:
        _langfuse_handler = None
except ImportError:
    _langfuse_handler = None


def get_chat_model(model: str | None = None, temperature: float = 0, max_retries: int = 3):
    """
    Returns a unified ChatOpenAI model instance with automatic multi-provider fallback:
    1. Tier 1 (Primary): Google Gemini 2.5 Flash
    2. Tier 2 (Secondary Fallback): Groq GPT-OSS 120B (zero <think> tokens)
    3. Tier 3 (Tertiary Fallback): OpenRouter Free Tier
    """
    callbacks = [_langfuse_handler] if _langfuse_handler else None

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    providers = []

    # 1. Tier 1: Google Gemini 2.5 Flash
    if gemini_key:
        providers.append(
            ChatOpenAI(
                model=model or PRIMARY_MODEL_NAME,
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                temperature=temperature,
                max_retries=max_retries,
                callbacks=callbacks,
            )
        )

    # 2. Tier 2: Groq GPT-OSS 120B (Clean instruction following, no <think> tokens)
    if groq_key:
        providers.append(
            ChatOpenAI(
                model=GROQ_MODEL_NAME,
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                temperature=temperature,
                max_retries=max_retries,
                callbacks=callbacks,
            )
        )

    # 3. Tier 3: OpenRouter Free Tier
    if openrouter_key:
        providers.append(
            ChatOpenAI(
                model=OPENROUTER_MODEL_NAME,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=temperature,
                max_retries=max_retries,
                callbacks=callbacks,
            )
        )

    if not providers:
        logger.warning("No LLM API keys found (GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY). Defaulting to dummy client.")
        return ChatOpenAI(
            model=model or PRIMARY_MODEL_NAME,
            api_key="missing-key",
            temperature=temperature,
            max_retries=max_retries,
        )

    primary = providers[0]
    fallbacks = providers[1:]

    return primary.with_fallbacks(fallbacks) if fallbacks else primary
