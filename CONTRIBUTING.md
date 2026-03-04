# Contributing to SmartCommerce Kenya

Thank you for your interest in contributing to SmartCommerce Kenya! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/franklineXonguti/Smartcommerce-Kenya.git
   cd Smartcommerce-Kenya
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Configure your .env file
   python manage.py migrate
   python manage.py runserver
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Using Docker**
   ```bash
   docker-compose up
   ```

## Development Workflow

### Branching Strategy

We follow a Gitflow-lite model:

- `main` - Production-ready code only
- `develop` - Integration branch for features
- `feature/<short-desc>-<id>` - New features (e.g., `feature/auth-jwt-002`)
- `release/vX.Y.Z` - Release preparation
- `hotfix/<short-desc>` - Urgent production fixes

### Starting a New Feature

1. Always branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-001
   ```

2. Make your changes in small, logical commits

3. Push your branch:
   ```bash
   git push -u origin feature/your-feature-001
   ```

4. Open a Pull Request to `develop`

### Commit Message Convention

We use **Conventional Commits** format:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

#### Types

- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `docs` - Documentation changes
- `chore` - Maintenance tasks
- `ci` - CI/CD changes
- `perf` - Performance improvements
- `build` - Build system changes

#### Examples

```bash
feat(auth): add JWT login and refresh endpoints
fix(payment): handle failed M-Pesa callback gracefully
test(cart): add integration tests for guest carts
docs: update API usage guide for vendors
ci: configure GitHub Actions for backend tests
```

#### Guidelines

- Use present tense, imperative mood ("add" not "added")
- Keep the summary line under 72 characters
- Reference issue numbers when applicable
- One logical change per commit

## Code Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Maximum line length: 88 characters (Black default)
- Use meaningful variable and function names

### JavaScript/React (Frontend)

- Use ES6+ syntax
- Follow Airbnb style guide
- Use functional components with hooks
- Prop-types or TypeScript for type checking
- Meaningful component and variable names

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

## Testing

### Backend Tests

```bash
cd backend
python manage.py test
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Coverage

Aim for at least 80% test coverage on new code.

## Pull Request Process

1. **Before submitting:**
   - Ensure all tests pass
   - Run linters and fix any issues
   - Update documentation if needed
   - Add tests for new features

2. **PR Description should include:**
   - What changes were made
   - Why the changes were necessary
   - How to test the changes
   - Screenshots (for UI changes)
   - Related issue numbers

3. **Review Process:**
   - At least one approval required
   - All CI checks must pass
   - Address review comments promptly
   - Squash commits if requested

4. **After Approval:**
   - Maintainer will merge using squash or rebase
   - Delete your feature branch after merge

## Code Review Guidelines

### As a Reviewer

- Be respectful and constructive
- Focus on code quality, not personal preferences
- Suggest improvements, don't demand
- Approve when satisfied, even if minor suggestions remain

### As an Author

- Don't take feedback personally
- Respond to all comments
- Ask for clarification if needed
- Thank reviewers for their time

## Reporting Issues

### Bug Reports

Include:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, browser, versions)
- Screenshots or error logs

### Feature Requests

Include:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Mockups or examples (if applicable)

## Kenya-Specific Considerations

When working on Kenya-specific features:

- **Phone Numbers:** Validate format `+2547XXXXXXXX` or `07XXXXXXXX`
- **Currency:** Default to KES (Kenyan Shillings)
- **Counties:** Use official 47 Kenyan counties
- **Addresses:** Include county, town, ward, landmark fields
- **M-Pesa:** Test with Daraja sandbox credentials
- **Delivery:** Consider Kenyan geography and logistics

## Questions?

- Open an issue for general questions
- Tag maintainers in PRs for urgent reviews
- Check existing issues and PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
