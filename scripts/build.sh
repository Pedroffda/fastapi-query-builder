#!/bin/bash

# Build script for FastAPI Query Builder

set -e

echo "🚀 Building FastAPI Query Builder..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install --upgrade pip
pip install build twine

# Run tests
echo "🧪 Running tests..."
pytest --cov=query_builder --cov-report=term-missing

# Run linting
echo "🔍 Running linting..."
black --check .
isort --check-only .
flake8 .
mypy .

# Build package
echo "🔨 Building package..."
python -m build

# Check package
echo "✅ Checking package..."
twine check dist/*

echo "🎉 Build completed successfully!"
echo "📦 Package files:"
ls -la dist/

echo ""
echo "To publish to TestPyPI:"
echo "twine upload --repository testpypi dist/*"
echo ""
echo "To publish to PyPI:"
echo "twine upload dist/*"
