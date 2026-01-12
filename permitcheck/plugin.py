import os
import abc
import sys
import importlib
from typing import Dict, List, Optional, Set, Tuple

from collections import defaultdict
from permitcheck.utils import get_basedir, check_subclass
from permitcheck.exceptions import PluginLoadError

class Plugin(abc.ABC):
    @abc.abstractmethod
    def get_name(self) -> str:
        """Returns the name of the plugin."""
        raise NotImplementedError

    @abc.abstractmethod
    def run(self) -> Optional[Dict[str, Set[str]]]:
        """Processes the input data and returns license information."""
        raise NotImplementedError

    @abc.abstractmethod
    def load_settings(self) -> Optional[Tuple[Set[str], Set[str], Set[str]]]:
        """Load PermitCheck settings"""
        raise NotImplementedError

class PluginManager:
    def __init__(self, plugindirs: Optional[List[str]] = None) -> None:
        self.plugindirs: List[str] = plugindirs if plugindirs is not None else []
        self.plugins: Dict[str, Plugin] = defaultdict(list)
        self.basedir: str = get_basedir()

    def load_plugins(self, plugin: Optional[str] = None) -> Dict[str, Plugin]:
        """Loads all plugins from the plugin directory."""
        self.plugindirs.insert(0, f"{self.basedir}/plugins")

        pth = os.getenv('PERMITCHECK_PLUGINPATH')
        if pth is not None:
            self.plugindirs.extend(pth.split(os.pathsep))

        syspath = sys.path
        for eplugin in self.plugindirs:
            sys.path = [f"{eplugin}"] + syspath
            fnames = os.listdir(eplugin)

            for fname in fnames:
                if (fname.startswith(".#") or fname.startswith("__")):
                    continue
                if not fname.startswith("for_"):
                    continue
                elif fname.endswith(".py"):
                    modname = fname[:-3]
                    self._load_plugin(modname[4:], modname)
                elif fname.endswith(".pyc"):
                    modname = fname[:-4]
                    self._load_plugin(modname[4:], modname)
        sys.path = syspath
        return self.plugins


    def _load_plugin(self, lang: str, module: str) -> None:
        """Dynamically loads a plugin module."""
        try:
            module = __import__(module)
            for attr in dir(module):
                plugin_class = getattr(module, attr)
                if isinstance(plugin_class, type) and check_subclass(plugin_class, Plugin):
                    self.plugins[lang] = plugin_class()
                    return
        except ImportError as e:
            raise PluginLoadError(f"Failed to load plugin '{module}' for language '{lang}': {e}")
        except Exception as e:
            raise PluginLoadError(f"Error initializing plugin '{module}': {e}")

    def get_plugins_by_language(self, lang: str) -> Optional[Plugin]:
        """Returns plugins that support a specific language."""
        if lang in self.plugins:
            return self.plugins[lang]
        
        available = ', '.join(self.plugins.keys()) if self.plugins else 'none'
        print(f"Plugin for '{lang}' is not loaded. Available plugins: {available}")
        return None
    
    def get_supported_languages(self) -> List[str]:
        return list(self.plugins.keys())

    def run_plugin(self, plugin_name: str) -> Optional[Dict[str, Set[str]]]:
        """Runs a specific plugin by name."""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].run()
        else:
            raise ValueError(f"Plugin '{plugin_name}' not found.")
