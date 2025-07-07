#!/bin/bash

echo "🔧 Setting up Terminal Dashboard for GitHub..."

# Initialize git repository if not already done
if [ ! -d ".git" ]; then
    echo "📂 Initializing Git repository..."
    git init
fi

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Odoo credentials before running the application"
fi

# Add all files to git
echo "📦 Adding files to Git..."
git add .

# Create initial commit if no commits exist
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "📝 Creating initial commit..."
    git commit -m "Initial commit: Terminal Dashboard v0.1.0

Features:
- Real-time dashboard for terminal operations
- Odoo v17 integration via External API
- Vue 3 frontend with Tailwind CSS
- FastAPI backend with async support
- Docker support and CI/CD pipeline
- Comprehensive documentation"
fi

echo ""
echo "✅ Git setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a new repository on GitHub"
echo "2. Add the remote origin:"
echo "   git remote add origin https://github.com/your-username/terminal-dashboard.git"
echo "3. Push to GitHub:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4. Edit .env with your Odoo credentials"
echo "5. Run ./setup.sh to install dependencies"
echo "6. Run ./start.sh to start the application"
echo ""
echo "📚 Documentation is ready in README.md"
echo "🔧 CI/CD pipeline is configured in .github/workflows/"
echo "🐳 Docker setup is available with docker-compose.yml"
