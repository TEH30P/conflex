from collections.abc import Mapping, Sequence
import copy as m_cp

r'''
#!!!TODO: build conf purpose
self._l_node = {
    section('main', {
        'missing' << is_value(default='default'), 
        'int' << is_value(),
        'ints' << is_list(),
        'complex' << is_value(attrs={'kind', 'type'}),
    }),
    section('ext', {
        section('foo', {'a', 'b'}),
        section('bar', {'a', 'b'})
    })
}
'''

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


class OptAbc:
    def __init__(self, iv_kind: str):
        self.kind = iv_kind


class OptSection(OptAbc):
    def __init__(self):
        super().__init__(iv_kind='s')


class OptItemAbc(OptAbc):
    def __init__(self, iv_kind: str):
        super().__init__(iv_kind)
        self.default = None

    def value_parse(self, iv):
        raise NotImplementedError('Method must be overridden.')


class OptValue(OptItemAbc):
    def __init__(self, iv_default=None):
        super().__init__('v')
        if iv_default is None:
            self.default = None
        elif type(iv_default) is not str and isinstance(iv_default, (Mapping, Sequence)):
            raise AttributeError(r'Default value for `v` kind of options should be str, int, float, etc.')
        else:
            self.default = self.value_parse(iv_default)

    def value_parse(self, iv):
        return iv


class OptValueInt(OptValue):
    def value_parse(self, iv: str) -> int:
        return _opt_int_parse(iv)


class OptValueEnum(OptValue):
    def __init__(self, il_mapping, iv_default=None):
        if isinstance(il_mapping, Mapping):
            self._l_mapping = il_mapping
        else:
            self._l_mapping = dict(il_mapping)

        if len(self._l_mapping) == 0:
            raise AttributeError(r'Parameter il_mapping is empty.')

        super().__init__(iv_default)

    def value_parse(self, iv):
        return self._l_mapping[iv]


class OptValueFloat(OptValue):
    def value_parse(self, iv: str) -> float:
        return _opt_float_parse(iv)


class OptList(OptItemAbc):
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


class OptListInt(OptList):
    def value_parse(self, iv: str) -> int:
        return _opt_int_parse(iv)


class OptListFloat(OptList):
    def value_parse(self, iv: str) -> float:
        return _opt_float_parse(iv)


class OptRdValue:
    def __init__(self, iv_raw, iv_manager: OptValue):
        self._manager = iv_manager
        self._raw = iv_raw

    @property
    def v(self):
        v = self._raw
        if isinstance(v, Mapping):
            v = v.get('v')
        return self._manager.default if v is None else self._manager.value_parse(v)


class OptRdList:
    def __init__(self, iv_raw, iv_manager: OptList):
        self._manager = iv_manager
        self._raw = iv_raw

    @property
    def l(self):
        v_raw = self._raw

        if v_raw is None:
            v_raw = self._manager.default
        elif isinstance(v_raw, Mapping):
            v_raw = v_raw.get('l')
        return \
            [self._manager.value_parse(v) for v in v_raw] \
            if isinstance(v_raw, Sequence) and not type(v_raw) is str \
            else [self._manager.value_parse(v_raw)]


class Config(Mapping):
    def __init__(self, il_parser: dict):
        self._l_conf: dict = {}
        self._l_parser = il_parser
        self._v_iter = None

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
                l_ret = (self._l_parser[f'{iv_parent_path}/{iv_raw}'].kind, iv_raw)
            elif self._l_parser[f'{iv_parent_path}/{l_key_part[1]}'].kind != l_key_part[0]:
                raise KeyError(r'Option exist but have different kind.')
            else:
                l_ret = (l_key_part[0], l_key_part[1])
        elif v_key_part_len == 1:
            l_ret = (self._l_parser[f'{iv_parent_path}/{iv_raw}'].kind, iv_raw)
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
            raise AttributeError('Sections can not have a value.')
        elif v_pref == 'v':
            return OptRdValue(v_conf_opt, self._l_parser[v_path]).v
        elif v_pref == 'l':
            return OptRdList(v_conf_opt, self._l_parser[v_path]).l

    def load_d(self, il_raw_conf: dict) -> None:
        if isinstance(il_raw_conf, Mapping):
            self._l_conf = il_raw_conf
        else:
            self._l_conf = dict(il_raw_conf)


class ConfigIter:
    def __init__(self, iv_parent: Config, il_option: dict):
        self._v_parent = iv_parent
        self._l_path: list = [v_k for v_k, v_i in il_option.items() if v_i.kind != 's']
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
