"""Data models for Prompt Vault CLI."""

from dataclasses import dataclass
from typing import Self

from .errors import ValidationError


@dataclass(frozen=True)
class Prompt:
    """A reusable prompt stored in the vault."""

    name: str
    content: str
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize prompt fields."""
        if not isinstance(self.name, str):
            raise ValidationError("Prompt name must be a string.")
        if not isinstance(self.content, str):
            raise ValidationError("Prompt content must be a string.")
        if self.description is not None and not isinstance(self.description, str):
            raise ValidationError("Prompt description must be a string or None.")

        normalized_name = self.name.strip()
        if not normalized_name:
            raise ValidationError("Prompt name cannot be empty.")
        if not self.content.strip():
            raise ValidationError("Prompt content cannot be empty.")

        normalized_description = (
            self.description.strip() if self.description is not None else None
        )

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(
            self,
            "description",
            normalized_description or None,
        )

    def to_dict(self) -> dict[str, str | None]:
        """Return a JSON-compatible dictionary."""
        return {
            "name": self.name,
            "content": self.content,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Create a prompt from a JSON-compatible dictionary."""
        if not isinstance(data, dict):
            raise ValidationError("Prompt data must be a dictionary.")

        missing_fields = [
            field for field in ("name", "content") if field not in data
        ]
        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValidationError(f"Missing required prompt field(s): {fields}.")

        allowed_fields = {"name", "content", "description"}
        unexpected_fields = [
            str(field) for field in data if field not in allowed_fields
        ]
        if unexpected_fields:
            fields = ", ".join(unexpected_fields)
            raise ValidationError(f"Unexpected prompt field(s): {fields}.")

        return cls(
            name=data["name"],  # type: ignore[arg-type]
            content=data["content"],  # type: ignore[arg-type]
            description=data.get("description"),  # type: ignore[arg-type]
        )
