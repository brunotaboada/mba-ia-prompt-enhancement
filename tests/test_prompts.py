import yaml


def _load_prompt():
    with open("prompts/bug_to_user_story_v2.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_prompt_has_system_prompt():
    prompt = _load_prompt()
    assert "system_prompt" in prompt
    assert prompt["system_prompt"].strip() != ""


def test_prompt_has_role_definition():
    prompt = _load_prompt()
    system_prompt = prompt["system_prompt"].lower()
    assert "you are" in system_prompt or "voce e" in system_prompt
    assert (
        "product manager" in system_prompt
        or "senior product manager" in system_prompt
        or "gerente de produto" in system_prompt
    )


def test_prompt_mentions_format():
    prompt = _load_prompt()
    merged = f"{prompt.get('system_prompt', '')}\n{prompt.get('user_prompt', '')}".lower()
    assert "markdown" in merged or "user story" in merged or "historia de usuario" in merged


def test_prompt_has_few_shot_examples():
    prompt = _load_prompt()
    examples = prompt.get("few_shot_examples", [])
    assert isinstance(examples, list)
    assert len(examples) >= 1
    assert all("input" in ex and "output" in ex for ex in examples)


def test_prompt_no_todos():
    prompt = _load_prompt()
    serialized = yaml.safe_dump(prompt).lower()
    assert "[todo]" not in serialized


def test_minimum_techniques():
    prompt = _load_prompt()
    techniques = prompt.get("techniques", [])
    assert isinstance(techniques, list)
    assert len(techniques) >= 2
