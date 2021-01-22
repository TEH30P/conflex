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
        self.v_kind: str = iv_kind
        self.v_name: str = ''
        self.l_child: Set = set()

    def name_set(self, iv: str):
        if len(iv) == 0:
            raise ValueError('Config option name must not to be empty.')

        v_kind, v_name = _opt_name_split(iv)

        if len([v for v in v_name if v.isspace() or v == '/']):
            raise ValueError('Config option name must not contains `/` or space characters.')
        if len(self.v_name):
            raise ValueError('Name of option is already set it can not be updated.')
        if len(v_kind) != 0 and v_kind != self.v_kind:
            raise ValueError('Kind of option can not be updated.')

        self.v_name = v_name

    # self << iv
    def __lshift__(self, iv):
        if isinstance(iv, Set):
            self.l_child = frozenset(iv)
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
        return hash(self.v_name)

    def __eq__(self, iv):
        if isinstance(iv, str):
            if iv == self.v_name:
                raise KeyError(f'The option named `{self.v_name}` is already exists.')
        elif isinstance(iv, DefOptAbc):
            if iv.v_name == self.v_name:
                raise KeyError(f'The option named `{self.v_name}` is already exists.')
        else:
            raise TypeError('Only plain strings `str` or derived from `DefOptAbc` objects allowed.')
        return False


class DefSection(DefOptAbc):
    def __init__(self):
        super().__init__('s')


class DefItemAbc(DefOptAbc):
    def __init__(self, iv_kind: str):
        super().__init__(iv_kind)
        self.v_default = None

    def value_parse(self, iv):
        raise NotImplementedError('Method must be overridden.')


class DefValue(DefItemAbc):
    def __init__(self, iv_default=None):
        super().__init__('v')
        if iv_default is None:
            self.v_default = None
        elif type(iv_default) is not str and isinstance(iv_default, (Mapping, Sequence)):
            raise TypeError(r'Default value for `v` kind of options should be str, int, float, etc.')
        else:
            self.v_default = self.value_parse(iv_default)

    def value_parse(self, iv):
        return iv


class DefValueInt(DefValue):
    def value_parse(self, iv: str) -> int:
        return _opt_int_parse(iv)


class DefValueEnum(DefValue):
    def __init__(self, il_mapping: dict, iv_default=None):
        if isinstance(il_mapping, Mapping):
            self._l_mapping = il_mapping
        else:
            self._l_mapping = dict(il_mapping)

        if len(self._l_mapping) == 0:
            raise ValueError(r'Parameter il_mapping is empty.')

        super().__init__(iv_default)

    def value_parse(self, iv):
        return self._l_mapping[iv]


class DefValueFloat(DefValue):
    def value_parse(self, iv: str) -> float:
        return _opt_float_parse(iv)


class DefList(DefItemAbc):
    def __init__(self, iv_default: list = None):
        super().__init__('l')
        if iv_default is None:
            self.v_default = []
        else:
            self.v_default = \
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


class OptValue:
    def __init__(self, iv_raw, iv_manager: DefValue):
        self._manager = iv_manager
        self._raw = iv_raw

    @property
    def v(self):
        v = self._raw
        if isinstance(v, Mapping):
            v = v.get('v')
        return self._manager.v_default if v is None else self._manager.value_parse(v)


class OptList:
    def __init__(self, iv_raw, iv_manager: DefList):
        self._manager = iv_manager
        self._raw = iv_raw

    @property
    def l(self):
        v_raw = self._raw

        if v_raw is None:
            v_raw = self._manager.v_default
        elif isinstance(v_raw, Mapping):
            v_raw = v_raw.get('l')
        return \
            [self._manager.value_parse(v) for v in v_raw] \
            if isinstance(v_raw, Sequence) and not type(v_raw) is str \
            else [self._manager.value_parse(v_raw)]


def def_opt(iv_name: str) -> DefOptAbc:
    v_kind, v_name = _opt_name_split(iv_name)

    if v_kind in ['', 's']:
        return v_name >> DefSection()
    elif v_kind == 'v':
        return v_name >> DefValue()
    elif v_kind == 'l':
        return v_name >> DefList()


class Config(Mapping):
    def __init__(self, il_parser: set):
        self._l_conf: dict = {}
        self._l_parser = self._parser_dict_create(il_parser)
        self._v_iter = None

    def _parser_dict_create(self, il_tree: set) -> dict:
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
                    if len(v_v.l_child):
                        l_l_root.append((f'{v_kp}/{v_v.v_name}', v_v.l_child))
                        v_v.l_child = frozenset()
                    l_plain[f'{v_kp}/{v_v.v_name}'] = v_v
                elif isinstance(v_v, str):
                    l_plain[f'{v_kp}/{v_v}'] = def_opt(v_v)

        return l_plain

    def _my_iter(self):
        if self._v_iter is None:
            self._v_iter = ConfigIter(self, self._l_parser)
        return self._v_iter

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
                l_ret = (self._l_parser[f'{iv_parent_path}/{iv_raw}'].v_kind, iv_raw)
            elif self._l_parser[f'{iv_parent_path}/{l_key_part[1]}'].v_kind != l_key_part[0]:
                raise KeyError(r'Option exist but have different kind.')
            else:
                l_ret = (l_key_part[0], l_key_part[1])
        elif v_key_part_len == 1:
            l_ret = (self._l_parser[f'{iv_parent_path}/{iv_raw}'].v_kind, iv_raw)
        return l_ret

    def _value_get(self, iv_path: str):
        v_conf_opt: dict = self._l_conf
        v_path: str = ''
        v_pref: str = ''
        v_key: str = '/'
        for v_key_raw in iv_path.split('/'):
            if v_key == '/':
                if len(v_key_raw) != 0:
                    raise KeyError(r'Option path have invalid format. '
                                   r'Format is: `{ "/" , option-or-section }`,'
                                   r' "/" at beginning is required.')
                v_key = ''
                continue
            if len(v_key_raw) == 0:
                raise KeyError(r'Option path have invalid format.'
                               r'Format is: `{ "/" , option-or-section }`,'
                               r' repeatable "/" is proshibited.')
            v_pref, v_key = self._subkey_translate(v_key_raw, v_path)
            v_path += '/' + v_key
            if v_conf_opt is not None:
                v_conf_opt = v_conf_opt.get(v_key, v_conf_opt.get(f'{v_pref}_{v_key}'))

        if len(v_pref) == 0:
            raise KeyError(r'Option path is empty.')
        elif v_pref == 's':
            raise TypeError('Sections can not have a value.')
        elif v_pref == 'v':
            return OptValue(v_conf_opt, self._l_parser[v_path]).v
        elif v_pref == 'l':
            return OptList(v_conf_opt, self._l_parser[v_path]).l

    def load_d(self, il_raw_conf: dict) -> None:
        if isinstance(il_raw_conf, Mapping):
            self._l_conf = il_raw_conf
        else:
            self._l_conf = dict(il_raw_conf)


class ConfigIter:
    def __init__(self, iv_parent: Config, il_option: dict):
        self._v_parent = iv_parent
        self._l_path: list = [v_k for v_k, v_i in il_option.items() if v_i.v_kind != 's']
        self._v_path_len = len(self._l_path)
        self._v_path_idx = -1

    def __next__(self):
        self._v_path_idx += 1
        if self._v_path_idx >= self._v_path_len:
            raise StopIteration
        else:
            return self._l_path[self._v_path_idx], self._v_parent._value_get(self._l_path[self._v_path_idx])

    def __len__(self):
        return len(self._l_path)
