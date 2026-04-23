# Branch-Based Configuration

Teams need different behavior per environment — production uses a tuned model config, staging uses a test config, dev uses defaults. This project shows how `[branch_to_environment]` in obproject.toml maps git branches to named environments, each with its own perimeter, deployment config, and flow configs.

This is the reference implementation for the branch→environment→config resolution chain.

## Architecture

```
obproject.toml:
  [branch_to_environment]
    "main"       → "production"
    "develop"    → "staging"
    "feature/*"  → "dev"
    "*"          → "dev"

  [environments.production]
    perimeter = "default"
    deployment_config = "config.prod.yml"
    flow_configs.special_config = "configs/flow.prod.json"

  [environments.staging]  → configs/flow.staging.json
  [environments.dev]      → configs/flow.json

BranchConfigExampleFlow
  → reads Config("special_config") which resolves to the right JSON
    based on which branch the flow is deployed from
```

API deployment in `deployments/api/` also switches config per branch via `deployment_config`.

## Platform features used

- **[branch_to_environment]**: Maps branch globs to environment names. First match wins. `obproject-deploy` resolves the current branch to an environment at deploy time.
- **[environments.\<name\>]**: Per-environment config — perimeter, deployment config path, flow config paths. This is an ob-project-utils feature that wraps Metaflow's `Config` with branch-aware path resolution.
- **Config()**: Metaflow's `Config` object loads JSON at deploy time. ob-project-utils resolves which JSON file via the environment's `flow_configs` mapping.
- **Perimeter switching**: Each environment can bind to a different perimeter for compute isolation.
- **Apps**: Deployment config switches per branch (`config.prod.yml` vs `config.yml`).

## Flows

| Flow | Trigger | What it does |
|------|---------|-------------|
| BranchConfigExampleFlow | Manual | Reads branch-specific config, prints values to demonstrate resolution |

## CI strategy

Deploy + teardown. Generated via `obproject-ci generate`. Push deploys to the branch's environment; PR merge/branch delete tears down resources.

## Run locally

```bash
python flows/example/flow.py run
```

Locally, `Config` reads the default path (`configs/flow.json`). Branch-specific resolution only applies when deployed via `obproject-deploy`.

## Good to know

- `[branch_to_environment]` uses glob patterns. `"feature/*"` matches `feature/my-thing`. First match wins — put specific patterns before catch-alls.
- `Config("special_config")` in the flow code doesn't specify a path — the path comes from `[environments.<env>.flow_configs.special_config]` in obproject.toml. The flow is environment-agnostic; the config resolution is external.
- `deployment_config` switches the entire deployment config file per environment — useful for different resource requests, scaling, or auth settings between prod and dev.
- Perimeter switching is optional — all three environments here use `"default"`. In a real setup, production would use a dedicated perimeter with stricter access controls.
