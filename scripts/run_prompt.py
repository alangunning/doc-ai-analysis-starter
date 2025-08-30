import argparse
import json
from pathlib import Path
import yaml
from openai import OpenAI


def run_prompt(prompt_file: Path, input_text: str) -> str:
    spec = yaml.safe_load(prompt_file.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for msg in reversed(messages):
        if msg.get("role") == "user":
            msg["content"] = msg.get("content", "") + "\n\n" + input_text
            break
    client = OpenAI()
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
    (args.outdir / (args.markdown_doc.stem + ".json")).write_text(result + "\n")
