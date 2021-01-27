from collections.abc import Mapping, Sequence, Set
import copy as m_cp


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

    def name_set(self, iv: str):
        if len(iv) == 0:
            raise ValueError('Config option name must not to be empty.')

        v_kind, v_name = _opt_name_split(iv)

        if len([v for v in v_name if v.isspace() or v == '/']):
            raise ValueError('Config option name must not contains `/` or space characters.')
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
    def __init__(self, iv_default=None):
        super().__init__('v')
        if iv_default is None:
            self.default = None
        elif type(iv_default) is not str and isinstance(iv_default, (Mapping, Sequence)):
            raise TypeError(r'Default value for `v` kind of options should be str, int, float, etc.')
        else:
            self.default = self.value_parse(iv_default)

    def value_parse(self, iv):
        return iv


class DefValueInt(DefValue):
    def value_parse(self, iv: str) -> int:
        return _opt_int_parse(iv)


class DefValueEnum(DefValue):
    def __init__(self, il_mapping: dict, iv_default=None):
        if isinstance(il_mapping, Mapping):
            self._mapping_l = il_mapping
        else:
            self._mapping_l = dict(il_mapping)

        if len(self._mapping_l) == 0:
            raise ValueError(r'Parameter il_mapping is empty.')

        super().__init__(iv_default)

    def value_parse(self, iv):
        return self._mapping_l[iv]


class DefValueFloat(DefValue):
    def value_parse(self, iv: str) -> float:
        return _opt_float_parse(iv)


class DefList(DefItemAbc):
    def __init__(self, iv_default: list = None):
        super().__init__('l')
        if iv_default is None:
            self.default = []
        else:
            self.default = \
                [self.value_parse(v)
                 for v in (iv_default if isinstance(iv_default, Sequence) else list(iv_default))]

    def value_parse(self, iv):
        return iv


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


class Config(Mapping):
    def __init__(self, il_parser: set = None):
        self._conf_l: dict = {}
        self._parser_l: Mapping[str, DefItemAbc] = self._parser_dict_create(il_parser) if il_parser is not None else {}
        self._iter = None
        self._path_prefix = ''

    @staticmethod
    def _parser_dict_create(il_tree: set) -> dict:
        """Create plain dict parser from input tree of opt definitions `DefOptAbc objects`.

        :param il_tree: Set
        :return: None
        """

        if not isinstance(il_tree, Set):
            raise TypeError(f'{type(il_tree).__qualname__} is not `set` of `frozenset`')

        l_l_root: list = [('', il_tree)]
        l_plain: dict = {}

        while len(l_l_root):
            v_kp, l_root = l_l_root.pop()

            for v_v in l_root:
                if isinstance(v_v, DefOptAbc):
                    if len(v_v.child_l):
                        l_l_root.append((f'{v_kp}/{v_v.name}', v_v.child_l))
                        v_v.child_l = frozenset()
                    l_plain[f'{v_kp}/{v_v.name}'] = v_v
                elif isinstance(v_v, str):
                    l_plain[f'{v_kp}/{_opt_name_split(v_v)[1]}'] = def_opt(v_v)

        return l_plain

    def _my_iter(self):
        if self._iter is None:
            self._iter = ConfigIter(self, self._parser_l)
        return self._iter

    def __getitem__(self, item):
        return self._value_get(item)

    def __iter__(self):
        return m_cp.copy(self._my_iter())

    def __len__(self):
        return len(self._my_iter())

    def _subkey_translate(self, iv_raw: str, iv_parent_path: str) -> (str, str):
        l_key_part = iv_raw.split('_', maxsplit=1)
        l_ret = ('', '')

        v_key_part_len = len(l_key_part)
        if v_key_part_len == 2:
            if l_key_part[0] not in ['s', 'v', 'l']:
                l_ret = (str(self._parser_l[f'{iv_parent_path}/{iv_raw}'].kind), iv_raw)
            elif self._parser_l[f'{iv_parent_path}/{l_key_part[1]}'].kind != l_key_part[0]:
                raise KeyError(f'Option `{iv_parent_path}/{l_key_part[1]}` exist but have different kind.')
            else:
                l_ret = (l_key_part[0], l_key_part[1])
        elif v_key_part_len == 1:
            l_ret = (str(self._parser_l[f'{iv_parent_path}/{iv_raw}'].kind), iv_raw)
        return l_ret

    def _value_get(self, iv_path: str):
        if len(iv_path) == 0:
            raise KeyError(r'Option path is empty.')
        if iv_path[0] != '/':
            raise KeyError(r'Option path have invalid format. '
                           r'Format is: `{ "/" , option-or-section }`,'
                           r' "/" at beginning is required.')
        v_path_raw = iv_path[1:]
        l_conf_opt: list = [self._conf_l]
        l_conf_opt_tmp: list = []
        v_path: str = self._path_prefix
        v_kind: str = ''
        v_ret_list: bool = False
        v_key: str = ''
        v_opt = None
        for v_key_raw in v_path_raw.split('/'):
            if len(v_key_raw) == 0:
                raise KeyError(r'Option path have invalid format.'
                               r'Format is: `{ "/" , option-or-section }`,'
                               r' repeatable "/" is prohibited.')
            v_kind, v_key = self._subkey_translate(v_key_raw, v_path)
            v_path += '/' + v_key
            v_ret_list = v_ret_list or v_kind == 'l'
            for v_opt in l_conf_opt:
                l_conf_opt_tmp.extend(Config._subkey_get(v_kind, v_key, v_opt))
            l_conf_opt.clear()
            l_conf_opt, l_conf_opt_tmp = l_conf_opt_tmp, l_conf_opt

        if v_kind == 's':
            raise TypeError('Sections can not have a value.')

        if len(l_conf_opt) == 0:
            l_conf_opt = self._parser_l[v_path].default_get(iv_path) \
                if v_kind == 'l' else [self._parser_l[v_path].default_get(iv_path)]
        else:
            for v_opt in l_conf_opt:
                if isinstance(v_opt, Mapping):
                    v_opt = v_opt.get('v')
                if v_opt is None:
                    if v_kind == 'l':
                        l_conf_opt_tmp.extend(self._parser_l[v_path].default_get(v_path))
                    if v_kind == 'v':
                        l_conf_opt_tmp.append(self._parser_l[v_path].default_get(v_path))
                else:
                    l_conf_opt_tmp.append(self._parser_l[v_path].value_parse(v_opt))
            l_conf_opt.clear()
            l_conf_opt, l_conf_opt_tmp = l_conf_opt_tmp, l_conf_opt

        if v_ret_list:
            return l_conf_opt
        else:
            return l_conf_opt[0] if len(l_conf_opt) else None

    def load_d(self, il_raw_conf: dict) -> None:
        if isinstance(il_raw_conf, Mapping):
            self._conf_l = il_raw_conf
        else:
            self._conf_l = dict(il_raw_conf)


class ConfigIter:
    def __init__(self, iv_parent: Config, il_option: dict):
        self._parent = iv_parent
        self._path_l: list = [v_k for v_k, v_i in il_option.items() if v_i.kind != 's']
        self._path_len = len(self._path_l)
        self._path_idx = -1

    def __next__(self):
        self._path_idx += 1
        if self._path_idx >= self._path_len:
            raise StopIteration
        else:
            return self._path_l[self._path_idx], self._parent._value_get(self._path_l[self._path_idx])

    def __len__(self):
        return len(self._path_l)
