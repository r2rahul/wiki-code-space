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

    search_parser = subparsers.add_parser("search", help="Search project wiki")
    search_parser.add_argument("query", help="Wiki search query")
    search_parser.add_argument(
        "--project",
        dest="project_name",
        default=None,
        help="Override project_name from config/wiki_engine.yaml",
    )
    search_parser.add_argument(
        "--config",
        dest="config_path",
        default="config/wiki_engine.yaml",
        help="Path to wiki_engine YAML config",
    )
    search_parser.add_argument(
        "-n",
        dest="result_count",
        type=int,
        default=10,
        help="Maximum search results",
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
    init_qmd_group = init_parser.add_mutually_exclusive_group()
    init_qmd_group.add_argument(
        "--qmd-index",
        dest="qmd_enabled",
        action="store_true",
        default=True,
        help="Enable qmd wiki indexing and qmd-first search",
    )
    init_qmd_group.add_argument(
        "--no-qmd-index",
        dest="qmd_enabled",
        action="store_false",
        help="Disable qmd wiki indexing and use markdown search fallback",
    )
    migrate_parser = subparsers.add_parser("migrate", help=argparse.SUPPRESS)
    migrate_parser.add_argument("target_dir")
    migrate_parser.add_argument("--project", dest="project_name", default=None)
    migrate_parser.add_argument(
        "--config",
        dest="config_path",
        default="config/wiki_engine.yaml",
    )
    migrate_parser.set_defaults(qmd_enabled=True)

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


def run_search(
    query_text: str,
    project_name: str | None,
    config_path: str,
    result_count: int,
) -> int:
    """Execute qmd-first wiki search and print a concise result."""

    repo_root = Path.cwd()
    updater = WikiUpdater(repo_root=repo_root, config_path=repo_root / config_path)
    result = updater.search(
        query_text=query_text,
        project_override=project_name,
        result_count=result_count,
    )

    print(f"wiki_engine search backend={result.get('backend', 'unknown')}")
    print(f"status={result.get('status', 'unknown')}")

    if result.get("backend") == "qmd" and isinstance(result.get("stdout"), str):
        print(result["stdout"])
        return 0

    for item in result.get("results", []):
        print(
            f"{item['path']}:{item['line']} "
            f"(score={item['score']}) {item['snippet']}"
        )
    if not result.get("results"):
        print("No wiki results found")
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

    if args.command == "search":
        return run_search(
            query_text=args.query,
            project_name=args.project_name,
            config_path=args.config_path,
            result_count=args.result_count,
        )

    if args.command in {"init", "migrate"}:
        result = initialize_project(
            target_dir=args.target_dir,
            project_name=args.project_name,
            config_relpath=args.config_path,
            qmd_enabled=args.qmd_enabled,
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
        print(f"guide_path={result.guide_path}")
        print(f"bootstrap_path={result.bootstrap_path}")
        print(f"changed_files={len(result.changed_files)}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
