import argparse
import base64
import json
from pathlib import Path
import yaml
from openai import OpenAI


def call_model(raw_bytes: bytes, md_text: str, prompt_path: Path) -> str:
    spec = yaml.safe_load(prompt_path.read_text())
    client = OpenAI(base_url="https://models.inference.ai.azure.com")
    result = client.responses.create(
        model=spec["model"],
        temperature=spec.get("temperature", 0),
        input=[
            {"role": "system", "content": spec.get("system", "")},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": spec.get("user", "")},
                    {"type": "document", "format": "pdf", "b64_content": base64.b64encode(raw_bytes).decode()},
                    {"type": "text", "text": md_text},
                ],
            },
        ],
        response_format=spec.get("response_format"),
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
