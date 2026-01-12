#!/usr/bin/env python
from __future__ import absolute_import
import sys
import argparse

import permitcheck
from permitcheck.plugin import PluginManager
from permitcheck.license.update import License
from permitcheck.lint import PermitCheck
from permitcheck.exceptions import (
    PermitCheckError,
    ConfigurationError,
    PluginLoadError
)

def main():
    parser = argparse.ArgumentParser(description=permitcheck.__description__)
    parser.add_argument('--verbose', action='store_true', help="Enable verbose mode")
    parser.add_argument('-v', '--version', action='version', version=f'PermitCheck {permitcheck.__version__}')

    parser.add_argument(
        '-l', '--lang',
        choices=['python', 'npm'], # ['python', 'java', 'npm'],
        nargs='+',  # one or more options
        help='Select one or more languages from: python' # python, java, npm
    )
    parser.add_argument('-u', '--update', action='store_true', help="Enable update mode")
    parser.add_argument('--license', action='store_true', help="Enable license mode")

    args = parser.parse_args()

    try:
        if getattr(args, 'license', False):
            License.get()
            return

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
                    print("-" * 15)
                    print(f"   {plugins[lang].get_name().upper()}")
                    print("-" * 15)
                    PermitCheck(deps, settings)
        else:
            print("No plugins found. Please ensure plugins are available.")
            sys.exit(1)
    
    except ConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PluginLoadError as e:
        print(f"Plugin Error: {e}", file=sys.stderr)
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
