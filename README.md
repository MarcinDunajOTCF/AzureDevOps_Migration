# AzureDevOps_Migration

Minimal helper for planning Azure DevOps project migration between organizations.

## Usage

```bash
python3 migration_tool.py \
  --source-org-url https://dev.azure.com/sourceOrg \
  --source-project SourceProject \
  --target-org-url https://dev.azure.com/targetOrg \
  --target-project TargetProject \
  --repos repo1,repo2 \
  --output /tmp/migration-plan.md
```

The generated Markdown plan includes:
- target project creation command
- mirror migration commands for each repository
- short post-migration checklist
