"""
Client for calling the deployed Branch Config Example API.

This demonstrates how to call APIs across multiple deployments
(production, staging, dev) in a multi-branch, multi-perimeter setup.

The client automatically:
1. Reads obproject.toml to find the right perimeter for the environment
2. Switches to that perimeter
3. Lists apps and finds the deployment matching project + branch
4. Calls the API

Usage:
    # Call production deployment (auto-switches to production perimeter)
    python client.py --env production

    # Call staging deployment
    python client.py --env staging

    # Call dev deployment (default)
    python client.py --env dev

    # Call specific URL directly (no perimeter switch)
    python client.py --url https://your-api-url.outerbounds.xyz
"""

import requests
import os
import argparse
import subprocess
import re
from metaflow.metaflow_config import SERVICE_HEADERS

def get_auth_headers():
    if os.environ.get("METAFLOW_SERVICE_AUTH_KEY"):
        return {"x-api-key": os.environ.get("METAFLOW_SERVICE_AUTH_KEY")}
    from metaflow.metaflow_config import SERVICE_HEADERS

    return SERVICE_HEADERS

def read_obproject_config():
    """Read obproject.toml to get environment configuration"""
    try:
        import toml
    except ImportError:
        try:
            import tomllib as toml
        except ImportError:
            return None

    try:
        with open("../../obproject.toml", "rb" if hasattr(toml, "load") else "r") as f:
            if hasattr(toml, "load"):
                return toml.load(f)  # tomllib (Python 3.11+)
            else:
                return toml.loads(f.read())  # toml package
    except FileNotFoundError:
        return None


def load_env_config():
    """
    Load environment configuration from obproject.toml.

    Reads [branch_to_environment] and [environments.*] sections to build
    a mapping of environment names to their branch patterns and perimeters.

    Returns dict like:
    {
        "production": {"branch": "main", "perimeter": "default"},
        "staging": {"branch": "develop", "perimeter": "default"},
        ...
    }
    """
    config = read_obproject_config()
    if not config:
        print("⚠️  Warning: Could not read obproject.toml, using default config")
        return {
            "production": {"branch": "main", "perimeter": "default"},
            "staging": {"branch": "develop", "perimeter": "default"},
            "dev": {"branch": None, "perimeter": "default"},
        }

    env_config = {}
    branch_to_env = config.get("branch_to_environment", {})
    environments = config.get("environments", {})

    # Build environment config by mapping branch patterns to environment settings
    for env_name, env_settings in environments.items():
        # Find which branch pattern maps to this environment
        branch_pattern = None
        for pattern, env in branch_to_env.items():
            if env == env_name:
                # Use the first non-wildcard match as the "main" branch for this env
                if "*" not in pattern:
                    branch_pattern = pattern
                    break

        env_config[env_name] = {
            "branch": branch_pattern,  # None if only wildcard matches
            "perimeter": env_settings.get("perimeter", "default")
        }

    return env_config


# Load configuration from obproject.toml at module import time
ENV_CONFIG = load_env_config()


def switch_perimeter(perimeter):
    """Switch to the specified perimeter"""
    print(f"   🔄 Switching to perimeter: {perimeter}")
    try:
        subprocess.run(
            ["outerbounds", "perimeter", "switch", "--id", perimeter, "--force"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"   ✅ Switched to perimeter: {perimeter}")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
        print(f"   ❌ Failed to switch perimeter: {error_msg}")
        return False


def discover_app_url(environment, project_name="branch_config_example"):
    """
    Discover app URL using `outerbounds app list` command.

    Parses table output to find deployment matching project and branch tags.
    """
    try:
        # Get list of apps in current perimeter (table format)
        result = subprocess.run(
            ["outerbounds", "app", "list"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse table output
        lines = result.stdout.strip().split('\n')

        target_branch = ENV_CONFIG[environment]["branch"]

        for line in lines:
            # Look for lines with tags containing our project and branch
            if f"project={project_name}" in line:
                # Check if it matches our target branch
                if target_branch and f"branch={target_branch}" in line:
                    # Extract URL using regex
                    url_match = re.search(r'https://[^\s]+', line)
                    if url_match:
                        url = url_match.group(0)
                        # Convert UI URL to API URL (ui-c-xxx -> api-c-xxx)
                        url = url.replace('https://ui-', 'https://api-')
                        # Extract app name (first column)
                        name_match = re.match(r'(\S+)', line)
                        app_name = name_match.group(1) if name_match else "unknown"
                        print(f"   ✅ Found deployment: {app_name} (branch={target_branch})")
                        return url
                # For dev, match any branch that's not main/develop
                elif not target_branch:
                    if "branch=main" not in line and "branch=develop" not in line:
                        url_match = re.search(r'https://[^\s]+', line)
                        if url_match:
                            url = url_match.group(0)
                            # Convert UI URL to API URL (ui-c-xxx -> api-c-xxx)
                            url = url.replace('https://ui-', 'https://api-')
                            # Extract branch from tags
                            branch_match = re.search(r'branch=(\S+)', line)
                            branch = branch_match.group(1) if branch_match else "unknown"
                            name_match = re.match(r'(\S+)', line)
                            app_name = name_match.group(1) if name_match else "unknown"
                            print(f"   ✅ Found deployment: {app_name} (branch={branch})")
                            return url

        print(f"   ❌ No deployment found for environment '{environment}'")
        print(f"      Make sure the app is deployed to this perimeter")
        return None

    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to list apps: {e.stderr}")
        return None


def call_api(base_url, endpoint="/", method="GET", json_data=None):
    """Make authenticated API call"""
    headers = get_auth_headers()
    url = base_url.rstrip("/") + endpoint

    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=json_data)

    # Check if response is successful
    response.raise_for_status()

    # Try to parse as JSON
    try:
        return response.json()
    except ValueError:
        # Not JSON, return text
        return {"response": response.text, "status_code": response.status_code}


def main():
    parser = argparse.ArgumentParser(description="Call Branch Config Example API")
    parser.add_argument(
        "--env",
        choices=["production", "staging", "dev"],
        default="dev",
        help="Environment to call (production, staging, or dev)"
    )
    parser.add_argument(
        "--url",
        help="Direct URL to API (overrides --env and perimeter switching)"
    )
    parser.add_argument(
        "--project",
        default="branch_config_example",
        help="Project name to filter deployments"
    )
    args = parser.parse_args()

    # Determine which URL to use
    if args.url:
        base_url = args.url
        print(f"📡 Calling API at: {base_url}")
    else:
        print(f"📡 Calling {args.env} environment deployment")

        # Step 1: Switch to the correct perimeter
        perimeter = ENV_CONFIG[args.env]["perimeter"]
        if not switch_perimeter(perimeter):
            return

        # Step 2: Discover app URL in that perimeter
        print(f"   🔍 Discovering app URL...")
        base_url = discover_app_url(args.env, args.project)
        if not base_url:
            print("\n💡 Tips:")
            print(f"   - Deploy the app: cd ../../ && obproject-deploy")
            print(f"   - Or call directly: python client.py --url https://your-api-url")
            return

    print("\n" + "="*60)

    # Call root endpoint
    print("\n🔹 GET /")
    try:
        result = call_api(base_url, "/")
        print(f"   Response: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Call health endpoint
    print("\n🔹 GET /health")
    try:
        health = call_api(base_url, "/health")
        print(f"   Response: {health}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "="*60)
    print("\n✅ Done!")
    print(f"\n💡 Multi-environment workflow:")
    print(f"   python client.py --env production  # Auto-switches to production perimeter")
    print(f"   python client.py --env staging     # Auto-switches to staging perimeter")
    print(f"   python client.py --env dev         # Auto-switches to dev perimeter")


if __name__ == "__main__":
    main()
