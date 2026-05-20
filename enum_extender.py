"""
enum_extender - a Python version of https://github.com/buildthomas/EnumExtender
"""

from enum import Enum as PyEnum

class EnumRegistry:
    def __init__(self):
        self._enums = {}

    def new(self, name, items):
        if not isinstance(name, str):
            raise TypeError("Enum name must be a string")

        if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
            raise TypeError("Enum items must be a list of strings")

        if name in self._enums:
            raise ValueError(f"Enum '{name}' already exists")

        # Create a real Python Enum class dynamically
        enum_class = PyEnum(name, {item: index for index, item in enumerate(items)})

        self._enums[name] = enum_class
        return enum_class

    def __getattr__(self, name):
        if name in self._enums:
            return self._enums[name]
        raise AttributeError(f"Enum '{name}' does not exist")

    def find(self, name):
        return self._enums.get(name)

    def from_value(self, enum_name, value):
        enum_class = self._enums.get(enum_name)
        if enum_class is None:
            return None

        for item in enum_class:
            if item.value == value:
                return item
        return None


# Exported instance
Enums = EnumRegistry()
