#!/usr/bin/env python3
"""Generate a practical migration plan for Azure DevOps project moves."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import quote, urlparse


def _normalize_org_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid organization URL: {raw_url}")
    return raw_url.rstrip("/")


def _read_repos(args: argparse.Namespace) -> list[str]:
    repos: list[str] = []

    if args.repos:
        repos.extend(part.strip() for part in args.repos.split(",") if part.strip())

    if args.repos_file:
        file_path = Path(args.repos_file)
        if not file_path.is_file():
            raise ValueError(f"Repository list file was not found: {file_path}")
        repos.extend(line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip())

    unique_repos: list[str] = []
    seen: set[str] = set()
    for repo in repos:
        if repo not in seen:
            seen.add(repo)
            unique_repos.append(repo)

    return unique_repos


def _build_repo_url(org_url: str, project_name: str, repo_name: str) -> str:
    return f"{org_url}/{quote(project_name)}/_git/{quote(repo_name)}"


def _safe_temp_repo_name(repo_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", repo_name)


def build_plan(source_org_url: str, source_project: str, target_org_url: str, target_project: str, repos: list[str]) -> str:
    lines = [
        "# Azure DevOps Migration Plan",
        "",
        "## Scope",
        f"- Source organization: `{source_org_url}`",
        f"- Source project: `{source_project}`",
        f"- Target organization: `{target_org_url}`",
        f"- Target project: `{target_project}`",
        "",
        "## Prerequisites",
        "- Azure DevOps CLI extension installed: `az extension add --name azure-devops`",
        "- Authenticated in Azure CLI (`az login`) with access to both organizations",
        "",
        "## Suggested Commands",
        "```bash",
        f"az devops configure --defaults organization={target_org_url} project=\"{target_project}\"",
        f"az devops project create --name \"{target_project}\" --organization \"{target_org_url}\"",
        "```",
        "",
    ]

    if not repos:
        lines.extend(
            [
                "## Repositories",
                "No repositories were provided. Re-run with `--repos` or `--repos-file` to generate repository mirroring commands.",
                "",
            ]
        )
    else:
        lines.extend(["## Repository Mirroring Commands", ""])
        for repo in repos:
            safe_repo = _safe_temp_repo_name(repo)
            source_url = _build_repo_url(source_org_url, source_project, repo)
            target_url = _build_repo_url(target_org_url, target_project, repo)
            lines.extend(
                [
                    f"### {repo}",
                    "```bash",
                    f"git clone --mirror \"{source_url}\" \"/tmp/{safe_repo}.git\"",
                    f"git -C \"/tmp/{safe_repo}.git\" push --mirror \"{target_url}\"",
                    f"rm -rf \"/tmp/{safe_repo}.git\"",
                    "```",
                    "",
                ]
            )

    lines.extend(
        [
            "## Next Steps",
            "- Validate branch policies and permissions in the target project",
            "- Recreate service connections, pipelines, variable groups, and agent pools",
            "- Run smoke tests in target pipelines before cutover",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an Azure DevOps project migration plan.")
    parser.add_argument("--source-org-url", required=True, help="Source Azure DevOps organization URL.")
    parser.add_argument("--source-project", required=True, help="Source project name.")
    parser.add_argument("--target-org-url", required=True, help="Target Azure DevOps organization URL.")
    parser.add_argument("--target-project", required=True, help="Target project name.")
    parser.add_argument(
        "--repos",
        help="Comma-separated repository names to include in the migration plan.",
    )
    parser.add_argument(
        "--repos-file",
        help="Path to a file containing repository names (one per line).",
    )
    parser.add_argument("--output", help="Optional output file path for the generated plan.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    source_org = _normalize_org_url(args.source_org_url)
    target_org = _normalize_org_url(args.target_org_url)
    repos = _read_repos(args)

    plan = build_plan(source_org, args.source_project, target_org, args.target_project, repos)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plan, encoding="utf-8")
        print(f"Migration plan written to {output_path}")
    else:
        print(plan)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
