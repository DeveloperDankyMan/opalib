# __init__.py
import os
import importlib

# Get all .py files in this folder (excluding this file)
pkg_dir = os.path.dirname(__file__)
for file in os.listdir(pkg_dir):
    if file.endswith(".py") and file != "__init__.py":
        module_name = file[:-3]
        module = importlib.import_module(f".{module_name}", package=__name__)
        
        # Expose everything from the module to the package level
        for attribute in dir(module):
            if not attribute.startswith("_"):
                globals()[attribute] = getattr(module, attribute)
