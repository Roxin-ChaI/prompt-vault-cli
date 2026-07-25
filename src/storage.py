"""JSON storage for Prompt Vault CLI."""

import json
import os
from collections.abc import Sequence
from pathlib import Path
from tempfile import NamedTemporaryFile

from .errors import (
    DuplicatePromptError,
    PromptNotFoundError,
    StorageError,
    ValidationError,
)
from .models import Prompt


class PromptStorage:
    """Load and save prompts in a local JSON file."""

    def __init__(self, data_path: str | Path = Path("data.json")) -> None:
        self.data_path = Path(data_path)

    def load(self) -> list[Prompt]:
        """Load prompts from the data file."""
        try:
            contents = self.data_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except (OSError, UnicodeError) as exc:
            raise StorageError(
                f'Could not read data file "{self.data_path}": {exc}'
            ) from exc

        if not contents.strip():
            raise StorageError(
                f'Data file "{self.data_path}" is empty; expected a JSON list.'
            )

        try:
            data = json.loads(contents)
        except json.JSONDecodeError as exc:
            raise StorageError(
                f'Data file "{self.data_path}" contains invalid JSON '
                f"at line {exc.lineno}, column {exc.colno}."
            ) from exc

        if not isinstance(data, list):
            raise StorageError(
                f'Data file "{self.data_path}" must contain a top-level JSON list.'
            )

        prompts: list[Prompt] = []
        for index, record in enumerate(data, start=1):
            if not isinstance(record, dict):
                raise StorageError(
                    f'Prompt record {index} in "{self.data_path}" '
                    "must be a JSON object."
                )

            try:
                prompts.append(Prompt.from_dict(record))
            except ValidationError as exc:
                raise StorageError(
                    f'Invalid prompt record {index} in "{self.data_path}": {exc}'
                ) from exc

        return prompts

    def save(self, prompts: Sequence[Prompt]) -> None:
        """Save prompts to the data file using atomic replacement."""
        temporary_path: Path | None = None

        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            records = [prompt.to_dict() for prompt in prompts]

            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.data_path.parent,
                prefix=f".{self.data_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(
                    records,
                    temporary_file,
                    ensure_ascii=False,
                    indent=2,
                )
                temporary_file.write("\n")
                temporary_file.flush()

            os.replace(temporary_path, self.data_path)
        except (OSError, UnicodeError) as exc:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

            raise StorageError(
                f'Could not save data file "{self.data_path}": {exc}'
            ) from exc

    def add(self, prompt: Prompt) -> None:
        """Add a prompt unless its name already exists."""
        prompts = self.load()
        prompt_name = prompt.name.casefold()

        if any(existing.name.casefold() == prompt_name for existing in prompts):
            raise DuplicatePromptError(
                f'A prompt named "{prompt.name}" already exists.'
            )

        prompts.append(prompt)
        self.save(prompts)

    def list_all(self) -> list[Prompt]:
        """Return all stored prompts in insertion order."""
        return self.load()

    def search(self, query: str) -> list[Prompt]:
        """Find prompts whose names contain the query."""
        if not isinstance(query, str):
            raise ValidationError("Search query must be a string.")

        normalized_query = query.strip()
        if not normalized_query:
            raise ValidationError("Search query cannot be empty.")

        folded_query = normalized_query.casefold()
        return [
            prompt
            for prompt in self.load()
            if folded_query in prompt.name.casefold()
        ]

    def delete(self, name: str) -> Prompt:
        """Delete and return a prompt matching the supplied name."""
        if not isinstance(name, str):
            raise ValidationError("Prompt name must be a string.")

        normalized_name = name.strip()
        if not normalized_name:
            raise ValidationError("Prompt name cannot be empty.")

        folded_name = normalized_name.casefold()
        prompts = self.load()

        for index, prompt in enumerate(prompts):
            if prompt.name.casefold() == folded_name:
                deleted_prompt = prompts.pop(index)
                self.save(prompts)
                return deleted_prompt

        raise PromptNotFoundError(
            f'Prompt "{normalized_name}" does not exist.'
        )
