"""Command-line interface for Prompt Vault CLI."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .errors import VaultError
from .models import Prompt
from .storage import PromptStorage


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Store and manage reusable prompt templates locally."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new prompt.")
    add_parser.add_argument("--name", required=True, help="Unique prompt name.")
    add_parser.add_argument("--content", required=True, help="Prompt text.")
    add_parser.add_argument(
        "--description",
        help="Optional short description.",
    )

    subparsers.add_parser("list", help="List all stored prompts.")

    search_parser = subparsers.add_parser(
        "search",
        help="Search for prompts by name.",
    )
    search_parser.add_argument("query", help="Name or partial name to find.")

    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete a prompt by name.",
    )
    delete_parser.add_argument("name", help="Name of the prompt to delete.")

    return parser


def _format_prompts(prompts: Sequence[Prompt]) -> str:
    """Format prompts for deterministic command-line output."""
    return "\n\n".join(
        "\n".join(
            (
                f"Name: {prompt.name}",
                f"Description: {prompt.description or '(none)'}",
                f"Content: {prompt.content}",
            )
        )
        for prompt in prompts
    )


def main(
    argv: Sequence[str] | None = None,
    storage: PromptStorage | None = None,
) -> int:
    """Run the command-line application and return its exit code."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    prompt_storage = (
        storage
        if storage is not None
        else PromptStorage(Path("data.json"))
    )

    try:
        if arguments.command == "add":
            prompt = Prompt(
                name=arguments.name,
                content=arguments.content,
                description=arguments.description,
            )
            prompt_storage.add(prompt)
            print(f"Added prompt: {prompt.name}")
            return 0

        if arguments.command == "list":
            prompts = prompt_storage.list_all()
            if not prompts:
                print("No prompts stored.")
            else:
                print(_format_prompts(prompts))
            return 0

        if arguments.command == "search":
            prompts = prompt_storage.search(arguments.query)
            if not prompts:
                print(
                    f'Error: no prompts found matching "{arguments.query}".',
                    file=sys.stderr,
                )
                return 1

            print(_format_prompts(prompts))
            return 0

        if arguments.command == "delete":
            deleted_prompt = prompt_storage.delete(arguments.name)
            print(f"Deleted prompt: {deleted_prompt.name}")
            return 0
    except VaultError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
