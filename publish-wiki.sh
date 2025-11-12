#!/bin/bash

# Script to publish wiki pages to GitHub Wiki
# Usage: ./publish-wiki.sh

set -e

WIKI_DIR=".github/wiki"
WIKI_REPO="https://github.com/andrea-ragalzi/document-intelligent-hub.wiki.git"
TEMP_DIR="/tmp/wiki-temp"

echo "📚 Publishing Wiki to GitHub..."

# Check if wiki directory exists
if [ ! -d "$WIKI_DIR" ]; then
    echo "❌ Wiki directory not found: $WIKI_DIR"
    exit 1
fi

# Remove temp directory if exists
rm -rf "$TEMP_DIR"

echo "🔄 Cloning wiki repository..."
git clone "$WIKI_REPO" "$TEMP_DIR" 2>/dev/null || {
    echo "⚠️  Wiki not initialized yet. Please:"
    echo "   1. Go to https://github.com/andrea-ragalzi/document-intelligent-hub"
    echo "   2. Click 'Settings' → Enable 'Wikis'"
    echo "   3. Go to 'Wiki' tab → Create first page"
    echo "   4. Run this script again"
    exit 1
}

echo "📝 Copying wiki pages..."
cp "$WIKI_DIR"/*.md "$TEMP_DIR/"

cd "$TEMP_DIR"

echo "🔍 Checking for changes..."
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to publish"
    cd -
    rm -rf "$TEMP_DIR"
    exit 0
fi

echo "📤 Committing and pushing changes..."
git add .
git commit -m "Update wiki documentation - $(date +'%Y-%m-%d %H:%M:%S')"
git push origin master

cd -
rm -rf "$TEMP_DIR"

echo "✅ Wiki published successfully!"
echo "🌐 View at: https://github.com/andrea-ragalzi/document-intelligent-hub/wiki"
