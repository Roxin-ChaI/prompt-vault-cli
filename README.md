# Prompt Vault CLI

Prompt Vault CLI is a lightweight local command-line application for storing and managing reusable prompt templates in a JSON file.

## Features

- Add prompts with required names and content
- List prompts in insertion order
- Search prompt names with case-insensitive partial matching
- Delete prompts with case-insensitive exact matching
- Store optional prompt descriptions
- Persist data locally in human-readable JSON
- Prevent duplicate names, including case-only duplicates
- Reduce data-loss risk through atomic file replacement
- Report clear application errors with predictable exit codes
- Verify behavior with automated pytest coverage

## Requirements

- Python 3.12 or newer
- pytest, required only for running the tests

The application itself uses only the Python standard library.

## Setup

Clone the repository, or enter an existing checkout:

```shell
git clone <repository-url>
cd prompt-vault-cli
```

Create a virtual environment:

```shell
python -m venv .venv
```

Activate it on macOS or Linux:

```shell
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install pytest for development and testing:

```shell
python -m pip install pytest
```

## Usage

Run commands from the repository root.

```text
python -m src.main add --name NAME --content CONTENT [--description DESCRIPTION]
python -m src.main list
python -m src.main search QUERY
python -m src.main delete NAME
```

Add a prompt:

```shell
python -m src.main add --name "code-review" --content "Review the following code."
```

Add a prompt with a description:

```shell
python -m src.main add --name "email summary" --content "Summarize this email." --description "Creates a concise email summary."
```

List all prompts:

```shell
python -m src.main list
```

Search by a full or partial name:

```shell
python -m src.main search "review"
```

Delete a prompt by name:

```shell
python -m src.main delete "code-review"
```

## Output examples

Successful add:

```text
Added prompt: code-review
```

Listing prompts, including one without a description:

```text
Name: code-review
Description: (none)
Content: Review the following code.

Name: email summary
Description: Creates a concise email summary.
Content: Summarize this email.
```

Duplicate-name error:

```text
Error: A prompt named "code-review" already exists.
```

Search with no result:

```text
Error: no prompts found matching "translate".
```

Successful delete:

```text
Deleted prompt: code-review
```

Application errors are written to standard error (`stderr`). Successful output is written to standard output (`stdout`).

## Data storage

The default data file is `data.json` in the current working directory. A missing file represents an empty vault, and the file is created when the first prompt is added. Runtime `data.json` files are ignored by Git.

Data is stored as readable UTF-8 JSON, with prompts kept in insertion order. Prompt names preserve their original casing, while duplicate checking, searching, and deletion use case-insensitive comparisons.

Writes use a temporary file in the same directory followed by atomic replacement to reduce data-loss risk. Empty, malformed, unreadable, or structurally invalid files produce a clear `StorageError` instead of being silently discarded or replaced.

## Exit codes

- `0`: the command completed successfully
- `1`: an expected application or storage error occurred
- `2`: `argparse` rejected the command-line syntax

## Running tests

Run the complete test suite:

```shell
python -m pytest -v
```

Run individual suites:

```shell
python -m pytest tests/test_models.py -v
python -m pytest tests/test_storage.py -v
python -m pytest tests/test_cli.py -v
```

Compile the source and tests to check Python syntax:

```shell
python -m compileall src tests
```

## Project structure

```text
prompt-vault-cli/
├── REQUIREMENTS.md
├── IMPLEMENTATION_PLAN.md
├── README.md
├── LEARNING_LOG.md
├── src/
│   ├── __init__.py
│   ├── errors.py
│   ├── models.py
│   ├── storage.py
│   └── main.py
└── tests/
    ├── test_models.py
    ├── test_storage.py
    └── test_cli.py
```

Production modules:

- `src/__init__.py` marks `src` as a Python package.
- `src/errors.py` defines the application exception hierarchy.
- `src/models.py` defines and validates the `Prompt` data model.
- `src/storage.py` manages JSON persistence and prompt collection operations.
- `src/main.py` defines CLI parsing, output formatting, and exit-code handling.

## Design notes

- `Prompt` is an immutable dataclass.
- Validation and normalization belong to the model.
- JSON persistence and collection operations belong to `PromptStorage`.
- CLI parsing, formatting, and exit-code translation belong to `main.py`.
- Prompt names are compared with `casefold()` while their stored casing is preserved.
- Tests inject temporary storage paths so they do not modify real user data.

## Scope

The current version intentionally does not include:

- A web interface
- A database
- Cloud synchronization
- Authentication
- External AI API integration
- Prompt editing
- Tags or categories
- Import or export commands

## Learning workflow

This repository was built incrementally through requirements definition, an approved implementation plan, small implementation stages, automated tests, manual CLI integration testing, read-only code review, review-driven fixes, and focused Git commits.

`LEARNING_LOG.md` is reserved for the developer's own reflection.
