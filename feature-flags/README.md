# Julep Feature Flags Service

This directory contains the feature flags service for Julep using Unleash with OpenFeature integration.

## Quick Start

### 1. Create External Volume

First, create the external volume for persistent data:

```bash
docker volume create unleash_db_data
```

### 2. Start Feature Flags Service

From the root of the Julep project:

```bash
# Start only feature flags services
docker-compose --profile feature-flags up -d

# Or start all services including feature flags
docker-compose --profile feature-flags --profile default up -d
```

This will start:
- **Unleash Server** on `http://localhost:4242` (localhost only for security)
- **PostgreSQL Database** (v16) on port `5433`

### 3. Access Unleash Dashboard

1. Open `http://localhost:4242` in your browser (only accessible from localhost)
2. Login with these **default credentials**:
   - **Username**: `admin`
   - **Password**: `unleash4all`

> **Security Note**: The dashboard is only accessible from localhost (127.0.0.1) for security. In production, use secure admin tokens and consider additional authentication layers.

### 4. Create Feature Flags

Create the `auto_tool_calls` feature flag manually in the dashboard:

1. Go to **Feature flags** → **Create feature flag**
2. **Name**: `auto_tool_calls`
3. **Description**: `Controls whether automatic tool calling is enabled in prompt steps`
4. **Type**: `Release`
5. **Project**: `default`
6. Click **Create feature flag**

## Configuration

### Environment Variables

Copy `env.example` to `.env` and customize:

```bash
cp feature-flags/env.example feature-flags/.env
```

Key variables:

```bash
# Database
UNLEASH_DB_NAME=unleash
UNLEASH_DB_USER=unleash
UNLEASH_DB_PASSWORD=unleash_password
UNLEASH_DB_PORT=5433

# Server
UNLEASH_PORT=4242
UNLEASH_URL=http://localhost:4242

# API Tokens (Change in production!)
UNLEASH_API_TOKEN=default:development.unleash-insecure-api-token
UNLEASH_ADMIN_TOKEN=*:*.unleash-insecure-admin-api-token

# Authentication
UNLEASH_AUTH_TYPE=open-source
```

### Security Configuration

#### Development
- Dashboard bound to `localhost:4242` (not publicly accessible)
- Default insecure tokens for easy development

#### Production Recommendations
1. **Change all default passwords and tokens**:
   ```bash
   UNLEASH_API_TOKEN=default:production.$(openssl rand -hex 32)
   UNLEASH_ADMIN_TOKEN=*:*.$(openssl rand -hex 32)
   ```

2. **Use external database** with proper credentials

3. **Enable SSL/TLS** with reverse proxy (nginx/traefik)

4. **Additional security layers**:
   - VPN access for admin dashboard
   - OAuth/SAML authentication (Unleash Enterprise)
   - Reverse proxy with basic auth

5. **Network security**:
   ```yaml
   # For production, consider internal network only
   ports:
     - "127.0.0.1:4242:4242"  # localhost only
   ```

## Usage in Agents API

### Architecture: OpenFeature + Unleash

This implementation uses **OpenFeature** as the standard interface with a **custom Unleash provider**. This architecture provides:

- **Vendor Independence**: Easy to switch from Unleash to LaunchDarkly, Flagsmith, or any other provider
- **Standardized API**: Consistent interface regardless of the underlying provider
- **Future-Proof**: Can migrate providers without changing application code
- **Thread-Safe Singleton**: Efficient resource usage with proper initialization

### Install Dependencies

The dependencies are already added to `agents-api/pyproject.toml`:
- `openfeature-sdk>=0.8.1` - OpenFeature SDK for vendor independence
- `UnleashClient>=5.12.0` - Unleash Python client (used by our custom provider)

### Basic Usage

```python
from agents_api.common.utils.feature_flags import is_auto_tool_calls_enabled

# Check if auto tool calls is enabled for a developer
developer_id = context.execution_input.developer_id
if is_auto_tool_calls_enabled(developer_id):
    # Use new tool calling logic
    result = await new_tool_calling_logic(context)
else:
    # Use old logic
    result = await old_logic(context)
```

### Advanced Usage

```python
from agents_api.common.utils.feature_flags import get_feature_flag_value

# Get any feature flag value with context
value = get_feature_flag_value(
    flag_name="auto_tool_calls",
    default_value=False,
    developer_id=developer_id,
    user_tier="premium",
    region="us-east-1"
)
```

### Environment Context

Feature flags automatically include environment context:

```python
# Environment is automatically detected from DEPLOYMENT_ENV
# development, staging, production, etc.
is_enabled = is_auto_tool_calls_enabled(developer_id)
```

### Switching Providers (Future)

Thanks to OpenFeature, switching providers is easy:

```python
# To switch to LaunchDarkly (example):
# 1. Install: pip install launchdarkly-openfeature
# 2. Replace provider in feature_flags.py:
from launchdarkly_openfeature import LaunchDarklyProvider
api.set_provider(LaunchDarklyProvider("your-sdk-key"))

# 3. No changes needed in application code!
# is_auto_tool_calls_enabled() still works the same way
```

## Feature Flags

### auto_tool_calls

Controls whether automatic tool calling is enabled in prompt steps.

- **Type**: Release flag
- **Default**: `False`
- **Targeting**: By developer_id and environment
- **Environments**: development, staging, production

### computer-use-2024-10-22

Controls access to computer use beta features.

- **Type**: Release flag
- **Default**: `False`
- **Targeting**: By developer_id and environment
- **Environments**: development, staging, production

## Management

### Starting/Stopping

```bash
# Start feature flags services
docker-compose --profile feature-flags up -d

# Stop feature flags services
docker-compose --profile feature-flags down

# View logs
docker-compose --profile feature-flags logs -f
```

### Adding New Flags

1. Access Unleash dashboard at `http://localhost:4242`
2. Click **Create feature flag**
3. Configure name, description, type, and targeting
4. Add flag constant to `FeatureFlags` class in utils
5. Create convenience function if needed
6. Test with gradual rollout

### Monitoring

Access Unleash dashboard at `http://localhost:4242` to:
- Monitor flag usage and metrics
- Manage rollout percentages
- Set up targeting rules by developer_id, environment, etc.
- View audit logs

## Integration with Julep

The feature flags service integrates seamlessly with Julep's architecture:

- **Profiles**: Use `--profile feature-flags` to start only when needed
- **External Volume**: Persistent data survives container restarts
- **Environment Variables**: Configurable for different environments
- **Manual Setup**: Create feature flags as needed via the dashboard
- **OpenFeature**: Vendor-neutral integration in agents-api for future flexibility
- **Security**: Localhost-only access with configurable authentication
- **Performance**: Thread-safe singleton pattern with lazy initialization