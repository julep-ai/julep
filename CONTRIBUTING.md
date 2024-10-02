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