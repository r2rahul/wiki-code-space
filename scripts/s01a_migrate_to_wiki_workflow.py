"""Script entrypoint to migrate existing projects to wiki_engine workflow."""

from __future__ import annotations

import argparse
import sys

from wiki_engine.migration import migrate_project


def build_parser() -> argparse.ArgumentParser:
    """Build parser for migration script."""

    parser = argparse.ArgumentParser(
        prog="s01a_migrate_to_wiki_workflow.py",
        description="Migrate an existing project folder into wiki workflow",
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
    """Run migration and print concise run summary."""

    parser = build_parser()
    args = parser.parse_args(argv)

    result = migrate_project(
        target_dir=args.target_dir,
        project_name=args.project_name,
        config_relpath=args.config_path,
    )

    print("wiki migration completed")
    print(f"project_root={result.project_root}")
    print(f"project_name={result.project_name}")
    print(f"config_path={result.config_path}")
    print(f"changed_files={len(result.update_result.changed_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
