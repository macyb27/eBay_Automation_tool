#!/bin/bash

# 🚀 eBay Automation Tool - GitHub Repository Setup & Push Script
# Automated deployment to GitHub for Macyb27

echo "🚀 eBay Automation Tool - GitHub Deployment"
echo "============================================"
echo ""

# Repository Configuration
GITHUB_USER="Macyb27"
REPO_NAME="eBay_Automation_tool"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo "📊 Repository Information:"
echo "User: ${GITHUB_USER}"
echo "Repository: ${REPO_NAME}"
echo "URL: ${REPO_URL}"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository!"
    echo "Please run 'git init' first"
    exit 1
fi

# Check if we have commits
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "❌ Error: No commits found!"
    echo "Please commit your changes first"
    exit 1
fi

echo "✅ Git repository is ready"
echo "✅ Commits available: $(git rev-list --count HEAD)"
echo "✅ Total files: $(git ls-files | wc -l)"
echo ""

# Check if remote origin already exists
if git remote get-url origin >/dev/null 2>&1; then
    echo "🔗 Remote 'origin' already exists: $(git remote get-url origin)"
    echo "Updating remote URL..."
    git remote set-url origin "${REPO_URL}"
else
    echo "🔗 Adding remote origin..."
    git remote add origin "${REPO_URL}"
fi

echo "✅ Remote origin configured: ${REPO_URL}"
echo ""

# Display current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📋 Current branch: ${CURRENT_BRANCH}"
echo ""

# Show what will be pushed
echo "📦 Files to be pushed:"
git ls-files | head -10
echo "... and $(( $(git ls-files | wc -l) - 10 )) more files"
echo ""

echo "🔍 Latest commit:"
git log --oneline -1
echo ""

echo "⚡ Repository Statistics:"
echo "Python files: $(find . -name '*.py' | wc -l)"
echo "Lines of Python code: $(find . -name '*.py' -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo 'N/A')"
echo "Docker files: $(find . -name 'Dockerfile*' -o -name 'docker-compose*.yml' | wc -l)"
echo "Documentation files: $(find . -name '*.md' | wc -l)"
echo ""

echo "🎯 Key Features in Repository:"
echo "✅ Ultra-Fast AI Vision Analysis (GPT-4V)"
echo "✅ Real-time eBay Market Research" 
echo "✅ Automated Content Generation"
echo "✅ High-Performance FastAPI Backend"
echo "✅ Production-Ready Docker Deployment"
echo "✅ Comprehensive Testing Suite"
echo "✅ One-Click Setup Script"
echo ""

echo "🚀 READY TO PUSH TO GITHUB!"
echo ""
echo "⚠️  IMPORTANT INSTRUCTIONS:"
echo ""
echo "1. First, create the GitHub repository:"
echo "   - Go to: https://github.com/new"
echo "   - Repository name: eBay_Automation_tool"
echo "   - Description: Ultra-Fast AI-Powered eBay Listing Generator"
echo "   - Visibility: Public (recommended for portfolio)"
echo "   - DO NOT initialize with README, .gitignore, or license"
echo "   - Click 'Create repository'"
echo ""
echo "2. Then run the push command:"
echo "   git push -u origin ${CURRENT_BRANCH}"
echo ""
echo "3. After successful push:"
echo "   - Repository will be available at: ${REPO_URL}"
echo "   - Set up GitHub Pages for documentation (optional)"
echo "   - Configure repository settings and description"
echo "   - Add topics/tags: python, fastapi, ai, ebay, automation, docker"
echo ""

# Prepare the push command but don't execute automatically
echo "💡 Quick Push Commands (run after creating GitHub repo):"
echo ""
echo "git push -u origin ${CURRENT_BRANCH}"
echo ""
echo "# If you want to set main as default branch:"
echo "git branch -M main"
echo "git push -u origin main"
echo ""

echo "✅ Setup complete! Repository is ready for GitHub."
echo "📂 Local repository size: $(du -sh . | cut -f1)"
echo ""
echo "🎉 After pushing, your eBay Automation Tool will be publicly available!"
echo "Perfect for your portfolio and showcasing your AI development skills! 🚀"