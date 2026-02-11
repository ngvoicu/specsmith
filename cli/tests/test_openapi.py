"""Tests for the openapi command — context gathering, CLI integration, helpers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from specsmith.ai.openapi import (
    ApiContext,
    _count_endpoints,
    _count_schemas,
    _detect_framework,
    _endpoint_slug,
    _parse_endpoint_docs,
    _strip_yaml_fences,
    gather_api_context,
    validate_openapi_yaml,
)
from specsmith.cli import app

runner = CliRunner()

MOCK_OPENAPI_YAML = """\
openapi: 3.1.1
info:
  title: Test API
  version: 0.1.0
paths:
  /api/users:
    get:
      summary: List users
      operationId: listUsers
      responses:
        '200':
          description: Success
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
"""

MOCK_ENDPOINT_DOCS_OUTPUT = """\
--- FILE: get-api-users.md ---
# GET /api/users

> listUsers — List all users

## UI Behavior

### What to Display
- Show a table of users with id and name columns

### User Flows
- Page load triggers GET /api/users
- Success displays user table

### State Transitions
- Loading → Success with user list

### Loading & Error States
- Show skeleton table while loading

## API Usage

### Request
- **Method:** GET
- **URL:** /api/users

### Response
#### Success (200)
```json
[{"id": 1, "name": "Alice"}]
```

### Business Rules
- Returns all active users

### Edge Cases
- Empty list when no users exist
"""


# ── Helper tests ─────────────────────────────────────────────────────


def test_strip_yaml_fences_with_yaml_fence():
    text = "```yaml\nopenapi: 3.1.1\ninfo:\n  title: Test\n```"
    result = _strip_yaml_fences(text)
    assert result == "openapi: 3.1.1\ninfo:\n  title: Test"


def test_strip_yaml_fences_with_yml_fence():
    text = "```yml\nopenapi: 3.1.1\n```"
    result = _strip_yaml_fences(text)
    assert result == "openapi: 3.1.1"


def test_strip_yaml_fences_no_fences():
    text = "openapi: 3.1.1\ninfo:\n  title: Test"
    result = _strip_yaml_fences(text)
    assert result == text


def test_strip_yaml_fences_generic_fence():
    text = "```\nopenapi: 3.1.1\n```"
    result = _strip_yaml_fences(text)
    assert result == "openapi: 3.1.1"


def test_endpoint_slug_simple():
    assert _endpoint_slug("GET", "/api/users") == "get-api-users"


def test_endpoint_slug_with_param():
    assert _endpoint_slug("POST", "/api/pulse/forms/{formId}") == "post-api-pulse-forms-formid"


def test_endpoint_slug_root():
    assert _endpoint_slug("GET", "/") == "get-"


def test_endpoint_slug_nested():
    assert _endpoint_slug("DELETE", "/api/v1/users/{userId}/posts/{postId}") == "delete-api-v1-users-userid-posts-postid"


def test_validate_openapi_yaml_valid():
    assert validate_openapi_yaml(MOCK_OPENAPI_YAML) is True


def test_validate_openapi_yaml_invalid():
    assert validate_openapi_yaml("not: valid: yaml: [[[") is False


def test_validate_openapi_yaml_missing_key():
    assert validate_openapi_yaml("title: test\nversion: 1") is False


def test_parse_endpoint_docs():
    result = _parse_endpoint_docs(MOCK_ENDPOINT_DOCS_OUTPUT)
    assert len(result) == 1
    assert result[0][0] == "get-api-users.md"
    assert "# GET /api/users" in result[0][1]


def test_parse_endpoint_docs_multiple():
    text = (
        "--- FILE: get-api-users.md ---\n# GET /api/users\nContent A\n\n"
        "--- FILE: post-api-users.md ---\n# POST /api/users\nContent B\n"
    )
    result = _parse_endpoint_docs(text)
    assert len(result) == 2
    assert result[0][0] == "get-api-users.md"
    assert result[1][0] == "post-api-users.md"


def test_parse_endpoint_docs_empty():
    result = _parse_endpoint_docs("")
    assert result == []


# ── Framework detection tests ────────────────────────────────────────


def test_detect_framework_express(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"dependencies": {"express": "^4.18"}}')
    assert _detect_framework(tmp_path) == "express"


def test_detect_framework_nestjs(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"dependencies": {"@nestjs/core": "^10.0"}}')
    assert _detect_framework(tmp_path) == "nestjs"


def test_detect_framework_fastapi(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["fastapi>=0.100"]')
    assert _detect_framework(tmp_path) == "fastapi"


def test_detect_framework_spring(tmp_path: Path):
    (tmp_path / "pom.xml").write_text("<project><parent><artifactId>spring-boot-starter-parent</artifactId></parent></project>")
    assert _detect_framework(tmp_path) == "spring"


def test_detect_framework_django(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("django>=4.2\ncelery>=5.0")
    assert _detect_framework(tmp_path) == "django"


def test_detect_framework_unknown(tmp_path: Path):
    assert _detect_framework(tmp_path) == "unknown"


# ── Context gathering tests ──────────────────────────────────────────


def test_gather_api_context_empty_project(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    ctx = gather_api_context(tmp_path, [])
    assert ctx.project_name == tmp_path.name
    assert ctx.has_api_code is False
    assert ctx.endpoint_count == 0


def test_gather_api_context_with_routes(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    routes_dir = tmp_path / "src" / "routes"
    routes_dir.mkdir(parents=True)
    (routes_dir / "users.ts").write_text(
        'import { Router } from "express";\n'
        'const router = Router();\n'
        'router.get("/users", listUsers);\n'
        'router.post("/users", createUser);\n'
    )
    (tmp_path / "package.json").write_text('{"dependencies": {"express": "^4.18"}}')

    ctx = gather_api_context(tmp_path, [])
    assert ctx.has_api_code is True
    assert ctx.endpoint_count >= 2
    assert len(ctx.route_files) >= 1


def test_gather_api_context_with_include(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "extra.md").write_text("# Extra context for the AI")

    ctx = gather_api_context(tmp_path, ["extra.md"])
    assert len(ctx.extra_files) == 1
    assert ctx.extra_files[0][0] == "extra.md"


def test_count_endpoints_spring():
    files = [("UserController.java", '@GetMapping("/users")\n@PostMapping("/users")\n@DeleteMapping("/users/{id}")')]
    assert _count_endpoints(files) == 3


def test_count_endpoints_express():
    files = [("routes.ts", 'router.get("/users", handler);\nrouter.post("/users", handler);')]
    assert _count_endpoints(files) == 2


def test_count_schemas_typescript():
    files = [("user.dto.ts", "export class CreateUserDto {\n  name: string;\n}\nexport interface User {\n  id: number;\n}")]
    assert _count_schemas(files) == 2


def test_count_schemas_python():
    files = [("models.py", "class User(BaseModel):\n    name: str\n\n@dataclass\nclass Config:\n    debug: bool")]
    assert _count_schemas(files) == 2


def test_api_context_to_prompt_context():
    ctx = ApiContext(
        project_name="test-api",
        project_structure="test-api/\n  src/",
        route_files=[("src/routes.ts", "router.get('/users')")],
    )
    prompt = ctx.to_prompt_context()
    assert "test-api" in prompt
    assert "Route / Controller Files" in prompt
    assert "router.get" in prompt


# ── CLI integration tests ────────────────────────────────────────────


def test_openapi_no_api_key(tmp_path: Path):
    """Should fail when ANTHROPIC_API_KEY is not set."""
    with patch.dict("os.environ", {}, clear=True):
        # Remove the key if present
        import os
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        with patch.dict("os.environ", env, clear=True):
            result = runner.invoke(app, ["openapi", "--path", str(tmp_path)])
            assert result.exit_code == 1
            assert "ANTHROPIC_API_KEY" in result.output


@patch("specsmith.ai.openapi.create_client")
def test_openapi_creates_directory(mock_client, tmp_path: Path):
    """Should create .openapi/ directory and write files."""
    (tmp_path / ".git").mkdir()

    # Mock the API calls
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=MOCK_OPENAPI_YAML)]
    mock_client.return_value.messages.create.return_value = mock_msg

    # Second call returns endpoint docs
    mock_msg2 = MagicMock()
    mock_msg2.content = [MagicMock(text=MOCK_ENDPOINT_DOCS_OUTPUT)]

    mock_client.return_value.messages.create.side_effect = [mock_msg, mock_msg2]

    result = runner.invoke(app, [
        "openapi",
        "--path", str(tmp_path),
        "--api-key", "test-key",
    ])
    assert result.exit_code == 0
    assert (tmp_path / ".openapi").is_dir()
    assert (tmp_path / ".openapi" / "openapi.yaml").exists()
    assert (tmp_path / ".openapi" / "endpoints").is_dir()


@patch("specsmith.ai.openapi.create_client")
def test_openapi_overwrites_existing(mock_client, tmp_path: Path):
    """Should overwrite existing openapi.yaml."""
    (tmp_path / ".git").mkdir()
    openapi_dir = tmp_path / ".openapi"
    openapi_dir.mkdir()
    (openapi_dir / "openapi.yaml").write_text("old content")

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=MOCK_OPENAPI_YAML)]
    mock_msg2 = MagicMock()
    mock_msg2.content = [MagicMock(text="")]
    mock_client.return_value.messages.create.side_effect = [mock_msg, mock_msg2]

    result = runner.invoke(app, [
        "openapi",
        "--path", str(tmp_path),
        "--api-key", "test-key",
    ])
    assert result.exit_code == 0
    assert "Updated" in result.output
    content = (openapi_dir / "openapi.yaml").read_text()
    assert "openapi: 3.1.1" in content


@patch("specsmith.ai.openapi.create_client")
def test_openapi_dry_run(mock_client, tmp_path: Path):
    """Should print to stdout and not create files."""
    (tmp_path / ".git").mkdir()

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=MOCK_OPENAPI_YAML)]
    mock_msg2 = MagicMock()
    mock_msg2.content = [MagicMock(text=MOCK_ENDPOINT_DOCS_OUTPUT)]
    mock_client.return_value.messages.create.side_effect = [mock_msg, mock_msg2]

    result = runner.invoke(app, [
        "openapi",
        "--dry-run",
        "--path", str(tmp_path),
        "--api-key", "test-key",
    ])
    assert result.exit_code == 0
    assert "openapi: 3.1.1" in result.output
    assert not (tmp_path / ".openapi").exists()


@patch("specsmith.ai.openapi.create_client")
def test_openapi_generates_endpoint_docs(mock_client, tmp_path: Path):
    """Should create endpoint markdown files in endpoints/ directory."""
    (tmp_path / ".git").mkdir()

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=MOCK_OPENAPI_YAML)]
    mock_msg2 = MagicMock()
    mock_msg2.content = [MagicMock(text=MOCK_ENDPOINT_DOCS_OUTPUT)]
    mock_client.return_value.messages.create.side_effect = [mock_msg, mock_msg2]

    result = runner.invoke(app, [
        "openapi",
        "--path", str(tmp_path),
        "--api-key", "test-key",
    ])
    assert result.exit_code == 0
    endpoints_dir = tmp_path / ".openapi" / "endpoints"
    assert endpoints_dir.is_dir()
    assert (endpoints_dir / "get-api-users.md").exists()
    content = (endpoints_dir / "get-api-users.md").read_text()
    assert "# GET /api/users" in content


@patch("specsmith.ai.openapi.create_client")
def test_openapi_passes_existing_spec(mock_client, tmp_path: Path):
    """When updating, existing spec should be passed to the AI."""
    (tmp_path / ".git").mkdir()
    openapi_dir = tmp_path / ".openapi"
    openapi_dir.mkdir()
    existing = "openapi: 3.1.1\ninfo:\n  title: Old API\n  version: 0.0.1"
    (openapi_dir / "openapi.yaml").write_text(existing)

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=MOCK_OPENAPI_YAML)]
    mock_msg2 = MagicMock()
    mock_msg2.content = [MagicMock(text="")]
    mock_client.return_value.messages.create.side_effect = [mock_msg, mock_msg2]

    runner.invoke(app, [
        "openapi",
        "--path", str(tmp_path),
        "--api-key", "test-key",
    ])

    # Check that the first API call included the existing spec
    first_call = mock_client.return_value.messages.create.call_args_list[0]
    user_msg = first_call.kwargs["messages"][0]["content"]
    assert "Old API" in user_msg
