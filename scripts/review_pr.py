import argparse
import json
import os
from pathlib import Path

import yaml
from openai import OpenAI

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "pr-review.prompt.yaml"


def review_pr(pr_body: str, prompt_path: Path = PROMPT_FILE) -> str:
    spec = yaml.safe_load(prompt_path.read_text())
    client = OpenAI()
    response = client.responses.create(
        model=spec["model"],
        temperature=spec.get("temperature", 0),
        input=[
            {"role": "system", "content": spec["system"]},
            {"role": "user", "content": spec["user"] + "\n\n" + pr_body},
        ],
        response_format=spec.get("response_format"),
    )
    data = json.loads(response.output[0].content[0].get("text", "{}"))
    return data.get("summary", "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-body")
    parser.add_argument("--prompt", type=Path, default=PROMPT_FILE)
    args = parser.parse_args()

    body = args.pr_body or os.environ.get("PR_BODY", "")
    print(review_pr(body, args.prompt))

