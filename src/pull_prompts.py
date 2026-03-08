import os

import langchainhub
from langchain_core.prompts import ChatPromptTemplate
from langsmith.utils import LangSmithNotFoundError
from requests.exceptions import HTTPError
from utils import load_environment, save_yaml, stringify_prompt_from_hub_object

# Create a client instance
hub_client = langchainhub.Client()


def _push_minimal_v1_to_langsmith(target_repo: str) -> None:
    """Push a minimal low-quality v1 prompt to LangSmith if it doesn't exist."""
    minimal_v1 = {
        "name": "bug_to_user_story",
        "version": "v1",
        "description": "Baseline low-quality prompt for challenge",
        "tags": ["baseline", "v1"],
        "techniques": [],
        "system_prompt": "Convert the bug report below into a user story.\n\n{bug_report}",
        "user_prompt": "{bug_report}",
        "few_shot_examples": [],
    }
    
    # Create ChatPromptTemplate for LangSmith
    messages = [
        ("system", minimal_v1["system_prompt"]),
        ("human", minimal_v1["user_prompt"]),
    ]
    prompt_template = ChatPromptTemplate.from_messages(messages)
    
    print(f"  → Pushing minimal v1 to {target_repo}...")
    langchainhub.Client().push(target_repo, object=prompt_template, new_repo_is_public=True)
    print(f"  ✓ Pushed successfully")


def main() -> None:
    load_environment()
    source_prompt = os.getenv("LANGSMITH_PROMPT_SOURCE", "leonanluppi/bug_to_user_story_v1")

    print(f"Pulling prompt from LangSmith Hub: {source_prompt}")
    
    try:
        # Strategy 1: Try to pull from LangSmith
        prompt_object = hub_client.pull(source_prompt)
        normalized = stringify_prompt_from_hub_object(prompt_object)
        print("✓ Successfully pulled from LangSmith")
        
    except (HTTPError, LangSmithNotFoundError) as e:
        # Strategy 2: If 404 (not found), push a minimal v1 first, then pull
        if "404" in str(e) or "not found" in str(e).lower():
            print(f"⚠️  Prompt not found in LangSmith")
            _push_minimal_v1_to_langsmith(source_prompt)
            prompt_object = hub_client.pull(source_prompt)
            normalized = stringify_prompt_from_hub_object(prompt_object)
            print("✓ Pushed and pulled minimal v1")
        else:
            raise
    
    save_yaml("prompts/bug_to_user_story_v1.yml", normalized)
    save_yaml("prompts/raw_prompts.yml", normalized)
    print("Saved to prompts/bug_to_user_story_v1.yml and prompts/raw_prompts.yml")


if __name__ == "__main__":
    main()
