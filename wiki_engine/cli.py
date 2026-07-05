"""Command-line interface for wiki_engine workflows."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from wiki_engine.agent_install import install_agent_instructions
from wiki_engine.migration import initialize_project
from wiki_engine.updater import WikiUpdater


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser with update workflow command."""

    parser = argparse.ArgumentParser(prog="wiki-engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update_parser = subparsers.add_parser("update", help="Run coherent wiki update")
    update_parser.add_argument(
        "--project",
        dest="project_name",
        default=None,
        help="Override project_name from config/wiki_engine.yaml",
    )
    update_parser.add_argument(
        "--config",
        dest="config_path",
        default="config/wiki_engine.yaml",
        help="Path to wiki_engine YAML config",
    )

    init_parser = subparsers.add_parser(
        "init",
        help="Initialize wiki workflow in an existing project folder",
    )
    init_parser.add_argument(
        "target_dir",
        help="Path to existing project directory",
    )
    init_parser.add_argument(
        "--project",
        dest="project_name",
        default=None,
        help="Optional project name override",
    )
    init_parser.add_argument(
        "--config",
        dest="config_path",
        default="config/wiki_engine.yaml",
        help="Relative config path in target project",
    )
    migrate_parser = subparsers.add_parser("migrate", help=argparse.SUPPRESS)
    migrate_parser.add_argument("target_dir")
    migrate_parser.add_argument("--project", dest="project_name", default=None)
    migrate_parser.add_argument(
        "--config",
        dest="config_path",
        default="config/wiki_engine.yaml",
    )

    for agent_name in ("codex", "vscode", "claude", "gemini"):
        agent_parser = subparsers.add_parser(
            agent_name,
            help=f"Install {agent_name} wiki maintenance instructions",
        )
        agent_parser.add_argument(
            "--project",
            dest="project_name",
            default=None,
            help="Override project_name from config/wiki_engine.yaml",
        )
        agent_parser.add_argument(
            "--config",
            dest="config_path",
            default="config/wiki_engine.yaml",
            help="Path to wiki_engine YAML config",
        )
    return parser


def run_update(project_name: str | None, config_path: str) -> int:
    """Execute update command and print concise result summary."""

    repo_root = Path.cwd()
    updater = WikiUpdater(repo_root=repo_root, config_path=repo_root / config_path)
    result = updater.update(project_override=project_name)

    print("wiki_engine update completed")
    print(f"changed_files={len(result.changed_files)}")
    print(f"bridge_edges={result.graph_result.get('bridge_edge_count', 0)}")
    print(f"qmd_status={result.qmd_result.get('status', 'unknown')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for python -m wiki_engine.cli and script usage."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "update":
        return run_update(
            project_name=args.project_name,
            config_path=args.config_path,
        )

    if args.command in {"init", "migrate"}:
        result = initialize_project(
            target_dir=args.target_dir,
            project_name=args.project_name,
            config_relpath=args.config_path,
        )
        print("wiki_engine init completed")
        print(f"project_root={result.project_root}")
        print(f"project_name={result.project_name}")
        print(f"config_path={result.config_path}")
        print(f"changed_files={len(result.update_result.changed_files)}")
        print(
            "bridge_edges="
            f"{result.update_result.graph_result.get('bridge_edge_count', 0)}"
        )
        print(
            "qmd_status="
            f"{result.update_result.qmd_result.get('status', 'unknown')}"
        )
        return 0

    if args.command in {"codex", "vscode", "claude", "gemini"}:
        repo_root = Path.cwd()
        updater = WikiUpdater(
            repo_root=repo_root,
            config_path=repo_root / args.config_path,
        )
        project_name = args.project_name or updater.config.project_name
        result = install_agent_instructions(
            repo_root=repo_root,
            project_name=project_name,
            agent_name=args.command,
            jinja_env=updater.jinja_env,
        )
        print("wiki_engine agent install completed")
        print(f"agent={result.agent_name}")
        print(f"instruction_path={result.instruction_path}")
        print(f"skill_path={result.skill_path}")
        print(f"changed_files={len(result.changed_files)}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
