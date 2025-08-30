import argparse
import base64
import json
from pathlib import Path

import os
from dotenv import load_dotenv
import yaml
from openai import OpenAI

load_dotenv()


def call_model(raw_bytes: bytes, md_text: str, prompt_path: Path) -> str:
    spec = yaml.safe_load(prompt_path.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            messages[i]["content"] = [
                {"type": "input_text", "text": msg.get("content", "")},
                {"type": "document", "format": "pdf", "b64_content": base64.b64encode(raw_bytes).decode()},
                {"type": "text", "text": md_text},
            ]
            break
    base_url = os.environ.get("OPENAI_BASE_URL", "https://models.github.ai")
    client = OpenAI(api_key=os.environ.get("GITHUB_TOKEN"), base_url=base_url)
    result = client.responses.create(
        model=spec["model"],
        **spec.get("modelParameters", {}),
        input=messages,
    )
    return result.output[0].content[0].get("text", "")


def main(raw_path: Path, md_path: Path, prompt_path: Path) -> None:
    response = call_model(raw_path.read_bytes(), md_path.read_text(), prompt_path)
    verdict = json.loads(response)
    if not verdict.get("match", False):
        raise SystemExit(f"Mismatch detected: {verdict}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("raw", type=Path)
    p.add_argument("markdown", type=Path)
    p.add_argument("--prompt", type=Path, default=Path("prompts/validate-md.prompt.yaml"))
    args = p.parse_args()
    main(args.raw, args.markdown, args.prompt)
