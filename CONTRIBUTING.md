# Contributing to SystemFlow

Thank you for your interest in contributing! Here are some guidelines:

## How to Contribute

1. **Bug Reports** — Open an issue with:
   - Description
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs (`journalctl -u marzban-security-bot -n 50`)
   - System info (OS, Python version, Marzban version)

2. **Feature Requests** — Open a discussion with:
   - Feature description
   - Use case
   - Expected behavior

3. **Pull Requests**:
   - Fork the repo
   - Create feature branch
   - Write tests if applicable
   - Update documentation
   - Submit PR with clear description

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to classes and functions
- Keep functions focused (single responsibility)
- Use meaningful variable names

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add GeoIP caching
fix: resolve callback error in log monitor
docs: update installation guide
refactor: simplify database queries
chore: update dependencies
```

## Development Setup

```bash
git clone https://github.com/R3G1ST/SystemFlow.git
cd SystemFlow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
python bot.py
```

## Testing

```bash
# Run tests (coming soon)
pytest
```

## Need Help?

- Open an issue
- Start a discussion
- Contact maintainer
