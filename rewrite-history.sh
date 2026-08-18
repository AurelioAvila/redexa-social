#!/bin/bash
# Run this from the social-dashboard repo root, in Git Bash.
# A full backup already exists at:
#   C:\Users\aurel\social-dashboard-full-history-backup-20260818-111902.bundle
set -e

echo "Current branch/status:"
git status --short
git branch --show-current

echo
echo "Creating fresh orphan history..."
git checkout --orphan license-reset-tmp
git add -A
git commit -m "Initial commit under the proprietary license

Git history before this point contained the project as it existed
under the MIT License (through v1.4.0) and has been removed: MIT
permits redistribution of code obtained under it, which is now in
direct tension with a paid-plans product. This is not retroactive -
copies already taken under MIT keep that grant - it only stops new
clones of the old source through this repository. See LICENSE and
the License section of README.md for the full explanation."

echo
echo "Replacing master with the new history..."
git branch -D master
git branch -m master

echo
echo "Deleting old version tags locally..."
for t in v1.1.0 v1.2.0 v1.2.1 v1.2.2 v1.2.3 v1.2.4 v1.2.5 v1.2.6 v1.2.7 v1.2.8 v1.2.9 v1.3.0 v1.3.1 v1.3.2 v1.3.3 v1.3.4 v1.4.0; do
  git tag -d "$t" 2>/dev/null || true
done

echo
echo "Force-pushing new history to origin/master..."
git push origin master --force

echo
echo "Deleting old version tags on origin..."
for t in v1.1.0 v1.2.0 v1.2.1 v1.2.2 v1.2.3 v1.2.4 v1.2.5 v1.2.6 v1.2.7 v1.2.8 v1.2.9 v1.3.0 v1.3.1 v1.3.2 v1.3.3 v1.3.4 v1.4.0; do
  git push origin ":refs/tags/$t" 2>/dev/null || true
done

echo
echo "Done. Verifying:"
git log --oneline
echo "Tags remaining (should be empty):"
git tag -l
