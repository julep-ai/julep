## Contributing

We welcome contributions to this project! There are several ways you can contribute:

### Reporting Issues

If you find a bug or have a feature request, please submit an issue on the [GitHub Issues](https://github.com/julep-ai/julep/issues) page. When reporting a bug, please include:
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots if applicable 

### Submitting Pull Requests

To contribute code changes:

1. Fork the repository 
2. Create a new branch for your changes
3. Make your changes and commit them with descriptive messages
4. Push your changes to your fork
5. Open a pull request to the main repository

Please ensure your code follows the existing style and passes all tests.

## Project Overview and Architecture

### Key Components

1. **agents-api**: The core API service for Julep.
2. **typespec**: API specifications and contracts.
3. **integrations-service**: Handles external integrations.
4. **embedding-service**: Manages text embeddings.
5. **memory-store**: Handles persistent storage.
6. **llm-proxy**: Proxy for language model interactions.
7. **scheduler**: Manages task scheduling.
8. **gateway**: API gateway and routing.
9. **monitoring**: System monitoring and metrics.

### Technology Stack

- **FastAPI**: Web framework for building APIs
- **TypeSpec**: API specification language
- **Cozo**: Database system
- **Temporal**: Workflow engine
- **Docker**: Containerization

### Relationships Between Components

The `agents-api` serves as the central component, interacting with most other services:
- It uses `typespec` definitions for API contracts.
- Communicates with `integrations-service` for external tool interactions.
- Utilizes `embedding-service` for text processing.
- Stores data in `memory-store`.
- Interacts with language models through `llm-proxy`.
- Uses `scheduler` for task management.
- All API requests pass through the `gateway`.
- `monitoring` observes the entire system.

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
   - Install Docker and Docker Compose
   - Set up necessary API keys and environment variables

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

### Documentation Improvements 

Improvements to documentation are always appreciated! If you see areas that could be clarified or expanded, feel free to make the changes and submit a pull request.

### Sharing Feedback and Ideas

We'd love to hear your feedback and ideas for the project! Feel free to submit an issue or contact the maintainers directly to share your thoughts. Your input is very valuable in shaping the future direction of the project.

### Setup Instructions

##### 1. Clone the Repository
Clone the repository from your preferred source:

```bash
git clone <repository_url>
```

##### 2. Navigate to the Root Directory
Change to the root directory of the project:

```bash
cd <repository_root>
```

##### 3. Set Up Environment Variables
- Create a `.env` file in the root directory.
- Refer to the `.env.example` file for a list of required variables.
- Ensure that all necessary variables are set in the `.env` file.

##### 4. Create a Docker Volume for Backup
Create a Docker volume named `cozo_backup`:

```bash
docker volume create cozo_backup
```

##### 5. Run the Project using Docker Compose
You can run the project in two different modes: **Single Tenant** or **Multi-Tenant**. Choose one of the following commands based on your requirement:

###### Single-Tenant Mode
Run the project in single-tenant mode:

```bash
docker compose --env-file .env --profile temporal-ui --profile single-tenant --profile embedding-cpu --profile self-hosted-db up --force-recreate --build --watch
```

> **Note:** In single-tenant mode, you can interact with the SDK directly without the need for the API KEY.

###### Multi-Tenant Mode
Run the project in multi-tenant mode:

```bash
docker compose --env-file .env --profile temporal-ui --profile multi-tenant --profile embedding-cpu --profile self-hosted-db up --force-recreate --build --watch
```

> **Note:** In multi-tenant mode, you need to generate a JWT token locally that act as an API KEY to interact with the SDK.

##### 6. Generate a JWT Token (Only for Multi-Tenant Mode)

To generate a JWT token, `jwt-cli` is required. Kindly install the same before proceeding with the next steps.

Use the following command and replace `JWT_SHARED_KEY` with the corresponding key from your `.env` file to generate a JWT token:

```bash
jwt encode --secret JWT_SHARED_KEY --alg HS512 --exp=$(date -j -v +10d +%s) --sub '00000000-0000-0000-0000-000000000000' '{}'
```

This command generates a JWT token that will be valid for 10 days.

##### 7. Access and Interact
- **Temporal UI**: You can access the Temporal UI through the specified port in your `.env` file.
- **API Interactions**: Depending on the chosen mode, interact with the setup using the provided endpoints.

##### Troubleshooting
- Ensure that all required Docker images are available.
- Check for missing environment variables in the `.env` file.
- Use the `docker compose logs` command to view detailed logs for debugging.


Remember, contributions aren't limited to code. Documentation improvements, bug reports, and feature suggestions are also valuable contributions to the project.
