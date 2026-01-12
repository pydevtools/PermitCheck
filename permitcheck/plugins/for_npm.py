"""NPM plugin for PermitCheck."""

import sys
from permitcheck.plugin import Plugin


class NpmPlugin(Plugin):
    """Plugin for NPM package manager (not yet implemented)."""
    
    def get_name(self):
        return "npm"

    def run(self):
        """NPM plugin not yet implemented."""
        print("NPM support is not yet implemented.", file=sys.stderr)
        return None

    def load_settings(self):
        return None