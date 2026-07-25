"""Unit tests for JSON prompt storage."""

import json
import os
from pathlib import Path

import pytest

from src.errors import StorageError
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
