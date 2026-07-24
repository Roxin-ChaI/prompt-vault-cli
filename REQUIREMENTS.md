# Prompt Vault CLI

## 1. Project Goal

Create a lightweight Python command-line application for storing and managing reusable prompt templates locally.

The purpose of this project is to practice a complete Agentic Coding workflow, including requirements definition, planning, implementation, testing, review, and documentation.

## 2. Core Features

The application must support the following operations:

1. Add a prompt
2. List all prompts
3. Search for prompts by name
4. Delete a prompt
5. Store prompt data in a local JSON file

## 3. Prompt Data Model

Each prompt must contain:

- `name`: a unique prompt name
- `content`: the actual prompt text
- `description`: an optional short description

Example:

```json
{
  "name": "code-review",
  "content": "Review the following code and identify potential problems.",
  "description": "A reusable prompt for reviewing source code."
}

```

## 4. Technical Requirements

- Python 3.12+
- Prefer the Python standard library
- Use type hints
- Use `pytest` for automated testing
- Store data in a local JSON file
- Provide clear error messages
- Keep the project architecture simple
- Do not use a database
- Do not create a web interface
- Do not connect to an external AI API

## 5. CLI Commands

The application should provide the following commands:

- `add`: add a new prompt
- `list`: display all stored prompts
- `search`: search for prompts by name
- `delete`: delete a prompt by name

Expected command format:

```text
python -m src.main add
python -m src.main list
python -m src.main search
python -m src.main delete
```
The exact command arguments and input style will be decided during the planning phase.


## 6. Error Handling

The application must handle the following situations:

- The data file does not exist
- The JSON data file is empty or corrupted
- A prompt name already exists
- The prompt name is empty
- The prompt content is empty
- A search returns no results
- The user attempts to delete a nonexistent prompt

The application should display clear error messages instead of showing an unhandled Python traceback.

## 7. Testing Requirements

Automated tests must cover:

- Adding a valid prompt
- Listing stored prompts
- Searching for an existing prompt
- Searching with no matching results
- Deleting an existing prompt
- Attempting to delete a nonexistent prompt
- Rejecting duplicate prompt names
- Rejecting empty prompt names or content
- Handling a missing data file
- Handling an empty or corrupted JSON file

## 8. Acceptance Criteria

The project is considered complete when:

- All four main CLI commands work correctly
- Prompt data persists between program executions
- Invalid input produces clear and understandable error messages
- All automated tests pass
- The README includes installation and usage instructions
- The project structure and code are easy to understand

## 9. Scope Limitations

The first version will not include:

- User accounts or authentication
- Database storage
- A graphical or web interface
- Cloud synchronization
- Import or export functionality
- Prompt tags or categories
- Prompt editing or version history
- LLM API integration
- MCP integration
- RAG functionality
- Multi-agent functionality
