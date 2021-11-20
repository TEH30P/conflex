from typing import Mapping, Sequence, Set, List, Any, Union

import copy as m_cp
import logging as m_log

gv_log = m_log.getLogger(__name__)
NODE_SEP: str = '/'

def _opt_int_parse(iv: str) -> int:
    if type(iv) is not str:
        return int(iv)

    v_mult: int = \
        { 'KB': 1024
        , 'MB': 1024 * 1024
        , 'GB': 1024 * 1024 * 1024
        , 'TB': 1024 * 1024 * 1024 * 1024
        , 'PB': 1024 * 1024 * 1024 * 1024 * 1024
        }.get(iv[-2:], 1)
    if v_mult > 1:
        return int(iv[:-2]) * v_mult
    else:
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


class DefOptAbc:
    def __init__(self, iv_kind: str):
        self.kind: str = iv_kind
        self.name: str = ''
        self.child_l: Set = set()
        self.required = False

    def name_set(self, iv: str):
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
        if isinstance(iv, Set):
            self.child_l = frozenset(iv)
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

    def __eq__(self, iv):
        # !!!TODO: deprecated, duplicate detection should be in `Config.__init__` and parser tree should be a `dict`.
        if isinstance(iv, str):
            if iv == self.name:
                raise KeyError(f'The option named `{self.name}` is already exists.')
        elif isinstance(iv, DefOptAbc):
            if iv.name == self.name:
                raise KeyError(f'The option named `{self.name}` is already exists.')
        else:
            raise TypeError('Only plain strings `str` or derived from `DefOptAbc` objects allowed.')
        return False


class DefSection(DefOptAbc):
    def __init__(self):
        super().__init__('s')


class DefItemAbc(DefOptAbc):
    def __init__(self, iv_kind: str):
        super().__init__(iv_kind)
        self.default = None

    def value_parse(self, iv):
        raise NotImplementedError('Method must be overridden.')

    def default_get(self, iv_path: str):
        raise NotImplementedError('Method must be overridden.')


class DefValue(DefItemAbc):
    def __init__(self, iv_default=None, iv_required: bool = None):
        super().__init__('v')
        if iv_default is not None:
            # !!!TODO: replace with allowable type list
            assert isinstance(iv_default, str) or not isinstance(iv_default, (Mapping, Sequence)) \
                , r'Default value for `v` kind of options should be str, int, float, etc.'
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


class DefValueInt(DefValue):
    def value_parse(self, iv: str) -> int:
        return _opt_int_parse(iv)


class DefValueChoise(DefValue):
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


class DefValueFloat(DefValue):
    def value_parse(self, iv: str) -> float:
        return _opt_float_parse(iv)


class DefList(DefItemAbc):
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


class DefListInt(DefList):
    def value_parse(self, iv: str) -> int:
        return _opt_int_parse(iv)


class DefListFloat(DefList):
    def value_parse(self, iv: str) -> float:
        return _opt_float_parse(iv)


def def_opt(iv_name: str) -> DefOptAbc:
    v_kind, v_name = _opt_name_split(iv_name)

    if v_kind in ['', 's']:
        return v_name >> DefSection()
    elif v_kind == 'v':
        return v_name >> DefValue()
    elif v_kind == 'l':
        return v_name >> DefList()


def _parser_dict_create(il_tree: set) -> dict:
    """Create plain dict parser from input tree of opt definitions `DefOptAbc objects`.

    :param il_tree: Set
    :return: None
    """

    assert isinstance(il_tree, Set), f'{type(il_tree).__qualname__} is not `set` of `frozenset`'

    l_l_root: list = [('', il_tree)]
    l_plain: dict = {}

    while len(l_l_root):
        v_kp, l_root = l_l_root.pop()

        for v_v in l_root:
            if isinstance(v_v, DefOptAbc):
                if len(v_v.child_l):
                    l_l_root.append((f'{v_kp}{NODE_SEP}{v_v.name}', v_v.child_l))
                    v_v.child_l = frozenset()
                l_plain[f'{v_kp}{NODE_SEP}{v_v.name}'] = v_v
            elif isinstance(v_v, str):
                l_plain[f'{v_kp}{NODE_SEP}{_opt_name_split(v_v)[1]}'] = def_opt(v_v)

    return l_plain


class ConfTreeWalker:
    def __init__(self, il_tree_slice: list = []):
        self.node_curr_l: list = il_tree_slice
        self.kind_curr: str = ''
        self.key_curr: str = ''
        self.path_curr: str = ''
        self.path_raw_curr: str = ''
        self.is_slice_list = False

    def move(self, il_parser: Mapping[str, DefItemAbc], iv_key_raw: str):
        self._curr_set(il_parser, iv_key_raw)
        self.is_slice_list = True if self.is_slice_list else self.kind_curr == 'l'
        l_node_new: list = []
        for v_opt in self.node_curr_l:
            if v_opt is None:
                continue
            if not isinstance(v_opt, Mapping):
                l_node_new.append(None)
                continue
            v_opt = v_opt.get(self.key_curr, v_opt.get(f'{self.kind_curr}_{self.key_curr}'))
            if self.kind_curr == 'l' and isinstance(v_opt, list):
                l_node_new.extend(v_opt)
            else:
                l_node_new.append(v_opt)
        self.node_curr_l = l_node_new

    def value_get(self, il_parser: Mapping[str, DefItemAbc]) -> Union[list, Any]:
        if self.kind_curr == 's':
            raise TypeError('Sections can not have a value.')
        v_parser: DefItemAbc = il_parser[self.path_curr]
        l_ret: list = []
        if len(self.node_curr_l) == 0:
            l_ret = v_parser.default_get(self.path_raw_curr) \
                if self.kind_curr == 'l' else [v_parser.default_get(self.path_raw_curr)]
        else:
            for v_opt in self.node_curr_l:
                if isinstance(v_opt, Mapping):
                    v_opt = v_opt.get('v')
                if v_opt is None:
                    if self.kind_curr == 'l':
                        l_ret.extend(v_parser.default_get(self.path_raw_curr))
                    if self.kind_curr == 'v':
                        l_ret.append(v_parser.default_get(self.path_raw_curr))
                else:
                    l_ret.append(v_parser.value_parse(v_opt))
        if self.is_slice_list:
            return l_ret
        else:
            return l_ret[0] if len(l_ret) else None

    def _curr_set(self, il_parser: Mapping[str, DefItemAbc], iv_raw: str):
        l_key_part = iv_raw.split('_', maxsplit=1)
        v_key_part_len = len(l_key_part)
        if v_key_part_len == 2:
            if l_key_part[0] not in ['s', 'v', 'l']:
                self.kind_curr = str(il_parser[f'{self.path_curr}{NODE_SEP}{iv_raw}'].kind)
                self.key_curr = iv_raw
            elif il_parser[f'{self.path_curr}{NODE_SEP}{l_key_part[1]}'].kind != l_key_part[0]:
                raise KeyError(f'Option `{self.path_curr}{NODE_SEP}{l_key_part[1]}` exist but have different kind.')
            else:
                self.kind_curr, self.key_curr = l_key_part
        elif v_key_part_len == 1:
            self.kind_curr = str(il_parser[f'{self.path_curr}{NODE_SEP}{iv_raw}'].kind)
            self.key_curr = iv_raw
        self.path_raw_curr += f'{NODE_SEP}{iv_raw}'
        self.path_curr += f'{NODE_SEP}{self.key_curr}'


class Config(Mapping):
    def __init__(self, il_parser: set = None):
        self._walker_l = [ConfTreeWalker()]
        self._parser_l: Mapping[str, DefItemAbc] = _parser_dict_create(il_parser) if il_parser is not None else {}
        self._iter = None

    def _my_iter(self):
        if self._iter is None:
            self._iter = ConfigIter(self, self._parser_l)
        return self._iter

    def __getitem__(self, item):
        return self._node_get(item).value_get(self._parser_l)

    def __iter__(self):
        return m_cp.copy(self._my_iter())

    def __len__(self):
        return len(self._my_iter())

    def _node_get(self, iv_path: str) -> ConfTreeWalker:
        assert isinstance(iv_path, str), r'Option path is not a str.'
        if len(iv_path) == 0:
            raise KeyError(r'Option path is empty.')
        if iv_path[0] != NODE_SEP:
            raise KeyError(r'Option path have invalid format. '
                           f'Format is: `{{ "{NODE_SEP}" , option-or-section }}`,'
                           f' "{NODE_SEP}" at beginning is required.')
        v_path_raw = iv_path[1:]
        v_walker = m_cp.copy(self._walker_l[0])
        for v_key_raw in v_path_raw.split(NODE_SEP):
            if len(v_key_raw) == 0:
                raise KeyError(r'Option path have invalid format.'
                               f'Format is: `{{ "{NODE_SEP}" , option-or-section }}`,'
                               f' repeatable "{NODE_SEP}" is prohibited.')
            v_walker.move(self._parser_l, v_key_raw)
        return v_walker

    def slice(self, iv_path: str):
        v_walker: ConfTreeWalker = self._node_get(iv_path)
        for v_node in v_walker.node_curr_l:
            v_child = ConfTreeWalker([v_node])
            v_child.key_curr = v_walker.key_curr
            v_child.kind_curr = v_walker.kind_curr if v_walker.kind_curr == 's' else 'v'
            v_child.path_curr = v_walker.path_curr
            v_child.path_raw_curr = v_walker.path_raw_curr
            yield SubConfig([v_child], self._parser_l)

    def node(self, iv_path: str):
        return SubConfig([self._node_get(iv_path)], self._parser_l)

    def load_d(self, il_raw_conf) -> None:
        if isinstance(il_raw_conf, Mapping):
            self._walker_l[0].node_curr_l = [il_raw_conf]
        else:
            self._walker_l[0].node_curr_l = [dict(il_raw_conf)]


class SubConfig(Config):
    def __init__(self, il_parent_opt: Sequence[ConfTreeWalker], il_parser: Mapping[str, DefItemAbc]):
        super().__init__()
        self._walker_l: Sequence[ConfTreeWalker] = il_parent_opt
        self._parser_l = il_parser
        self.kind = il_parent_opt[0].kind_curr
        self.path = il_parent_opt[0].path_raw_curr

    @property
    def v(self):
        return self._walker_l[0].value_get(self._parser_l)

    def _node_get(self, iv_path: str) -> ConfTreeWalker:
        assert isinstance(iv_path, str), r'Option sub-path is not a str.'
        if len(iv_path) == 0:
            raise KeyError(r'Option sub-path is empty.')
        if iv_path[0] != NODE_SEP:
            raise KeyError(r'Option sub-path have invalid format. '
                           f'Format is: `{{ "{NODE_SEP}" , option-or-section }}`,'
                           f' "{NODE_SEP}" at beginning is required.')
        v_path_raw = iv_path[1:]
        v_walker = m_cp.copy(self._walker_l[0])
        for v_key_raw in v_path_raw.split(NODE_SEP):
            if len(v_key_raw) == 0:
                raise KeyError(r'Option sub-path have invalid format.'
                               f'Format is: `{{ "{NODE_SEP}" , option-or-section }}`,'
                               f' repeatable "{NODE_SEP}" is prohibited.')
            v_walker.move(self._parser_l, v_key_raw)
        return v_walker

    def load_d(self, il_raw_conf) -> None:
        v_path: str = self._walker_l[0].path_raw_curr
        if isinstance(il_raw_conf, Mapping):
            self._walker_l[0] = ConfTreeWalker([il_raw_conf])
        else:
            self._walker_l[0] = ConfTreeWalker([dict(il_raw_conf)])
        self._walker_l[0] = self._node_get(v_path)


class ConfigIter:
    def __init__(self, iv_parent: Config, il_option: Mapping[str, DefItemAbc]):
        self._parent = iv_parent
        self._path_l: list = [v_k for v_k, v_i in il_option.items() if v_i.kind != 's']
        self._path_len = len(self._path_l)
        self._path_idx = -1

    def __next__(self):
        self._path_idx += 1
        if self._path_idx >= self._path_len:
            raise StopIteration
        else:
            return self._path_l[self._path_idx], self._parent[self._path_l[self._path_idx]]

    def __len__(self):
        return len(self._path_l)
