#!/usr/bin/env python
from __future__ import absolute_import
import sys
import argparse

import permitcheck
from permitcheck.plugin import PluginManager
from permitcheck.license.update import License
from permitcheck.lint import PermitCheck
from permitcheck.core.cache import LicenseCache
from permitcheck.exceptions import (
    PermitCheckError,
    ConfigurationError,
    PluginLoadError
)

def main():
    parser = argparse.ArgumentParser(
        description=permitcheck.__description__,
        epilog="Examples:\n"
               "  permitcheck -l python --format json\n"
               "  permitcheck -l python --format html > report.html\n"
               "  permitcheck --clear-cache\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Main options
    parser.add_argument('--verbose', '-V', action='store_true', help="Enable verbose output with detailed information")
    parser.add_argument('-v', '--version', action='version', version=f'PermitCheck {permitcheck.__version__}')
    parser.add_argument('-q', '--quiet', action='store_true', help="Suppress non-error output")

    # Language selection
    parser.add_argument(
        '-l', '--lang',
        choices=['python', 'npm'],
        nargs='+',
        metavar='LANG',
        help='Languages to check: python, npm'
    )
    
    # Output formats
    parser.add_argument(
        '--format',
        choices=['console', 'json', 'simple', 'html', 'markdown', 'csv', 'sarif'],
        default='console',
        help='Output format: console, json, simple, html, markdown, csv, sarif (default: console)'
    )
    
    # Output file
    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Write output to file instead of stdout'
    )
    
    # Cache options
    parser.add_argument('--no-cache', action='store_true', help='Bypass license cache for this run')
    parser.add_argument('--clear-cache', action='store_true', help='Clear license cache and exit')
    
    # Other options
    parser.add_argument('-u', '--update', action='store_true', help="Update license database")
    parser.add_argument('--license', action='store_true', help="Show license information")

    args = parser.parse_args()

    try:
        # Handle cache clearing
        if getattr(args, 'clear_cache', False):
            cache = LicenseCache()
            cache.clear()
            if not args.quiet:
                print(f"✓ Cache cleared: {cache.cache_file}")
            return
        
        if getattr(args, 'license', False):
            License.get()
            return
        
        # Setup output
        output_file = None
        if args.output:
            output_file = open(args.output, 'w')
            if not args.quiet and args.format != 'json':
                print(f"Writing output to {args.output}...")

        output_format = getattr(args, 'format', 'console')
        plugins = None
        manager = PluginManager()
        
        if not getattr(args, "lang", []):
            plugins = manager.load_plugins()

        for elang in getattr(args, "lang", []) or []:
            plugins = manager.load_plugins(elang)

        if plugins:
            for lang in plugins:
                deps = manager.run_plugin(lang)
                settings = plugins[lang].load_settings()
                
                if deps:
                    # Redirect stdout to file if output file specified
                    if output_file:
                        old_stdout = sys.stdout
                        sys.stdout = output_file
                    
                    # Print language header for console mode
                    if output_format == 'console' and not args.quiet:
                        if not output_file:  # Only print header if not redirecting
                            print("-" * 15)
                            print(f"   {plugins[lang].get_name().upper()}")
                            print("-" * 15)
                    
                    # If verbose, show dependency count (to stderr)
                    if args.verbose and not args.quiet:
                        print(f"Found {len(deps)} dependencies", file=sys.stderr)
                    
                    PermitCheck(deps, settings, output_format=output_format)
                    
                    # Restore stdout and flush
                    if output_file:
                        sys.stdout.flush()
                        sys.stdout = old_stdout
        else:
            if not args.quiet:
                print("❌ No plugins found. Please ensure plugins are available.", file=sys.stderr)
            sys.exit(1)
        
        # Close output file if opened
        if output_file:
            output_file.close()
            if not args.quiet:
                print(f"✓ Report saved to {args.output}")
    
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PluginLoadError as e:
        print(f"❌ Plugin Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PermitCheckError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
            print("Use --verbose for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
