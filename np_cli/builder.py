from typing import Tuple, Any, Callable
from argparse import ArgumentParser
import yaml
import re

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

        # Move schemes to __schemes__ and set all arg values to None
        for attr_name in self.get_arg_names():
            scheme = getattr(self, attr_name)

            setattr(self, attr_name, None)
            self.__schemes__[attr_name] = self.set_defaults(scheme)

    @staticmethod
    def set_defaults(scheme: dict) -> dict:  # TODO remove
        """Set all default values for a scheme"""
        scheme.setdefault(ARGS, [])
        scheme.setdefault(KWARGS, {})
        scheme.setdefault(SAVE, True)
        return scheme

    def get_arg_names(self) -> str:
        """Fetches all args"""
        all_attrs = {**vars(self.__class__)}
        for cls in self.__class__.__bases__:
            # If descended to ConfigBuilder, stop
            if cls is ConfigBuilder:
                break

            # Parse all attrs
            all_attrs = {**all_attrs, **vars(cls)}

        for name, value in all_attrs.items():
            if re.match("^__.*__$", name) is not None or isinstance(value, Callable):
                continue
            yield name

    def get_arg_name_scheme_value(self) -> Tuple[str, dict, Any]:
        """Fetches all available attr names, schemes and values"""
        for arg_name in self.get_arg_names():
            yield arg_name, self.__schemes__[arg_name], getattr(self, arg_name)

    def to_dict(self, exclude_unsaved: bool = False) -> dict:
        data = {}
        for name, scheme, value in self.get_arg_name_scheme_value():
            if not scheme[SAVE] and exclude_unsaved:
                continue
            data[name] = value
        return data

    def __repr__(self):
        return self.to_dict()

    ################################################################

    def save(self, path: Path):
        """Dump config to yalm file"""
        with path.open("w") as file:
            yaml.dump(self.to_dict(exclude_unsaved=True), file, indent=4)

    @classmethod
    def load(cls, path: Path):
        """Load config from yaml file"""
        self = cls()

        with path.open("r") as file:
            data = yaml.load(file)

        for name, scheme, value in self.get_arg_name_scheme_value():
            try:
                if scheme[SAVE]:
                    setattr(self, name, data[name])

            except KeyError:
                raise KeyError(f"Config is missing required key '{name}'")

        return self

    ################################################################
    @classmethod
    def cli(cls, description: str):
        """Creates command line arguments parser"""
        self = cls()

        ################################################################
        # Create parser
        parser = ArgumentParser(description=description)
        groups = {}

        for name, scheme, value in self.get_arg_name_scheme_value():
            # Set constants and skip
            if CONSTANT in scheme.keys():
                setattr(self, name, scheme[CONSTANT])
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
                    scheme[KWARGS]["dest"] = name
            except IndexError:
                pass
            target_parser.add_argument(*scheme[ARGS], **scheme[KWARGS])

        ################################################################
        # Parse
        args = parser.parse_args()
        for name, value in vars(args).items():
            setattr(self, name, value)

        return self
