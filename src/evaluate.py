import os
from pathlib import Path
from typing import Dict, List
from statistics import mean
import json

from langsmith import Client
from langsmith.evaluation import evaluate as ls_evaluate
from dataset import DATASET
from metrics import (
    evaluate_output,
    evaluate_output_with_judge,
    tone_score as calc_tone_score,
    acceptance_criteria_score as calc_acceptance_criteria_score,
    user_story_format_score as calc_user_story_format_score,
    completeness_score as calc_completeness_score,
)
from utils import build_messages, get_llm, load_environment, load_yaml, normalize_prompt_payload


DATASET_NAME = "bug_to_user_story_eval"


def _preview_text(text: str, limit: int = 72) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _is_enabled(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _ensure_langsmith_dataset(client: Client, eval_items: List[Dict[str, str]]) -> str:
    """Create or refresh the shared evaluation dataset in LangSmith."""
    print("\n" + "=" * 48)
    print("Creating/Updating LangSmith Dataset...")
    print("=" * 48)

    try:
        existing = client.read_dataset(dataset_name=DATASET_NAME)
        dataset_id = existing.id
        print(f"Found existing dataset: {DATASET_NAME}")

        examples = list(client.list_examples(dataset_id=dataset_id))
        for ex in examples:
            client.delete_example(example_id=ex.id)
        print(f"Cleared {len(examples)} existing examples")
    except Exception:
        ds = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Bug reports for user story conversion evaluation",
        )
        dataset_id = ds.id
        print(f"Created new dataset: {DATASET_NAME}")

    for item in eval_items:
        client.create_example(
            inputs={"bug_report": item["bug_report"]},
            outputs=None,
            dataset_id=dataset_id,
        )

    print(f"Added {len(eval_items)} examples to dataset")
    print(f"Dataset ID: {dataset_id}")
    print("=" * 48 + "\n")
    return dataset_id


def _status(scores: dict, threshold: float) -> str:
    all_good = all(value >= threshold for value in scores.values())
    avg_good = mean(scores.values()) >= threshold
    return "APPROVED" if all_good and avg_good else "FAILED"


def _blend_scores(primary: Dict[str, float], secondary: Dict[str, float]) -> Dict[str, float]:
    return {key: round((primary[key] + secondary[key]) / 2.0, 4) for key in primary.keys()}


def _build_eval_items(sample_size: int) -> List[Dict[str, str]]:
    """Return exactly sample_size items by cycling DATASET when needed."""
    if sample_size <= len(DATASET):
        return DATASET[:sample_size]

    expanded: List[Dict[str, str]] = []
    idx = 0
    while len(expanded) < sample_size:
        source = DATASET[idx % len(DATASET)]
        cycle_number = (idx // len(DATASET)) + 1
        expanded.append(
            {
                "id": f"{source['id']}-r{cycle_number}",
                "bug_report": source["bug_report"],
            }
        )
        idx += 1
    return expanded


# ---------------------------------------------------------------------------
# LangSmith evaluators — each receives a Run and an Example and returns an
# EvaluationResult-compatible dict.
# ---------------------------------------------------------------------------

def _make_heuristic_evaluators():
    """Return a list of evaluator callables for langsmith.evaluation.evaluate()."""

    def tone_evaluator(run, example):
        text = run.outputs.get("output", "")
        return {"key": "tone_score", "score": round(calc_tone_score(text), 4)}

    def ac_evaluator(run, example):
        text = run.outputs.get("output", "")
        return {"key": "acceptance_criteria_score", "score": round(calc_acceptance_criteria_score(text), 4)}

    def format_evaluator(run, example):
        text = run.outputs.get("output", "")
        return {"key": "user_story_format_score", "score": round(calc_user_story_format_score(text), 4)}

    def completeness_evaluator(run, example):
        text = run.outputs.get("output", "")
        return {"key": "completeness_score", "score": round(calc_completeness_score(text), 4)}

    return [tone_evaluator, ac_evaluator, format_evaluator, completeness_evaluator]


def _make_llm_judge_evaluator(judge_llm):
    """Return an evaluator that uses an LLM judge to score all four metrics."""

    def llm_judge_evaluator(run, example):
        text = run.outputs.get("output", "")
        bug_report = example.inputs.get("bug_report", "")
        scores = evaluate_output_with_judge(judge_llm, bug_report, text)
        if scores is None:
            return {"key": "llm_judge_avg", "score": 0.0}
        return {"key": "llm_judge_avg", "score": round(mean(scores.values()), 4)}

    return llm_judge_evaluator


def _make_hybrid_evaluators(judge_llm):
    """Return evaluators that blend heuristic + LLM-judge scores (hybrid mode)."""

    def _hybrid(metric_name, heuristic_fn):
        def evaluator(run, example):
            text = run.outputs.get("output", "")
            bug_report = example.inputs.get("bug_report", "")
            h_score = round(heuristic_fn(text), 4)
            judged = evaluate_output_with_judge(judge_llm, bug_report, text)
            if judged is not None and metric_name in judged:
                blended = round((h_score + judged[metric_name]) / 2.0, 4)
            else:
                blended = h_score
            return {"key": metric_name, "score": blended}
        return evaluator

    return [
        _hybrid("tone_score", calc_tone_score),
        _hybrid("acceptance_criteria_score", calc_acceptance_criteria_score),
        _hybrid("user_story_format_score", calc_user_story_format_score),
        _hybrid("completeness_score", calc_completeness_score),
    ]


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    load_environment()

    client = Client()

    prompt_path = os.getenv("PROMPT_FILE", "prompts/bug_to_user_story_v2.yml")
    prompt_version = "v2" if "v2" in prompt_path else "v1"

    threshold = float(os.getenv("MIN_METRIC_THRESHOLD", "0.9"))
    sample_size = int(os.getenv("EVAL_SAMPLE_SIZE", str(len(DATASET))))
    evaluation_mode = os.getenv("EVAL_MODE", "hybrid").strip().lower()
    if evaluation_mode not in {"heuristic", "llm", "hybrid"}:
        evaluation_mode = "hybrid"
    if sample_size < 1:
        sample_size = len(DATASET)

    eval_items = _build_eval_items(sample_size)

    print(f"\nLangSmith tracing enabled: {os.getenv('LANGCHAIN_TRACING_V2', 'false')}")
    print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'prompt-engineering-challenge')}")

    # --- ensure shared dataset exists in LangSmith ---
    _ensure_langsmith_dataset(client, eval_items)

    prompt_payload = normalize_prompt_payload(load_yaml(prompt_path))
    response_llm = get_llm("response")
    judge_llm = get_llm("evaluation") if evaluation_mode in {"llm", "hybrid"} else None
    log_progress = _is_enabled(os.getenv("LOG_PROGRESS"), default=True)
    progress_state = {"started": 0, "total": len(eval_items)}

    # --- target function: the prompt under test ---
    def target(inputs: dict) -> dict:
        progress_state["started"] += 1
        current = progress_state["started"]
        bug_report = inputs["bug_report"]
        if log_progress:
            print(
                f"[{current}/{progress_state['total']}] Generating output for: {_preview_text(bug_report)}",
                flush=True,
            )
        messages = build_messages(prompt_payload, inputs["bug_report"])
        result = response_llm.invoke(messages)
        return {"output": getattr(result, "content", str(result))}

    # --- pick evaluators based on mode ---
    if evaluation_mode == "heuristic":
        evaluators = _make_heuristic_evaluators()
    elif evaluation_mode == "llm":
        evaluators = _make_heuristic_evaluators()
        if judge_llm:
            evaluators.append(_make_llm_judge_evaluator(judge_llm))
    else:  # hybrid
        if judge_llm:
            evaluators = _make_hybrid_evaluators(judge_llm)
        else:
            evaluators = _make_heuristic_evaluators()

    experiment_prefix = f"bug-to-user-story-{prompt_version}"

    print("Running prompt evaluation via LangSmith experiment...")
    print(f"Mode: {evaluation_mode}")
    print(f"Samples: {sample_size}")
    print(f"Experiment prefix: {experiment_prefix}")
    print("=" * 48)

    # --- run LangSmith evaluate() — this creates a real experiment ---
    experiment_results = ls_evaluate(
        target,
        data=DATASET_NAME,
        evaluators=evaluators,
        experiment_prefix=experiment_prefix,
        max_concurrency=1,
    )

    # --- collect results from the experiment ---
    aggregate: Dict[str, List[float]] = {
        "tone_score": [],
        "acceptance_criteria_score": [],
        "user_story_format_score": [],
        "completeness_score": [],
    }
    detailed_results: List[Dict[str, object]] = []

    for index, result in enumerate(experiment_results, start=1):
        run = result["run"]
        feedback = result.get("evaluation_results", {})
        eval_results_list = feedback.get("results", [])

        bug_report = run.inputs.get("bug_report", "")
        generated_output = (run.outputs or {}).get("output", "")

        scores: Dict[str, float] = {}
        for er in eval_results_list:
            if er.key in aggregate and er.score is not None:
                scores[er.key] = er.score

        # Fill any missing metrics with heuristic fallback
        heuristic = evaluate_output(generated_output)
        for key in aggregate:
            if key not in scores:
                scores[key] = heuristic[key]

        detailed_results.append(
            {
                "id": str(run.id)[:8],
                "bug_report": bug_report,
                "generated_output": generated_output,
                "scores": scores,
            }
        )
        for metric_name, metric_value in scores.items():
            aggregate[metric_name].append(metric_value)

        if log_progress:
            print(
                f"[{index}/{sample_size}] Completed: "
                f"tone={scores['tone_score']}, "
                f"acceptance={scores['acceptance_criteria_score']}, "
                f"format={scores['user_story_format_score']}, "
                f"completeness={scores['completeness_score']}",
                flush=True,
            )

    final_scores = {key: round(mean(values), 4) if values else 0.0 for key, values in aggregate.items()}

    print("\n" + "=" * 48)
    print(f"Prompt: {prompt_payload['name']}_{prompt_payload['version']}")
    print(f"- Tone Score: {final_scores['tone_score']}")
    print(f"- Acceptance Criteria Score: {final_scores['acceptance_criteria_score']}")
    print(f"- User Story Format Score: {final_scores['user_story_format_score']}")
    print(f"- Completeness Score: {final_scores['completeness_score']}")
    print(f"- Average: {round(mean(final_scores.values()), 4)}")
    print("=" * 48)

    status = _status(final_scores, threshold)
    if status == "APPROVED":
        print(f"Status: APPROVED - all metrics are >= {threshold}")
    else:
        print(f"Status: FAILED - one or more metrics are below {threshold}")

    print(f"\nView experiments in LangSmith: https://smith.langchain.com/")
    print(f"Compare v1 vs v2 in the Datasets & Experiments tab using dataset: {DATASET_NAME}")

    output_path = Path("evaluation_results.json")
    output_path.write_text(json.dumps(detailed_results, indent=2), encoding="utf-8")
    print(f"Detailed results written to {output_path}")


if __name__ == "__main__":
    main()
