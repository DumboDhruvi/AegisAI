"""Integration tests for Cloud Deployment, Docker configurations, and deployment CLI."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from aegis.cli.cloud_deploy import (
    check_environment_variables,
    generate_ecs_task_definition,
    validate_docker_compose_config,
)
from aegis.cli.cloud_deploy import (
    main as deploy_cli_main,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_dockerfile_api_structure() -> None:
    """Verify backend Dockerfile follows multi-stage security best practices."""
    dockerfile = REPO_ROOT / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile must exist at repository root"

    content = dockerfile.read_text(encoding="utf-8")

    # Multi-stage verification
    assert "FROM python:3.10-slim AS builder" in content
    assert "FROM python:3.10-slim AS runtime" in content

    # Security: Non-root user
    assert "useradd -r -g aegis" in content
    assert "USER aegis" in content

    # Port and Healthcheck
    assert "EXPOSE 8000" in content
    assert "HEALTHCHECK" in content
    assert "http://localhost:8000/health" in content

    # Uvicorn entrypoint
    assert "uvicorn" in content
    assert "aegis.api.main:app" in content


def test_dockerfile_dashboard_structure() -> None:
    """Verify Streamlit dashboard Dockerfile follows container best practices."""
    dockerfile = REPO_ROOT / "Dockerfile.dashboard"
    assert dockerfile.exists(), "Dockerfile.dashboard must exist at repository root"

    content = dockerfile.read_text(encoding="utf-8")

    # Multi-stage verification
    assert "FROM python:3.10-slim AS builder" in content
    assert "FROM python:3.10-slim AS runtime" in content

    # Security: Non-root user
    assert "useradd -r -g aegis" in content
    assert "USER aegis" in content

    # Port and Healthcheck
    assert "EXPOSE 8501" in content
    assert "HEALTHCHECK" in content
    assert "/_stcore/health" in content

    # Streamlit execution
    assert "streamlit" in content
    assert "src/aegis/dashboard/app.py" in content


def test_docker_compose_specification() -> None:
    """Validate docker-compose.yml service topology and configurations."""
    compose_path = REPO_ROOT / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"

    with compose_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "services" in config
    services = config["services"]

    # All three required services must exist
    assert "postgres" in services
    assert "app" in services
    assert "dashboard" in services

    # Postgres service
    pg = services["postgres"]
    assert "pgvector/pgvector" in pg["image"]
    assert "healthcheck" in pg

    # API service
    app = services["app"]
    assert "healthcheck" in app
    assert "depends_on" in app
    assert "postgres" in app["depends_on"]

    # Dashboard service
    dash = services["dashboard"]
    assert "healthcheck" in dash
    assert "depends_on" in dash
    assert "app" in dash["depends_on"]

    # Volumes and networks
    assert "volumes" in config and "pgdata" in config["volumes"]
    assert "networks" in config and "aegis-network" in config["networks"]


def test_dockerignore_exclusions() -> None:
    """Verify sensitive files and build artifacts are excluded in .dockerignore."""
    dockerignore = REPO_ROOT / ".dockerignore"
    assert dockerignore.exists(), ".dockerignore must exist"

    content = dockerignore.read_text(encoding="utf-8")
    lines = {line.strip() for line in content.splitlines() if line.strip()}

    assert ".git" in lines
    assert ".venv" in lines
    assert "__pycache__" in lines
    assert ".env" in lines
    assert "tests/" in lines or "tests" in lines


def test_check_environment_variables_validation() -> None:
    """Verify environment check handles clean and erroneous environment configs."""
    # Valid environment
    env_valid = {
        "AEGIS_ENV": "development",
        "AEGIS_PORT": "8000",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
        "OPENAI_API_KEY": "sk-test-key",
    }
    is_ready, diags = check_environment_variables(env_valid)
    assert is_ready is True
    assert not any(d.startswith("[ERROR]") for d in diags)

    # Invalid port: Non-numeric
    env_bad_port = {"AEGIS_PORT": "not-a-port"}
    is_ready, diags = check_environment_variables(env_bad_port)
    assert is_ready is False
    assert any("Non-numeric port" in d for d in diags)

    # Invalid port: Out of range
    env_out_range = {"AEGIS_PORT": "70000"}
    is_ready, diags = check_environment_variables(env_out_range)
    assert is_ready is False
    assert any("Invalid port range" in d for d in diags)

    # Error: Production pointing to localhost
    env_prod_local = {
        "AEGIS_ENV": "production",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
    }
    is_ready, diags = check_environment_variables(env_prod_local)
    assert is_ready is False
    assert any("Production environment should not point to localhost" in d for d in diags)


def test_validate_docker_compose_config(tmp_path: Path) -> None:
    """Verify compose validator handles valid and broken compose files."""
    # Test valid real compose file
    is_valid, diags = validate_docker_compose_config(REPO_ROOT / "docker-compose.yml")
    assert is_valid is True

    # Test non-existent path
    is_valid, diags = validate_docker_compose_config(tmp_path / "missing.yml")
    assert is_valid is False
    assert any("File not found" in d for d in diags)

    # Test incomplete compose file missing services
    bad_compose = tmp_path / "bad-compose.yml"
    bad_compose.write_text("services:\n  only_one:\n    image: test", encoding="utf-8")
    is_valid, diags = validate_docker_compose_config(bad_compose)
    assert is_valid is False
    assert any("Missing required service" in d for d in diags)


def test_generate_ecs_task_definition() -> None:
    """Verify ECS task definition structure matches AWS Fargate specifications."""
    task_def = generate_ecs_task_definition(
        image_repo="my-registry.amazonaws.com/aegis",
        image_tag="v1.0.0",
        cpu=2048,
        memory=4096,
        aws_region="us-west-2",
    )

    assert task_def["family"] == "aegis-ai-production"
    assert task_def["cpu"] == "2048"
    assert task_def["memory"] == "4096"
    assert task_def["networkMode"] == "awsvpc"
    assert "FARGATE" in task_def["requiresCompatibilities"]

    containers = task_def["containerDefinitions"]
    assert len(containers) == 2

    api_ctr = next(c for c in containers if c["name"] == "aegis-api")
    assert api_ctr["image"] == "my-registry.amazonaws.com/aegis:v1.0.0"
    assert api_ctr["portMappings"][0]["containerPort"] == 8000
    assert api_ctr["logConfiguration"]["options"]["awslogs-region"] == "us-west-2"

    dash_ctr = next(c for c in containers if c["name"] == "aegis-dashboard")
    assert dash_ctr["image"] == "my-registry.amazonaws.com/aegis-dashboard:v1.0.0"
    assert dash_ctr["portMappings"][0]["containerPort"] == 8501


def test_deploy_cli_main(tmp_path: Path) -> None:
    """Verify cloud deployment CLI options and output generation."""
    task_def_path = tmp_path / "test_task_def.json"
    exit_code = deploy_cli_main(
        [
            "--check-env",
            "--validate-compose",
            str(REPO_ROOT / "docker-compose.yml"),
            "--generate-task-def",
            str(task_def_path),
        ]
    )

    assert exit_code == 0
    assert task_def_path.exists()

    generated_data = json.loads(task_def_path.read_text(encoding="utf-8"))
    assert generated_data["family"] == "aegis-ai-production"
