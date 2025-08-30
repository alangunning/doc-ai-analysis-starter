import argparse
from pathlib import Path

from dotenv import load_dotenv
import yaml
from openai import OpenAI

load_dotenv()


def review(pr_body: str, prompt_path: Path) -> str:
    spec = yaml.safe_load(prompt_path.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for msg in reversed(messages):
        if msg.get("role") == "user":
            msg["content"] = msg.get("content", "") + "\n\n" + pr_body
            break
    client = OpenAI()
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
    print(review(args.pr_body, args.prompt))
