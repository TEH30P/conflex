from typing import Mapping, Sequence, List, Iterable, Sized, Tuple, Any, Union, AbstractSet
from abc import ABC, abstractmethod

import copy as m_cp
import logging as m_log

gv_log = m_log.getLogger(__name__)
NODE_SEP: str = '/'


def _opt_int_parse(iv: str) -> int:
    if type(iv) is not str:
        return int(iv)
    v_m: int = {
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024,
        'TB': 1024 * 1024 * 1024 * 1024,
        'PB': 1024 * 1024 * 1024 * 1024 * 1024
        }.get(iv[-2:], 1)
    if v_m > 1:
        return int(iv[:-2]) * v_m
    v_m: int = {
        'K': 1000,
        'M': 1000 * 1000,
        'G': 1000 * 1000 * 1000,
        'T': 1000 * 1000 * 1000 * 1000,
        'P': 1000 * 1000 * 1000 * 1000 * 1000
        }.get(iv[-1:], 1)
    if v_m > 1:
        return int(iv[:-1]) * v_m
    return int(iv)


def _opt_float_parse(iv: str) -> float:
    return float(iv)


def _opt_name_split(iv: str):
    l_name = iv.split('_', maxsplit=1)
    if len(l_name) == 2:
        if l_name[0] not in ['s', 'v', 'l']:
            return '', iv
        else:
            return l_name[0], l_name[1]
    else:
        return '', iv


class NodeAbc(ABC):
    """
    Abstract base class for all config options and sections.
    """
    def __init__(self, iv_kind: str):
        self.kind: str = iv_kind
        self.name: str = ''
        self.child_l: Sequence = []
        self.required = False

    def name_set(self, iv: str):
        assert isinstance(iv, str)
        if len(iv) == 0:
            raise ValueError('Config option name must not to be empty.')

        v_kind, v_name = _opt_name_split(iv)

        if len([v for v in v_name if v.isspace() or v == NODE_SEP]):
            raise ValueError(f'Config option name must not contains `{NODE_SEP}` or space characters.')
        if len(self.name):
            raise ValueError('Name of option is already set it can not be updated.')
        if len(v_kind) != 0 and v_kind != self.kind:
            raise ValueError('Kind of option can not be updated.')

        self.name = v_name

    # self << iv
    def __lshift__(self, iv):
        if not isinstance(iv, str) and isinstance(iv, Sequence):
            self.child_l = iv
        elif isinstance(iv, NodeAbc):
            self.child_l = (iv,)
        else:
            raise SyntaxError(
                'Config option definition syntax is:'
                '\n`option-name-as-string , ">>" , option-object [ , "<<" , "{" , child-options-as-set , "}" ]`')
        return self

    # iv >> self
    def __rrshift__(self, iv):
        if type(iv) is str:
            self.name_set(iv)
        else:
            raise SyntaxError(
                'Config option definition syntax is:'
                '\n`option-name-as-string , ">>" , option-object [ , "<<" , "{" , child-options-as-set , "}" ]`')
        return self

    def __hash__(self):
        return hash(self.name)


class Section(NodeAbc):
    """
    Config section.
    """
    def __init__(self):
        super().__init__('s')


class OptionAbc(NodeAbc):
    """
    Root class for all config options.
    """
    def __init__(self, iv_kind: str):
        super().__init__(iv_kind)
        self.default = None

    @abstractmethod
    def value_parse(self, iv):
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def default_get(self, iv_path: str):
        raise NotImplementedError()  # pragma: no cover


class OptValue(OptionAbc):
    """
    Single valued untyped option.
    """
    def __init__(self, iv_default=None, iv_required: bool = None):
        super().__init__('v')
        if iv_default is not None:
            # !!!TODO: replace with allowable type list
            assert isinstance(iv_default, str) or not isinstance(iv_default, (Mapping, Sequence)),\
                r'Default value for `v` kind of options should be str, int, float, etc.'
            self.default = self.value_parse(iv_default)
        else:
            self.default = None
            self.required = True if iv_required is None else iv_required

    def value_parse(self, iv):
        return iv

    def default_get(self, iv_path: str):
        if self.required:
            raise KeyError(f'The config option at {iv_path} is required.')
        return self.default


class OptVInt(OptValue):
    """
    Single valued option that should contain `int` value.
    Supports suffixes `K` for 1000 and `KB` for 1024 multiplier and also `M`, `G`, `P`, `T` , `MB`, `GB`, `PB`, `TB`
    suffixes with similar behavior.
    """
    def value_parse(self, iv: str) -> int:
        return _opt_int_parse(iv)


class OptVChoice(OptValue):
    """
    Single valued option that contain `str` keys which is mapped to some values.
    """
    def __init__(self, il_mapping: dict, iv_default=None, iv_required: bool = None):
        if isinstance(il_mapping, Mapping):
            self._mapping_l = il_mapping
        else:
            self._mapping_l = dict(il_mapping)
        if len(self._mapping_l) == 0:
            raise ValueError(r'Parameter il_mapping is empty.')
        super().__init__(iv_default, iv_required)

    def value_parse(self, iv):
        return self._mapping_l[iv]


class OptVFloat(OptValue):
    """
    Single valued option that should contain `float` value.
    """
    def value_parse(self, iv: str) -> float:
        return _opt_float_parse(iv)


class OptList(OptionAbc):
    """
    List contained option with untyped values.
    """
    def __init__(self, iv_default=None, iv_required: bool = None):
        super().__init__('l')
        if iv_default is None:
            self.default = []
            self.required = True if iv_required is None else iv_required
        else:
            self.default = \
                [self.value_parse(v)
                 for v in (iv_default if isinstance(iv_default, Sequence) else [iv_default])]
            self.required = False

    def value_parse(self, iv):
        return iv
    
    def default_get(self, iv_path: str):
        if self.required:
            raise KeyError(f'The config option at {iv_path} is required.')
        return self.default


class OptLInt(OptList):
    """
    List contained option with values of type `int`. Multiplication prefixes is supported.
    """
    def value_parse(self, iv: str) -> int:
        return _opt_int_parse(iv)


class OptLFloat(OptList):
    """
    List contained option with values of type `float`.
    """
    def value_parse(self, iv: str) -> float:
        return _opt_float_parse(iv)


def as_node(iv_name: str) -> NodeAbc:
    """
    :param iv_name: name of the config node (option or section).
        If name have a prefix "s_" function returns `Section` object named without prefix.
        Also function returns object with non-refixed name for prefix "v_" --`OptValue` and for prefix
        "l_" -- `OptList`. If name have no prefix ("s_", "v_", "l_") then function returns `Section`.
    :return: Option or section object.
    """
    v_kind, v_name = _opt_name_split(iv_name)

    if v_kind in ['', 's']:
        return v_name >> Section()
    elif v_kind == 'v':
        return v_name >> OptValue()
    elif v_kind == 'l':
        return v_name >> OptList()


def _parser_dict_create(il_tree) -> dict:
    """Create plain dict parser from input tree of opt definitions `NodeAbc objects`.

    :param il_tree: NodeAbc or Sequence
    :return: None
    """
    assert isinstance(il_tree, (NodeAbc, Sequence)), f'{type(il_tree).__qualname__} is not NodeAbc or Sequence'
    l_l_root: list = [('', [il_tree] if isinstance(il_tree, NodeAbc) else il_tree)]
    l_plain: dict = {}
    while len(l_l_root):
        v_kp, l_root = l_l_root.pop()
        if v_kp:
            v_kp = f'{v_kp}{NODE_SEP}'
        for v_v in l_root:
            if isinstance(v_v, NodeAbc):
                if len(v_v.child_l):
                    child_l: list = v_v.child_l if isinstance(v_v.child_l, list) else list(v_v.child_l)
                    l_l_root.append((f'{v_kp}{v_v.name}', child_l))
                    v_v.child_l = ()
                if f'{v_kp}{v_v.name}' in l_plain:
                    raise KeyError(f'The option named `{v_kp}{v_v.name}` is already exists.')
                l_plain[f'{v_kp}{v_v.name}'] = v_v
            elif isinstance(v_v, str):
                if f'{v_kp}{_opt_name_split(v_v)[1]}' in l_plain:
                    raise KeyError(f'The option named `{v_kp}{_opt_name_split(v_v)[1]}` is already exists.')
                l_plain[f'{v_kp}{_opt_name_split(v_v)[1]}'] = as_node(v_v)
    return l_plain


class ConfTreeWalker:
    class Missing:
        ...

    def __init__(self, il_tree_slice: list):
        self.node_l: list = il_tree_slice
        self.kind: str = ''
        self.key: str = ''
        self.path: str = ''
        self.path_raw: str = ''
        self.is_slice_list = False

    def move(self, il_parser: Mapping[str, OptionAbc], iv_key_raw: str):
        self._curr_set(il_parser, iv_key_raw)
        self.is_slice_list = True if self.is_slice_list else self.kind == 'l'
        l_node_new: list = []
        for v_opt in self.node_l:
            if not isinstance(v_opt, Mapping):
                l_node_new.append(self.Missing())
                continue
            if self.key in v_opt:
                v_opt = v_opt[self.key]
            elif f'{self.kind}_{self.key}' in v_opt:
                v_opt = v_opt[f'{self.kind}_{self.key}']
            else:
                l_node_new.append(self.Missing())
                continue
            if self.kind in ('s', 'l') and isinstance(v_opt, list):
                l_node_new.extend(v_opt)
            else:
                l_node_new.append(v_opt)
        self.node_l = l_node_new

    def node_exist(self) -> bool:
        return any([type(v) is not self.Missing for v in self.node_l])

    def slice_exist(self, iv_idx) -> bool:
        v_nd = self.node_l[iv_idx] if len(self.node_l) > iv_idx else None
        return v_nd is not None and type(v_nd) is not self.Missing

    def value_get(self, il_parser: Mapping[str, OptionAbc]) -> Union[list, Any]:
        if self.kind == 's':
            raise TypeError('Sections can not have a value.')
        v_parser: OptionAbc = il_parser[self.path]
        l_ret: list = []
        for v_opt in self.node_l:
            if isinstance(v_opt, Mapping):
                v_opt = v_opt.get('v')
            if type(v_opt) is self.Missing:
                if self.kind == 'l':
                    l_ret.extend(v_parser.default_get(self.path_raw))
                if self.kind == 'v':
                    l_ret.append(v_parser.default_get(self.path_raw))
            else:
                l_ret.append(v_parser.value_parse(v_opt))
        if self.is_slice_list:
            return l_ret
        else:
            return l_ret[0] if len(l_ret) else None

    def _curr_set(self, il_parser: Mapping[str, OptionAbc], iv_raw: str):
        l_key_part = iv_raw.split('_', maxsplit=1)
        v_key_part_len = len(l_key_part)
        v_path_pref: str = f'{self.path}{NODE_SEP}' if self.path else ''
        if v_key_part_len == 2:
            if l_key_part[0] not in ['s', 'v', 'l']:
                self.kind = str(il_parser[f'{v_path_pref}{iv_raw}'].kind)
                self.key = iv_raw
            elif il_parser[f'{v_path_pref}{l_key_part[1]}'].kind != l_key_part[0]:
                raise KeyError(f'Option `{v_path_pref}{l_key_part[1]}` exist but have different kind.')
            else:
                self.kind, self.key = l_key_part
        elif v_key_part_len == 1:
            self.kind = str(il_parser[f'{v_path_pref}{iv_raw}'].kind)
            self.key = iv_raw
        self.path_raw = f'{v_path_pref}{iv_raw}'
        self.path = f'{v_path_pref}{self.key}'


def _walker_knot_merge(il_walker: List[ConfTreeWalker]) -> ConfTreeWalker:
    v_wl = il_walker[-1]
    for v in il_walker:
        if v.node_exist():
            v_wl = v
    return v_wl


def _walker_slice_merge(il_walker: List[ConfTreeWalker], iv_node_idx: int) -> ConfTreeWalker:
    v_nd = None
    for v in il_walker:
        if v.slice_exist(iv_node_idx):
            v_nd = v.node_l[iv_node_idx]
    v_wl: ConfTreeWalker = il_walker[-1]
    v_r = ConfTreeWalker([v_nd])
    v_r.key = v_wl.key
    v_r.kind = v_wl.kind if v_wl.kind == 's' else 'v'
    v_r.path = v_wl.path
    v_r.path_raw = v_wl.path_raw
    return v_r


class Config(Mapping[str, Any]):
    """
    Root class for configuration.
    Represent dictionary of configuration options with keys containing full path to corresponding option separated with
    `conflex.NODE_SEP` string.
    """
    def __init__(self, il_parser: Union[NodeAbc, Sequence] = None):
        self._walker_l = [ConfTreeWalker([])]
        self._parser_l: Mapping[str, OptionAbc] = _parser_dict_create(il_parser) if il_parser is not None else {}

    def __getitem__(self, item: str):
        return _walker_knot_merge(self._node_get(self._walker_l_copy(), item)).value_get(self._parser_l)

    def __iter__(self):
        return self._parser_l.keys().__iter__()

    def __len__(self):
        return len(self._parser_l)

    def items(self):
        return ConfigItemsView(self._walker_l, self._parser_l)

    def _walker_l_copy(self) -> List[ConfTreeWalker]:
        return [m_cp.copy(v) for v in self._walker_l]

    def _node_get(self, il_walker: List[ConfTreeWalker], iv_path: str) -> List[ConfTreeWalker]:
        assert isinstance(iv_path, str), r'Option path is not a str.'
        if len(iv_path) == 0:
            raise KeyError(r'Option path is empty.')
        l_wl = il_walker
        for v_key_raw in iv_path.split(NODE_SEP):
            if len(v_key_raw) == 0:
                raise KeyError(r'Option path have invalid format.'
                               f'Format is: `option-or-section , {{ "{NODE_SEP}" , option-or-section }}`,'
                               f' repeatable "{NODE_SEP}" is prohibited.')
            for v in l_wl:
                v.move(self._parser_l, v_key_raw)
        return l_wl

    def slice(self, iv_path: str):
        l_wl: List[ConfTreeWalker] = self._node_get(self._walker_l_copy(), iv_path)
        v_len = max((len(v.node_l) for v in l_wl))
        for v_idx in range(v_len):
            yield SubConfig([_walker_slice_merge(l_wl, v_idx)], self._parser_l)

    def knot(self, iv_path: str):
        return SubConfig(self._node_get(self._walker_l_copy(), iv_path), self._parser_l)

    def load_dicts(self, ill_raw_conf: Iterable[Union[Mapping, Iterable]]) -> None:
        l_wl: List[ConfTreeWalker] = []
        for l_raw_conf in ill_raw_conf:
            if isinstance(l_raw_conf, Mapping):
                l_wl.append(ConfTreeWalker([l_raw_conf]))
            else:
                l_wl.append(ConfTreeWalker([dict(l_raw_conf)]))
        self._walker_l = l_wl


class SubConfig(Config):
    """
    Class inherited from `Config` represent sub-tree of configuration.
    `Config.node` and `Config.slice` returns objects of this type.
    """
    def __init__(self, il_parent_walker: List[ConfTreeWalker], il_parser: Mapping[str, OptionAbc]):
        super().__init__()
        assert all(type(v) is ConfTreeWalker for v in il_parent_walker)
        self._walker_l = il_parent_walker
        self._parser_l = il_parser
        self.kind = il_parent_walker[0].kind
        self.path = il_parent_walker[0].path_raw

    @property
    def v(self):
        return _walker_knot_merge(self._walker_l).value_get(self._parser_l)

    def _node_get(self, il_walker: List[ConfTreeWalker], iv_path: str) -> List[ConfTreeWalker]:
        assert isinstance(iv_path, str), r'Option sub-path is not a str.'
        if len(iv_path) == 0:
            raise KeyError(r'Option sub-path is empty.')
        l_wl = il_walker
        for v_key_raw in iv_path.split(NODE_SEP):
            if len(v_key_raw) == 0:
                raise KeyError(r'Option sub-path have invalid format.'
                               f'Format is: `option-or-section , {{ "{NODE_SEP}" , option-or-section }}`,'
                               f' repeatable "{NODE_SEP}" is prohibited.')
            for v in l_wl:
                v.move(self._parser_l, v_key_raw)
        return l_wl

    def load_dicts(self, ill_raw_conf: Iterable[Union[Mapping, Iterable]]) -> None:
        l_wl: List[ConfTreeWalker] = []
        for l_raw_conf in ill_raw_conf:
            if isinstance(l_raw_conf, Mapping):
                l_wl.append(ConfTreeWalker([l_raw_conf]))
            else:
                l_wl.append(ConfTreeWalker([dict(l_raw_conf)]))
        self._walker_l = self._node_get(l_wl, self._walker_l[0].path_raw)


class ConfigItemsView(Iterable, Sized):
    def __init__(self, il_walker: List[ConfTreeWalker], il_parser: Mapping[str, OptionAbc]):
        assert all(type(v) is ConfTreeWalker for v in il_walker)
        self._walker_l = il_walker
        self._parser_l = il_parser
        self._opt_path_l = set((v_k for v_k, v_i in il_parser.items() if v_i.kind != 's'))

    def __iter__(self):
        return ConfigIter(SubConfig(self._walker_l, self._parser_l), self._opt_path_l)

    def __len__(self) -> int:
        return len(self._opt_path_l)

    def __contains__(self, iv: Tuple[str, Any]) -> bool:
        assert type(iv) is tuple and len(iv) == 2
        assert isinstance(iv[0], str), r'Option path is not a str.'
        v_path: str = iv[0]
        if len(v_path) == 0:
            return False
        if v_path not in self._opt_path_l:
            return False
        l_wl = [m_cp.copy(v) for v in self._walker_l]
        for v_key_raw in v_path.split(NODE_SEP):
            v_exist: bool = False
            for v in l_wl:
                v.move(self._parser_l, v_key_raw)
                v_exist = v_exist or v.node_exist()
            if not v_exist:
                return False
        return _walker_knot_merge(l_wl).value_get(self._parser_l) == iv[1]


class ConfigIter:
    # !!!TODO: optimize this. switch to use `ConfTreeWalker`.
    def __init__(self, iv_parent: SubConfig, il_path: Iterable[str]):
        self._conf = iv_parent
        self._path_offset = len(self._conf.path)
        self._path_iter = il_path.__iter__()

    def __next__(self):
        v_path = self._path_iter.__next__()[self._path_offset:]
        return v_path, self._conf[v_path]
