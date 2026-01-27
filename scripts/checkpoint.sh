#!/usr/bin/env bash
set -euo pipefail

ts="$(date +"%Y-%m-%d_%H%M")"
out="docs/checkpoints/${ts}_checkpoint.md"

git_status="$(git status --porcelain=v1 || true)"
git_head="$(git rev-parse --short HEAD 2>/dev/null || echo "no-commits")"
git_branch="$(git branch --show-current 2>/dev/null || echo "unknown")"

cat > "$out" <<EOF
# Checkpoint: $ts

## Repo state
- branch: $git_branch
- head: $git_head

## Working tree
\`\`\`
$git_status
\`\`\`

## What changed
- (fill this in)

## Verification
- (paste output summary from \`make verify\`)

## Next steps
- (fill this in)
EOF

cp "$out" docs/CHECKPOINT.md
echo "Wrote: $out"
echo "Updated: docs/CHECKPOINT.md"
