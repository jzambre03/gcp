#!/bin/bash

# Script to verify what's actually in a golden/drift branch
# Usage: ./verify_branch_contents.sh <repo_url> <branch_name>

REPO_URL="$1"
BRANCH_NAME="$2"

if [ -z "$REPO_URL" ] || [ -z "$BRANCH_NAME" ]; then
    echo "Usage: $0 <repo_url> <branch_name>"
    echo "Example: $0 https://gitlab.verizon.com/user/repo.git golden_prod_20251015_123456_abc123"
    exit 1
fi

echo "=========================================="
echo "Verifying branch contents"
echo "Repository: $REPO_URL"
echo "Branch: $BRANCH_NAME"
echo "=========================================="
echo ""

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "📁 Cloning to: $TEMP_DIR"
echo ""

# Clone only the specific branch (shallow)
git clone --single-branch --branch "$BRANCH_NAME" --depth 1 "$REPO_URL" "$TEMP_DIR" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Failed to clone branch $BRANCH_NAME"
    rm -rf "$TEMP_DIR"
    exit 1
fi

cd "$TEMP_DIR"

echo "=========================================="
echo "1. FILES IN COMMIT (Git tree)"
echo "=========================================="
echo "Running: git ls-tree -r --name-only HEAD"
echo ""

git ls-tree -r --name-only HEAD > /tmp/git_tree_files.txt
TREE_FILE_COUNT=$(wc -l < /tmp/git_tree_files.txt | tr -d ' ')

echo "Total files in Git tree: $TREE_FILE_COUNT"
echo ""
echo "First 20 files:"
head -20 /tmp/git_tree_files.txt
echo ""

# Check for .git/ in tree
GIT_DIR_IN_TREE=$(grep -c "^\.git/" /tmp/git_tree_files.txt)
if [ "$GIT_DIR_IN_TREE" -gt 0 ]; then
    echo "🚨 WARNING: Found .git/ files in Git tree!"
    grep "^\.git/" /tmp/git_tree_files.txt | head -10
else
    echo "✅ No .git/ files in Git tree (correct)"
fi
echo ""

echo "=========================================="
echo "2. FILES IN WORKING DIRECTORY"
echo "=========================================="
echo "Running: find . -type f (excluding .git/)"
echo ""

find . -type f | grep -v "^\./.git/" | sed 's|^\./||' > /tmp/working_dir_files.txt
WORKING_FILE_COUNT=$(wc -l < /tmp/working_dir_files.txt | tr -d ' ')

echo "Total files in working directory: $WORKING_FILE_COUNT"
echo ""
echo "First 20 files:"
head -20 /tmp/working_dir_files.txt
echo ""

echo "=========================================="
echo "3. FILE TYPE BREAKDOWN (in Git tree)"
echo "=========================================="
echo ""

echo "YAML files:"
grep -E '\.(yml|yaml)$' /tmp/git_tree_files.txt | wc -l | tr -d ' '

echo "Properties files:"
grep -E '\.properties$' /tmp/git_tree_files.txt | wc -l | tr -d ' '

echo "XML files:"
grep -E '\.xml$' /tmp/git_tree_files.txt | wc -l | tr -d ' '

echo "Java files:"
grep -E '\.java$' /tmp/git_tree_files.txt | wc -l | tr -d ' '

echo "Python files:"
grep -E '\.py$' /tmp/git_tree_files.txt | wc -l | tr -d ' '

echo ""

echo "=========================================="
echo "4. CHECK FOR UNEXPECTED FILES"
echo "=========================================="
echo ""

# Check for source code files
SOURCE_CODE_COUNT=$(grep -E '\.(java|py|js|ts|go|rb|php|cpp|c|h)$' /tmp/git_tree_files.txt | wc -l | tr -d ' ')
if [ "$SOURCE_CODE_COUNT" -gt 0 ]; then
    echo "⚠️  Found $SOURCE_CODE_COUNT source code files (unexpected for config-only branch):"
    grep -E '\.(java|py|js|ts|go|rb|php|cpp|c|h)$' /tmp/git_tree_files.txt | head -10
else
    echo "✅ No source code files found (good)"
fi
echo ""

# Check for .git/ files in working directory (should exist but not tracked)
if [ -d ".git" ]; then
    echo "✅ .git/ directory exists in working directory (normal - Git metadata)"
    GIT_DIR_SIZE=$(du -sh .git 2>/dev/null | cut -f1)
    echo "   Size: $GIT_DIR_SIZE"
else
    echo "❌ .git/ directory missing (shouldn't happen)"
fi
echo ""

echo "=========================================="
echo "5. COMMIT INFORMATION"
echo "=========================================="
echo ""

echo "Commit message:"
git log -1 --pretty=format:"%B" | head -5
echo ""
echo ""

echo "Commit stats:"
git show --stat HEAD | tail -5
echo ""

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo "Files in Git tree (what will be cloned):  $TREE_FILE_COUNT"
echo "Files in working directory:                $WORKING_FILE_COUNT"
echo ".git/ files in Git tree:                   $GIT_DIR_IN_TREE"
echo "Source code files:                         $SOURCE_CODE_COUNT"
echo ""

if [ "$TREE_FILE_COUNT" -lt 100 ] && [ "$GIT_DIR_IN_TREE" -eq 0 ] && [ "$SOURCE_CODE_COUNT" -eq 0 ]; then
    echo "✅ Branch looks like a valid config-only branch!"
else
    echo "⚠️  Branch might contain more than just config files"
fi

# Cleanup
cd /
rm -rf "$TEMP_DIR"
rm -f /tmp/git_tree_files.txt /tmp/working_dir_files.txt

echo ""
echo "Done!"

