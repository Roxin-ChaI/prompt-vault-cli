"""Unit tests for JSON prompt storage."""

import json
import os
from pathlib import Path

import pytest

from src.errors import (
    DuplicatePromptError,
    PromptNotFoundError,
    StorageError,
    ValidationError,
)
from src.models import Prompt
from src.storage import PromptStorage


def test_missing_file_loads_as_empty_list(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")

    assert storage.load() == []


def test_valid_json_loads_prompt_objects(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    data_path.write_text(
        json.dumps(
            [
                {
                    "name": "Code-Review",
                    "content": "Review this code.",
                    "description": "A review prompt.",
                }
            ]
        ),
        encoding="utf-8",
    )

    prompts = PromptStorage(data_path).load()

    assert prompts == [
        Prompt(
            name="Code-Review",
            content="Review this code.",
            description="A review prompt.",
        )
    ]


def test_save_creates_data_file(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    storage = PromptStorage(data_path)

    storage.save([Prompt(name="code-review", content="Review this code.")])

    assert data_path.is_file()


def test_save_and_reload_round_trip(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    expected = [
        Prompt(
            name="Code-Review",
            content="\n  Review this code.  \n",
            description="A review prompt.",
        ),
        Prompt(name="summarize", content="Summarize the following text."),
    ]

    storage.save(expected)

    assert storage.load() == expected


def test_unicode_remains_readable_in_saved_file(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    storage = PromptStorage(data_path)

    storage.save(
        [
            Prompt(
                name="翻译",
                content="请翻译这段文字。 👋",
                description="中文提示词",
            )
        ]
    )

    contents = data_path.read_text(encoding="utf-8")
    assert "翻译" in contents
    assert "请翻译这段文字。 👋" in contents
    assert "中文提示词" in contents


def test_saved_json_has_top_level_list(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    PromptStorage(data_path).save(
        [Prompt(name="code-review", content="Review this code.")]
    )

    data = json.loads(data_path.read_text(encoding="utf-8"))

    assert isinstance(data, list)
    assert data[0]["name"] == "code-review"


def test_saved_json_uses_two_space_indentation_and_one_final_newline(
    tmp_path: Path,
) -> None:
    data_path = tmp_path / "data.json"
    PromptStorage(data_path).save(
        [Prompt(name="code-review", content="Review this code.")]
    )

    contents = data_path.read_text(encoding="utf-8")

    assert '\n    "name": "code-review"' in contents
    assert contents.endswith("\n")
    assert not contents.endswith("\n\n")


@pytest.mark.parametrize("contents", ["", "   ", "\n\t"])
def test_empty_or_whitespace_only_file_raises_storage_error(
    tmp_path: Path,
    contents: str,
) -> None:
    data_path = tmp_path / "data.json"
    data_path.write_text(contents, encoding="utf-8")

    with pytest.raises(StorageError, match="empty") as exc_info:
        PromptStorage(data_path).load()

    assert str(data_path) in str(exc_info.value)


def test_malformed_json_raises_storage_error(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    data_path.write_text('[{"name": "unfinished"}', encoding="utf-8")

    with pytest.raises(StorageError, match="invalid JSON") as exc_info:
        PromptStorage(data_path).load()

    assert str(data_path) in str(exc_info.value)


def test_invalid_utf8_raises_storage_error_without_altering_file(
    tmp_path: Path,
) -> None:
    data_path = tmp_path / "data.json"
    invalid_contents = b"\xff\xfe\xfa"
    data_path.write_bytes(invalid_contents)

    with pytest.raises(StorageError, match="Could not read data file") as exc_info:
        PromptStorage(data_path).load()

    assert str(data_path) in str(exc_info.value)
    assert data_path.read_bytes() == invalid_contents


def test_os_error_while_reading_is_wrapped_and_chained(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_path = tmp_path / "data.json"
    data_path.write_text("[]\n", encoding="utf-8")
    read_error = OSError("simulated read failure")

    def fail_read_text(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> str:
        raise read_error

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    with pytest.raises(StorageError, match="Could not read data file") as exc_info:
        PromptStorage(data_path).load()

    assert str(data_path) in str(exc_info.value)
    assert exc_info.value.__cause__ is read_error


@pytest.mark.parametrize(
    "data",
    [
        {"name": "code-review"},
        "not a list",
        42,
        None,
    ],
)
def test_wrong_top_level_json_type_raises_storage_error(
    tmp_path: Path,
    data: object,
) -> None:
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(StorageError, match="top-level JSON list") as exc_info:
        PromptStorage(data_path).load()

    assert str(data_path) in str(exc_info.value)


def test_non_dictionary_record_raises_storage_error(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps(["not a prompt"]), encoding="utf-8")

    with pytest.raises(StorageError, match="must be a JSON object") as exc_info:
        PromptStorage(data_path).load()

    assert str(data_path) in str(exc_info.value)


@pytest.mark.parametrize(
    "record",
    [
        {"content": "Review this code."},
        {"name": "", "content": "Review this code."},
        {"name": "code-review", "content": 123},
        {
            "name": "code-review",
            "content": "Review this code.",
            "unexpected": "value",
        },
    ],
)
def test_invalid_prompt_record_raises_storage_error(
    tmp_path: Path,
    record: dict[str, object],
) -> None:
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps([record]), encoding="utf-8")

    with pytest.raises(StorageError, match="Invalid prompt record") as exc_info:
        PromptStorage(data_path).load()

    assert str(data_path) in str(exc_info.value)


def test_failed_read_does_not_alter_original_file(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    original_contents = '{"invalid": true}\n'
    data_path.write_text(original_contents, encoding="utf-8")

    with pytest.raises(StorageError):
        PromptStorage(data_path).load()

    assert data_path.read_text(encoding="utf-8") == original_contents


def test_saving_to_nested_path_creates_parent_directory(tmp_path: Path) -> None:
    data_path = tmp_path / "nested" / "vault" / "data.json"

    PromptStorage(data_path).save(
        [Prompt(name="code-review", content="Review this code.")]
    )

    assert data_path.is_file()


def test_failed_save_preserves_original_and_removes_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_path = tmp_path / "data.json"
    original_contents = "[]\n"
    data_path.write_text(original_contents, encoding="utf-8")
    storage = PromptStorage(data_path)

    def fail_replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        raise OSError("replacement failed")

    monkeypatch.setattr("src.storage.os.replace", fail_replace)

    with pytest.raises(StorageError, match="Could not save data file") as exc_info:
        storage.save([Prompt(name="code-review", content="Review this code.")])

    assert str(data_path) in str(exc_info.value)
    assert data_path.read_text(encoding="utf-8") == original_contents
    assert list(tmp_path.glob(".data.json.*.tmp")) == []


def test_add_prompt_to_missing_data_file(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    storage = PromptStorage(data_path)
    prompt = Prompt(name="Code-Review", content="Review this code.")

    storage.add(prompt)

    assert data_path.is_file()
    assert storage.load() == [prompt]
    assert storage.load()[0].name == "Code-Review"


def test_adding_multiple_prompts_preserves_insertion_order(
    tmp_path: Path,
) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompts = [
        Prompt(name="summarize", content="Summarize this text."),
        Prompt(name="code-review", content="Review this code."),
        Prompt(name="translate", content="Translate this text."),
    ]

    for prompt in prompts:
        storage.add(prompt)

    assert storage.list_all() == prompts


def test_added_prompts_persist_after_reloading(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    prompt = Prompt(name="code-review", content="Review this code.")

    PromptStorage(data_path).add(prompt)
    reloaded_storage = PromptStorage(data_path)

    assert reloaded_storage.list_all() == [prompt]


def test_exact_duplicate_name_is_rejected(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    storage.add(Prompt(name="code-review", content="Review this code."))

    with pytest.raises(DuplicatePromptError, match="already exists"):
        storage.add(Prompt(name="code-review", content="Different content."))


def test_case_only_duplicate_name_is_rejected(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    storage.add(Prompt(name="Code-Review", content="Review this code."))

    with pytest.raises(DuplicatePromptError, match="already exists"):
        storage.add(Prompt(name="code-review", content="Different content."))


def test_duplicate_rejection_does_not_modify_data_file(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    storage = PromptStorage(data_path)
    storage.add(Prompt(name="Code-Review", content="Review this code."))
    original_contents = data_path.read_bytes()

    with pytest.raises(DuplicatePromptError):
        storage.add(Prompt(name="CODE-REVIEW", content="Different content."))

    assert data_path.read_bytes() == original_contents


def test_listing_missing_vault_returns_empty_list(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "missing.json")

    assert storage.list_all() == []


def test_listing_returns_prompts_in_insertion_order(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompts = [
        Prompt(name="summarize", content="Summarize this text."),
        Prompt(name="code-review", content="Review this code."),
    ]
    storage.save(prompts)

    assert storage.list_all() == prompts


def test_listing_returns_an_independent_collection(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompt = Prompt(name="code-review", content="Review this code.")
    storage.save([prompt])

    listed_prompts = storage.list_all()
    listed_prompts.clear()

    assert storage.list_all() == [prompt]


def test_search_by_exact_name(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompt = Prompt(name="code-review", content="Review this code.")
    storage.save([prompt])

    assert storage.search("code-review") == [prompt]


def test_search_by_partial_name(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompt = Prompt(name="code-review", content="Review this code.")
    storage.save([prompt])

    assert storage.search("review") == [prompt]


def test_search_is_case_insensitive_and_strips_query(
    tmp_path: Path,
) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompt = Prompt(name="Code-Review", content="Review this code.")
    storage.save([prompt])

    assert storage.search("  CODE-REVIEW  ") == [prompt]


def test_search_results_preserve_insertion_order(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompts = [
        Prompt(name="review-summary", content="Summarize a review."),
        Prompt(name="translate", content="Translate this text."),
        Prompt(name="code-review", content="Review this code."),
        Prompt(name="review-email", content="Review this email."),
    ]
    storage.save(prompts)

    assert storage.search("review") == [prompts[0], prompts[2], prompts[3]]


def test_search_with_no_matches_returns_empty_list(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    storage.save(
        [Prompt(name="code-review", content="Review this code.")]
    )

    assert storage.search("translate") == []


@pytest.mark.parametrize("query", ["", "   ", "\n\t"])
def test_empty_search_query_is_rejected(
    tmp_path: Path,
    query: str,
) -> None:
    storage = PromptStorage(tmp_path / "data.json")

    with pytest.raises(ValidationError, match="Search query cannot be empty"):
        storage.search(query)


@pytest.mark.parametrize("query", [None, 123, ["review"]])
def test_wrong_search_query_type_is_rejected(
    tmp_path: Path,
    query: object,
) -> None:
    storage = PromptStorage(tmp_path / "data.json")

    with pytest.raises(ValidationError, match="must be a string"):
        storage.search(query)  # type: ignore[arg-type]


def test_search_does_not_modify_data_file(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    storage = PromptStorage(data_path)
    storage.save(
        [Prompt(name="code-review", content="Review this code.")]
    )
    original_contents = data_path.read_bytes()

    storage.search("review")

    assert data_path.read_bytes() == original_contents


def test_delete_existing_prompt(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompt = Prompt(name="code-review", content="Review this code.")
    storage.save([prompt])

    storage.delete("code-review")

    assert storage.list_all() == []


def test_delete_is_case_insensitive_and_strips_name(
    tmp_path: Path,
) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompt = Prompt(name="Code-Review", content="Review this code.")
    storage.save([prompt])

    storage.delete("  CODE-REVIEW  ")

    assert storage.list_all() == []


def test_delete_returns_removed_prompt(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompt = Prompt(name="Code-Review", content="Review this code.")
    storage.save([prompt])

    deleted_prompt = storage.delete("code-review")

    assert deleted_prompt == prompt
    assert deleted_prompt.name == "Code-Review"


def test_other_prompts_remain_after_deletion(tmp_path: Path) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    prompts = [
        Prompt(name="summarize", content="Summarize this text."),
        Prompt(name="code-review", content="Review this code."),
        Prompt(name="translate", content="Translate this text."),
    ]
    storage.save(prompts)

    storage.delete("code-review")

    assert storage.list_all() == [prompts[0], prompts[2]]


def test_delete_nonexistent_prompt_raises_not_found(
    tmp_path: Path,
) -> None:
    storage = PromptStorage(tmp_path / "data.json")
    storage.save(
        [Prompt(name="code-review", content="Review this code.")]
    )

    with pytest.raises(PromptNotFoundError, match="does not exist"):
        storage.delete("missing")


def test_failed_deletion_does_not_modify_data_file(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    storage = PromptStorage(data_path)
    storage.save(
        [Prompt(name="code-review", content="Review this code.")]
    )
    original_contents = data_path.read_bytes()

    with pytest.raises(PromptNotFoundError):
        storage.delete("missing")

    assert data_path.read_bytes() == original_contents


@pytest.mark.parametrize("name", ["", "   ", "\n\t"])
def test_empty_delete_name_is_rejected(
    tmp_path: Path,
    name: str,
) -> None:
    storage = PromptStorage(tmp_path / "data.json")

    with pytest.raises(ValidationError, match="Prompt name cannot be empty"):
        storage.delete(name)


@pytest.mark.parametrize("name", [None, 123, ["code-review"]])
def test_wrong_delete_name_type_is_rejected(
    tmp_path: Path,
    name: object,
) -> None:
    storage = PromptStorage(tmp_path / "data.json")

    with pytest.raises(ValidationError, match="must be a string"):
        storage.delete(name)  # type: ignore[arg-type]
