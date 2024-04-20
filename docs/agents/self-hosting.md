---
description: Learn how to configure and deploy Julep with Docker.
---

# Self-hosting

Julep is available as a hosted service or as a self managed instance.  This guide assumes you are running the commands from the machine you intend to host from.

## Running Julep

Follow these steps to start Julep locally:

{% code overflow="wrap" lineNumbers="true" %}
```bash
# Add the docker compose to your project dir
wget https://raw.githubusercontent.com/julep-ai/julep/dev/deploy/docker-compose.yml

# Add the .env file to your project dir
wget https://raw.githubusercontent.com/julep-ai/julep/dev/deploy/.env.example -O .env

# Pull the latest images
docker compose pull

# Start the services (in detached mode)
docker compose up -d
```
{% endcode %}

After all the services have started you can see them running in the background:

{% code lineNumbers="true" %}
```bash
docker compose ps
```
{% endcode %}

### Environment Variables

You can use environment variables to control authentication and authorisation with the platform and in between services.

You also need to define the OpenAI API Key here.

### Accessing the API

The API is available through the following endpoint:

* `http://<your-ip>:8000`

### Restarting all services

You can restart services to pick up any configuration changes by running:

{% code lineNumbers="true" %}
```bash
# Stop and remove the containers
docker compose down

# Recreate and start the containers
docker compose up -d
```
{% endcode %}

> Be aware that this will result in downtime. Simply restarting the services does not apply configuration changes.

### Stopping all services

You can stop Julep by running `docker compose stop` in the same directory as your `docker-compose.yml` file.

**Uninstall and delete all data**

{% code lineNumbers="true" %}
```bash
# Stop docker and remove volumes
docker compose down -v
```
{% endcode %}

> **Be careful!**
>
> This will wipe out all the conversation history and memories in the database and storage volumes

## Advanced

If you want to deploy Julep to production, [let's hop on a call](https://calendly.com/diwank-julep/45min)!

We'll help you customise the platform and help you get set up with:

* Multi-tenancy
* Reverse proxy along with authentication and authorisation
* Self-hosted LLMs
* & more



