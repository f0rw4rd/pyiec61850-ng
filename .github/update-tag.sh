#!/bin/bash
set -e

echo "Deleting existing v1.6.0 tag locally and remotely..."

# Delete the tag locally (ignore errors if it doesn't exist)
git tag -d v1.6.0 2>/dev/null || echo "Local tag v1.6.0 doesn't exist"

# Delete the tag remotely (ignore errors if it doesn't exist)
git push --delete origin v1.6.0 2>/dev/null || echo "Remote tag v1.6.0 doesn't exist or was already deleted"

# Wait a moment to ensure GitHub has processed the tag deletion
echo "Waiting 3 seconds for GitHub to process..."
sleep 3

# Create a new tag
echo "Creating new v1.6.0 tag..."
git tag -a v1.6.0 -m "Fixed shared library inclusion in wheel package"

# Push the new tag
echo "Pushing new tag to remote..."
git push origin v1.6.0

echo "Done! Tag v1.6.0 has been recreated and pushed."
echo "GitHub Actions workflow should now be triggered."