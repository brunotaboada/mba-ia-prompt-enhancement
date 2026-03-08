import os
from typing import List, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from requests.exceptions import HTTPError

from utils import load_environment, load_yaml, normalize_prompt_payload


def _build_push_payload(prompt_data: dict) -> ChatPromptTemplate:
    messages: List[Tuple[str, str]] = [
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ]
    return ChatPromptTemplate.from_messages(messages)


def main() -> None:
    load_environment()

    # Create a client instance after environment is loaded
    ls_client = Client()

    target_repo = os.getenv("LANGSMITH_PROMPT_TARGET", "{your_username}/bug_to_user_story_v2")
    public_repo = os.getenv("LANGSMITH_PROMPT_PUBLIC", "true").strip().lower() == "true"

    payload = load_yaml("prompts/bug_to_user_story_v2.yml")
    prompt_data = normalize_prompt_payload(payload)
    prompt_template = _build_push_payload(prompt_data)

    try:
        commit_hash = ls_client.push_prompt(
            target_repo,
            object=prompt_template,
            is_public=public_repo,
            description=prompt_data.get("description", ""),
            tags=prompt_data.get("tags", []),
        )
        print(f"Prompt pushed to {target_repo}")
        print(f"Prompt URL: {commit_hash}")
    except HTTPError as exc:
        if "409" in str(exc) and "Nothing to commit" in str(exc):
            print(f"Prompt already up-to-date at {target_repo} (no changes detected)")
        else:
            raise

    print(f"Techniques: {', '.join(prompt_data.get('techniques', []))}")
    print(f"Tags: {', '.join(prompt_data.get('tags', []))}")


if __name__ == "__main__":
    main()
