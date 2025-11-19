# Branch-Based Configuration Example

This repository demonstrates how to use branch-based deployment configuration with Outerbounds projects, enabling automatic environment selection based on git branches.

## Overview

Different branches automatically deploy to different **perimeters** with different **app configurations**:

| Branch | Environment | Perimeter | Config File | Resources |
|--------|-------------|-----------|-------------|-----------|
| `main` | production | production | `config.prod.yml` | 2 CPU, 2Gi RAM, 4 workers |
| `develop` | staging | staging | `config.staging.yml` | 1 CPU, 1Gi RAM, 2 workers |
| `feature/*` | dev | dev | `config.yml` | 0.5 CPU, 512Mi RAM, 1 worker |

## Configuration

All branch-based deployment logic lives in `obproject.toml`:

```toml
platform = 'your-platform.outerbounds.xyz'
project = 'branch_config_example'
title = 'Branch-Based Configuration Example'

# Map branches to environments (supports glob patterns)
[branch_to_environment]
"main" = "production"
"develop" = "staging"
"feature/*" = "dev"
"*" = "dev"  # Catch-all default

# Environment-specific settings
[environments.production]
perimeter = "production"
deployment_config = "config.prod.yml"

[environments.staging]
perimeter = "staging"
deployment_config = "config.staging.yml"

[environments.dev]
perimeter = "dev"
deployment_config = "config.yml"
```

### Configuration Keys Explained

- **`branch_to_environment`**: Maps git branch patterns to environment names
  - Supports glob patterns (e.g., `feature/*` matches `feature/new-ui`, `feature/bug-fix`)
  - First match wins (order matters!)
  - `*` acts as a catch-all fallback

- **`environments.<name>.perimeter`**: The Outerbounds perimeter to deploy to
  - Flows, apps, and assets will be deployed to this perimeter
  - The CLI automatically switches to this perimeter before deployment

- **`environments.<name>.deployment_config`**: Path to the app config file
  - Each app in `deployments/` can have environment-specific YAML configs
  - Controls resources, environment variables, workers, etc.

## How It Works

### Local Deployment

When you run `obproject-deploy` locally:

1. **Branch Detection**: Detects current git branch via `git rev-parse --abbrev-ref HEAD`
2. **Environment Mapping**: Maps branch to environment using `branch_to_environment` patterns
3. **Perimeter Switch**: Executes `outerbounds perimeter switch --id <perimeter> --force`
4. **Deployment**: Deploys flows and apps using the environment's `deployment_config`

```bash
# Example: Deploy from main branch
git checkout main
obproject-deploy

# Output:
# Deploying to the main branch (aka --production)
# 🔄 Switching to perimeter: production
# ✅ Switched to perimeter: production
# 🟩🟩🟩 Registering Assets
# 🟩🟩🟩 Discovering Flows
# 🟩🟩🟩 Deploying flows
# 🟩🟩🟩 Deploying apps and endpoints
#   → Uses config.prod.yml (2 CPU, 4 workers)
# ✅✅✅ Deployment successful!
```

### CI/CD Deployment

The same `obproject-deploy` command works in CI/CD without modification! The CI workflow just needs to:

1. **Authenticate** with a service principal (can use any perimeter for auth)
2. **Call `obproject-deploy`** - branch detection and perimeter switching happens automatically

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
        ├── config.yml          # Dev config (0.5 CPU, 1 worker)
        ├── config.staging.yml  # Staging config (1 CPU, 2 workers)
        └── config.prod.yml     # Production config (2 CPU, 4 workers)
```

## Usage Examples

### Local Deployment

```bash
# Deploy from main branch
git checkout main
obproject-deploy
# → Switches to 'production' perimeter
# → Deploys flows to prod Metaflow branch
# → Deploys apps using config.prod.yml

# Deploy from develop branch
git checkout develop
obproject-deploy
# → Switches to 'staging' perimeter
# → Deploys flows to test.develop Metaflow branch
# → Deploys apps using config.staging.yml

# Deploy from feature branch
git checkout feature/new-ui
obproject-deploy
# → Switches to 'dev' perimeter
# → Deploys flows to test.feature_new_ui Metaflow branch
# → Deploys apps using config.yml
```