# Julep Mintlify Documentation

## Development

Install the [Mintlify CLI](https://www.npmjs.com/package/mintlify) to preview the documentation changes locally. To install, use the following command:

```bash
npm i -g mintlify
```

Run the following command at the root of your documentation (where mint.json is):

```bash
mintlify dev
```

### Troubleshooting

- Mintlify dev isn't running - Run `mintlify install` it'll re-install dependencies.
- Page loads as a 404 - Make sure you are running in a folder with `mint.json`

## Responses API

This section provides an overview and guide for the new `responses-api` implementation.

### Overview

The Responses API allows clients to create model responses with text, image, and other inputs, and receive structured outputs. It supports streaming responses, function calling, and other advanced features.

### Getting Started

#### Prerequisites

- Python 3.12
- [uv](https://github.com/astral-sh/uv) for package management

#### Installation

1. Clone the repository.
2. Install dependencies:

```bash
uv venv
uv pip install -e .
```

#### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
RESPONSES_API_DEBUG=false
RESPONSES_API_ENV=development
RESPONSES_API_LOG_LEVEL=INFO
RESPONSES_API_HOST=0.0.0.0
RESPONSES_API_PORT=8080
RESPONSES_API_DATABASE_URL=
OPENAI_API_KEY=your_openai_api_key
RESPONSES_API_DEFAULT_MODEL=gpt-4o
RESPONSES_API_KEY=your_api_key
SENTRY_DSN=
RESPONSES_API_ENABLE_METRICS=false
RESPONSES_API_CORS_ORIGINS=*
```

#### Running the API

```bash
uvicorn responses_api.web:app --reload
```

Or with gunicorn:

```bash
gunicorn responses_api.web:app -c gunicorn_conf.py
```

#### Docker

Build the Docker image:

```bash
docker build -t responses-api .
```

Run the Docker container:

```bash
docker run -p 8080:8080 responses-api
```

### API Documentation

Once the API is running, you can access the API documentation at:

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### Development

#### Code Generation

To generate code from the OpenAPI spec:

```bash
poe codegen
```

#### Linting and Formatting

```bash
poe lint
poe format
```

#### Type Checking

```bash
poe typecheck
```

#### Running Tests

```bash
poe test
```

### License

This project is licensed under the Apache 2.0 License.

## Build/Lint/Test Commands

- Python lint: `poe lint` or `ruff check`
- Python format: `poe format` or `ruff format`
- Python typecheck: `poe typecheck` or `pytype --config pytype.toml`
- Python test: `poe test` or use `pytest tests/test_file.py::test_function`
- SQL validation: `poe validate-sql`
- Full check: `poe check` (lint + format + validate-sql + typecheck)
- Node build: `yarn build` or `./scripts/build`
- Node test: `yarn test` or `./scripts/test`
- Node lint: `yarn lint` or `./scripts/lint`
- Node format: `yarn format` or `./scripts/format`

## Code Style Guidelines

- Python: Use snake_case for variables/functions, PascalCase for classes
- Python: Strict typing with annotations; use pydantic for data validation
- Python: Max line length 96 characters, 4 spaces indentation
- TypeScript: camelCase for variables/functions, PascalCase for classes
- Import order: standard library, third-party, local packages
- Define custom exceptions in dedicated exceptions.py modules
- Use async/await patterns consistently where applicable
- Follow microservice architecture patterns within Docker Compose
- Add docstrings to functions/classes for better documentation