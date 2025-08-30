import argparse
from pathlib import Path
import yaml
from openai import OpenAI


def review(pr_body: str, prompt_path: Path) -> str:
    spec = yaml.safe_load(prompt_path.read_text())
    client = OpenAI()
    response = client.responses.create(
        model=spec["model"],
        temperature=spec.get("temperature", 0),
        input=[
            {"role": "system", "content": spec.get("system", "")},
            {"role": "user", "content": spec.get("user", "") + "\n\n" + pr_body},
        ],
        response_format=spec.get("response_format"),
    )
    return response.output[0].content[0].get("text", "")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("prompt", type=Path, help="Path to pr-review.prompt.yaml")
    p.add_argument("pr_body", help="Pull request description")
    args = p.parse_args()
    print(review(args.pr_body, args.prompt))
