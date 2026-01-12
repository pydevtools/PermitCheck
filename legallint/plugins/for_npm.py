from legallint.plugin import Plugin

class NpmPlugin(Plugin):
    def get_name(self):
        return "npm"

    def run(self):
        """NPM plugin not yet implemented."""
        print("NPM support is not yet implemented.")
        return None

    def load_settings(self):
        return None