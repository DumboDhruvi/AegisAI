"""Cloud deployment helper and verification utility for AegisAI.

Validates environment configurations, Docker specifications, and AWS ECS
task definitions to ensure deployment readiness before release.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml


def check_environment_variables(
    env: dict[str, str] | None = None,
) -> tuple[bool, list[str]]:
    """Validate that required environment variables are configured for deployment.

    Returns:
        tuple[bool, list[str]]: (is_ready, list_of_diagnostics)
    """
    source_env = env if env is not None else dict(os.environ)
    diagnostics: list[str] = []

    # Database URL check
    db_url = source_env.get("DATABASE_URL")
    if not db_url:
        diagnostics.append("[WARNING] DATABASE_URL is not set; will fallback to default.")
    elif "localhost" in db_url and source_env.get("AEGIS_ENV") == "production":
        diagnostics.append("[ERROR] Production environment should not point to localhost database.")

    # LLM API Keys (at least one key should exist in production)
    api_keys = [
        source_env.get("OPENAI_API_KEY"),
        source_env.get("GEMINI_API_KEY"),
        source_env.get("ANTHROPIC_API_KEY"),
    ]
    if not any(api_keys):
        diagnostics.append(
            "[WARNING] No LLM provider API keys detected "
            "(OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY)."
        )

    # Port configuration
    port_str = source_env.get("AEGIS_PORT", "8000")
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            diagnostics.append(f"[ERROR] Invalid port range: {port}")
    except ValueError:
        diagnostics.append(f"[ERROR] Non-numeric port value: {port_str}")

    has_errors = any(d.startswith("[ERROR]") for d in diagnostics)
    return not has_errors, diagnostics


def validate_docker_compose_config(compose_path: Path) -> tuple[bool, list[str]]:
    """Parse and validate docker-compose.yml for required services and healthchecks."""
    diagnostics: list[str] = []
    if not compose_path.exists():
        return False, [f"[ERROR] File not found: {compose_path}"]

    try:
        with compose_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return False, [f"[ERROR] Failed to parse YAML: {e}"]

    if not isinstance(data, dict):
        return False, ["[ERROR] docker-compose.yml content is not a mapping"]

    services = data.get("services", {})
    required_services = ["postgres", "app", "dashboard"]
    for service in required_services:
        if service not in services:
            diagnostics.append(f"[ERROR] Missing required service: {service}")
        else:
            svc_conf = services[service]
            if "healthcheck" not in svc_conf:
                diagnostics.append(f"[WARNING] Service '{service}' does not specify a healthcheck.")

    has_errors = any(d.startswith("[ERROR]") for d in diagnostics)
    return not has_errors, diagnostics


def generate_ecs_task_definition(
    image_repo: str = "123456789012.dkr.ecr.us-east-1.amazonaws.com/aegis-ai",
    image_tag: str = "latest",
    cpu: int = 1024,
    memory: int = 2048,
    aws_region: str = "us-east-1",
) -> dict[str, Any]:
    """Generate production-grade AWS ECS Fargate task definition JSON."""
    return {
        "family": "aegis-ai-production",
        "networkMode": "awsvpc",
        "requiresCompatibilities": ["FARGATE"],
        "cpu": str(cpu),
        "memory": str(memory),
        "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
        "taskRoleArn": "arn:aws:iam::123456789012:role/aegisTaskRole",
        "containerDefinitions": [
            {
                "name": "aegis-api",
                "image": f"{image_repo}:{image_tag}",
                "essential": True,
                "portMappings": [
                    {
                        "containerPort": 8000,
                        "hostPort": 8000,
                        "protocol": "tcp",
                    }
                ],
                "environment": [
                    {"name": "AEGIS_ENV", "value": "production"},
                    {"name": "AEGIS_PORT", "value": "8000"},
                    {"name": "AEGIS_LOG_LEVEL", "value": "INFO"},
                ],
                "secrets": [
                    {
                        "name": "DATABASE_URL",
                        "valueFrom": (
                            "arn:aws:secretsmanager:us-east-1:123456789012:secret:aegis/db-url"
                        ),
                    },
                    {
                        "name": "OPENAI_API_KEY",
                        "valueFrom": (
                            "arn:aws:secretsmanager:us-east-1:123456789012:secret:aegis/openai-key"
                        ),
                    },
                ],
                "healthCheck": {
                    "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3,
                    "startPeriod": 15,
                },
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/aegis-ai",
                        "awslogs-region": aws_region,
                        "awslogs-stream-prefix": "api",
                    },
                },
            },
            {
                "name": "aegis-dashboard",
                "image": f"{image_repo}-dashboard:{image_tag}",
                "essential": True,
                "portMappings": [
                    {
                        "containerPort": 8501,
                        "hostPort": 8501,
                        "protocol": "tcp",
                    }
                ],
                "environment": [
                    {"name": "AEGIS_API_URL", "value": "http://localhost:8000"},
                    {"name": "AEGIS_ENV", "value": "production"},
                ],
                "healthCheck": {
                    "command": [
                        "CMD-SHELL",
                        "curl -f http://localhost:8501/_stcore/health || exit 1",
                    ],
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3,
                    "startPeriod": 20,
                },
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/aegis-ai",
                        "awslogs-region": aws_region,
                        "awslogs-stream-prefix": "dashboard",
                    },
                },
            },
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for deployment checks and artifact generation."""
    parser = argparse.ArgumentParser(description="AegisAI Cloud Deployment Verification CLI")
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check environment variables for deployment readiness",
    )
    parser.add_argument(
        "--validate-compose",
        metavar="PATH",
        type=Path,
        default=Path("docker-compose.yml"),
        help="Validate docker-compose.yml configuration",
    )
    parser.add_argument(
        "--generate-task-def",
        metavar="OUT_FILE",
        type=Path,
        help="Generate AWS ECS Fargate task definition JSON",
    )

    args = parser.parse_args(argv)

    status_ok = True

    if args.check_env:
        ok, diags = check_environment_variables()
        for d in diags:
            print(d)
        if not ok:
            status_ok = False
        else:
            print("[INFO] Environment variable check passed.")

    if args.validate_compose:
        ok, diags = validate_docker_compose_config(args.validate_compose)
        for d in diags:
            print(d)
        if not ok:
            status_ok = False
        else:
            print(f"[INFO] Compose file validation passed: {args.validate_compose}")

    if args.generate_task_def:
        task_def = generate_ecs_task_definition()
        args.generate_task_def.parent.mkdir(parents=True, exist_ok=True)
        with args.generate_task_def.open("w", encoding="utf-8") as f:
            json.dump(task_def, f, indent=2)
        print(f"[INFO] Generated AWS ECS task definition at {args.generate_task_def}")

    return 0 if status_ok else 1


if __name__ == "__main__":
    sys.exit(main())
