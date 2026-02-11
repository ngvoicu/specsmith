---
description: Scan the project codebase and generate or update .openapi/openapi.yaml + per-endpoint documentation in .openapi/endpoints/
disable-model-invocation: true
---

# Generate OpenAPI Spec + Endpoint Docs

You are about to scan this project's codebase and generate a comprehensive
OpenAPI 3.1.1 specification plus per-endpoint documentation. Output goes to:

```
.openapi/
├── openapi.yaml              # OpenAPI 3.1.1 spec
└── endpoints/
    ├── get-api-users.md       # One file per endpoint
    ├── post-api-users.md
    └── ...
```

## Phase 1: Detect Framework and Tech Stack

Read the project's package manifests to identify the web framework:
- `package.json` (Express, Fastify, NestJS, Koa, Hono, Next.js)
- `pyproject.toml` / `requirements.txt` (FastAPI, Django, Flask)
- `pom.xml` / `build.gradle` (Spring Boot)
- `go.mod` (Gin, Echo, Fiber)
- `Gemfile` (Rails)
- `Cargo.toml` (Axum, Actix)

Also detect:
- Server port (from config files, env defaults, or main entry point)
- Base URL path prefix (e.g., `/api/v1`)
- Authentication approach (JWT, OAuth, API keys, session)

## Phase 2: Scan for API Endpoints

Use Glob and Grep to find all route/controller/handler files. Read each one
thoroughly. For every endpoint, capture:

- HTTP method (GET, POST, PUT, PATCH, DELETE)
- Route path (with path parameters)
- Query parameters (with types and defaults)
- Request body schema (field names, types, validation rules)
- Response schema (field names, types)
- Authentication requirements
- Which module/tag group it belongs to

Common patterns to search for:
- **Spring**: `@GetMapping`, `@PostMapping`, `@RequestMapping`, `@RestController`
- **NestJS**: `@Get()`, `@Post()`, `@Controller()`
- **Express/Fastify**: `app.get()`, `router.post()`, `server.route()`
- **FastAPI**: `@router.get()`, `@app.post()`
- **Django**: `path()`, `urlpatterns`
- **Go**: `.GET()`, `.POST()`, `HandleFunc()`

Read 10-30 files. Do not just list file names — read the actual implementation
to understand request/response shapes.

## Phase 3: Scan for Schemas and DTOs

Find all data transfer objects, models, entities, and validation schemas:

- TypeScript/JS: `*.dto.ts`, `*.schema.ts`, `*.model.ts`, Zod schemas, class-validator
- Python: Pydantic models, dataclasses, serializers
- Java/Kotlin: entity classes, DTOs, record types
- Go: struct definitions in handler/model packages
- Ruby: ActiveRecord models, serializers

For each schema, capture:
- Field names and types
- Required vs optional fields
- Validation rules (min, max, pattern, enum values)
- Nested object relationships
- Inheritance/composition

## Phase 4: Scan for Security Configuration

Look for:
- JWT/token verification middleware
- OAuth2 configuration
- API key validation
- Role-based access control decorators/annotations
- CORS configuration
- Security filters/interceptors

## Phase 5: Check for Existing Files

If `.openapi/openapi.yaml` already exists:
1. Read it completely
2. Note any manually written descriptions, examples, or documentation
3. Plan to preserve manual additions while updating from code

If `.openapi/endpoints/*.md` files exist:
1. Read each one
2. Note manually written content
3. Plan to preserve manual additions while updating

## Phase 6: Generate the OpenAPI 3.1.1 Spec

Write a complete OpenAPI 3.1.1 YAML file to `.openapi/openapi.yaml`.

Structure:
```yaml
openapi: 3.1.1
info:
  title: <Project Name> API
  description: <inferred from code/readme>
  version: <from package manifest>
servers:
  - url: http://localhost:<port>
    description: Local development server
tags:
  - name: <Module>
    description: <what this group does>
paths:
  /path/{param}:
    get:
      summary: <Short description>
      description: |
        <Detailed description>

        **UISpec:** See [endpoints/<method>-<path-slug>.md](./endpoints/<method>-<path-slug>.md)
      operationId: <camelCase>
      tags: [<Module>]
      security:
        - bearerAuth: []
      parameters: [...]
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SchemaName'
components:
  schemas:
    SchemaName:
      type: object
      properties: ...
      required: [...]
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

Quality standards:
- Every endpoint in the codebase must appear in the spec
- Every request/response type must be a named schema under `components/schemas`
- Use `$ref` everywhere instead of inline schemas
- Include `operationId` for every operation
- Group endpoints with tags matching the module/controller structure
- Mark required fields accurately based on validation decorators
- Include format hints (date-time, email, int64, etc.)
- Each endpoint description must link to its endpoint doc

## Phase 7: Generate Endpoint Documentation

For each endpoint, create a markdown file at `.openapi/endpoints/<method>-<path-slug>.md`.

Filename convention: `{method}-{path-slug}.md` where:
- method is lowercase (get, post, put, delete, patch)
- path-slug is the URL path with slashes replaced by hyphens, braces removed
- Example: `GET /api/pulse/forms/{formId}` → `get-api-pulse-forms-formid.md`

Each endpoint doc follows this template:

```markdown
# METHOD /path/to/endpoint

> operationId — short description

## UI Behavior

### What to Display
- Map response fields to UI components
- Describe the layout and data presentation
- Note conditional rendering

### User Flows
- What triggers the API call
- What happens after success/failure
- Navigation and state changes

### State Transitions
- Loading → Success / Error states
- Empty states (no data)
- How the UI changes between states

### Loading & Error States
- Skeleton/placeholder UI during loading
- Error messages for each error code
- Retry behavior

## API Usage

### Request
- Method, URL, authentication
- Parameters table (name, type, required, description, example)

### Response
#### Success (200/201)
- Full JSON example with realistic data
- Field descriptions

#### Error Responses
- Each error code with description and example

### Business Rules
- Validation rules and preconditions
- Side effects
- Ordering/timing constraints

### Edge Cases
- Concurrent requests
- Empty/null data
- Boundary values
```

## Phase 8: Write and Report

1. Create `.openapi/` directory if it doesn't exist
2. Create `.openapi/endpoints/` directory if it doesn't exist
3. Write `openapi.yaml`
4. Write each endpoint doc to `endpoints/<name>.md`
5. Report what was generated:
   - Number of endpoints documented
   - Number of schemas defined
   - Security schemes found
   - Number of endpoint doc files created
   - Any endpoints that need manual review
