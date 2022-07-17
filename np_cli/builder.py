from typing import Tuple, Any, Union
from argparse import ArgumentParser
import yaml

from pathlib import Path


class NPArg:
    def __init__(self, save: bool = True, group_name: str = None):
        self.save = save
        self.group_name = group_name

        self.args = ()
        self.kwargs = {}

    def add(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self

    def __repr__(self) -> Tuple[tuple, dict]:
        return self.args, self.kwargs


class NPConstant:
    def __init__(self, value: Any, save: bool = True):
        self.value = value
        self.save = save

    def __repr__(self):
        return self.value


class NPNull:
    def __repr__(self) -> str:
        return self.__class__.__name__


class ConfigBuilder:
    def __init__(self):
        self.__schemes__ = {}

        # Move schemes to __schemes__ and set all arg values to NPNull
        for attr_name in self.get_arg_names():
            scheme = getattr(self, attr_name)

            setattr(self, attr_name, NPNull())
            self.__schemes__[attr_name] = scheme

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
            if isinstance(value, (NPArg, NPConstant)):
                yield name

    def get_arg_name_scheme_value(self) -> Tuple[str, Union[NPArg, NPConstant], Any]:
        """Fetches all available attr names, schemes and values"""
        for arg_name in self.get_arg_names():
            yield arg_name, self.__schemes__[arg_name], getattr(self, arg_name)

    def to_dict(self, exclude_unsaved: bool = False) -> dict:
        data = {}
        for name, scheme, value in self.get_arg_name_scheme_value():
            if not scheme.save and exclude_unsaved:
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
                if scheme.save:
                    setattr(self, name, data[name])

            except KeyError:
                raise KeyError(f"Config is missing required key '{name}'")

        return self

    ################################################################
    @classmethod
    def cli(cls, *args):
        """Creates command line arguments parser"""
        self = cls()

        ################################################################
        # Create parser
        parser = ArgumentParser(*args)
        groups = {}

        for name, scheme, value in self.get_arg_name_scheme_value():
            # Set constant and continue
            if isinstance(scheme, NPConstant):
                setattr(self, name, scheme.value)
                continue

            # Create group if needed and select as target
            if scheme.group_name is not None:
                groups.setdefault(scheme.group_name, parser.add_argument_group(scheme.group_name))
                target_parser = groups[scheme.group_name]
            else:
                target_parser = parser

            try:
                if scheme.args[0].startswith("-"):
                    scheme.kwargs["dest"] = name
            except IndexError:
                pass
            target_parser.add_argument(*scheme.args, **scheme.kwargs)

        ################################################################
        # Parse
        args = parser.parse_args()
        for name, value in vars(args).items():
            setattr(self, name, value)

        return self
