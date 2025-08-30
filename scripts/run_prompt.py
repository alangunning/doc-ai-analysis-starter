import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
import yaml
from openai import OpenAI

load_dotenv()


def run_prompt(prompt_file: Path, input_text: str) -> str:
    """Execute ``prompt_file`` against ``input_text`` and return model output."""

    spec = yaml.safe_load(prompt_file.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for msg in reversed(messages):
        if msg.get("role") == "user":
            msg["content"] = msg.get("content", "") + "\n\n" + input_text
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
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path)
    parser.add_argument("markdown_doc", type=Path)
    parser.add_argument("--outdir", default="outputs", type=Path)
    args = parser.parse_args()

    result = run_prompt(args.prompt, args.markdown_doc.read_text())
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / (args.markdown_doc.stem + ".json")).write_text(
        result + "\n", encoding="utf-8"
    )
