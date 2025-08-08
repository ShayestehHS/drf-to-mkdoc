# Contributing to DRF to MkDocs

Thank you for your interest in contributing to DRF to MkDocs! This document provides guidelines and information for contributors.

## Getting Started

1. **Fork the repository**
   - Go to the main repository page
   - Click the "Fork" button to create your own copy

2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/drf-to-mkdoc.git
   cd drf-to-mkdoc
   ```

3. **Set up development environment**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and single-purpose

### Documentation

- Update README.md if adding new features
- Add docstrings to new functions and classes
- Update inline comments for complex logic
- Consider adding examples for new functionality

## Making Changes

1. **Make your changes**
   - Implement your feature or fix
   - Follow the coding guidelines above
   - Test your changes thoroughly

2. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description of changes"
   ```

3. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a pull request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the pull request template

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No breaking changes (or clearly documented)
- [ ] Feature is tested with multiple Django versions

### Pull Request Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring

## Testing
Describe how you tested your changes.

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where necessary
- [ ] I have made corresponding changes to documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective
```

## Issue Reporting

When reporting issues, please include:

- **Django version**: The version you're using
- **DRF version**: Django REST Framework version
- **Python version**: Your Python version
- **Error message**: Full error traceback
- **Steps to reproduce**: Clear steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened

## Code of Conduct

- Be respectful and inclusive
- Focus on the code and technical discussions
- Help others learn and improve
- Report any inappropriate behavior to maintainers

## Questions?

If you have questions about contributing, feel free to:

- Open an issue for general questions
- Ask in pull request comments
- Contact maintainers directly

Thank you for contributing to DRF to MkDocs! 