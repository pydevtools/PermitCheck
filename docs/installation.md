# Installation Guide

## Requirements

- Python 3.10 or higher
- pip or uv package manager

## Installation Methods

### Using pip (Recommended)

```bash
pip install permitcheck
```

### Using uv

```bash
uv add permitcheck
```

### From Source

```bash
git clone https://github.com/kirankotari/permitcheck.git
cd permitcheck
uv sync
```

### Development Installation

For contributing or development:

```bash
git clone https://github.com/kirankotari/permitcheck.git
cd permitcheck
uv sync
uv run pytest  # Verify installation
```

## Verify Installation

```bash
permitcheck --version
```

Expected output:
```
PermitCheck 2.0.0
```

## Platform-Specific Notes

### Linux

No additional steps required.

### macOS

No additional steps required.

### Windows

Use PowerShell or Command Prompt:

```powershell
pip install permitcheck
```

## Upgrading

### From pip

```bash
pip install --upgrade permitcheck
```

### From uv

```bash
uv add --upgrade permitcheck
```

## Uninstallation

```bash
pip uninstall permitcheck
```

## Troubleshooting

### Permission Errors

On Linux/macOS, you may need to use:

```bash
pip install --user permitcheck
```

Or use a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install permitcheck
```

### Python Version Issues

Check your Python version:

```bash
python --version
```

If you have multiple Python versions, use:

```bash
python3.10 -m pip install permitcheck
```

### Network Issues

If you're behind a proxy:

```bash
pip install --proxy http://proxy.example.com:8080 permitcheck
```

## Next Steps

- Read the [Configuration Guide](configuration.md)
- Explore [Output Formats](output-formats.md)
- Set up [CI/CD Integration](ci-cd-integration.md)
