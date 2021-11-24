import pytest
import conflex as m_c

l_test_dict: dict = {
    'simple_nulls0': [{
        's_main': {
            'v_lost': None,
            'l_lost_list': None,
            'v_bool': 'true',
            'v_int': 42,
            'v_bigint': '2KB',
            'v_float': 3.141592,
            'l_empty_list': [],
            'l_int_list': [1, 2, 3],
            'l_complex_list': [
                {'v': 1,  'v_as': 'I'},
                {'v': 5,  'v_as': 'V'},
                {'v': 10, 'v_as': 'X'},
                {'v': 42, 'v_as': None}],
            'v_complex': {
                'v': 'ok',
                'v_kind': 'nice'}}}],
    'simple_merge': [
        {'s_main': {
            'v_bool': 'shadow',
            'v_int': 42,
            'v_bigint': 'shadow',
            'v_float': None,
            'l_empty_list': [],
            'l_int_list': [4, 3, 2],
            'l_complex_list': [
                {'v': 0, 'v_as': 'shadow'},
                {'v': 0, 'v_as': 'shadow'},
                {'v': 0, 'v_as': 'shadow'},
                {'v': 0, 'v_as': 'shadow'},
                {'v': 1000, 'v_as': 'M'}],
            'v_complex': {
                'v': 'shadow',
                'v_kind': 'nice'}}},
        {'s_main': {
            'v_bool': 'true',

            'v_bigint': '2KB',
            'v_float': 3.141592,
            'l_int_list': [1, 2, 3],
            'l_complex_list': [
                {'v': 1, 'v_as': 'I'},
                {'v': 5, 'v_as': 'V'},
                {'v': 10, 'v_as': 'X'},
                {'v': 42}],
            'v_complex': {
                'v': 'ok'}}}
    ]

}


@pytest.fixture(
    scope='module',
    params=[
        'fl:simple.yaml',
        'fl:simple_nopref.yaml',
        'fl:simple_fullpath.yaml',
        # !!!REM: None is treated as None, not missing. Keep dict for testing `missing indicators`.
        #'kv:simple_nulls0',
        'kv:simple_merge'
    ])
def fv_conf_dict(request):
    import yaml
    import io
    l_conf: list = []
    if str(request.param)[:2] == 'fl':
        with io.open(request.param[3:]) as v_rd:
            l_conf = [yaml.load(v_rd, Loader=yaml.BaseLoader)]
    if str(request.param)[:2] == 'kv':
        l_conf = l_test_dict[request.param[3:]]
    return l_conf


@pytest.fixture(scope='module')
def fv_conf_object(fv_conf_dict):
    class TestConf(m_c.Config):
        def __init__(self):
            super(TestConf, self).__init__([])
            self._l_parser = \
                { 'main': m_c.Section()
                , 'main/lost': m_c.OptValue(iv_default='default')
                , 'main/lost/sub_lost': m_c.OptValue(iv_default='sub_default')
                , 'main/empty_list': m_c.OptList(iv_required=False)
                , 'main/lost_list': m_c.OptList(iv_default=list('default'))
                , 'main/bool': m_c.OptVChoice({'True': True, 'true': True, 'False': False, 'false': False})
                , 'main/int': m_c.OptVInt()
                , 'main/bigint': m_c.OptVInt()
                , 'main/float': m_c.OptVFloat()
                , 'main/int_list': m_c.OptLInt()
                , 'main/complex_list': m_c.OptLInt()
                , 'main/complex_list/as': m_c.OptValue(iv_default='?')
                , 'main/complex': m_c.OptValue()
                , 'main/complex/kind': m_c.OptValue()}

    v_ret = m_c.Config([
        'main' >> m_c.Section() << [
            'lost' >> m_c.OptValue(iv_default='default') << [
                'sub_lost' >> m_c.OptValue(iv_default='sub_default')
            ],
            'lost_list' >> m_c.OptList(iv_default=list('default')),
            'bool' >> m_c.OptVChoice({'True': True, 'true': True, 'False': False, 'false': False}),
            'int' >> m_c.OptVInt(),
            'bigint' >> m_c.OptVInt(),
            'float' >> m_c.OptVFloat(),
            'empty_list' >> m_c.OptList(iv_required=False),
            'int_list' >> m_c.OptLInt(),
            'complex_list' >> m_c.OptLInt() << [
                'as' >> m_c.OptValue(iv_default='?')],
            'complex' >> m_c.OptValue() << [
                'kind' >> m_c.OptValue()]]])
    v_ret.load_dicts(fv_conf_dict)
    return v_ret


def test_config_values(fv_conf_object):
    assert fv_conf_object['main/lost'] == 'default'
    assert fv_conf_object['main/lost/sub_lost'] == 'sub_default'
    assert fv_conf_object['main/lost_list'] == list('default')
    assert fv_conf_object['main/bool']  # == True
    assert fv_conf_object['main/int'] == 42
    assert fv_conf_object['main/bigint'] == (2 * 1024)
    assert fv_conf_object['main/empty_list'] == []
    assert fv_conf_object['main/int_list'] == [1, 2, 3]
    assert fv_conf_object['main/complex_list'] == [1, 5, 10, 42]
    assert fv_conf_object['main/complex_list/as'] == ['I', 'V', 'X', '?']
    assert fv_conf_object['main/float'] == 3.141592
    assert fv_conf_object['main/complex'] == 'ok'
    assert fv_conf_object['main/complex/kind'] == 'nice'


def test_subconfig_values(fv_conf_object):
    v_sconf_object = fv_conf_object.knot('main/complex')
    assert v_sconf_object.v == 'ok'
    assert v_sconf_object['kind'] == 'nice'
    v_sconf_object = fv_conf_object.knot('s_main/l_complex_list')
    assert v_sconf_object.v == [1, 5, 10, 42]
    assert v_sconf_object['v_as'] == ['I', 'V', 'X', '?']
    if len(fv_conf_object._walker_l) > 1:
        assert [v.v for v in fv_conf_object.slice('main/complex_list')] == [1, 5, 10, 42, 1000]
        assert [v['as'] for v in fv_conf_object.slice('main/complex_list')] == ['I', 'V', 'X', '?', 'M']
        assert [v.v for v in fv_conf_object.slice('main/complex')] == ['ok']
        with pytest.raises(KeyError) as x:
            l_ = [v['kind'] for v in fv_conf_object.slice('main/complex')]
    else:
        assert [v.v for v in fv_conf_object.slice('main/complex_list')] == [1, 5, 10, 42]
        assert [v['as'] for v in fv_conf_object.slice('main/complex_list')] == ['I', 'V', 'X', '?']
        assert [v.v for v in fv_conf_object.slice('main/complex')] == ['ok']
        assert [v['kind'] for v in fv_conf_object.slice('main/complex')] == ['nice']


def test_config_errors(fv_conf_object):
    with pytest.raises(TypeError) as x:
        v = fv_conf_object['main']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['/main/int']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['main/dummy']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['main/l_int']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['main//int']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['main/z_int']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['']


def test_subconfig_errors(fv_conf_object):
    with pytest.raises(TypeError) as x:
        v = fv_conf_object.knot('main').v
    v_sconf_object = fv_conf_object.knot('main/complex')
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['dummy']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['l_kind']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['z_kind']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['/kind']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['']


def test_config_kind_values(fv_conf_object):
    assert fv_conf_object['s_main/v_lost'] == 'default'
    assert fv_conf_object['s_main/v_lost/v_sub_lost'] == 'sub_default'
    assert fv_conf_object['s_main/l_lost_list'] == list('default')
    assert fv_conf_object['s_main/v_bool']  # == True
    assert fv_conf_object['s_main/v_int'] == 42
    assert fv_conf_object['s_main/v_bigint'] == (2 * 1024)
    assert fv_conf_object['s_main/l_empty_list'] == []
    assert fv_conf_object['s_main/l_int_list'] == [1, 2, 3]
    assert fv_conf_object['s_main/l_complex_list'] == [1, 5, 10, 42]
    assert fv_conf_object['s_main/l_complex_list/v_as'] == ['I', 'V', 'X', '?']
    assert fv_conf_object['s_main/v_float'] == 3.141592
    assert fv_conf_object['s_main/v_complex'] == 'ok'
    assert fv_conf_object['s_main/v_complex/v_kind'] == 'nice'


def test_subconfig_kind_values(fv_conf_object):
    v_sconf_object = fv_conf_object.knot('s_main/v_complex')
    assert v_sconf_object.v == 'ok'
    assert v_sconf_object['v_kind'] == 'nice'
    v_sconf_object = fv_conf_object.knot('s_main/l_complex_list')
    assert v_sconf_object.v == [1, 5, 10, 42]
    assert v_sconf_object['v_as'] == ['I', 'V', 'X', '?']
    if len(fv_conf_object._walker_l) > 1:
        assert [v.v for v in fv_conf_object.slice('s_main/l_complex_list')] == [1, 5, 10, 42, 1000]
        assert [v['as'] for v in fv_conf_object.slice('s_main/l_complex_list')] == ['I', 'V', 'X', '?', 'M']
        assert [v.v for v in fv_conf_object.slice('s_main/v_complex')] == ['ok']
        with pytest.raises(KeyError) as x:
            l_ = [v['kind'] for v in fv_conf_object.slice('s_main/v_complex')]
    else:
        assert [v.v for v in fv_conf_object.slice('s_main/l_complex_list')] == [1, 5, 10, 42]
        assert [v['as'] for v in fv_conf_object.slice('s_main/l_complex_list')] == ['I', 'V', 'X', '?']
        assert [v.v for v in fv_conf_object.slice('s_main/v_complex')] == ['ok']
        assert [v['kind'] for v in fv_conf_object.slice('s_main/v_complex')] == ['nice']


def test_config_kind_errors(fv_conf_object):
    with pytest.raises(TypeError):
        v = fv_conf_object['s_main']
    with pytest.raises(KeyError):
        v = fv_conf_object['s_main/v_dummy']
    with pytest.raises(KeyError):
        v = fv_conf_object['s_main/l_int']
    with pytest.raises(KeyError):
        v = fv_conf_object['s_main//v_int']
    with pytest.raises(KeyError):
        v = fv_conf_object['s_main/z_int']
    with pytest.raises(KeyError):
        v = fv_conf_object['']
    with pytest.raises(AssertionError):
        v = fv_conf_object[None]


def test_config_iter(fv_conf_object):
    l_option = \
        { 'main': None
        , 'main/lost': 'default'
        , 'main/lost/sub_lost': 'sub_default'
        , 'main/lost_list': list('default')
        , 'main/bool': True
        , 'main/int': 42
        , 'main/bigint': 2 * 1024
        , 'main/float': 3.141592
        , 'main/empty_list': []
        , 'main/int_list': [1, 2, 3]
        , 'main/complex_list': [1, 5, 10, 42]
        , 'main/complex_list/as': ['I', 'V', 'X', '?']
        , 'main/complex': 'ok'
        , 'main/complex/kind': 'nice'}
    v_idx = -1
    v_it = fv_conf_object.items()
    for v_key, v_val in v_it:
        assert v_val == l_option[v_key]
        v_idx += 1
    assert v_idx >= 0
    assert ('', None) not in v_it
    assert ('main', None) not in v_it
    assert ('main/lost', None) not in v_it
    assert ('main/bool', True) in v_it
    assert ('main/bool', False) not in v_it
    assert len(v_it) == len(l_option) - 1  # one section
    assert len(fv_conf_object) == len(l_option)
    for v_key in fv_conf_object:
        assert v_key in l_option


def test_opt_manager_errors():
    with pytest.raises(ValueError):
        v = ' spaces ' >> m_c.OptValue()
    with pytest.raises(ValueError):
        v = 'path/sep' >> m_c.OptValue()
    with pytest.raises(ValueError):
        m_c.OptValue().name_set('')
    with pytest.raises(ValueError):
        m_c.OptValue().name_set('l_bad')
    with pytest.raises(ValueError):
        v = m_c.OptValue()
        v.name_set('main')
        v.name_set('niam')
    with pytest.raises(SyntaxError):
        v = m_c.OptValue() << 'wrong_side'
    with pytest.raises(SyntaxError):
        v = {'wrong', 'side'} >> m_c.OptValue()
    with pytest.raises(AssertionError):
        v = m_c.OptValue(iv_default={})
    with pytest.raises(ValueError):
        v = m_c.OptVInt(iv_default='bad')
    with pytest.raises(ValueError):
        v = m_c.OptVInt().value_parse('bad')
    with pytest.raises(ValueError):
        v = m_c.OptVFloat(iv_default='bad')
    with pytest.raises(ValueError):
        v = m_c.OptVInt().value_parse('bad')
    with pytest.raises(ValueError):
        v = m_c.OptVChoice({})


def test_opt_manager():
    v = m_c.as_node('main')
    assert v.name == 'main'
    assert v.kind == 's'
    assert not v.required
    assert type(v) == m_c.Section
    assert v.__hash__() == hash('main')

    v = m_c.as_node('v_main')
    assert v.name == 'main'
    assert v.kind == 'v'
    assert v.required
    assert type(v) == m_c.OptValue

    v = m_c.as_node('l_main')
    assert v.name == 'main'
    assert v.kind == 'l'
    assert v.required
    assert type(v) == m_c.OptList

    v = 'main' >> m_c.Section()
    assert v.name == 'main'
    assert v.kind == 's'
    assert not v.required
    assert v != 'niam'

    v = 'main' >> m_c.OptValue(iv_default='ok')
    assert v.name == 'main'
    assert v.kind == 'v'
    assert v.default == 'ok'
    assert not v.required
    assert v.value_parse('ok') == 'ok'

    v = 'main' >> m_c.OptVInt(iv_default='1')
    assert v.name == 'main'
    assert v.kind == 'v'
    assert v.default == 1
    assert not v.required
    assert v.value_parse('42') == 42
    assert v.value_parse('1KB') == 1024

    v = 'main' >> m_c.OptVFloat(iv_default='1')
    assert v.name == 'main'
    assert v.default == 1.0
    assert not v.required
    assert v.value_parse('42') == 42.0

    v = 'main' >> m_c.OptVChoice(il_mapping={'Yes': 1, 'No': -1}, iv_default='Yes')
    assert v.name == 'main'
    assert v.default == 1
    assert not v.required
    assert v.value_parse('No') == -1
    assert v.value_parse('Yes') == 1

    v = m_c.OptVChoice(il_mapping=[('Yes', 1), ('No', -1)], iv_default='Yes')
    assert v.value_parse('No') == -1
    assert v.value_parse('Yes') == 1

    v = 'main' >> m_c.OptList(iv_default=None)
    assert v.name == 'main'
    assert v.kind == 'l'
    assert v.default == []
    assert v.required
    assert v.value_parse('ok') == 'ok'

    v = m_c.OptList(iv_default=[])
    assert v.default == []
    assert not v.required

    v = 'main' >> m_c.OptLInt(iv_default='42')
    assert v.name == 'main'
    assert v.kind == 'l'
    assert v.default == [4, 2]
    assert not v.required
    assert v.value_parse('42') == 42
    assert v.value_parse('1K') == 1000

    v = m_c.OptLInt(iv_default=range(0, 2))
    assert v.default == [0, 1]

    v = m_c.OptLInt(iv_default=[0, 1])
    assert v.default == [0, 1]

    v = 'main' >> m_c.OptLFloat(iv_default='42')
    assert v.name == 'main'
    assert v.kind == 'l'
    assert not v.required
    assert v.default == [4.0, 2.0]
    assert v.value_parse('42') == 42.0

    v = m_c.OptLFloat(iv_default=range(0, 2))
    assert v.default == [0.0, 1.0]

    v = m_c.OptLFloat(iv_default=[0, 1])
    assert v.default == [0.0, 1.0]

    v = m_c.OptLFloat(iv_default=[27.01, 16.09])
    assert v.default == [27.01, 16.09]


def test_conf_load():
    v = m_c.Config(
        ['s' >> m_c.Section() <<
         ['v_a',
             'v_b',
             'l_c',
             'l' >> m_c.OptList(),
             'v' >> m_c.OptValue()]
         ])
    v.load_dicts([{'s': {'a': 1, 'b': 2}}])
    assert v._walker_l[0].node_l[0]['s']['a'] == 1
    assert v._walker_l[0].node_l[0]['s']['b'] == 2
    assert v._parser_l['s'].kind == 's'
    assert v._parser_l['s'].name == 's'
    assert not v._parser_l['s'].required
    assert v._parser_l['s/a'].kind == 'v'
    assert v._parser_l['s/a'].name == 'a'
    assert v._parser_l['s/a'].required
    assert v._parser_l['s/b'].kind == 'v'
    assert v._parser_l['s/b'].name == 'b'
    assert v._parser_l['s/b'].required
    assert v._parser_l['s/c'].kind == 'l'
    assert v._parser_l['s/c'].name == 'c'
    assert v._parser_l['s/c'].required
    assert v._parser_l['s/l'].kind == 'l'
    assert v._parser_l['s/l'].name == 'l'
    assert v._parser_l['s/l'].required
    assert v._parser_l['s/v'].kind == 'v'
    assert v._parser_l['s/v'].name == 'v'
    assert v._parser_l['s/v'].required
    with pytest.raises(KeyError):
        print(v['s/v'])
    with pytest.raises(KeyError):
        print(v['s/l'])
    assert len([_ for _ in v._parser_l.keys() if _ not in {'s', 's/a', 's/b', 's/c', 's/l', 's/v'}]) == 0
    v = m_c.Config(['v_0' >> m_c.OptValue(iv_required=False) << ['v_00' >> m_c.OptValue() << ['v_000' >> m_c.OptValue(iv_default='42')]]])
    v.load_dicts([{}])
    with pytest.raises(KeyError):
        print(v['0/00'])
    assert v['0'] is None
    assert v['0/00/000'] == '42'
    v.load_dicts([[('s', {'a': 1, 'b': 2})]])
    assert v._walker_l[0].node_l[0]['s']['a'] == 1
    assert v._walker_l[0].node_l[0]['s']['b'] == 2


def test_subconf_load():
    v_c = m_c.Config(
        ('s' >> m_c.Section() <<
            ('v_a' >> m_c.OptValue() <<
                ('v_aa', 'v_ab'))
        )
    )
    v_c.load_dicts([{'s': {'a': {'v': 'a0', 'aa': 0, 'ab': 1}}}])
    v_sc = v_c.knot('s/a')
    v_sc.load_dicts([{'s': {'a': {'v': 'a1', 'aa': 42, 'ab': 24}}}])
    assert v_sc.v == 'a1'
    assert v_sc['aa'] == 42
    v_sc.load_dicts([[('s', {'a': {'v': 'a1'}})]])


def test_abc():
    v = m_c.NodeAbc('_')
    assert v.kind == '_'
    assert v.name == ''

    v = 'main' >> m_c.NodeAbc('_')
    assert v.name == 'main'

    with pytest.raises(TypeError):
        v = m_c.OptionAbc('_')
    with pytest.raises(TypeError):
        v = m_c.OptionAbc('_')


def test_conf_errors():
    with pytest.raises(AssertionError):
        v = m_c.Config(42)
    with pytest.raises(KeyError):
        v = m_c.Config((
            m_c.as_node('main') << (
                'twin' >> m_c.OptValue(iv_default='default'),
                'twin' >> m_c.OptVInt()
            )
        ))
    with pytest.raises(KeyError):
        v = m_c.Config([
            m_c.as_node('main') << [
                'v_twin',
                'v_twin'
            ]
        ])
