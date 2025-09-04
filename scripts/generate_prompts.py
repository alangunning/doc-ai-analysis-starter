import argparse
import json
import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

from openai import OpenAI

from doc_ai.openai import upload_file, create_response


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Generate validation and analysis prompts for a PDF")
    parser.add_argument("pdf", type=Path, help="Path to PDF document")
    parser.add_argument(
        "--model",
        default=os.getenv("PROMPT_GEN_MODEL", "gpt-4o-mini"),
        help="Model name override",
    )
    parser.add_argument(
        "--base-model-url",
        default=os.getenv("PROMPT_GEN_BASE_MODEL_URL") or os.getenv("BASE_MODEL_URL") or "https://api.openai.com/v1",
        help="Model base URL override",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for generated prompt files (defaults to PDF directory)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write request/response details to this file",
    )
    args = parser.parse_args()

    console = Console()
    logger = None
    log_path = args.log_file
    if args.verbose or log_path is not None:
        logger = logging.getLogger("doc_ai.generate_prompts")
        logger.setLevel(logging.DEBUG)
        if args.verbose:
            sh = RichHandler(console=console, show_time=False)
            sh.setLevel(logging.DEBUG)
            logger.addHandler(sh)
        if log_path is None:
            log_path = args.pdf.with_suffix(".generate.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing required environment variable: OPENAI_API_KEY")

    client = OpenAI(api_key=api_key, base_url=args.base_model_url)

    file_id = upload_file(client, args.pdf, logger=logger)

    system = (
        "You design GitHub model prompt YAML files. Given a PDF, you create both validation and analysis prompts."
    )
    user = (
        "Analyze the attached PDF and infer its document type. "
        "Produce two YAML prompts suitable for GitHub Models:\n"
        "1. validate.prompt.yaml – instructions to validate a converted rendition against the PDF.\n"
        "2. analysis.prompt.yaml – instructions to extract structured data from this type of document.\n"
        "Return a JSON object with keys 'validate_prompt' and 'analysis_prompt' whose values are YAML strings."
        "Each YAML must include name, description, model, modelParameters (temperature: 0), and messages."
        "Do not wrap the YAML in code fences."
    )

    result = create_response(
        client,
        model=args.model,
        system=[system],
        texts=[user],
        file_ids=[file_id],
        temperature=0,
        logger=logger,
    )

    text = (result.output_text or "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Model did not return valid JSON: {text}") from exc

    validate_yaml = data.get("validate_prompt", "").strip()
    analysis_yaml = data.get("analysis_prompt", "").strip()
    if not validate_yaml or not analysis_yaml:
        raise SystemExit("Missing prompt data in model response")

    out_dir = args.output_dir or args.pdf.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    validate_path = out_dir / f"{args.pdf.stem}.validate.prompt.yaml"
    analysis_path = out_dir / f"{args.pdf.stem}.analysis.prompt.yaml"
    validate_path.write_text(validate_yaml, encoding="utf-8")
    analysis_path.write_text(analysis_yaml, encoding="utf-8")

    console.print(f"Wrote [green]{validate_path}[/] and [green]{analysis_path}[/]")
