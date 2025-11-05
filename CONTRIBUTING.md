# Contributing to OsMEN

Thank you for your interest in contributing to OsMEN! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful and constructive in all interactions.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs
- Include detailed steps to reproduce
- Specify your environment (OS, Docker version, etc.)
- Include relevant logs

### Suggesting Features

- Open a GitHub Issue with the "enhancement" label
- Describe the feature and its use case
- Explain why it would be valuable

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/dwilli15/OsMEN.git
   cd OsMEN
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add comments where needed
   - Update documentation

4. **Test your changes**
   ```bash
   # Test agents
   python agents/boot_hardening/boot_hardening_agent.py
   
   # Test Docker setup
   docker-compose up -d
   docker-compose ps
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Describe your changes
   - Reference any related issues
   - Include screenshots for UI changes

## Development Guidelines

### Code Style

**Python**
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions and classes

**JSON**
- Indent with 2 spaces
- Use consistent naming conventions

**Shell Scripts**
- Use bash
- Add comments for complex logic
- Make scripts executable

### Project Structure

```
OsMEN/
├── agents/           # Agent implementations
│   ├── boot_hardening/
│   ├── daily_brief/
│   └── focus_guardrails/
├── langflow/         # Langflow flows and config
│   ├── flows/
│   └── config/
├── n8n/              # n8n workflows
│   └── workflows/
├── tools/            # Tool integrations
│   ├── simplewall/
│   ├── sysinternals/
│   └── ffmpeg/
├── docs/             # Documentation
└── docker-compose.yml
```

### Adding New Agents

1. **Create agent directory**
   ```bash
   mkdir -p agents/my_agent
   ```

2. **Implement agent class**
   ```python
   # agents/my_agent/my_agent.py
   class MyAgent:
       def __init__(self):
           pass
       
       def perform_task(self):
           pass
   ```

3. **Create Langflow flow**
   - Design flow in Langflow UI
   - Export as JSON
   - Save to `langflow/flows/my_agent_specialist.json`

4. **Create n8n workflow**
   - Design workflow in n8n UI
   - Export as JSON
   - Save to `n8n/workflows/my_agent_trigger.json`

5. **Update documentation**
   - Add to README.md
   - Update USAGE.md
   - Add examples

### Testing

**Manual Testing**
- Test agent directly with Python
- Test through Langflow UI
- Test through n8n workflows
- Verify Docker setup

**Integration Testing**
- Test full workflow end-to-end
- Verify data flow between components
- Check memory storage in Qdrant

### Documentation

- Update README.md for major changes
- Add/update docs/ files as needed
- Include code examples
- Add screenshots for UI features

## Git Workflow

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring

### Commit Messages

Format: `type: description`

Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `test:` - Tests
- `chore:` - Maintenance

Examples:
```
feat: add research intelligence agent
fix: correct boot hardening check logic
docs: update setup guide
```

## Review Process

1. **Automated Checks**
   - Docker build succeeds
   - Python syntax valid
   - JSON files valid

2. **Code Review**
   - Maintainer reviews code
   - Feedback provided
   - Revisions requested if needed

3. **Testing**
   - Manual testing by reviewer
   - Integration testing

4. **Merge**
   - Approved PRs merged to main
   - Branch deleted after merge

## Questions?

- Open a GitHub Discussion
- Comment on relevant issues
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
