"""Tests for the Prompt Vault command-line interface."""

from pathlib import Path

import pytest

from src.main import build_parser, main
from src.models import Prompt
from src.storage import PromptStorage


@pytest.fixture
def storage(tmp_path: Path) -> PromptStorage:
    """Return storage isolated to a temporary data file."""
    return PromptStorage(tmp_path / "data.json")


@pytest.mark.parametrize(
    ("argv", "command"),
    [
        (["add", "--name", "one", "--content", "Content."], "add"),
        (["list"], "list"),
        (["search", "one"], "search"),
        (["delete", "one"], "delete"),
    ],
)
def test_parser_contains_required_commands(
    argv: list[str],
    command: str,
) -> None:
    arguments = build_parser().parse_args(argv)

    assert arguments.command == command


def test_missing_command_exits_with_code_two(
    storage: PromptStorage,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([], storage)

    assert exc_info.value.code == 2


@pytest.mark.parametrize(
    "argv",
    [
        ["add"],
        ["add", "--name", "code-review"],
        ["add", "--content", "Review this code."],
    ],
)
def test_missing_required_add_arguments_exit_with_code_two(
    storage: PromptStorage,
    argv: list[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv, storage)

    assert exc_info.value.code == 2


def test_missing_search_query_exits_with_code_two(
    storage: PromptStorage,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["search"], storage)

    assert exc_info.value.code == 2


def test_missing_delete_name_exits_with_code_two(
    storage: PromptStorage,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["delete"], storage)

    assert exc_info.value.code == 2


def test_add_creates_and_persists_prompt(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(
        [
            "add",
            "--name",
            "code-review",
            "--content",
            "Review this code.",
        ],
        storage,
    )

    assert result == 0
    assert storage.list_all() == [
        Prompt(name="code-review", content="Review this code.")
    ]
    assert capsys.readouterr() == (
        "Added prompt: code-review\n",
        "",
    )


def test_add_supports_omitted_description(
    storage: PromptStorage,
) -> None:
    result = main(
        [
            "add",
            "--name",
            "code-review",
            "--content",
            "Review this code.",
        ],
        storage,
    )

    assert result == 0
    assert storage.list_all()[0].description is None


def test_add_supports_provided_description(
    storage: PromptStorage,
) -> None:
    result = main(
        [
            "add",
            "--name",
            "code-review",
            "--content",
            "Review this code.",
            "--description",
            "A review prompt.",
        ],
        storage,
    )

    assert result == 0
    assert storage.list_all()[0].description == "A review prompt."


def test_add_prints_normalized_stored_name(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(
        [
            "add",
            "--name",
            "  Code-Review  ",
            "--content",
            "Review this code.",
        ],
        storage,
    )

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "Added prompt: Code-Review\n"
    assert captured.err == ""


def test_duplicate_add_returns_one_and_only_prints_error(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    storage.add(Prompt(name="Code-Review", content="Review this code."))

    result = main(
        [
            "add",
            "--name",
            "code-review",
            "--content",
            "Different content.",
        ],
        storage,
    )

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err == (
        'Error: A prompt named "code-review" already exists.\n'
    )


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("   ", "Review this code."),
        ("code-review", "   "),
    ],
)
def test_invalid_prompt_input_returns_one(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
    name: str,
    content: str,
) -> None:
    result = main(
        ["add", "--name", name, "--content", content],
        storage,
    )

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err.startswith("Error: ")


def test_empty_list_prints_exact_message_and_returns_zero(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(["list"], storage)

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "No prompts stored.\n"
    assert captured.err == ""


def test_list_prints_all_fields_and_missing_description(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    storage.save(
        [Prompt(name="code-review", content="Review this code.")]
    )

    result = main(["list"], storage)

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == (
        "Name: code-review\n"
        "Description: (none)\n"
        "Content: Review this code.\n"
    )
    assert captured.err == ""


def test_list_preserves_order_and_uses_one_blank_line(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    storage.save(
        [
            Prompt(
                name="summarize",
                content="Summarize this text.",
                description="A summary prompt.",
            ),
            Prompt(name="code-review", content="Review this code."),
        ]
    )

    result = main(["list"], storage)

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == (
        "Name: summarize\n"
        "Description: A summary prompt.\n"
        "Content: Summarize this text.\n"
        "\n"
        "Name: code-review\n"
        "Description: (none)\n"
        "Content: Review this code.\n"
    )
    assert captured.err == ""


@pytest.mark.parametrize(
    "query",
    ["Code-Review", "Review", "CODE-REVIEW"],
)
def test_exact_partial_and_case_insensitive_search(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
    query: str,
) -> None:
    prompt = Prompt(name="Code-Review", content="Review this code.")
    storage.save([prompt])

    result = main(["search", query], storage)

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == (
        "Name: Code-Review\n"
        "Description: (none)\n"
        "Content: Review this code.\n"
    )
    assert captured.err == ""


def test_search_preserves_match_order_and_uses_list_format(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    storage.save(
        [
            Prompt(name="review-summary", content="Summarize a review."),
            Prompt(name="translate", content="Translate this text."),
            Prompt(
                name="code-review",
                content="Review this code.",
                description="A review prompt.",
            ),
        ]
    )

    search_result = main(["search", "review"], storage)
    search_output = capsys.readouterr().out

    assert search_result == 0
    assert search_output == (
        "Name: review-summary\n"
        "Description: (none)\n"
        "Content: Summarize a review.\n"
        "\n"
        "Name: code-review\n"
        "Description: A review prompt.\n"
        "Content: Review this code.\n"
    )


def test_search_with_no_matches_returns_one_and_only_prints_error(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    storage.save(
        [Prompt(name="code-review", content="Review this code.")]
    )

    result = main(["search", "missing"], storage)

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err == (
        'Error: no prompts found matching "missing".\n'
    )


def test_whitespace_only_search_returns_one_through_validation_error(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(["search", "   "], storage)

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err == "Error: Search query cannot be empty.\n"


def test_delete_removes_prompt_case_insensitively_and_prints_stored_name(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prompt = Prompt(name="Code-Review", content="Review this code.")
    storage.save([prompt])

    result = main(["delete", "code-review"], storage)

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "Deleted prompt: Code-Review\n"
    assert captured.err == ""
    assert storage.list_all() == []


def test_delete_keeps_other_prompts_persisted(
    storage: PromptStorage,
) -> None:
    remaining = Prompt(name="summarize", content="Summarize this text.")
    removed = Prompt(name="code-review", content="Review this code.")
    storage.save([remaining, removed])

    result = main(["delete", "code-review"], storage)

    assert result == 0
    assert storage.list_all() == [remaining]


def test_delete_missing_prompt_returns_one_and_only_prints_error(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(["delete", "missing"], storage)

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err == 'Error: Prompt "missing" does not exist.\n'


def test_malformed_json_returns_one_without_traceback(
    storage: PromptStorage,
    capsys: pytest.CaptureFixture[str],
) -> None:
    storage.data_path.write_text("{invalid json", encoding="utf-8")

    result = main(["list"], storage)

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err.startswith("Error: ")
    assert str(storage.data_path) in captured.err
    assert "Traceback" not in captured.err
