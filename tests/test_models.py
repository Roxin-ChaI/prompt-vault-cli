"""Unit tests for the Prompt data model."""

import pytest

from src.errors import ValidationError
from src.models import Prompt


def test_create_valid_prompt() -> None:
    prompt = Prompt(
        name="code-review",
        content="Review this code.",
        description="A code review prompt.",
    )

    assert prompt.name == "code-review"
    assert prompt.content == "Review this code."
    assert prompt.description == "A code review prompt."


def test_name_whitespace_is_trimmed() -> None:
    prompt = Prompt(name="  code-review  ", content="Review this code.")

    assert prompt.name == "code-review"


def test_original_name_casing_is_preserved() -> None:
    prompt = Prompt(name="  Code-Review  ", content="Review this code.")

    assert prompt.name == "Code-Review"


def test_content_whitespace_is_preserved() -> None:
    content = "\n  Review this code carefully.  \n"

    prompt = Prompt(name="code-review", content=content)

    assert prompt.content == content


def test_description_whitespace_is_trimmed() -> None:
    prompt = Prompt(
        name="code-review",
        content="Review this code.",
        description="  A code review prompt.  ",
    )

    assert prompt.description == "A code review prompt."


@pytest.mark.parametrize("description", ["", "   ", "\n\t"])
def test_empty_description_is_normalized_to_none(description: str) -> None:
    prompt = Prompt(
        name="code-review",
        content="Review this code.",
        description=description,
    )

    assert prompt.description is None


@pytest.mark.parametrize("name", ["", "   ", "\n\t"])
def test_empty_name_is_rejected(name: str) -> None:
    with pytest.raises(ValidationError, match="name cannot be empty"):
        Prompt(name=name, content="Review this code.")


@pytest.mark.parametrize("content", ["", "   ", "\n\t"])
def test_empty_content_is_rejected(content: str) -> None:
    with pytest.raises(ValidationError, match="content cannot be empty"):
        Prompt(name="code-review", content=content)


@pytest.mark.parametrize(
    ("field_name", "values"),
    [
        ("name", {"name": 123, "content": "Review this code."}),
        ("content", {"name": "code-review", "content": 123}),
        (
            "description",
            {
                "name": "code-review",
                "content": "Review this code.",
                "description": 123,
            },
        ),
    ],
)
def test_wrong_field_types_are_rejected(
    field_name: str,
    values: dict[str, object],
) -> None:
    with pytest.raises(ValidationError, match=field_name):
        Prompt(**values)  # type: ignore[arg-type]


def test_prompt_serializes_to_dictionary() -> None:
    prompt = Prompt(
        name="code-review",
        content="Review this code.",
        description="A code review prompt.",
    )

    assert prompt.to_dict() == {
        "name": "code-review",
        "content": "Review this code.",
        "description": "A code review prompt.",
    }


def test_prompt_deserializes_from_dictionary() -> None:
    prompt = Prompt.from_dict(
        {
            "name": "  Code-Review  ",
            "content": "\nReview this code.\n",
            "description": "  A code review prompt.  ",
        }
    )

    assert prompt == Prompt(
        name="Code-Review",
        content="\nReview this code.\n",
        description="A code review prompt.",
    )


@pytest.mark.parametrize(
    "data",
    [
        {"content": "Review this code."},
        {"name": "code-review"},
        {},
    ],
)
def test_missing_required_dictionary_fields_are_rejected(
    data: dict[str, object],
) -> None:
    with pytest.raises(ValidationError, match="Missing required prompt field"):
        Prompt.from_dict(data)


def test_unexpected_dictionary_fields_are_rejected() -> None:
    data = {
        "name": "code-review",
        "content": "Review this code.",
        "category": "development",
    }

    with pytest.raises(ValidationError, match="Unexpected prompt field"):
        Prompt.from_dict(data)


@pytest.mark.parametrize(
    "data",
    [
        {"name": 123, "content": "Review this code."},
        {"name": "code-review", "content": 123},
        {
            "name": "code-review",
            "content": "Review this code.",
            "description": 123,
        },
    ],
)
def test_dictionary_field_types_are_validated(data: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Prompt.from_dict(data)
