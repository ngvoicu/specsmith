"""OpenAPI spec generation — context gathering, API calls, endpoint doc generation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from specsmith.ai.client import create_client
from specsmith.ai.openapi_prompts import ENDPOINT_DOC_SYSTEM_PROMPT, OPENAPI_SYSTEM_PROMPT


# ── Data ─────────────────────────────────────────────────────────────


@dataclass
class ApiContext:
    """Structured API context gathered from codebase scan."""

    project_name: str = ""
    project_structure: str = ""
    package_info: str = ""
    route_files: list[tuple[str, str]] = field(default_factory=list)
    schema_files: list[tuple[str, str]] = field(default_factory=list)
    middleware_files: list[tuple[str, str]] = field(default_factory=list)
    config_files: list[tuple[str, str]] = field(default_factory=list)
    extra_files: list[tuple[str, str]] = field(default_factory=list)
    endpoint_count: int = 0
    schema_count: int = 0
    has_api_code: bool = False

    def to_prompt_context(self) -> str:
        parts: list[str] = []
        parts.append(f"# Project: {self.project_name}\n")

        if self.project_structure:
            parts.append(f"## Project Structure\n{self.project_structure}\n")

        if self.package_info:
            parts.append(f"## Package Manifests\n{self.package_info}\n")

        for label, files in [
            ("Route / Controller Files", self.route_files),
            ("Schema / DTO Files", self.schema_files),
            ("Middleware / Security Files", self.middleware_files),
            ("Configuration Files", self.config_files),
            ("Additional Files", self.extra_files),
        ]:
            if files:
                parts.append(f"## {label}\n")
                for fpath, content in files:
                    parts.append(f"### {fpath}\n```\n{content}\n```\n")

        return "\n".join(parts)


# ── Framework detection ──────────────────────────────────────────────

_SKIP_DIRS = {
    "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
    "target", ".gradle", ".idea", ".git", ".specs", ".openapi",
}

_FRAMEWORK_MARKERS: dict[str, list[tuple[str, str]]] = {
    # file, substring → framework
    "package.json": [
        ("@nestjs/core", "nestjs"),
        ("express", "express"),
        ("fastify", "fastify"),
        ("koa", "koa"),
        ("hono", "hono"),
        ("next", "nextjs"),
    ],
    "pyproject.toml": [
        ("fastapi", "fastapi"),
        ("django", "django"),
        ("flask", "flask"),
    ],
    "requirements.txt": [
        ("fastapi", "fastapi"),
        ("django", "django"),
        ("flask", "flask"),
    ],
    "pom.xml": [
        ("spring-boot", "spring"),
    ],
    "build.gradle": [
        ("spring-boot", "spring"),
    ],
    "build.gradle.kts": [
        ("spring-boot", "spring"),
    ],
    "go.mod": [
        ("gin-gonic/gin", "gin"),
        ("labstack/echo", "echo"),
        ("gofiber/fiber", "fiber"),
    ],
    "Gemfile": [
        ("rails", "rails"),
    ],
    "Cargo.toml": [
        ("axum", "axum"),
        ("actix-web", "actix"),
    ],
}

# Framework-specific glob patterns for routes/controllers
_ROUTE_PATTERNS: dict[str, list[str]] = {
    "spring": ["**/*Controller.java", "**/*Controller.kt", "**/*Resource.java", "**/*Resource.kt"],
    "nestjs": ["**/*.controller.ts", "**/*.controller.js"],
    "express": ["**/routes/**/*.ts", "**/routes/**/*.js", "**/*.router.ts", "**/*.router.js"],
    "fastify": ["**/routes/**/*.ts", "**/routes/**/*.js", "**/*.route.ts", "**/*.route.js"],
    "koa": ["**/routes/**/*.ts", "**/routes/**/*.js", "**/*.router.ts"],
    "hono": ["**/routes/**/*.ts", "**/*.route.ts"],
    "nextjs": ["**/app/**/route.ts", "**/app/**/route.js", "**/pages/api/**/*.ts", "**/pages/api/**/*.js"],
    "fastapi": ["**/routers/**/*.py", "**/routes/**/*.py", "**/api/**/*.py", "**/endpoints/**/*.py"],
    "django": ["**/views.py", "**/urls.py", "**/api/**/*.py", "**/views/**/*.py"],
    "flask": ["**/routes.py", "**/views.py", "**/api/**/*.py"],
    "gin": ["**/handler*.go", "**/routes*.go", "**/api/**/*.go"],
    "echo": ["**/handler*.go", "**/routes*.go", "**/api/**/*.go"],
    "fiber": ["**/handler*.go", "**/routes*.go", "**/api/**/*.go"],
    "rails": ["**/controllers/**/*.rb", "**/routes.rb"],
    "axum": ["**/handlers/**/*.rs", "**/routes.rs", "**/api/**/*.rs"],
    "actix": ["**/handlers/**/*.rs", "**/routes.rs", "**/api/**/*.rs"],
}

_GENERIC_ROUTE_PATTERNS = [
    "**/*controller*.*",
    "**/*Controller*.*",
    "**/routes/**",
    "**/*router*.*",
    "**/*handler*.*",
    "**/api/**",
]

_SCHEMA_PATTERNS: dict[str, list[str]] = {
    "spring": ["**/dto/**/*.java", "**/dto/**/*.kt", "**/entity/**/*.java", "**/entity/**/*.kt",
               "**/model/**/*.java", "**/model/**/*.kt"],
    "nestjs": ["**/*.dto.ts", "**/*.entity.ts", "**/*.schema.ts", "**/models/**/*.ts"],
    "express": ["**/*.dto.ts", "**/*.model.ts", "**/models/**/*.ts", "**/schemas/**/*.ts"],
    "fastapi": ["**/models/**/*.py", "**/schemas/**/*.py", "**/dto/**/*.py"],
    "django": ["**/models.py", "**/serializers.py", "**/models/**/*.py"],
    "flask": ["**/models.py", "**/schemas.py", "**/models/**/*.py"],
    "gin": ["**/models/**/*.go", "**/dto/**/*.go", "**/types/**/*.go"],
    "rails": ["**/models/**/*.rb", "**/serializers/**/*.rb"],
}

_GENERIC_SCHEMA_PATTERNS = [
    "**/*.dto.*",
    "**/*.entity.*",
    "**/*.schema.*",
    "**/models/**",
    "**/schemas/**",
    "**/entities/**",
    "**/dto/**",
]

_MIDDLEWARE_PATTERNS = [
    "**/*auth*.*",
    "**/*middleware*.*",
    "**/*security*.*",
    "**/*guard*.*",
    "**/*interceptor*.*",
    "**/middleware/**",
]

_CONFIG_PATTERNS = [
    "**/application.yml",
    "**/application.yaml",
    "**/application.properties",
    "**/application-*.yml",
    ".env.example",
    ".env.sample",
    "**/config/server*.*",
    "**/config/app*.*",
]

# Regex patterns for counting endpoints
_ENDPOINT_PATTERNS = [
    # Spring
    r"@(Get|Post|Put|Patch|Delete)Mapping",
    r"@RequestMapping",
    # NestJS / Express decorators
    r"@(Get|Post|Put|Patch|Delete|Head|Options)\(",
    # Express / Koa / Fastify method calls
    r"\.(get|post|put|patch|delete|head|options)\s*\(",
    # FastAPI / Flask
    r"@(app|router|blueprint)\.(get|post|put|patch|delete)\(",
    # Django urls
    r"path\s*\(",
    # Go handler registration
    r"\.(GET|POST|PUT|PATCH|DELETE|Handle|HandleFunc)\(",
]


# ── Helpers ──────────────────────────────────────────────────────────


def _build_tree(project_root: Path) -> str:
    """Build directory tree (top 3 levels)."""
    lines: list[str] = []
    for root, dirs, files in os.walk(project_root):
        depth = str(root).replace(str(project_root), "").count(os.sep)
        if depth >= 3:
            dirs.clear()
            continue
        dirs[:] = [d for d in sorted(dirs) if not d.startswith(".") and d not in _SKIP_DIRS]
        indent = "  " * depth
        lines.append(f"{indent}{os.path.basename(root)}/")
        for f in sorted(files)[:20]:
            lines.append(f"{indent}  {f}")
    return "\n".join(lines)


def _read_manifests(project_root: Path) -> str:
    """Read package manifests."""
    parts: list[str] = []
    for name in ("package.json", "pyproject.toml", "Cargo.toml", "go.mod",
                 "Gemfile", "pom.xml", "build.gradle", "build.gradle.kts"):
        fp = project_root / name
        if fp.exists():
            parts.append(f"### {name}\n```\n{fp.read_text()[:3000]}\n```")
    return "\n".join(parts)


def _detect_framework(project_root: Path) -> str:
    """Detect the primary web framework from package manifests."""
    for manifest, markers in _FRAMEWORK_MARKERS.items():
        fp = project_root / manifest
        if fp.exists():
            try:
                content = fp.read_text().lower()
            except OSError:
                continue
            for substring, framework in markers:
                if substring in content:
                    return framework
    return "unknown"


def _glob_files(project_root: Path, patterns: list[str], max_files: int = 30) -> list[Path]:
    """Glob for files matching any of the patterns, deduplicated."""
    seen: set[Path] = set()
    results: list[Path] = []
    for pattern in patterns:
        for p in sorted(project_root.glob(pattern)):
            if p.is_file() and p not in seen:
                # Skip files in ignored directories
                parts = p.relative_to(project_root).parts
                if any(part in _SKIP_DIRS for part in parts):
                    continue
                seen.add(p)
                results.append(p)
                if len(results) >= max_files:
                    return results
    return results


def _read_files(project_root: Path, paths: list[Path], per_file_cap: int = 4000) -> list[tuple[str, str]]:
    """Read files, returning (relative_path, content) tuples."""
    result: list[tuple[str, str]] = []
    for p in paths:
        try:
            content = p.read_text()[:per_file_cap]
            rel = str(p.relative_to(project_root))
            result.append((rel, content))
        except OSError:
            continue
    return result


def _count_endpoints(route_files: list[tuple[str, str]]) -> int:
    """Count approximate endpoint definitions from route file contents."""
    count = 0
    combined = re.compile("|".join(_ENDPOINT_PATTERNS))
    for _, content in route_files:
        count += len(combined.findall(content))
    return count


def _count_schemas(schema_files: list[tuple[str, str]]) -> int:
    """Count approximate schema/class definitions."""
    count = 0
    pattern = re.compile(
        r"(?:^|\n)\s*(?:export\s+)?(?:class|interface|type|struct|data\s+class|record|@dataclass|class\s+\w+\(BaseModel\))\s+\w+"
    )
    for _, content in schema_files:
        count += len(pattern.findall(content))
    return count


# ── Public API ───────────────────────────────────────────────────────


def gather_api_context(project_root: Path, include_paths: list[str]) -> ApiContext:
    """Scan the project and gather API-related context."""
    ctx = ApiContext(project_name=project_root.name)

    # 1. Project structure
    ctx.project_structure = _build_tree(project_root)

    # 2. Package manifests
    ctx.package_info = _read_manifests(project_root)

    # 3. Detect framework
    framework = _detect_framework(project_root)

    # 4. Route / controller files
    patterns = _ROUTE_PATTERNS.get(framework, []) + _GENERIC_ROUTE_PATTERNS
    route_paths = _glob_files(project_root, patterns)
    ctx.route_files = _read_files(project_root, route_paths)

    # 5. Schema / DTO files
    patterns = _SCHEMA_PATTERNS.get(framework, []) + _GENERIC_SCHEMA_PATTERNS
    schema_paths = _glob_files(project_root, patterns)
    ctx.schema_files = _read_files(project_root, schema_paths)

    # 6. Middleware / security
    middleware_paths = _glob_files(project_root, _MIDDLEWARE_PATTERNS, max_files=15)
    ctx.middleware_files = _read_files(project_root, middleware_paths)

    # 7. Config
    config_paths = _glob_files(project_root, _CONFIG_PATTERNS, max_files=10)
    ctx.config_files = _read_files(project_root, config_paths)

    # 8. User-specified include files
    for p in include_paths:
        fp = project_root / p
        if fp.exists() and fp.is_file():
            try:
                content = fp.read_text()[:4000]
                ctx.extra_files.append((p, content))
            except OSError:
                continue

    # 9. Stats
    ctx.endpoint_count = _count_endpoints(ctx.route_files)
    ctx.schema_count = _count_schemas(ctx.schema_files)
    ctx.has_api_code = ctx.endpoint_count > 0 or len(ctx.route_files) > 0

    return ctx


def _strip_yaml_fences(text: str) -> str:
    """Strip markdown YAML fences from LLM output."""
    text = text.strip()
    if text.startswith("```yaml"):
        text = text[len("```yaml"):].strip()
    elif text.startswith("```yml"):
        text = text[len("```yml"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def generate_openapi(
    api_key: str,
    model: str,
    context: ApiContext,
    existing_spec: str | None = None,
) -> str:
    """Call the Claude API to generate an OpenAPI 3.1.1 spec."""
    client = create_client(api_key)

    prompt_parts = [
        f"Generate an OpenAPI 3.1.1 specification for the project: {context.project_name}\n",
        context.to_prompt_context(),
    ]

    if existing_spec:
        prompt_parts.append(
            "\n## Existing OpenAPI Spec (update this)\n"
            "Below is the current openapi.yaml. Preserve any manually added "
            "descriptions, examples, and documentation. Update endpoints and "
            "schemas based on the current codebase.\n\n"
            f"```yaml\n{existing_spec[:15000]}\n```"
        )

    message = client.messages.create(
        model=model,
        max_tokens=16384,
        system=OPENAPI_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "\n".join(prompt_parts)}],
    )

    text = message.content[0].text
    return _strip_yaml_fences(text)


def _endpoint_slug(method: str, path: str) -> str:
    """Convert method + path to a filename slug.

    E.g. GET /api/pulse/forms/{formId} → get-api-pulse-forms-formid
    """
    slug = path.strip("/").replace("/", "-").replace("{", "").replace("}", "")
    slug = re.sub(r"[^a-zA-Z0-9-]", "", slug).lower()
    return f"{method.lower()}-{slug}"


def generate_endpoint_docs(
    api_key: str,
    model: str,
    context: ApiContext,
    openapi_yaml: str,
    existing_docs: dict[str, str] | None = None,
) -> list[tuple[str, str]]:
    """Generate per-endpoint markdown documentation.

    Returns list of (filename, content) tuples.
    """
    client = create_client(api_key)

    prompt_parts = [
        "Generate comprehensive per-endpoint documentation for these API endpoints.\n\n",
        "## OpenAPI Specification\n```yaml\n",
        openapi_yaml[:20000],
        "\n```\n\n",
        "## Source Code Context\n",
        context.to_prompt_context(),
    ]

    if existing_docs:
        prompt_parts.append("\n## Existing Endpoint Docs (preserve manual additions)\n")
        for fname, content in existing_docs.items():
            prompt_parts.append(f"\n--- EXISTING: {fname} ---\n{content[:3000]}\n")

    message = client.messages.create(
        model=model,
        max_tokens=16384,
        system=ENDPOINT_DOC_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "\n".join(prompt_parts)}],
    )

    return _parse_endpoint_docs(message.content[0].text)


def _parse_endpoint_docs(text: str) -> list[tuple[str, str]]:
    """Parse the LLM output into (filename, content) tuples.

    Expected format:
    --- FILE: get-api-users.md ---
    # GET /api/users
    ...
    --- FILE: post-api-users.md ---
    ...
    """
    results: list[tuple[str, str]] = []
    parts = re.split(r"---\s*FILE:\s*(.+?\.md)\s*---", text)

    # parts[0] is any text before the first marker (skip it)
    # Then alternating: filename, content, filename, content, ...
    i = 1
    while i < len(parts) - 1:
        filename = parts[i].strip()
        content = parts[i + 1].strip()
        if filename and content:
            results.append((filename, content))
        i += 2

    return results


def validate_openapi_yaml(text: str) -> bool:
    """Basic validation — check if the YAML is parseable."""
    try:
        data = yaml.safe_load(text)
        return isinstance(data, dict) and "openapi" in data
    except yaml.YAMLError:
        return False
