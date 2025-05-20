<div align="center" id="top">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Rapidly%20build%20AI%20workflows%20and%20agents&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&forks=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="320" height="160" />

  <p>
    <a href="https://dashboard.julep.ai">
      <img src="https://img.shields.io/badge/Get_API_Key-FF5733?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAxTDMgNXYxNGw5IDQgOS00VjVsLTktNHptMCAyLjh2MTYuNEw1IDE2LjJWNi44bDctMy4yem0yIDguMmwtMi0yLTIgMiAyIDIgMi0yeiIvPjwvc3ZnPg==" alt="Get API Key">
    </a>
    <a href="https://docs.julep.ai">
      <img src="https://img.shields.io/badge/Documentation-4B32C3?style=for-the-badge&logo=gitbook&logoColor=white" alt="Documentation">
    </a>
  </p>
  <p>
    <a href="https://hub.docker.com/u/julepai">
      <img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&style=for-the-badge&color=2496ED&logo=docker&logoColor=white" alt="Docker Version">
    </a>
    <a href="https://www.npmjs.com/package/@julep/sdk">
      <img src="https://img.shields.io/npm/v/@julep/sdk?style=for-the-badge&color=CB3837&logo=npm&logoColor=white" alt="NPM Version">
    </a>
    <a href="https://www.npmjs.com/package/@julep/sdk">
      <img src="https://img.shields.io/npm/dm/@julep/sdk?style=for-the-badge&color=CB3837&logo=npm&logoColor=white" alt="NPM Downloads">
    </a>
    <a href="https://pypi.org/project/julep/">
      <img src="https://img.shields.io/pypi/v/julep?style=for-the-badge&color=3776AB&logo=python&logoColor=white" alt="PyPI Version">
    </a>
    <a href="https://pypi.org/project/julep/">
      <img src="https://img.shields.io/pypi/dm/julep?style=for-the-badge&color=3776AB&logo=python&logoColor=white" alt="PyPI Downloads">
    </a>
  </p>
  
  <h3>
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
  </h3>
</div>

# Contributing to Julep

👋 Welcome! We're excited that you're interested in contributing to Julep. This guide will help you get started.

---

## 🚀 Quick Start

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes and test them
4. Submit a pull request

---

## 📝 Ways to Contribute

### 🐛 Reporting Issues

Found a bug? Have a feature request? [Submit an issue](https://github.com/julep-ai/julep/issues) with:

- [ ] Steps to reproduce
- [ ] Expected behavior
- [ ] Actual behavior
- [ ] Screenshots (if applicable)

### 💻 Contributing Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write/update tests
5. Push to your fork
6. Open a pull request

> 💡 **Tip:** Make sure your code follows our style guide and passes all tests.

---

## 🏗 Project Architecture

### Core Services

| Service | Description |
|---------|-------------|
| `agents-api` | Core API service |
| `memory-store` | PostgreSQL database with TimescaleDB for persistent storage |
| `blob-store` | Object storage for files and binary data |
| `integrations-service` | Adapters for external services and tools |
| `scheduler` | Temporal workflow engine for task scheduling and orchestration |
| `gateway` | API gateway for routing and request handling |
| `llm-proxy` | LiteLLM proxy for language model interactions |
| `monitoring` | Prometheus and Grafana monitoring infrastructure |
| `typespec` | API specifications in TypeSpec format |
| `sdks` | Node.js and Python client SDKs |
| `cli` | Command-line interface for Julep |

### Supporting Modules

- `deploy`: Deployment configs
- `documentation`: Project documentation assets
- `scripts`: Utility scripts and tools
- `cookbooks`: Usage examples and recipes

### Tech Stack

- **FastAPI**: Web framework for building APIs
- **TypeSpec**: API specification language
- **Timescale**: Database system
- **SeaweedFS**: Blob storage system
- **Grafana**: Monitoring and observability platform
- **Prometheus**: Monitoring and observability platform
- **LiteLLM**: LLM framework
- **Temporal**: Workflow engine
- **Docker**: Containerization

> To understand the relationships between the components, please refer to the [System Architecture](https://docs.julep.ai/docs/advanced/architecture-deep-dive) section.

## Understanding the Codebase

To get a comprehensive understanding of Julep, we recommend exploring the codebase in the following order:

1. **Project Overview**
   - Read `README.md` in the root directory
   - Explore `docs/` for detailed documentation

2. **System Architecture**
   - Examine `docker-compose.yml` in the root directory
   - Review `deploy/` directory for different deployment configurations

3. **API Specifications**
   - Learn about TypeSpec: https://typespec.io/docs/
   - Explore `typespec/` directory:
     - Start with `common/` folder
     - Review `main.tsp`
     - Examine each module sequentially

4. **Core API Implementation**
   - Learn about FastAPI: https://fastapi.tiangolo.com/
   - Explore `agents-api/` directory:
     - Review `README.md` for an overview
     - Examine `routers/` for API endpoints
     - Look into `models/` for data models

5. **Database and Storage**
   - Learn about Cozo: https://docs.cozodb.org/en/latest/tutorial.html
   - Review `agents-api/README.md` for database schema
   - Explore `agents-api/models/` for database queries

6. **Workflow Management**
   - Learn about Temporal: https://docs.temporal.io/develop/python
   - Explore `agents-api/activities/` for individual workflow steps
   - Review `agents-api/workflows/task_execution/` for main workflow logic

7. **Testing**
   - Examine `agents-api/tests/` for test cases

8. **Additional Services**
   - Explore other service directories (`integrations-service/`, `embedding-service/`, etc.) to understand their specific roles and implementations

## Contributing Guidelines

1. **Set Up Development Environment**
   - Clone the repository
   - Install pre-commit and enable hooks: `pip install pre-commit && pre-commit install`
   - Install Docker and Docker Compose
   - Set up necessary API keys and environment variables

   > You can check our [Local Setup](https://docs.julep.ai/docs/advanced/localsetup) section in the docs for more information.

2. **Choose an Area to Contribute**
   - Check the issue tracker for open issues
   - Look for "good first issue" labels for newcomers

3. **Make Changes**
   - Create a new branch for your changes
   - Write clean, well-documented code
   - Ensure your changes adhere to the project's coding standards

4. **Test Your Changes**
   - Run existing tests
   - Add new tests for new functionality
   - Ensure all tests pass before submitting your changes

5. **Submit a Pull Request**
   - Provide a clear description of your changes
   - Reference any related issues
   - Be prepared to respond to feedback and make adjustments

6. **Code Review**
   - Address any comments or suggestions from reviewers
   - Make necessary changes and push updates to your branch

7. **Merge**
   - Once approved, your changes will be merged into the main branch

### Adding a New Integration

The integration service is a crucial part of Julep, and we welcome contributions from the community to enhance its functionality and capabilities.

To contribute to the integration service, you can follow these steps:

1. **Add a new integration provider to our TypeSpec:** You can do so by:
   1. Adding the provider name to the `integrationProvider` alias in `typespec/tools/models.tsp`
   2. Adding a new file in `typespec/tools/` with the provider name. Take a look at the other integration files in the `typespec/tools/` directory for examples.

      > If the integration needs an API key or other form of authentication, you would have to add a `Setup` model to the integration definition file, where you would define the authentication parameters (`spider.tsp` is an example of this). Otherwise, you can omit the `Setup` model (`wikipedia.tsp` is an example of this).

2. **Generate the new OpenAPI schema and Pydantic models:** You need to `cd` into the root directory of the project and run `./scripts/generate_openapi_code.sh` to generate the new OpenAPI schema along with Pydantic models for the new changes.

   > The new OpenAPI schema will be generated in `./openapi.yaml` and the Pydantic models will be generated in `./integrations-service/integrations/autogen`. 

3. **Add the new integration logic in the integration service:** You need to add the new integration logic in the integration service by adding a new file in `integration-service/integrations/utils/integrations` with the provider name. Take a look at the other integration files in the same directory for examples.

4. **Add the new integration provider to the providers registry:** You need to add the new integration provider to the providers registry by adding a new entry to the `available_providers` dictionary in `integrations-service/integrations/providers.py`.

### Documentation Improvements

Improvements to documentation are always appreciated! If you see areas that could be clarified or expanded, feel free to make the changes and submit a pull request.

### Sharing Feedback and Ideas

We'd love to hear your feedback and ideas for the project! Feel free to submit an issue or contact the maintainers directly to share your thoughts. Your input is very valuable in shaping the future direction of the project.

Remember, contributions aren't limited to code. Documentation improvements, bug reports, and feature suggestions are also valuable contributions to the project.
