"""Output reporting for PermitCheck."""

import json
import sys
import csv
from enum import Enum
from typing import Dict, Set, Optional, TextIO
from dataclasses import asdict
from io import StringIO

from permitcheck.core.validator import ValidationResult, Classification
from permitcheck.exceptions import PermitCheckError, PermitCheckWarning, PermitCheckInfo


class OutputFormat(Enum):
    """Supported output formats."""
    CONSOLE = "console"
    JSON = "json"
    SIMPLE = "simple"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"
    SARIF = "sarif"


class Reporter:
    """Handles output reporting in various formats."""
    
    MARKS = {
        'allowed': '\u2714',    # ✔ check mark
        'error': '\u2716',      # ✖ error mark
        'warning': '\u203C',    # ‼ warning mark
        'skip': 's'             # s skip mark
    }
    
    def __init__(self, format: OutputFormat = OutputFormat.CONSOLE):
        self.format = format
    
    def report(
        self,
        result: ValidationResult,
        dependencies: Dict[str, Set[str]],
        language: str = "python",
        output: Optional[TextIO] = None
    ) -> None:
        """Generate report based on format.
        
        Args:
            result: Validation result
            dependencies: Original dependencies dict
            language: Language being checked
            output: Output stream (defaults to stdout)
        """
        output = output or sys.stdout
        
        if self.format == OutputFormat.JSON:
            self._report_json(result, dependencies, language, output)
        elif self.format == OutputFormat.SIMPLE:
            self._report_simple(result, output)
        elif self.format == OutputFormat.HTML:
            self._report_html(result, dependencies, language, output)
        elif self.format == OutputFormat.MARKDOWN:
            self._report_markdown(result, dependencies, language, output)
        elif self.format == OutputFormat.CSV:
            self._report_csv(result, dependencies, language, output)
        elif self.format == OutputFormat.SARIF:
            self._report_sarif(result, dependencies, language, output)
        else:
            self._report_console(result, dependencies, language, output)
    
    def _report_console(
        self,
        result: ValidationResult,
        dependencies: Dict[str, Set[str]],
        language: str,
        output: TextIO
    ) -> None:
        """Console output with colors and formatting."""
        # Print dependencies with marks
        for pkg_name, licenses in dependencies.items():
            license_str = '; '.join(sorted(licenses))
            
            if pkg_name in result.allowed:
                mark = self.MARKS['allowed']
            elif pkg_name in result.errors:
                mark = self.MARKS['error']
            elif pkg_name in result.warnings:
                mark = self.MARKS['warning']
            elif pkg_name in result.skipped:
                mark = self.MARKS['skip']
            else:
                mark = '?'
            
            output.write(f"{mark:<5} {pkg_name:<20} {license_str}\n")
        
        # Print summary
        if result.has_errors:
            output.write(str(PermitCheckError()) + "\n")
        elif result.has_warnings:
            output.write(str(PermitCheckWarning()) + "\n")
        else:
            output.write(str(PermitCheckInfo()) + "\n")
    
    def _report_simple(self, result: ValidationResult, output: TextIO) -> None:
        """Simple text output."""
        if result.has_errors:
            output.write("FAILED\n")
            output.write(f"Errors: {len(result.errors)}\n")
        elif result.has_warnings:
            output.write("WARNING\n")
            output.write(f"Warnings: {len(result.warnings)}\n")
        else:
            output.write("PASSED\n")
        
        output.write(f"Total checked: {result.total_checked}\n")
    
    def _report_json(
        self,
        result: ValidationResult,
        dependencies: Dict[str, Set[str]],
        language: str,
        output: TextIO
    ) -> None:
        """JSON output for programmatic consumption."""
        # Build detailed results
        detailed = {}
        for pkg_name, licenses in dependencies.items():
            status = "unknown"
            if pkg_name in result.allowed:
                status = "allowed"
            elif pkg_name in result.errors:
                status = "error"
            elif pkg_name in result.warnings:
                status = "warning"
            elif pkg_name in result.skipped:
                status = "skipped"
            
            detailed[pkg_name] = {
                "licenses": sorted(list(licenses)),
                "status": status
            }
        
        report = {
            "language": language,
            "summary": {
                "total": result.total_checked,
                "allowed": len(result.allowed),
                "errors": len(result.errors),
                "warnings": len(result.warnings),
                "skipped": len(result.skipped),
                "status": "failed" if result.has_errors else ("warning" if result.has_warnings else "passed")
            },
            "dependencies": detailed
        }
        
        json.dump(report, output, indent=2)
        output.write("\n")
    
    def _report_html(
        self,
        result: ValidationResult,
        dependencies: Dict[str, Set[str]],
        language: str,
        output: TextIO
    ) -> None:
        """HTML output with rich formatting and charts."""
        status_class = "success" if not result.has_errors else "failure"
        status_text = "PASSED" if not result.has_errors else "FAILED"
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PermitCheck Report - {language.upper()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .language {{ font-size: 1.2em; opacity: 0.9; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f9fafb;
            border-bottom: 2px solid #e5e7eb;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .summary-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .summary-card .label {{
            color: #6b7280;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}
        .summary-card.total .number {{ color: #667eea; }}
        .summary-card.allowed .number {{ color: #10b981; }}
        .summary-card.errors .number {{ color: #ef4444; }}
        .summary-card.warnings .number {{ color: #f59e0b; }}
        .summary-card.skipped .number {{ color: #6b7280; }}
        .status-badge {{
            display: inline-block;
            padding: 10px 30px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.2em;
            margin-top: 20px;
        }}
        .status-badge.success {{ background: #10b981; color: white; }}
        .status-badge.failure {{ background: #ef4444; color: white; }}
        .dependencies {{
            padding: 30px;
        }}
        .dependencies h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #1f2937;
        }}
        .dep-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .dep-table thead {{
            background: #f9fafb;
        }}
        .dep-table th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #e5e7eb;
        }}
        .dep-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #f3f4f6;
        }}
        .dep-table tr:hover {{
            background: #f9fafb;
        }}
        .status-icon {{
            display: inline-block;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            text-align: center;
            line-height: 24px;
            font-weight: bold;
            color: white;
            font-size: 14px;
        }}
        .status-icon.allowed {{ background: #10b981; }}
        .status-icon.error {{ background: #ef4444; }}
        .status-icon.warning {{ background: #f59e0b; }}
        .status-icon.skipped {{ background: #6b7280; }}
        .license-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .license-badge {{
            display: inline-block;
            padding: 4px 12px;
            background: #e0e7ff;
            color: #4338ca;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        .footer {{
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 0.9em;
            border-top: 1px solid #e5e7eb;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ PermitCheck Report</h1>
            <div class="language">Language: {language.upper()}</div>
            <div class="status-badge {status_class}">{status_text}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <div class="label">Total Packages</div>
                <div class="number">{result.total_checked}</div>
            </div>
            <div class="summary-card allowed">
                <div class="label">Allowed</div>
                <div class="number">{len(result.allowed)}</div>
            </div>
            <div class="summary-card errors">
                <div class="label">Errors</div>
                <div class="number">{len(result.errors)}</div>
            </div>
            <div class="summary-card warnings">
                <div class="label">Warnings</div>
                <div class="number">{len(result.warnings)}</div>
            </div>
            <div class="summary-card skipped">
                <div class="label">Skipped</div>
                <div class="number">{len(result.skipped)}</div>
            </div>
        </div>
        
        <div class="dependencies">
            <h2>📦 Dependencies</h2>
            <table class="dep-table">
                <thead>
                    <tr>
                        <th style="width: 60px;">Status</th>
                        <th>Package</th>
                        <th>Licenses</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # Sort dependencies by status (errors first, then warnings, allowed, skipped)
        sorted_deps = []
        for pkg_name, licenses in dependencies.items():
            if pkg_name in result.errors:
                status = ('error', '✖', 1)
            elif pkg_name in result.warnings:
                status = ('warning', '⚠', 2)
            elif pkg_name in result.allowed:
                status = ('allowed', '✓', 3)
            elif pkg_name in result.skipped:
                status = ('skipped', 'S', 4)
            else:
                status = ('unknown', '?', 5)
            
            sorted_deps.append((status[2], pkg_name, licenses, status[0], status[1]))
        
        sorted_deps.sort(key=lambda x: (x[0], x[1]))
        
        for _, pkg_name, licenses, status_class, status_icon in sorted_deps:
            license_badges = ''.join(f'<span class="license-badge">{lic}</span>' 
                                    for lic in sorted(licenses))
            html += f"""
                    <tr>
                        <td><span class="status-icon {status_class}">{status_icon}</span></td>
                        <td><strong>{pkg_name}</strong></td>
                        <td><div class="license-badges">{license_badges}</div></td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            Generated by PermitCheck v2.0.0
        </div>
    </div>
</body>
</html>
"""
        
        output.write(html)

    def _report_markdown(
        self,
        result: ValidationResult,
        dependencies: Dict[str, Set[str]],
        language: str,
        output: TextIO
    ) -> None:
        """Markdown output for documentation."""
        status = "✅ PASSED" if not result.has_errors else "❌ FAILED"
        
        md = f"""# PermitCheck Report - {language.upper()}

## Summary

**Status:** {status}

| Metric | Count |
|--------|-------|
| Total Dependencies | {result.total_checked} |
| Allowed | {len(result.allowed)} |
| Errors | {len(result.errors)} |
| Warnings | {len(result.warnings)} |
| Skipped | {len(result.skipped)} |

## Dependencies

| Status | Package | Licenses |
|--------|---------|----------|
"""
        
        # Sort by status
        for pkg_name, licenses in sorted(dependencies.items()):
            if pkg_name in result.errors:
                status_icon = "❌"
            elif pkg_name in result.warnings:
                status_icon = "⚠️"
            elif pkg_name in result.allowed:
                status_icon = "✅"
            elif pkg_name in result.skipped:
                status_icon = "⏭️"
            else:
                status_icon = "❓"
            
            license_str = ", ".join(sorted(licenses))
            md += f"| {status_icon} | `{pkg_name}` | {license_str} |\n"
        
        md += "\n---\n*Generated by PermitCheck v2.0.0*\n"
        output.write(md)

    def _report_csv(
        self,
        result: ValidationResult,
        dependencies: Dict[str, Set[str]],
        language: str,
        output: TextIO
    ) -> None:
        """CSV output for spreadsheet analysis."""
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Package', 'Licenses', 'Status', 'Language'])
        
        # Data rows
        for pkg_name, licenses in sorted(dependencies.items()):
            if pkg_name in result.errors:
                status = "ERROR"
            elif pkg_name in result.warnings:
                status = "WARNING"
            elif pkg_name in result.allowed:
                status = "ALLOWED"
            elif pkg_name in result.skipped:
                status = "SKIPPED"
            else:
                status = "UNKNOWN"
            
            license_str = "; ".join(sorted(licenses))
            writer.writerow([pkg_name, license_str, status, language])

    def _report_sarif(
        self,
        result: ValidationResult,
        dependencies: Dict[str, Set[str]],
        language: str,
        output: TextIO
    ) -> None:
        """SARIF output for security tools integration."""
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "PermitCheck",
                        "version": "2.0.0",
                        "informationUri": "https://github.com/kirankotari/permitcheck",
                        "rules": [
                            {
                                "id": "license-error",
                                "name": "LicenseError",
                                "shortDescription": {
                                    "text": "Dependency uses a prohibited license"
                                },
                                "fullDescription": {
                                    "text": "This dependency uses a license that is explicitly prohibited by policy"
                                },
                                "defaultConfiguration": {
                                    "level": "error"
                                }
                            },
                            {
                                "id": "license-warning",
                                "name": "LicenseWarning",
                                "shortDescription": {
                                    "text": "Dependency uses an unrecognized license"
                                },
                                "fullDescription": {
                                    "text": "This dependency uses a license that is not in the allowed list"
                                },
                                "defaultConfiguration": {
                                    "level": "warning"
                                }
                            }
                        ]
                    }
                },
                "results": []
            }]
        }
        
        # Add errors
        for pkg_name in result.errors:
            licenses = dependencies.get(pkg_name, set())
            sarif["runs"][0]["results"].append({
                "ruleId": "license-error",
                "level": "error",
                "message": {
                    "text": f"Package '{pkg_name}' uses prohibited license(s): {', '.join(licenses)}"
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": f"package:{language}/{pkg_name}"
                        }
                    }
                }],
                "properties": {
                    "package": pkg_name,
                    "licenses": list(licenses),
                    "language": language
                }
            })
        
        # Add warnings
        for pkg_name in result.warnings:
            licenses = dependencies.get(pkg_name, set())
            sarif["runs"][0]["results"].append({
                "ruleId": "license-warning",
                "level": "warning",
                "message": {
                    "text": f"Package '{pkg_name}' uses unrecognized license(s): {', '.join(licenses)}"
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": f"package:{language}/{pkg_name}"
                        }
                    }
                }],
                "properties": {
                    "package": pkg_name,
                    "licenses": list(licenses),
                    "language": language
                }
            })
        
        json.dump(sarif, output, indent=2)
