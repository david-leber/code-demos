# Testing Documentation

## Test Suite Overview

The face-swap-app has comprehensive test coverage with **92% code coverage** across unit tests, integration tests, and end-to-end smoke tests.

## Test Results

```
✅ 26 tests passed
⏭️  3 tests skipped (FFmpeg-dependent)
📊 92% code coverage
```

## Running Tests

### Quick Test Run

```bash
# Activate UV environment
source .venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_app.py

# Run specific test
pytest tests/test_app.py::TestHealthEndpoint::test_health_check
```

### Run Tests with Coverage

```bash
# Coverage report in terminal
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Structure

### 1. Unit Tests (`test_app.py`)

Tests for Flask application routes and endpoints:

- ✅ **Health endpoint** - API health checks
- ✅ **Index route** - Main page rendering
- ✅ **Photo upload** - File upload and validation
  - Valid images with faces
  - Images without faces
  - Invalid file types
  - Missing files
- ✅ **Video generation** - Video creation workflow
  - Missing parameters
  - Non-existent files
  - Successful generation (when FFmpeg available)
- ✅ **Download endpoint** - Video file downloads
- ✅ **File validation** - Allowed file extensions

**Coverage: 14 tests**

### 2. Face Detection Tests (`test_face_detection.py`)

Tests for MediaPipe face detection functionality:

- ✅ **Face detection** - Detecting faces in images
  - Valid images with faces
  - Images without faces
  - Non-existent files
  - Various image qualities
- ✅ **Face extraction** - Extracting and validating face regions
  - Face dimensions
  - Color format (BGR)
  - Padding application

**Coverage: 7 tests**

### 3. End-to-End Smoke Tests (`test_e2e_smoke.py`)

Complete workflow tests with realistic scenarios:

- ✅ **Complete workflow** - Upload → Select → Generate → Download
- ✅ **Edge cases** - Low quality images, multiple uploads
- ✅ **Error handling** - Invalid sequences, missing files
- ✅ **System health** - Dependencies, directories, FFmpeg

**Coverage: 8 tests**

## Test Fixtures

Located in `tests/conftest.py`:

### Synthetic Test Images

- `sample_face_image` - Realistic synthetic face for testing
- `sample_no_face_image` - Landscape image without face
- `sample_template_video` - Test video template (2 seconds)

### Flask Test Client

- `app` - Configured Flask app for testing
- `client` - Test client for making requests
- `runner` - CLI runner for command testing

## Code Coverage Breakdown

```
Name     Stmts   Miss  Cover   Missing
--------------------------------------
app.py     114      9    92%   92, 108-133, 140, 218
```

### Covered Areas (92%)

- ✅ Flask route handlers
- ✅ File upload and validation
- ✅ Face detection logic
- ✅ Error handling
- ✅ Helper functions

### Not Covered (8%)

- ⏭️ Video creation function (requires FFmpeg)
- ⏭️ Some error paths
- ⏭️ Main app execution (manual testing)

**Note:** Video processing is tested in integration tests but skipped in CI when FFmpeg is unavailable.

## Linting

### Ruff Configuration

The project uses **Ruff** for fast, comprehensive linting.

```bash
# Check for linting issues
ruff check app.py tests/

# Auto-fix issues
ruff check --fix app.py tests/

# Format code
ruff format app.py tests/
```

### Enabled Rules

- **E/W** - pycodestyle (PEP 8 compliance)
- **F** - pyflakes (error detection)
- **I** - isort (import sorting)
- **B** - flake8-bugbear (bug detection)
- **C4** - flake8-comprehensions (better comprehensions)
- **UP** - pyupgrade (modern Python syntax)

### Linting Results

```
✅ All checks passed!
```

All code passes linting with zero errors or warnings.

## Environment Management

The project uses **UV** for fast, reliable dependency management.

### Setup

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e ".[dev]"

# Or install directly
uv pip install flask opencv-python mediapipe pillow numpy werkzeug pytest pytest-cov pytest-flask ruff
```

### Benefits of UV

- ⚡ **Fast**: 10-100x faster than pip
- 🔒 **Reliable**: Consistent dependency resolution
- 📦 **Simple**: Single tool for all Python package management

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install FFmpeg
        run: sudo apt-get update && sudo apt-get install -y ffmpeg

      - name: Install dependencies
        run: |
          uv venv
          source .venv/bin/activate
          uv pip install -e ".[dev]"

      - name: Lint with ruff
        run: |
          source .venv/bin/activate
          ruff check app.py tests/

      - name: Run tests
        run: |
          source .venv/bin/activate
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Writing New Tests

### Test Template

```python
import pytest


class TestNewFeature:
    """Test description"""

    def test_basic_functionality(self, client):
        """Test basic case"""
        response = client.get('/new-endpoint')

        assert response.status_code == 200
        assert b'expected content' in response.data

    def test_error_case(self, client):
        """Test error handling"""
        response = client.get('/new-endpoint?invalid=param')

        assert response.status_code == 400
```

### Best Practices

1. **Clear test names** - Describe what is being tested
2. **One assertion per test** - Keep tests focused
3. **Use fixtures** - Reuse common setup code
4. **Test edge cases** - Not just happy paths
5. **Mock external dependencies** - Isolate unit tests

## Troubleshooting Tests

### Common Issues

**Issue: "FFmpeg not found"**
```bash
# Install FFmpeg
# Mac:
brew install ffmpeg

# Ubuntu:
sudo apt install ffmpeg

# Windows:
choco install ffmpeg
```

**Issue: "ModuleNotFoundError: No module named 'app'"**
```bash
# Make sure you're in the project directory
cd face-swap-app

# Activate virtual environment
source .venv/bin/activate
```

**Issue: "Face detection tests failing"**
```bash
# Verify MediaPipe is installed correctly
python -c "import mediapipe; print('OK')"

# Reinstall if needed
uv pip install --force-reinstall mediapipe
```

## Test Maintenance

### Adding New Tests

1. Create test file in `tests/`
2. Import necessary fixtures from `conftest.py`
3. Write test class and methods
4. Run tests: `pytest tests/test_new_feature.py`
5. Check coverage: `pytest --cov=app`

### Updating Fixtures

Edit `tests/conftest.py` to add new fixtures:

```python
@pytest.fixture
def new_fixture():
    """Fixture description"""
    # Setup
    data = create_test_data()

    yield data

    # Teardown
    cleanup(data)
```

## Performance

Test suite runs in **~1 second** on average:

- Unit tests: ~0.5s
- Integration tests: ~0.4s
- Smoke tests: ~0.3s

Fast test execution enables rapid development iteration.

## Summary

✅ **Comprehensive**: 29 tests covering all major functionality
✅ **Fast**: Complete suite runs in ~1 second
✅ **Reliable**: 92% code coverage
✅ **Clean**: All code passes linting
✅ **Modern**: Uses UV and Ruff for best practices

---

**Last Updated**: 2025-11-08
**Test Framework**: pytest 9.0.0
**Linter**: ruff 0.14.4
**Package Manager**: uv
