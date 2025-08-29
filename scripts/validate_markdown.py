import argparse
import base64
import json
from pathlib import Path
from openai import OpenAI

MODEL = "gpt-4.1-mini"

def call_model(raw_bytes: bytes, md_text: str) -> dict:
    client = OpenAI(base_url="https://models.inference.ai.azure.com")
    result = client.responses.create(
        model=MODEL,
        input=[
            {"role": "user", "content": [
                {"type": "input_text", "text": "Verify the Markdown matches the original document exactly."},
                {"type": "document", "format": "pdf", "b64_content": base64.b64encode(raw_bytes).decode()},
                {"type": "text", "text": md_text}
            ]}
        ]
    )
    return result.output[0].content[0].get("text", "")

def main(raw_path: Path, md_path: Path) -> None:
    response = call_model(raw_path.read_bytes(), md_path.read_text())
    verdict = json.loads(response)
    if not verdict.get("match", False):
        raise SystemExit(f"Mismatch detected: {verdict}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("raw", type=Path)
    p.add_argument("markdown", type=Path)
    args = p.parse_args()
    main(args.raw, args.markdown)
