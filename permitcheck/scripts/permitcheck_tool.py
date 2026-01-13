#!/usr/bin/env python
import sys
import argparse
from typing import Optional, TextIO

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


def parse_arguments() -> argparse.Namespace:
    """Parse and return command line arguments."""
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

    return parser.parse_args()


def handle_cache_clearing(args: argparse.Namespace) -> bool:
    """Handle cache clearing if requested.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if cache was cleared and program should exit, False otherwise
    """
    if getattr(args, 'clear_cache', False):
        cache = LicenseCache()
        cache.clear()
        if not args.quiet:
            print(f"✓ Cache cleared: {cache.cache_file}")
        return True
    return False


def handle_license_info(args: argparse.Namespace) -> bool:
    """Handle license information display if requested.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if license info was displayed and program should exit, False otherwise
    """
    if getattr(args, 'license', False):
        License.get()
        return True
    return False


def setup_output_file(args: argparse.Namespace) -> Optional[TextIO]:
    """Setup output file if specified.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Open file handle if output file specified, None otherwise
    """
    if args.output:
        output_file = open(args.output, 'w')
        if not args.quiet and args.format != 'json':
            print(f"Writing output to {args.output}...")
        return output_file
    return None


def load_plugins(manager: PluginManager, args: argparse.Namespace):
    """Load plugins based on language arguments.
    
    Args:
        manager: PluginManager instance
        args: Parsed command line arguments
        
    Returns:
        Dictionary of loaded plugins or None
    """
    if not getattr(args, "lang", []):
        return manager.load_plugins()
    
    plugins = None
    for elang in args.lang:
        plugins = manager.load_plugins(elang)
    return plugins


def print_language_header(plugin, output_format: str, args: argparse.Namespace, output_file: Optional[TextIO]) -> None:
    """Print language header for console mode.
    
    Args:
        plugin: Plugin instance
        output_format: Output format string
        args: Parsed command line arguments
        output_file: Open file handle or None
    """
    if output_format == 'console' and not args.quiet and not output_file:
        print("-" * 15)
        print(f"   {plugin.get_name().upper()}")
        print("-" * 15)


def print_dependency_count(deps: dict, args: argparse.Namespace) -> None:
    """Print dependency count if verbose mode.
    
    Args:
        deps: Dictionary of dependencies
        args: Parsed command line arguments
    """
    if args.verbose and not args.quiet:
        print(f"Found {len(deps)} dependencies", file=sys.stderr)


def process_plugin(lang: str, plugins: dict, manager: PluginManager, args: argparse.Namespace, 
                   output_file: Optional[TextIO], output_format: str) -> None:
    """Process a single plugin and run license checks.
    
    Args:
        lang: Language identifier
        plugins: Dictionary of loaded plugins
        manager: PluginManager instance
        args: Parsed command line arguments
        output_file: Open file handle or None
        output_format: Output format string
    """
    deps = manager.run_plugin(lang)
    settings = plugins[lang].load_settings()
    
    if not deps:
        return
    
    # Redirect stdout to file if output file specified
    old_stdout = None
    if output_file:
        old_stdout = sys.stdout
        sys.stdout = output_file
    
    try:
        print_language_header(plugins[lang], output_format, args, output_file)
        print_dependency_count(deps, args)
        PermitCheck(deps, settings, output_format=output_format)
    finally:
        # Restore stdout and flush
        if output_file:
            sys.stdout.flush()
            sys.stdout = old_stdout


def run_checks(args: argparse.Namespace, manager: PluginManager, 
               output_file: Optional[TextIO], output_format: str) -> None:
    """Run license checks for all specified plugins.
    
    Args:
        args: Parsed command line arguments
        manager: PluginManager instance
        output_file: Open file handle or None
        output_format: Output format string
    """
    plugins = load_plugins(manager, args)
    
    if not plugins:
        if not args.quiet:
            print("❌ No plugins found. Please ensure plugins are available.", file=sys.stderr)
        sys.exit(1)
    
    for lang in plugins:
        process_plugin(lang, plugins, manager, args, output_file, output_format)


def finalize_output(output_file: Optional[TextIO], args: argparse.Namespace) -> None:
    """Close output file and print success message.
    
    Args:
        output_file: Open file handle or None
        args: Parsed command line arguments
    """
    if output_file:
        output_file.close()
        if not args.quiet:
            print(f"✓ Report saved to {args.output}")


def handle_error(e: Exception, args: argparse.Namespace, error_type: str = "Error") -> None:
    """Handle different types of errors uniformly.
    
    Args:
        e: Exception that was raised
        args: Parsed command line arguments
        error_type: Type of error for specialized handling
    """
    if error_type == "Configuration":
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
    elif error_type == "Plugin":
        print(f"❌ Plugin Error: {e}", file=sys.stderr)
    elif error_type == "Unexpected":
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
            print("Use --verbose for more details.")
    else:
        print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """Main entry point for the PermitCheck CLI tool."""
    args = parse_arguments()

    try:
        # Handle special commands that exit early
        if handle_cache_clearing(args):
            return
        
        if handle_license_info(args):
            return
        
        # Setup output configuration
        output_file = setup_output_file(args)
        output_format = getattr(args, 'format', 'console')
        manager = PluginManager()
        
        # Run license checks
        run_checks(args, manager, output_file, output_format)
        
        # Finalize output
        finalize_output(output_file, args)
    
    except ConfigurationError as e:
        handle_error(e, args, "Configuration")
    except PluginLoadError as e:
        handle_error(e, args, "Plugin")
    except PermitCheckError as e:
        handle_error(e, args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        handle_error(e, args, "Unexpected")


if __name__ == "__main__":
    main()
