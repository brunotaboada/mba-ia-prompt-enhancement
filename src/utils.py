import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Tuple

import yaml
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


def load_environment() -> None:
    load_dotenv(override=False)


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_ollama_available(base_url: str, model: str, timeout: float = 2.0) -> bool:
    tags_url = f"{base_url.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False

    # Keep this check lightweight. If model is not found, we still allow usage
    # because Ollama can pull on demand in some setups.
    return "models" in payload and len(model) > 0


def get_llm(purpose: str = "response"):
    """Return an LLM client in fixed order: Ollama -> OpenAI -> Gemini."""
    load_environment()

    temperature = float(os.getenv("TEMPERATURE", "0"))

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    if purpose == "evaluation":
        openai_model = os.getenv("OPENAI_EVAL_MODEL", "gpt-4o")
        gemini_model = os.getenv("GEMINI_EVAL_MODEL", "gemini-2.5-flash")
    else:
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # 1) Ollama - only if server is reachable
    if is_ollama_available(ollama_base_url, ollama_model):
        return ChatOllama(model=ollama_model, base_url=ollama_base_url, temperature=temperature)

    # 2) OpenAI
    if os.getenv("OPENAI_API_KEY", "").strip():
        try:
            return ChatOpenAI(model=openai_model, temperature=temperature)
        except Exception:
            pass

    # 3) Gemini
    if os.getenv("GOOGLE_API_KEY", "").strip():
        try:
            return ChatGoogleGenerativeAI(model=gemini_model, temperature=temperature)
        except Exception:
            pass

    raise RuntimeError(
        "No model provider available. Sequence attempted: "
        "1) Ollama, 2) OpenAI, 3) Gemini. "
        "Ensure Ollama has the model pulled or configure OPENAI_API_KEY / GOOGLE_API_KEY."
    )


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def save_yaml(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as file:
        yaml.safe_dump(payload, file, sort_keys=False, allow_unicode=False)


def normalize_prompt_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = payload or {}
    return {
        "name": payload.get("name", "bug_to_user_story"),
        "version": payload.get("version", "v1"),
        "description": payload.get("description", ""),
        "tags": payload.get("tags", []),
        "techniques": payload.get("techniques", []),
        "system_prompt": payload.get("system_prompt", ""),
        "user_prompt": payload.get(
            "user_prompt",
            "Convert the following bug report into a high-quality user story:\n\n{bug_report}",
        ),
        "few_shot_examples": payload.get("few_shot_examples", []),
    }


def render_user_prompt(prompt_data: Dict[str, Any], bug_report: str) -> str:
    user_prompt = prompt_data["user_prompt"]
    return user_prompt.replace("{bug_report}", bug_report)


def build_messages(prompt_data: Dict[str, Any], bug_report: str) -> List[Tuple[str, str]]:
    user_prompt = render_user_prompt(prompt_data, bug_report)
    return [
        ("system", prompt_data["system_prompt"]),
        ("human", user_prompt),
    ]


def stringify_prompt_from_hub_object(prompt_obj: Any) -> Dict[str, Any]:
    """Best effort conversion from a LangChain Hub object into our YAML format."""
    system_text = ""
    user_text = ""

    # Handles ChatPromptTemplate-like objects.
    if hasattr(prompt_obj, "messages"):
        for message in prompt_obj.messages:
            message_type = getattr(message, "prompt", None)
            template = getattr(message_type, "template", "")
            role = getattr(message, "__class__", type("x", (), {})).__name__.lower()
            if "system" in role and not system_text:
                system_text = template
            elif ("human" in role or "user" in role) and not user_text:
                user_text = template

    if not user_text and hasattr(prompt_obj, "template"):
        user_text = getattr(prompt_obj, "template", "")

    return normalize_prompt_payload(
        {
            "name": "bug_to_user_story",
            "version": "v1",
            "description": "Pulled from LangSmith Prompt Hub",
            "tags": ["langsmith", "imported"],
            "techniques": [],
            "system_prompt": system_text,
            "user_prompt": user_text
            or "Convert the bug report into a user story with acceptance criteria:\n\n{bug_report}",
            "few_shot_examples": [],
        }
    )
