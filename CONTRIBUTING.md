# Contributing to Autonomous Code Orchestrator (ACO)

Thank you for your interest in contributing to ACO! This project uses a strict constitutional governance model to ensure autonomous operation quality.

## Prerequisites

### Required Software

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Beads CLI**
   ```bash
   curl -sSL https://raw.githubusercontent.com/steveyegge/beads/main/install.sh | bash
   which bd  # Should output the path to bd
   ```

3. **Git**
   ```bash
   git --version
   ```

## Development Setup

### 1. Clone and Set Up Environment

```bash
# Clone repository
git clone <repository-url>
cd codeframe-aco

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows

# Install dependencies in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black ruff mypy
```

### 2. Initialize Beads

If working on a fresh clone:

```bash
# Beads database is already in .beads/ (tracked in Git)
# Verify it works
bd list
bd ready
```

### 3. Verify Setup

```bash
# Run unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_models.py -v

# Check imports work
python -c "from beads import create_beads_client; print('OK')"
```

## Development Workflow

### Using Beads for Task Management

All work must be tracked as issues in Beads:

```bash
# Find ready work
bd ready

# Create new issue
bd create "Issue title" -t task -p 2

# Claim issue
bd update <issue-id> --status in_progress

# Close when done
bd close <issue-id>
```

### Creating a Feature Branch

```bash
# Branch naming: ###-feature-name (e.g., 003-api-client)
git checkout -b 003-new-feature

# Create spec directory
mkdir -p specs/003-new-feature

# Use Spec-kit for planning (if available)
/speckit.specify
/speckit.plan
/speckit.tasks
```

### Writing Code

1. **Follow TDD (Test-Driven Development)**:
   ```bash
   # Write tests first
   vim tests/unit/test_new_feature.py

   # Run tests (they should fail)
   pytest tests/unit/test_new_feature.py -v

   # Implement feature
   vim src/beads/new_feature.py

   # Run tests again (they should pass)
   pytest tests/unit/test_new_feature.py -v
   ```

2. **Maintain Coverage**:
   ```bash
   # Check coverage for beads package only
   pytest tests/ --cov=src/beads --cov-report=term --cov-report=html

   # Open coverage report
   open htmlcov/index.html  # Mac
   xdg-open htmlcov/index.html  # Linux
   ```

3. **Format Code**:
   ```bash
   # Format with black
   black src/ tests/

   # Lint with ruff
   ruff check src/ tests/

   # Type check with mypy
   mypy src/beads/
   ```

## Testing

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast, isolated tests
│   ├── test_client.py
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_exceptions.py
└── integration/         # Tests using bd CLI
    ├── test_issue_crud.py
    ├── test_dependencies.py
    └── test_end_to_end.py
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests (slower, may timeout)
pytest tests/integration/ -v

# Specific test class
pytest tests/unit/test_models.py::TestIssueModel -v

# Specific test
pytest tests/unit/test_models.py::TestIssueModel::test_issue_from_json -v

# With coverage
pytest tests/ --cov=src/beads --cov-report=term
```

### Writing Tests

1. **Use pytest fixtures** from `conftest.py`:
   ```python
   def test_something(test_beads_db, monkeypatch):
       monkeypatch.chdir(test_beads_db)
       client = BeadsClient(sandbox=True)
       # ... test code ...
   ```

2. **Isolate integration tests**:
   - Always use `sandbox=True` for BeadsClient
   - Always use `test_beads_db` fixture
   - Clean up created issues if possible

3. **Follow naming conventions**:
   - Test files: `test_*.py`
   - Test classes: `TestFeatureName`
   - Test methods: `test_specific_behavior`

## Quality Standards

### Code Coverage

- **Minimum**: 80% coverage for `src/beads/` package
- Exclude: `src/vector_memory/` (separate feature)
- Check: `pytest --cov=src/beads --cov-report=term`

### Code Quality

- **No linting errors**: Run `ruff check src/ tests/`
- **Type hints**: All public functions must have type hints
- **Docstrings**: All public classes and methods must have docstrings
- **Format**: Code must be formatted with `black`

### Security

- No hardcoded credentials
- No SQL injection vulnerabilities
- No command injection (be careful with subprocess calls)
- Validate all inputs from bd CLI

## Constitutional Compliance

All contributions must comply with `.specify/memory/constitution.md`:

1. **Vector Memory Architecture**: Information organized by (x, y, z) coordinates
2. **DAG-Driven Development**: Work tracked in Beads with dependencies
3. **Unified Development Cycle**: Consistent process for all issues
4. **Test-First Development**: 80% minimum coverage, TDD required
5. **Autonomous Operation**: Minimal human intervention
6. **Scope Control**: No infinite expansion
7. **Observability**: Complete audit trail

## Submitting Changes

### Before Committing

```bash
# Run all checks
black src/ tests/
ruff check src/ tests/
mypy src/beads/
pytest tests/ --cov=src/beads --cov-report=term

# Verify coverage ≥ 80%
# All tests should pass
# No linting errors
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(client): Add dependency tree querying

Implement get_dependency_tree() method to retrieve
upstream and downstream dependencies for an issue.

Closes: codeframe-aco-abc
Tests: tests/unit/test_client.py::TestDependencyTree
Coverage: 95% (+2%)
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

### Beads Integration

```bash
# Update issue status
bd update <issue-id> --status in_progress

# Commit changes
git add .
git commit -m "feat: Add new feature"

# Close issue when done
bd close <issue-id>

# Push to remote
git push origin <branch-name>
```

## Working with Beads Integration Layer

### Architecture

```
src/beads/
├── __init__.py       # Public API exports
├── client.py         # BeadsClient main interface
├── models.py         # Dataclasses (Issue, Dependency, etc.)
├── utils.py          # CLI execution helpers
└── exceptions.py     # Custom exception hierarchy
```

### Adding New Features

1. **Define models** in `models.py`:
   ```python
   @dataclass
   class NewModel:
       field: str

       @classmethod
       def from_json(cls, data: dict) -> 'NewModel':
           return cls(field=data['field'])
   ```

2. **Add client method** in `client.py`:
   ```python
   def new_operation(self, param: str) -> NewModel:
       """Do something with bd CLI."""
       args = ['new-command', param]
       result = _run_bd_command(args, timeout=self.timeout)
       return NewModel.from_json(result)
   ```

3. **Export in `__init__.py`**:
   ```python
   from beads.models import NewModel
   __all__ = [..., "NewModel"]
   ```

4. **Write tests**:
   - Unit tests in `tests/unit/test_models.py` or `test_client.py`
   - Integration tests in `tests/integration/`

## Common Tasks

### Running Examples

```bash
# Create test database
cd /tmp/test-beads
bd init --prefix test

# Run examples
python examples/select_task.py
python examples/discover_gaps.py simulate
python examples/manage_dag.py
```

### Debugging

```bash
# Enable verbose pytest output
pytest tests/unit/test_models.py -vv

# Show print statements
pytest tests/unit/test_models.py -v -s

# Drop into debugger on failure
pytest tests/unit/test_models.py -v --pdb

# Run single test with debugging
pytest tests/unit/test_models.py::TestIssue::test_from_json -vv -s
```

### Updating Dependencies

```bash
# List current dependencies
pip freeze

# Update specific package
pip install --upgrade package-name

# Update all
pip install --upgrade -r requirements.txt
```

## Getting Help

- **Documentation**: See [README.md](README.md), [CLAUDE.md](CLAUDE.md), [AGENTS.md](AGENTS.md)
- **Examples**: Check [examples/](examples/) directory
- **Specs**: See [specs/002-beads-integration/](specs/002-beads-integration/)
- **Issues**: Use `bd list` to see all tracked work
- **Constitution**: [.specify/memory/constitution.md](.specify/memory/constitution.md)

## License

[License information to be added]

## Code of Conduct

Be respectful, professional, and constructive. Focus on technical merit and constitutional compliance.
