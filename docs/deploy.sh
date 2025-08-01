#!/bin/bash
# Build and deploy documentation to gh-pages branch

# Exit on error
set -e

# Change to the docs directory
DOCS_DIR="$(realpath "$(dirname "$0")")"
cd "$DOCS_DIR" || exit 1

echo "Starting documentation deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

CURRENT_BRANCH=$(git branch --show-current)
print_status "Preparing deployment from master branch..."

# Stash any uncommitted changes before switching to master
if ! git diff --quiet || ! git diff --cached --quiet; then
    print_status "Stashing uncommitted changes..."
    git stash push -m "Auto-stash before gh-pages deployment at $(date)"
    STASHED=true
else
    STASHED=false
fi

cleanup() {
    # Change to the docs directory to clean up
    cd "$DOCS_DIR" || exit 1

    # Clean up gh-pages worktree if it exists
    if [ -n "$GHPAGES_WORKTREE" ] && [ -d "$GHPAGES_WORKTREE" ]; then
        print_status "Cleaning up gh-pages worktree..."
        git worktree remove "$GHPAGES_WORKTREE" --force 2>/dev/null || rm -rf "$GHPAGES_WORKTREE"
    fi

    # If we're not on the original branch and it exists, switch back
    if [ -n "$CURRENT_BRANCH" ] && [ "$(git branch --show-current)" != "$CURRENT_BRANCH" ]; then
        git checkout "$CURRENT_BRANCH" 2>/dev/null || true
    fi

    # Restore stashed changes if any were stashed
    if [ "$STASHED" = true ]; then
        print_status "Restoring stashed changes..."
        git stash pop 2>/dev/null || print_warning "Could not restore stashed changes"
    fi
}

trap cleanup EXIT

if [ "$CURRENT_BRANCH" != "master" ]; then
    print_status "Switching to master branch..."
    git checkout master
fi

# Get master commit after switching
MASTER_COMMIT=$(git rev-parse HEAD)
print_status "Building documentation from master branch commit: ${MASTER_COMMIT:0:8}"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    # Create virtual environment if it doesn't exist
    print_status "Creating virtual environment..."
    uv venv && source .venv/bin/activate && uv sync
else
    source .venv/bin/activate
fi

# Build documentation from master branch
print_status "Building documentation..."
make html SPHINXOPTS=-E

# Check if build/html directory exists
if [ ! -d "build/html" ]; then
    print_error "build/html directory not found"
    exit 1
fi

print_success "Documentation built successfully from master branch"
print_status "Preparing gh-pages worktree..."

# Create a temporary worktree for gh-pages branch
GHPAGES_WORKTREE=$(mktemp -d)

# Create or checkout gh-pages branch in worktree
print_status "Creating gh-pages worktree..."
if git show-ref --verify --quiet refs/heads/gh-pages; then
    git worktree add "$GHPAGES_WORKTREE" gh-pages
else
    git worktree add --orphan "$GHPAGES_WORKTREE" -b gh-pages
fi

# Work in the gh-pages worktree
cd "$GHPAGES_WORKTREE"

# Copy the built documentation to gh-pages worktree
print_status "Copying built documentation to gh-pages worktree..."
cp -r "$DOCS_DIR"/build/html/* .

# Create .nojekyll file to bypass GitHub's Jekyll processing
if [ ! -f ".nojekyll" ]; then
    echo "" >.nojekyll
fi

# Add all files to git
git add .

# Check if there are any changes to commit
if git diff --cached --quiet; then
    print_warning "No changes to commit"
else
    # Commit the changes
    print_status "Committing changes..."
    git commit -m "Deploy documentation to GitHub Pages

    Built from branch: master
    Build date: $(date)
    Source commit: $MASTER_COMMIT"

    print_success "Deployment process completed."
    print_status "Now you can push to remote gh-pages branch by doing:"
    print_status "git push origin gh-pages"
    print_status "GitHub Pages will be available at: https://$(git config --get remote.origin.url | sed 's/.*github\.com[:/]\([^/]*\)\/\([^/]*\)\.git.*/\1.github.io\/\2/')"
fi
