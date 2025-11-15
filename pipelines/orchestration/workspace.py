"""
Dynamic workspace configuration supporting multiple deployment modes.

Usage:
    # All Docker
    WORKSPACE_MODE=docker dagster-webserver -w workspace.py

    # All local
    WORKSPACE_MODE=local dagster-webserver -w workspace.py

    # Hybrid: specific projects
    PROJECTA_MODE=docker PROJECTB_MODE=local dagster-webserver -w workspace.py
"""

import os
from dagster._core.workspace.load_target import PythonFileTarget, GrpcServerTarget


def get_project_config(project_name: str, default_mode: str = "docker"):
    """Get configuration for a project based on environment variables."""
    # Check project-specific mode first, then fall back to global mode
    mode = os.getenv(f"{project_name.upper()}_MODE", os.getenv("WORKSPACE_MODE", default_mode))

    configs = {
        "projecta": {
            "docker": GrpcServerTarget(
                host=os.getenv("PROJECTA_HOST", "dagster-user-code-projecta"),
                port=int(os.getenv("PROJECTA_PORT", "4000")),
                location_name="projecta",
            ),
            "local": PythonFileTarget(
                python_file="orchestration/definitions.py",
                attribute="defs",
                location_name="projecta",
                working_directory="/home/user/cortex/pipelines",
            ),
        },
        "projectb": {
            "docker": GrpcServerTarget(
                host=os.getenv("PROJECTB_HOST", "dagster-user-code-projectb"),
                port=int(os.getenv("PROJECTB_PORT", "4001")),
                location_name="projectb",
            ),
            "local": PythonFileTarget(
                python_file="orchestration/definitions.py",
                attribute="defs",
                location_name="projectb",
                working_directory="/home/user/cortex/projectb",
            ),
        },
    }

    return configs[project_name][mode]


# Build workspace based on environment
def load_workspace():
    """Load workspace configuration dynamically."""
    targets = []

    # Add projects you want to load
    projects = os.getenv("WORKSPACE_PROJECTS", "projecta").split(",")

    for project in projects:
        project = project.strip()
        try:
            targets.append(get_project_config(project))
        except KeyError:
            print(f"Warning: Unknown project '{project}', skipping...")

    return targets


# Dagster looks for this variable
workspace = load_workspace()
