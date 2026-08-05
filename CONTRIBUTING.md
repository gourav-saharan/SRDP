# Contributing to SRDP (Steering Robot Data Processing)

Thank you for your interest in contributing to **SRDP**! We welcome bug reports, feature enhancements, documentation updates, and pull requests.

## How to Contribute

### 1. Reporting Bugs & Issues
- Check existing GitHub issues to avoid duplicate reports.
- Open a new issue with a descriptive title and detailed reproduction steps.
- Include OS version, Python version, error tracebacks, and sample data format if applicable.

### 2. Requesting Features
- Open a feature request issue explaining the motivation and proposed functionality.
- Describe how the feature enhances steering robot telemetry processing or data visualization.

### 3. Pull Request (PR) Workflow
1. Fork the repository on GitHub.
2. Create a topic branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Implement your changes adhering to standard PEP 8 formatting practices.
4. Test the application locally by running:
   ```bash
   python SRDP_App/main.py
   ```
5. Commit your changes with clear, descriptive commit messages.
6. Push to your branch and open a Pull Request against `main`.

---

## Code Guidelines
- Keep UI components decoupled from `core/data_manager.py` business logic.
- Ensure all newly supported file extensions handle empty or malformed files gracefully.
- Test custom plot configurations across both **Light** and **Dark** appearance modes.
