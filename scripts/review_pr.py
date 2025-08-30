import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
import yaml
from openai import OpenAI

load_dotenv()


def review_pr(pr_body: str, prompt_path: Path) -> str:
    """Run the PR review prompt against ``pr_body``."""

    spec = yaml.safe_load(prompt_path.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for msg in reversed(messages):
        if msg.get("role") == "user":
            msg["content"] = msg.get("content", "") + "\n\n" + pr_body
            break
    base_url = os.getenv("OPENAI_BASE_URL", "https://models.github.ai")
    client = OpenAI(api_key=os.getenv("GITHUB_TOKEN"), base_url=base_url)
    response = client.responses.create(
        model=spec["model"],
        **spec.get("modelParameters", {}),
        input=messages,
    )
    return response.output[0].content[0].get("text", "")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("prompt", type=Path, help="Path to pr-review.prompt.yaml")
    p.add_argument("pr_body", help="Pull request description")
    args = p.parse_args()
    print(review_pr(args.pr_body, args.prompt))
