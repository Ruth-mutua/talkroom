#!/bin/bash
set -e

echo "🧪 Running SecureTalkroom Test Suite"
echo "================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   Consider activating your virtual environment first"
fi

# Set test environment variables
export PYTHONPATH="${PYTHONPATH}:${PWD}"
export ENVIRONMENT=testing
export DEBUG=True

# Use test database
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_secure_talkroom"
export REDIS_URL="redis://localhost:6379/1"

# Generate a test secret key
export SECRET_KEY="test-secret-key-for-testing-only"

# Run tests with coverage
echo "🔍 Running tests with coverage..."
python -m pytest \
    tests/ \
    -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    --cov-fail-under=80 \
    --tb=short

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
    exit 1
fi

# Run linting
echo "🔍 Running code quality checks..."

# Black formatting check
echo "📝 Checking code formatting with black..."
black --check app/ tests/
if [ $? -ne 0 ]; then
    echo "❌ Code formatting issues found. Run 'black app/ tests/' to fix."
    exit 1
fi

# Flake8 linting
echo "🔍 Running flake8 linting..."
flake8 app/ tests/
if [ $? -ne 0 ]; then
    echo "❌ Linting issues found."
    exit 1
fi

# MyPy type checking
echo "🔍 Running mypy type checking..."
mypy app/
if [ $? -ne 0 ]; then
    echo "❌ Type checking issues found."
    exit 1
fi

# isort import sorting check
echo "🔍 Checking import sorting with isort..."
isort --check-only app/ tests/
if [ $? -ne 0 ]; then
    echo "❌ Import sorting issues found. Run 'isort app/ tests/' to fix."
    exit 1
fi

echo "✅ All code quality checks passed!"

# Generate coverage report
echo "📊 Coverage report generated at htmlcov/index.html"

echo "🎉 All tests and quality checks completed successfully!" 