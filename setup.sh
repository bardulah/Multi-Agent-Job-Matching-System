#!/bin/bash
#
# Setup script for Multi-Agent Job Application System
#

set -e  # Exit on error

echo "=================================="
echo "Job Application System Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/jobs
mkdir -p data/cvs
mkdir -p data/history
mkdir -p data/review
mkdir -p logs
mkdir -p templates
mkdir -p config
echo "✓ Directories created"

# Copy example files
echo ""
echo "Setting up configuration files..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file (please edit with your credentials)"
else
    echo "✓ .env file already exists"
fi

if [ ! -f "config.yaml" ]; then
    cp config.example.yaml config.yaml
    echo "✓ Created config.yaml file (please customize)"
else
    echo "✓ config.yaml already exists"
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x run_daily.sh
chmod +x setup.sh
echo "✓ Scripts are now executable"

# Create a sample CV template note
if [ ! -f "templates/README.txt" ]; then
    cat > templates/README.txt << 'EOF'
CV Template Directory
====================

Place your CV template file here as: cv_template.docx

The system will use this template as a base for generating tailored CVs.

If no template is provided, the system will generate CVs from scratch using your
configuration in config.yaml.

Template Requirements:
- Format: Microsoft Word (.docx)
- Name: cv_template.docx
- Should include your personal information, experience, education, and skills
- The system will extract and enhance this information based on job requirements
EOF
    echo "✓ Created template directory readme"
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your API keys and credentials:"
echo "   nano .env"
echo ""
echo "2. Customize config.yaml with your preferences and skills:"
echo "   nano config.yaml"
echo ""
echo "3. (Optional) Add your CV template to templates/cv_template.docx"
echo ""
echo "4. Test the configuration:"
echo "   python orchestrator.py --test"
echo ""
echo "5. Run the system manually:"
echo "   python orchestrator.py"
echo ""
echo "6. Set up daily scheduling (choose one):"
echo "   - Cron: Add run_daily.sh to your crontab"
echo "   - Python scheduler: python schedule.py"
echo ""
echo "For detailed instructions, see README.md"
echo ""
