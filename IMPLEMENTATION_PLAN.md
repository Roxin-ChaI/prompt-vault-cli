# Prompt Vault CLI Implementation Plan

This plan follows `REQUIREMENTS.md` as the source of truth. The architecture is intentionally small, uses the Python standard library for production code, and contains no database, web framework, external AI API, or unnecessary dependency.

## 1. Project Structure

```text
prompt-vault-cli/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── storage.py
│   └── errors.py
├── tests/
│   ├── test_models.py
│   ├── test_storage.py
│   └── test_cli.py
├── .gitignore
├── IMPLEMENTATION_PLAN.md
├── REQUIREMENTS.md
├── README.md
├── LEARNING_LOG.md
└── data.json              # Created at runtime and ignored by Git
```

This structure has five production Python modules when `__init__.py` is counted, meeting the project constraint. No packaging configuration is required for the expected `python -m src.main` invocation. A `pyproject.toml` could configure pytest, but it would add little value at this scale and will be omitted initially.

`LEARNING_LOG.md` will not be automatically modified during implementation. The user will complete it during the final reflection stage.

## 2. Module Responsibilities

### `src/__init__.py`

Marks `src` as a Python package and contains no application logic.

### `src/models.py`

Defines the immutable `Prompt` data model using `@dataclass(frozen=True)`.

Responsibilities:

- Represent the prompt name, content, and optional description.
- Validate field types and required values.
- Strip surrounding whitespace from names while preserving letter casing.
- Normalize optional descriptions.
- Preserve meaningful whitespace in prompt content.
- Convert between `Prompt` instances and JSON-compatible dictionaries.

### `src/storage.py`

Owns JSON persistence and prompt collection operations.

Responsibilities:

- Load and validate `data.json`.
- Treat a missing data file as an empty vault.
- Add prompts while enforcing unique names.
- List prompts in insertion order.
- Search for prompts by name.
- Delete prompts by name.
- Save changes safely using atomic replacement.

These operations remain together rather than introducing an unnecessary service layer.

### `src/errors.py`

Defines a small application-specific exception hierarchy:

- `VaultError`
- `ValidationError`
- `DuplicatePromptError`
- `PromptNotFoundError`
- `StorageError`

This gives the CLI clear, intentional errors to catch without relying on message matching or exposing internal exceptions.

### `src/main.py`

Owns the command-line interface.

Responsibilities:

- Define the `argparse` parser and four subcommands.
- Dispatch commands to storage operations.
- Format successful output for people to read.
- Translate known application errors into clear messages and exit codes.
- Provide a testable command entry point with dependency injection:

  ```python
  main(
      argv: Sequence[str] | None = None,
      storage: PromptStorage | None = None,
  ) -> int
  ```
- Call `raise SystemExit(main())` only at the module entry point.

### Test files

- `tests/test_models.py`: data-model validation, normalization, and serialization.
- `tests/test_storage.py`: JSON persistence and prompt collection behavior.
- `tests/test_cli.py`: command parsing, output, error messages, and exit codes.

### Documentation files

- `README.md`: installation, usage examples, storage behavior, and test instructions.
- `LEARNING_LOG.md`: reserved for the user's final reflection and not automatically modified.
- `REQUIREMENTS.md`: remains unchanged as the source of truth.

## 3. Prompt Data Model and Validation Rules

The model contains:

- `name: str`
- `content: str`
- `description: str | None`

It will use `@dataclass(frozen=True)`. Immutability is appropriate because version one has no editing feature. `slots=True` will be omitted because it adds unnecessary complexity for this small learning project.

### Name rules

- The value must be a string.
- Strip leading and trailing whitespace before storage.
- Reject the name if it is empty after stripping.
- Preserve the user's original letter casing in the model and JSON file.
- Never permanently convert the stored name to lowercase.
- Use `casefold()` only for comparisons:
  - Duplicate detection uses a case-insensitive full-name comparison.
  - Search uses a case-insensitive substring comparison.
  - Delete uses a case-insensitive full-name comparison.

For example, a name entered as `  Code-Review  ` is stored as `Code-Review`. A later name of `code-review` is considered a duplicate and can also locate or delete the stored prompt.

### Content rules

- The value must be a string.
- Reject content that is empty or contains only whitespace.
- Use `content.strip()` only to determine whether the value is empty.
- Otherwise preserve the content verbatim because whitespace can be meaningful in prompt templates.

### Description rules

- The value may be omitted or set to `None`.
- If supplied, it must be a string.
- Strip leading and trailing whitespace.
- Normalize an empty description to `None`.
- Represent an absent description as JSON `null`.

### Stored-data validation

Unexpected fields, incorrectly typed fields, or invalid prompt records in the JSON file will make the storage data invalid. They will not be silently discarded or corrected.

## 4. JSON Storage Design

The local `data.json` file will contain a top-level array of prompt objects:

```json
[
  {
    "name": "code-review",
    "content": "Review the following code and identify potential problems.",
    "description": "A reusable prompt for reviewing source code."
  }
]
```

Serialization rules:

- Use UTF-8 encoding.
- Use two-space indentation.
- Use `ensure_ascii=False` so Unicode remains readable.
- End the file with a newline.
- Keep the stable field order `name`, `content`, `description`.
- Preserve prompt insertion order.

### File behavior

- A missing file represents an empty vault.
- The file is created when the first prompt is added.
- An empty file produces a clear storage error.
- Malformed JSON produces a clear storage error.
- Valid JSON with an incorrect top-level type or invalid prompt record produces a clear storage error.
- An inaccessible file produces a clear storage error.
- Failed reads never cause the data file to be rewritten.
- Corrupted data is never silently replaced with an empty collection.

### Safe writes

Writes will be atomic:

1. Serialize the complete prompt collection to a temporary file in the same directory.
2. Flush and close the temporary file.
3. Replace `data.json` using `os.replace()`.

This reduces the risk of leaving partially written JSON if a write is interrupted.

### Storage location

The default path will be `Path("data.json")`, relative to the current working directory. This matches the existing `.gitignore`, keeps local data visible, and avoids platform-specific user-data directories. The path will be injectable internally so automated tests never access the real data file.

Other possible designs include storing the file beside the package, using a platform-specific user-data directory, or exposing a public path option. Those approaches add complexity that is not required for version one.

## 5. CLI Design

The CLI will use the standard-library `argparse` module.

Commands:

```text
python -m src.main add --name NAME --content CONTENT [--description DESCRIPTION]
python -m src.main list
python -m src.main search QUERY
python -m src.main delete NAME
```

Behavior:

- `add` stores a prompt and prints a short confirmation.
- `list` displays every prompt in insertion order.
- `search` performs a case-insensitive substring search on prompt names.
- `delete` performs a case-insensitive full-name match and prints a confirmation.
- `add` requires `--name` and `--content`; `--description` is optional.
- `list` accepts no command-specific arguments.
- All commands receive automatically generated help from `argparse`.

Prompts will be displayed as readable labeled records rather than raw JSON. An absent description will be shown clearly, such as `Description: (none)`.

### Input-style decision

Required command-line arguments are preferred over interactive questions. They are explicit, scriptable, and straightforward to automate and test. Version one will not include an interactive fallback.

### Search and ordering decisions

Search will use case-insensitive substring matching because it is more useful than exact-only search while remaining simple. Results and lists will retain insertion order rather than introducing a separate alphabetical sorting policy.

## 6. Error-Handling Strategy

Expected failures will not display Python tracebacks.

The application flow will be:

1. Model validation or a storage operation detects a known failure.
2. It raises a specific subclass of `VaultError`.
3. `main()` catches the known application error.
4. The CLI writes a concise message beginning with `Error:` to standard error.
5. The CLI returns a nonzero exit code.

Recommended exit codes:

- `0`: successful operation, including listing an empty vault.
- `1`: application failure, such as invalid input, a duplicate, a missing prompt, no search results, or invalid storage.
- `2`: malformed CLI syntax, handled automatically by `argparse`.

Expected messages will clearly identify the problem, for example:

- `Error: prompt name cannot be empty.`
- `Error: prompt content cannot be empty.`
- `Error: a prompt named "code-review" already exists.`
- `Error: no prompts matched "review".`
- `Error: prompt "missing" does not exist.`
- `Error: data.json is empty; expected a JSON array.`
- `Error: could not read data.json because it contains invalid JSON.`

Listing an empty vault is not an error; it prints `No prompts stored.` and returns `0`. A search with no matches is an unsuccessful lookup and returns `1`.

The application will catch anticipated validation, JSON, and filesystem failures. It will not wrap the whole program in a blanket `except Exception`, because that could hide programming defects during development.

## 7. Automated Testing Strategy

Tests will use `pytest`, with `tmp_path` for isolated storage and `capsys` for CLI output. Tests will call the testable `main()` function with argument lists and an injected temporary data path so they do not touch the user's real `data.json`.

### Model tests

- Create a valid prompt.
- Reject an empty name.
- Reject a whitespace-only name.
- Reject empty or whitespace-only content.
- Strip name whitespace while preserving name casing.
- Normalize the optional description.
- Preserve meaningful content whitespace.
- Serialize and deserialize correctly.
- Reject incorrectly typed fields.

### Storage tests

- A missing data file loads as an empty collection.
- Adding a prompt creates the data file.
- Added prompts persist after storage is reloaded.
- Listing returns stored prompts in insertion order.
- Duplicate names are rejected, including case-only variants.
- Search finds an existing prompt.
- Search supports partial, case-insensitive matching.
- A no-match search returns an empty result.
- An existing prompt can be deleted.
- Deletion uses a case-insensitive full-name comparison.
- Deleting a nonexistent prompt is rejected.
- An empty file produces `StorageError`.
- Corrupted JSON produces `StorageError`.
- An incorrect top-level JSON value produces `StorageError`.
- Malformed prompt records produce `StorageError`.
- Failed reads do not overwrite the original file.

### CLI tests

- Successful `add`, `list`, `search`, and `delete` commands.
- Successful commands print clear messages and return `0`.
- Duplicate and invalid-input errors go to standard error and return `1`.
- A no-result search returns a clear message and exit code `1`.
- Deleting a nonexistent prompt returns a clear message and exit code `1`.
- Listing an empty vault prints a clear message and returns `0`.
- Missing commands and malformed arguments are rejected by `argparse`.
- Storage errors are displayed without a traceback.

Direct invocation of `main()` is faster and more precise than subprocess-heavy testing. A single subprocess smoke test may be added only if explicit verification of `python -m src.main` is needed; otherwise it is unnecessary.

## 8. Requirements Traceability

| Requirement | Responsible module | Automated test file |
|---|---|---|
| Add a prompt | `src/storage.py`, `src/main.py` | `tests/test_storage.py`, `tests/test_cli.py` |
| List all prompts | `src/storage.py`, `src/main.py` | `tests/test_storage.py`, `tests/test_cli.py` |
| Search by name | `src/storage.py`, `src/main.py` | `tests/test_storage.py`, `tests/test_cli.py` |
| Delete by name | `src/storage.py`, `src/main.py` | `tests/test_storage.py`, `tests/test_cli.py` |
| Unique prompt names | `src/storage.py` | `tests/test_storage.py` |
| Required name and content | `src/models.py` | `tests/test_models.py`, `tests/test_cli.py` |
| Optional description | `src/models.py` | `tests/test_models.py` |
| Local JSON persistence | `src/storage.py` | `tests/test_storage.py` |
| Persistence between executions | `src/storage.py` | `tests/test_storage.py` |
| Missing data file | `src/storage.py` | `tests/test_storage.py`, `tests/test_cli.py` |
| Empty or corrupted JSON | `src/storage.py`, `src/errors.py` | `tests/test_storage.py`, `tests/test_cli.py` |
| Duplicate-name error | `src/storage.py`, `src/errors.py` | `tests/test_storage.py`, `tests/test_cli.py` |
| Empty-name or content error | `src/models.py`, `src/errors.py` | `tests/test_models.py`, `tests/test_cli.py` |
| Search with no results | `src/main.py` | `tests/test_cli.py` |
| Delete nonexistent prompt | `src/storage.py`, `src/errors.py` | `tests/test_storage.py`, `tests/test_cli.py` |
| Clear errors without tracebacks | `src/main.py`, `src/errors.py` | `tests/test_cli.py` |
| Four required CLI commands | `src/main.py` | `tests/test_cli.py` |
| Type hints and Python 3.12+ | All production modules | Covered by review and test execution under Python 3.12 |
| Automated tests using pytest | `tests/` | All three test files |
| Installation and usage documentation | `README.md` | Acceptance review |
| No database, web UI, external AI API, or out-of-scope features | Entire project structure | Architecture and acceptance review |

## 9. Recommended Implementation Order

1. Add the package skeleton and application-specific exception hierarchy.
2. Implement the `Prompt` model and its unit tests.
3. Implement JSON loading and structural validation.
4. Implement atomic JSON saving.
5. Implement and test add, list, search, and delete storage operations.
6. Build the `argparse` interface and human-readable output formatting.
7. Add CLI-level tests for all required success and failure scenarios.
8. Run the full test suite and manually exercise all four commands.
9. Complete `README.md` with installation, usage, data-file, and testing instructions.
10. Review the finished project against every acceptance criterion in `REQUIREMENTS.md`.

Implementation will not begin until this plan is approved for execution.
