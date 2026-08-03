"""Command-line interface for wiki_engine workflows."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

from wiki_engine.agent_install import install_agent_instructions
from wiki_engine.migration import initialize_project
from wiki_engine.updater import WikiUpdater


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser with update workflow command.

    Constructs an argument parser supporting update, search, init, migrate,
    and harness-specific Agent Skill installation.

    :return: Configured argument parser ready for parse_args().
    :rtype: argparse.ArgumentParser
    """

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

    install_parser = subparsers.add_parser(
        "install",
        help="Install wiki skills for an agent harness",
    )
    install_parser.add_argument(
        "agent_name",
        nargs="?",
        choices=("copilot", "codex", "claude", "gemini"),
        default="gemini",
        help="Harness to configure (default: gemini)",
    )
    install_parser.add_argument(
        "--project",
        dest="project_name",
        default=None,
        help="Override project_name from config/wiki_engine.yaml",
    )
    install_parser.add_argument(
        "--config",
        dest="config_path",
        default="config/wiki_engine.yaml",
        help="Path to wiki_engine YAML config",
    )
    install_parser.add_argument(
        "--user",
        action="store_true",
        help="Install only at user scope instead of modifying this project",
    )
    return parser


def run_update(project_name: str | None, config_path: str) -> int:
    """Execute update command and print concise result summary.

    Runs the wiki update workflow to regenerate wiki indices and bridge
    edges. Loads configuration from the specified path, optionally overriding
    the project name. Prints summary metrics to stdout.

    :param project_name: Optional project name override. If provided, overrides
                         the project_name from the config file.
    :type project_name: str | None
    :param config_path: Relative or absolute path to wiki_engine.yaml config.
    :type config_path: str
    :return: Exit code (0 on success, non-zero on error).
    :rtype: int
    """

    repo_root = Path.cwd()
    updater = WikiUpdater(repo_root=repo_root, config_path=repo_root / config_path)
    result = updater.update(project_override=project_name)

    print("wiki_engine update completed")
    print(f"changed_files={len(result.changed_files)}")
    print(f"bridge_edges={result.graph_result.get('bridge_edge_count', 0)}")
    print(f"qmd_status={result.qmd_result.get('status', 'unknown')}")
    if result.qmd_result.get("reason") == "qmd CLI not installed":
        print_qmd_fallback_notice()
    return 0


def run_search(
    query_text: str,
    project_name: str | None,
    config_path: str,
    result_count: int,
) -> int:
    """Execute qmd-first wiki search and print a concise result.

    Performs semantic wiki search using qmd (if available) or markdown fallback.
    Formats and prints search results to stdout with file paths, line numbers,
    and relevance scores.

    :param query_text: Search query string.
    :type query_text: str
    :param project_name: Optional project name override. If provided, overrides
                         the project_name from the config file.
    :type project_name: str | None
    :param config_path: Relative or absolute path to wiki_engine.yaml config.
    :type config_path: str
    :param result_count: Maximum number of search results to return.
    :type result_count: int
    :return: Exit code (0 on success, non-zero on error).
    :rtype: int
    """

    repo_root = Path.cwd()
    updater = WikiUpdater(repo_root=repo_root, config_path=repo_root / config_path)
    result = updater.search(
        query_text=query_text,
        project_override=project_name,
        result_count=result_count,
    )

    print(f"wiki_engine search backend={result.get('backend', 'unknown')}")
    print(f"status={result.get('status', 'unknown')}")
    if result.get("reason") == "qmd CLI not installed":
        print_qmd_fallback_notice()

    if result.get("backend") == "qmd" and isinstance(result.get("stdout"), str):
        print(result["stdout"])
        return 0

    for item in result.get("results", []):
        print(
            f"{item['path']}:{item['line']} (score={item['score']}) {item['snippet']}"
        )
    if not result.get("results"):
        print("No wiki results found")
    return 0


def print_qmd_fallback_notice() -> None:
    """Explain the optional qmd accelerator and fallback scale guidance."""

    print(
        "qmd is not installed; wiki_engine will default to index-based "
        "Markdown search. This works best for wikis with about 100 Markdown "
        "files or fewer; for larger wikis, consider installing qmd."
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for python -m wiki_engine.cli and script usage.

    Parses command-line arguments and dispatches to appropriate handler
    (update, search, init, migrate, or agent installation). Supports
    programmatic usage via argv parameter or direct CLI invocation.

    :param argv: Optional list of command-line arguments. If None, uses
                 sys.argv[1:]. Useful for testing and programmatic invocation.
    :type argv: list[str] | None
    :return: Exit code (0 on success, non-zero on error).
    :rtype: int
    """

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
        print(f"qmd_status={result.update_result.qmd_result.get('status', 'unknown')}")
        if result.update_result.qmd_result.get("reason") == "qmd CLI not installed":
            print_qmd_fallback_notice()
        return 0

    if args.command == "install":
        repo_root = Path.cwd()
        updater = WikiUpdater(
            repo_root=repo_root,
            config_path=repo_root / args.config_path,
        )
        project_name = args.project_name or updater.config.project_name
        result = install_agent_instructions(
            repo_root=repo_root,
            project_name=project_name,
            agent_name=args.agent_name,
            jinja_env=updater.jinja_env,
            user=args.user,
        )
        print("wiki_engine agent install completed")
        print(f"agent={result.agent_name}")
        print(f"scope={result.scope}")
        print(f"instruction_path={result.instruction_path}")
        print(f"refresh_command={result.refresh_command}")
        print(f"query_command={result.query_command}")
        for skill_path in result.skill_paths:
            print(f"skill_path={skill_path}")
        print(f"changed_files={len(result.changed_files)}")
        if shutil.which("qmd") is None:
            print_qmd_fallback_notice()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
