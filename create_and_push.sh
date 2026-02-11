#!/bin/bash
# Script to create GitHub repo and push code

REPO_NAME="sales-analytics-dashboard"
GITHUB_USER="ClaireInglehart"

echo "Creating GitHub repository: $REPO_NAME"
echo ""
echo "Please follow these steps:"
echo "1. Go to: https://github.com/new"
echo "2. Repository name: $REPO_NAME"
echo "3. Description: Sales Analytics Dashboard - Analyze business-product category relationships"
echo "4. Choose Public or Private"
echo "5. DO NOT check 'Initialize with README'"
echo "6. Click 'Create repository'"
echo ""
read -p "Press Enter once you've created the repository on GitHub..."

echo ""
echo "Adding remote and pushing code..."
git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git 2>/dev/null || git remote set-url origin https://github.com/$GITHUB_USER/$REPO_NAME.git

echo "Pushing to GitHub..."
git push -u origin sales-analytics-dashboard

echo ""
echo "✅ Done! Your repository is at:"
echo "https://github.com/$GITHUB_USER/$REPO_NAME/tree/sales-analytics-dashboard"

