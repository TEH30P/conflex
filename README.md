# Conflex
Flexible, extensible configuration reader for Python 3.6+ projects for multiple tree-like config sources.

## Introduction
**Conflex** means "flexible configuration" it is a tool for parsing tree-like configuration with 
any level of depth. Thus, here the configuration is a tree structure with two types of nodes: 
_Section_ and _Option_. _Sections_ is used for grouping other nodes and _option_ is a key-value 
pair. As it mentioned above depth is unlimited, _section_ can have a child _sections_  moreover
_options_ can have child _options_ or _sections_. Checkout the "test/*' files for a more extended 
examples.

The _option_ can contain list or single value. If list-typed _option_ contains single value it 
is not cause an error this value will be treated as list with one element.  

The input data is `dict` that contains tree representation for example `{ section : { key0 : value0, 
child_section { key00: value00, key01: value01 } } }`. YAML and JSON parsers returns that kind of
object.


## Basic usage
```python
# app/config.py
import conflex


def get_sourse(filename) -> dict:
    """
    Function that returns parsed to`dict` configuration.
    For example:
        {'main': {'master_ip': '192.168.0.1', 'master_port': 42}} 
    """
    ...


def load_config() -> Config:    
    config = Config((
        'main' >> Section() << (
            'master_ip'     << OptValue(iv_default='127.0.0.1'),
            'master_port'   << OptVInt(iv_required=True),
            'packet_size'   << OptVInt(iv_default='1KB') << (
                'source' << OptVChoice(
                    iv_default='conf',
                    il_mapping={'conf': 0, 'arg': 1})
        )))
    )
    sources = []
    sources.append(get_sourse('app_default.conf'))
    sources.append(get_sourse('app.conf'))
    config.load_dicts(sources)
    return config
``` 

```python
# app/main.py
from app.config import load_config

SRC_CONF = 0
SRC_ARG = 1

config = load_config()
print(config['main/master_ip'])
sub_config = config.knot('main')
print(sub_config['port'])
if sub_config['packet_size/source'] == SRC_CONF:
    print(sub_config['packet_size'])  # will output `int` 1024
print(dict(config.items()))
```

## Installation
```shell
pip install conflex
```
