# Contributing to Quantum Navigator

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

---

## Getting Started

### Prerequisites

- **Frontend**: Node.js 18+, npm or pnpm
- **Backend**: Python 3.10+, pip
- **Optional**: Pulser (`pip install pulser-core pulser-simulation`)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/MRamiBalles/quantum-navigator.git
cd quantum-navigator

# Install frontend dependencies
npm install

# Set up backend virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

---

## Project Structure

```
quantum-navigator/
├── src/                    # Frontend (TypeScript/React)
├── backend/                # Python middleware
│   ├── drivers/            # Hardware drivers
│   ├── schemas/            # JSON schemas
│   └── tests/              # Python tests
└── docs/                   # Documentation
```

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- **Frontend**: Components in `src/components/`
- **Backend**: Drivers in `backend/drivers/`
- **Docs**: Markdown in `docs/`

### 3. Run Tests

```bash
# Frontend tests
npm run test

# Backend tests
cd backend
pytest tests/ -v
```

### 4. Lint Your Code

```bash
# Frontend
npm run lint

# Backend
cd backend
ruff check .
mypy drivers/
```

### 5. Submit a Pull Request

- Write a clear description of changes
- Reference any related issues
- Ensure all tests pass

---

## Code Style

### TypeScript/React

- Use functional components with hooks
- Type all props and state
- Follow existing naming conventions
- Use `cn()` utility for conditional classes

### Python

- Follow PEP 8
- Use type hints everywhere
- Docstrings for public functions
- Pydantic models for data validation

---

## Adding a New Driver

1. Create directory: `backend/drivers/your_driver/`
2. Implement:
   - `schema.py` - Pydantic models for JSON IR
   - `validator.py` - Physics/constraint validation
   - `adapter.py` - Bridge to native SDK
3. Add tests: `backend/tests/test_your_driver.py`
4. Update `DEVICE_REGISTRY` if adding hardware support

---

## Documentation

- Update `README.md` for user-facing changes
- Update `docs/API_REFERENCE.md` for API changes
- Update `docs/ARCHITECTURE.md` for design changes
- Add docstrings and inline comments

---

## Commit Messages

Follow conventional commits:

```
feat: add support for QAOA templates
fix: correct blockade radius calculation
docs: update API reference for v2.0
test: add validator edge case tests
```

---

## Questions?

Open an issue or reach out to the maintainers.
