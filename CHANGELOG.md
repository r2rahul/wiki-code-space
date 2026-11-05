# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Align wiki concept front matter and index listings with OKF v0.2
  (`type`/`description`/`status`/`generated`; progressive-disclosure indexes)
- Align `log.md` with OKF date headings (`## YYYY-MM-DD`, newest first)
- Add `wiki_code_space/okf-base.yaml` for okflint validation

### Fixed

- Make session distillation idempotent so reusable-knowledge bullets are not
  re-appended to permanent notes on every update

## [0.5.2] - 2026-08-05

### Fixed

- Fix qmd missing package detection to suppress npm errors in logs

## [0.5.1] - 2026-08-04

### Fixed

- Fix Copilot skill path and preserve initialized index.md on refresh

### Changed

- Add wiki directory structure and usage guidelines to README

## [0.5.0] - 2026-08-03

### Changed

- Rename `wiki_engine` to `wiki_wspace` for consistency and clarity across documentation and scripts

## [0.4.0] - 2026-08-03

### Changed

- Bump version to 0.4.0, update installation instructions, and enhance project initialization workflow
- Refactor project naming and CLI commands for wiki_engine

### Added

- Enhance installation process to bootstrap config and skills for fresh projects
- Add regression tests for CLI entry points

## [0.3.0] - 2026-08-03

### Changed

- Refactor wiki_engine for improved agent skill installation and CLI functionality

## [0.2.0] - 2026-07-09

### Changed

- Fix release workflow to use uv build

## [0.1.1] - 2026-07-09

### Added

- Initial project setup with migration, updater, and CLI functionalities for wiki engine
- Agent prompt template and wiki refresh functionality
- Documentation and README
