# Branch-Based Configuration Example

This repository demonstrates how to use branch-based deployment configuration with Outerbounds projects.

## Overview

Different branches automatically deploy to different environments with different configurations:

| Branch | Environment | Perimeter | Config File | Resources |
|--------|-------------|-----------|-------------|-----------|
| `main` | production | production | `config.prod.yml` | 2 CPU, 2Gi RAM, 3 replicas |
| `develop` | staging | staging | `config.staging.yml` | 1 CPU, 1Gi RAM, 2 workers |
| `feature/*` | dev | dev | `config.yml` | 0.5 CPU, 512Mi RAM |

## Configuration

The magic happens in `obproject.toml`:

```toml
# Map branches to environments (supports glob patterns)
[deployment.branch_to_environment]
"main" = "production"
"develop" = "staging"
"feature/*" = "dev"
"*" = "dev"  # Catch-all default

# Environment-specific settings
[deployment.environments.production]
perimeter = "production"
deployment_config = "config.prod.yml"

[deployment.environments.staging]
perimeter = "staging"
deployment_config = "config.staging.yml"

[deployment.environments.dev]
perimeter = "dev"
deployment_config = "config.yml"
```

## How It Works

1. **Branch Detection**: When `obproject-deploy` runs, it detects the current git branch
2. **Environment Mapping**: The branch is mapped to an environment using `branch_to_environment`
3. **Config Lookup**: The environment's `deployment_config` and `perimeter` are used
4. **Deployment**: Apps are deployed using the branch-specific configuration

## Repository Structure

```
.
├── obproject.toml              # Branch-to-environment mappings
├── flows/
│   └── example/
│       └── flow.py             # Example Metaflow flow
└── deployments/
    └── api/
        ├── app.py              # FastAPI application
        ├── config.yml          # Dev config (default)
        ├── config.staging.yml  # Staging config
        └── config.prod.yml     # Production config
```

## Deployment Examples

### Deploy from main branch
```bash
git checkout main
obproject-deploy
# → Uses config.prod.yml, deploys to production perimeter
```

### Deploy from develop branch
```bash
git checkout develop
obproject-deploy
# → Uses config.staging.yml, deploys to staging perimeter
```

### Deploy from feature branch
```bash
git checkout feature/new-ui
obproject-deploy
# → Uses config.yml, deploys to dev perimeter
```

## Benefits

- **Automatic environment selection**: No manual flags or environment variables needed
- **Branch protection**: Production deploys only from `main`
- **Clear separation**: Different configs for different environments
- **Safe testing**: Feature branches automatically use dev environment
- **Flexible patterns**: Glob patterns support any branching strategy