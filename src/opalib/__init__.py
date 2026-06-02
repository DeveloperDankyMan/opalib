# __init__.py

"""opalib package API."""

import os
import importlib

__all__ = []

pkg_dir = os.path.dirname(__file__)
for file in os.listdir(pkg_dir):
    if file.endswith(".py") and file != "__init__.py":
        module_name = file[:-3]
        module = importlib.import_module(f".{module_name}", package=__name__)

        for attribute in dir(module):
            if attribute.startswith("_"):
                continue
            globals()[attribute] = getattr(module, attribute)
            if attribute not in __all__:
                __all__.append(attribute)

        globals()[module_name] = module
        if module_name not in __all__:
            __all__.append(module_name)
