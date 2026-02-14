#!/bin/bash
# Script to create a new GitHub repository and push this project

REPO_NAME="sales-analytics-dashboard"
GITHUB_USER="ClaireInglehart"
DESCRIPTION="Sales Analytics Dashboard - Analyze business-product category relationships to identify growth opportunities"

echo "🚀 Creating New GitHub Repository"
echo "=================================="
echo ""
echo "Repository name: $REPO_NAME"
echo "Description: $DESCRIPTION"
echo ""
echo "📋 Please follow these steps:"
echo ""
echo "1. Go to: https://github.com/new"
echo "2. Repository name: $REPO_NAME"
echo "3. Description: $DESCRIPTION"
echo "4. Choose Public or Private"
echo "5. ⚠️  DO NOT check 'Initialize with README'"
echo "6. ⚠️  DO NOT check 'Add .gitignore'"
echo "7. ⚠️  DO NOT check 'Choose a license'"
echo "8. Click 'Create repository'"
echo ""
read -p "Press Enter once you've created the repository on GitHub..."

echo ""
echo "🔄 Adding new remote..."
git remote remove new-origin 2>/dev/null
git remote add new-origin https://github.com/$GITHUB_USER/$REPO_NAME.git

echo ""
echo "📤 Pushing all branches to new repository..."
git push new-origin sales-analytics-dashboard
git push new-origin main 2>/dev/null || echo "Note: main branch doesn't exist locally"

echo ""
echo "✅ Done! Your new repository is at:"
echo "https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "To switch to the new repository as your main remote:"
echo "  git remote set-url origin https://github.com/$GITHUB_USER/$REPO_NAME.git"
echo "  git remote remove new-origin"

