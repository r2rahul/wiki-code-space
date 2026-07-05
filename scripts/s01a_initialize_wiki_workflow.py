"""Script entrypoint to initialize projects with wiki_engine workflow."""

from __future__ import annotations

import argparse
import sys

from wiki_engine.migration import initialize_project


def build_parser() -> argparse.ArgumentParser:
    """Build parser for initialization script."""

    parser = argparse.ArgumentParser(
        prog="s01a_initialize_wiki_workflow.py",
        description="Initialize an existing project folder with wiki workflow",
    )
    parser.add_argument("target_dir", help="Path to existing project folder")
    parser.add_argument(
        "--project",
        dest="project_name",
        default=None,
        help="Optional project name override",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        default="config/wiki_engine.yaml",
        help="Relative config path in target project",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run initialization and print concise run summary."""

    parser = build_parser()
    args = parser.parse_args(argv)

    result = initialize_project(
        target_dir=args.target_dir,
        project_name=args.project_name,
        config_relpath=args.config_path,
    )

    print("wiki init completed")
    print(f"project_root={result.project_root}")
    print(f"project_name={result.project_name}")
    print(f"config_path={result.config_path}")
    print(f"changed_files={len(result.update_result.changed_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
