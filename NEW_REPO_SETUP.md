# Create New GitHub Repository - Quick Guide

## Option 1: Use the Automated Script (Recommended)

1. **Create the repository on GitHub:**
   - Go to: https://github.com/new
   - Repository name: `sales-analytics-dashboard`
   - Description: `Sales Analytics Dashboard - Analyze business-product category relationships to identify growth opportunities`
   - Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license
   - Click "Create repository"

2. **Run the script:**
   ```bash
   cd /Users/claire/sales-analytics
   ./create_new_repo.sh
   ```
   Follow the prompts and enter your GitHub credentials when asked.

## Option 2: Manual Setup

After creating the repository on GitHub:

```bash
cd /Users/claire/sales-analytics

# Add new remote
git remote add new-repo https://github.com/ClaireInglehart/sales-analytics-dashboard.git

# Push all branches
git push new-repo sales-analytics-dashboard
git push new-repo main

# Make it your main remote (optional)
git remote set-url origin https://github.com/ClaireInglehart/sales-analytics-dashboard.git
git remote remove new-repo
```

## What Will Be Pushed

- ✅ All source code files
- ✅ Configuration files
- ✅ Sample data
- ✅ Documentation
- ✅ Setup scripts
- ✅ Both branches: `main` and `sales-analytics-dashboard`

## Repository URL

After setup, your repository will be at:
**https://github.com/ClaireInglehart/sales-analytics-dashboard**

