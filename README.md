# NP-CLI

*No Pain Command Line Interface*


# Usage

```python
from np_cli.builder import *

class ExampleConfig(ConfigBuilder):
    # Regular old constants, can be saved and loaded from config file
    pi = NPConstant(value=4)
    
    # All args and kwargs for .add() are the same as for parser.add_argument() except dest
    # dest could not be used
    path = NPArg().add("--path", type=str, help="Path to something")
    
    # Save or not to save to config file, True by default
    foo = NPArg(save=False).add("--foo")

    # group_name utilizes parser.add_argument_group() under the hood
    bar = NPArg(group_name="example_group").add("--bar")
```

### Create config from command line
```python
c = ExampleConfig.cli()
```

### Save and load from file
```python
from pathlib import Path

# Save
config_file = Path("/somewhere/something.yaml")
c.save(config_file)

# Load
c_new = ExampleConfig.load(config_file)
```

### Subclass config
```python
class FirstConfig(ConfigBuilder):
    foo = NPArg().add("--foo")

class SecondConfig(FirstConfig):
    bar = NPArg().add("--bar")
```