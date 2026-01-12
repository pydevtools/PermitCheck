# Output Formats

PermitCheck supports seven output formats for different use cases.

## Console (Default)

Human-readable output with emoji status indicators.

```bash
permitcheck -l python
```

**Output:**
```
---------------
   PYTHON
---------------
✔     pytest               MIT
✔     requests             Apache-2.0
✔     pyyaml               MIT
‼     certifi              MPL-2.0
✖     proprietary-pkg      Proprietary

PermitCheck: License compliance failed.
```

**Status Indicators:**
- ✔ (checkmark) - Allowed license
- ‼ (warning) - Unrecognized license
- ✖ (error) - Prohibited license
- s - Skipped package

## JSON

Machine-readable JSON for CI/CD pipelines and automation.

```bash
permitcheck -l python --format json
```

**Output:**
```json
{
  "language": "python",
  "summary": {
    "total": 12,
    "allowed": 10,
    "errors": 1,
    "warnings": 1,
    "skipped": 0,
    "status": "error"
  },
  "dependencies": {
    "pytest": {
      "licenses": ["MIT"],
      "status": "allowed"
    },
    "requests": {
      "licenses": ["Apache-2.0"],
      "status": "allowed"
    }
  }
}
```

**Use Cases:**
- CI/CD pipeline integration
- Automated reporting
- Data analysis
- API consumption

## HTML

Rich HTML report with charts, tables, and styling.

```bash
permitcheck -l python --format html -o report.html
```

**Features:**
- Responsive design
- Color-coded status badges
- Summary statistics cards
- Sortable dependency table
- Gradient headers
- Professional styling

**Use Cases:**
- Executive reports
- Audit documentation
- Team dashboards
- Stakeholder presentations

**Preview:**
- Summary cards showing total, allowed, errors, warnings
- Status: PASSED/FAILED badge
- Dependency table with package names, licenses, and status icons
- Footer with generation timestamp

## Markdown

Formatted Markdown for documentation and GitHub/GitLab.

```bash
permitcheck -l python --format markdown -o compliance.md
```

**Output:**
```markdown
# PermitCheck Report - PYTHON

## Summary

**Status:** ✅ PASSED

| Metric | Count |
|--------|-------|
| Total Dependencies | 12 |
| Allowed | 11 |
| Errors | 0 |
| Warnings | 1 |
| Skipped | 0 |

## Dependencies

| Status | Package | Licenses |
|--------|---------|----------|
| ✅ | `pytest` | MIT |
| ⚠️ | `certifi` | MPL-2.0 |
```

**Use Cases:**
- GitHub/GitLab documentation
- Wiki pages
- README files
- Pull request comments

## CSV

Spreadsheet-compatible format for analysis.

```bash
permitcheck -l python --format csv -o licenses.csv
```

**Output:**
```csv
Package,Licenses,Status,Language
pytest,MIT,ALLOWED,python
requests,Apache-2.0,ALLOWED,python
certifi,MPL-2.0,WARNING,python
proprietary-pkg,Proprietary,ERROR,python
```

**Use Cases:**
- Excel/Google Sheets analysis
- Data warehousing
- Bulk processing
- Historical tracking

## SARIF

Static Analysis Results Interchange Format for security tools.

```bash
permitcheck -l python --format sarif -o results.sarif
```

**Output:**
```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [{
    "tool": {
      "driver": {
        "name": "PermitCheck",
        "version": "2.0.0",
        "rules": [...]
      }
    },
    "results": [
      {
        "ruleId": "license-error",
        "level": "error",
        "message": {
          "text": "Package 'proprietary-pkg' uses prohibited license(s): Proprietary"
        }
      }
    ]
  }]
}
```

**Use Cases:**
- GitHub Security tab integration
- VS Code integration
- SonarQube integration
- Security dashboards
- CodeQL integration

**GitHub Integration:**
```yaml
- uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: results.sarif
```

## Simple

Minimal text output for scripts.

```bash
permitcheck -l python --format simple
```

**Output:**
```
Package: pytest - MIT (ALLOWED)
Package: requests - Apache-2.0 (ALLOWED)
Package: certifi - MPL-2.0 (WARNING)
Package: proprietary-pkg - Proprietary (ERROR)
```

**Use Cases:**
- Shell scripts
- Minimal logging
- Quick checks

## Comparison Matrix

| Format | Human-Readable | Machine-Readable | CI/CD | Reporting | Security Tools |
|--------|----------------|------------------|-------|-----------|----------------|
| Console | ✅ | ❌ | ⚠️ | ❌ | ❌ |
| JSON | ❌ | ✅ | ✅ | ✅ | ⚠️ |
| HTML | ✅ | ❌ | ❌ | ✅ | ❌ |
| Markdown | ✅ | ⚠️ | ⚠️ | ✅ | ❌ |
| CSV | ⚠️ | ✅ | ⚠️ | ✅ | ❌ |
| SARIF | ❌ | ✅ | ✅ | ⚠️ | ✅ |
| Simple | ✅ | ⚠️ | ✅ | ❌ | ❌ |

## Output Redirection

### Save to File

```bash
permitcheck -l python --format json -o results.json
permitcheck -l python --format html -o report.html
permitcheck -l python --format csv -o licenses.csv
```

### Pipe to Other Tools

```bash
# JSON parsing with jq
permitcheck -l python --format json | jq '.summary'

# CSV processing with awk
permitcheck -l python --format csv | awk -F',' '$3=="ERROR" {print $1}'

# Markdown preview
permitcheck -l python --format markdown | less
```

## Multiple Formats

Generate multiple reports in one run:

```bash
#!/bin/bash
# Generate all reports
permitcheck -l python --format json -o results.json
permitcheck -l python --format html -o report.html
permitcheck -l python --format csv -o licenses.csv
permitcheck -l python --format sarif -o results.sarif
permitcheck -l python --format markdown -o compliance.md
```

## Format Selection Guide

**Choose based on your needs:**

1. **Quick Local Check** → Console
2. **CI/CD Pipeline** → JSON or SARIF
3. **Executive Report** → HTML
4. **Documentation** → Markdown
5. **Data Analysis** → CSV
6. **Security Integration** → SARIF
7. **Scripting** → Simple or JSON

## Next Steps

- Set up [CI/CD Integration](ci-cd-integration.md)
- Explore [API Reference](api-reference.md)
- Review [Configuration](configuration.md)
