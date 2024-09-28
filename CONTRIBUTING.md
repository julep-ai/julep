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

## Building Docker Images with Buildx Bake

We use Docker Buildx Bake to build our Docker images. This allows us to build multiple images concurrently and efficiently. Follow these steps to build the Docker images:

1. Ensure you have Docker and Docker Buildx installed on your system.

2. Navigate to the root directory of the project where the `docker-bake.hcl` file is located.

3. To build all services, run:
   ```
   docker buildx bake --file docker-bake.hcl
   ```

4. To build a specific service, use:
   ```
   docker buildx bake --file docker-bake.hcl <service-name>
   ```
   Replace `<service-name>` with one of the following:
   - agents-api
   - agents-api-worker
   - cozo-migrate
   - memory-store
   - integrations
   - gateway
   - embedding-service-cpu
   - embedding-service-gpu

5. To set a custom tag for the images, use:
   ```
   docker buildx bake --file docker-bake.hcl --set *.tags=myorg/myimage:v1.0
   ```
   Replace `myorg/myimage:v1.0` with your desired image name and tag.

6. By default, the images are built with the "latest" tag. To specify a different tag, you can set the TAG variable:
   ```
   docker buildx bake --file docker-bake.hcl --set TAG=v1.2.3
   ```

Note: The `docker-bake.hcl` file defines the build contexts, Dockerfiles, and tags for each service. If you need to modify the build process for a specific service, update the corresponding target in the `docker-bake.hcl` file.

Thank you for your interest in contributing to this project!