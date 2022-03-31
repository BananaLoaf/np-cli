from typing import Tuple, Any, Callable
from argparse import ArgumentParser
import yaml

from pathlib import Path


ARGS = "ARGS"
KWARGS = "KWARGS"
GROUP_NAME = "GROUP_NAME"
# EXCLUSIVE_GROUP = "EXCLUSIVE_GROUP"
CONSTANT = "CONSTANT"
SAVE = "SAVE"

TYPE = "type"
ACTION = "action"
NARGS = "nargs"
REQUIRED = "required"
DEFAULT = "default"
CHOICES = "choices"
HELP = "help"


class ConfigBuilder:
    def __init__(self):
        self.__schemes__ = {}

        # Move schemes to __schemes__ and set all fields to None
        for field in self.get_fields():
            scheme = getattr(self, field)

            setattr(self, field, None)
            self.__schemes__[field] = self.set_defaults(scheme)

    @staticmethod
    def set_defaults(scheme: dict) -> dict:
        """Set all default values for a scheme"""
        scheme.setdefault(ARGS, [])
        scheme.setdefault(KWARGS, {})
        scheme.setdefault(SAVE, True)
        return scheme

    def get_fields(self) -> str:
        """Fetches all fields"""
        all_vars = {**vars(self.__class__)}
        for cls in self.__class__.__bases__:
            if cls.__name__ == ConfigBuilder.__name__:
                break
            else:
                all_vars = {**all_vars, **vars(cls)}

        for attr, value in all_vars.items():
            if not (attr.startswith("__") and attr.endswith("__")) and not isinstance(value, Callable):
                yield attr

    def get_field_scheme_value(self) -> Tuple[str, dict, Any]:
        """Fetches all available fields, schemes and values"""
        for field in self.get_fields():
            yield field, self.__schemes__[field], getattr(self, field)

    ################################################################
    def save(self, path: Path):
        """Dump yaml representation into the file"""
        self._cleanup()
        with path.open("w") as file:
            yaml.dump(self.to_dict(), file, indent=4)

    @classmethod
    def load(cls, path: Path):
        """Load config from yaml file"""
        self = cls()
        self._cleanup()

        with path.open("r") as file:
            data = yaml.load(file)

        for field in self.get_fields():
            try:
                setattr(self, field, data[field])
            except KeyError:
                raise KeyError(f"Config is missing required key '{field}'")

        return self

    def to_dict(self) -> dict:
        data = {}
        for field, scheme, value in self.get_field_scheme_value():
            data[field] = value
        return data

    def __repr__(self):
        return self.to_dict()

    ################################################################
    @classmethod
    def cli(cls, description: str):
        """Creates command line arguments parser"""
        self = cls()

        ################################################################
        # Create parser
        parser = ArgumentParser(description=description)
        groups = {}

        for field, scheme, value in self.get_field_scheme_value():
            # Set constants and skip
            if CONSTANT in scheme.keys():
                setattr(self, field, scheme[CONSTANT])
                continue

            # Create group and set as target for new argument
            if GROUP_NAME in scheme.keys():
                group_name = scheme[GROUP_NAME]

                groups.setdefault(group_name, parser.add_argument_group(group_name))
                target_parser = groups[group_name]

            else:
                target_parser = parser

            try:
                if scheme[ARGS][0].startswith("-"):
                    scheme[KWARGS]["dest"] = field
            except IndexError:
                pass
            target_parser.add_argument(*scheme[ARGS], **scheme[KWARGS])

        ################################################################
        # Parse
        args = parser.parse_args()
        for field, value in vars(args).items():
            setattr(self, field, value)

        return self

    def _cleanup(self):
        to_remove = []
        for field, scheme, value in self.get_field_scheme_value():
            if not scheme[SAVE]:
                to_remove.append(field)

        for field in to_remove:
            delattr(self, field)
            delattr(self.__class__, field)
            del self.__schemes__[field]
