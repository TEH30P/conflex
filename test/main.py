import pytest
import conflex as m_c

l_test_dict: dict = {
    'simple_nulls0': {
        's_main': {
            'v_lost': None,
            'l_lost_list': None,
            'v_bool': 'true',
            'v_int': 42,
            'v_bigint': '2KB',
            'v_float': 3.141592,
            'l_int_list': [1, 2, 3],
            'l_complex_list': [
                {'v': 1,  'v_as': 'I'},
                {'v': 5,  'v_as': 'V'},
                {'v': 10, 'v_as': 'X'},
                {'v': 42, 'v_as': None}],
            'v_complex': {
                'v': 'ok',
                'v_kind': 'nice'}}}
}


@pytest.fixture(
    scope='module',
    params=['fl:simple.yaml', 'fl:simple_nopref.yaml', 'fl:simple_fullpath.yaml', 'kv:simple_nulls0'])
def fv_conf_dict(request):
    import yaml, io

    l_conf: dict = {}
    if str(request.param)[:2] == 'fl':
        with io.open(request.param[3:]) as v_rd:
            l_conf = yaml.load(v_rd, Loader=yaml.BaseLoader)
    if str(request.param)[:2] == 'kv':
        l_conf = l_test_dict[request.param[3:]]
    #print(l_conf)

    return l_conf


@pytest.fixture(scope='module')
def fv_conf_object(fv_conf_dict):
    class TestConf(m_c.Config):
        def __init__(self):
            super(TestConf, self).__init__(set())
            self._l_parser = \
                { '/main': m_c.DefSection()
                , '/main/lost': m_c.DefValue(iv_default='default')
                , '/main/lost_list': m_c.DefList(iv_default=list('default'))
                , '/main/bool': m_c.DefValueChoise({'True': True, 'true': True, 'False': False, 'false': False})
                , '/main/int': m_c.DefValueInt()
                , '/main/bigint': m_c.DefValueInt()
                , '/main/float': m_c.DefValueFloat()
                , '/main/int_list': m_c.DefListInt()
                , '/main/complex_list': m_c.DefListInt()
                , '/main/complex_list/as': m_c.DefValue(iv_default='?')
                , '/main/complex': m_c.DefValue()
                , '/main/complex/kind': m_c.DefValue()}

    v_ret = m_c.Config({
        'main' >> m_c.DefSection() << {
            'lost' >> m_c.DefValue(iv_default='default'),
            'lost_list' >> m_c.DefList(iv_default=list('default')),
            'bool' >> m_c.DefValueChoise({'True': True, 'true': True, 'False': False, 'false': False}),
            'int' >> m_c.DefValueInt(),
            'bigint' >> m_c.DefValueInt(),
            'float' >> m_c.DefValueFloat(),
            'int_list' >> m_c.DefListInt(),
            'complex_list' >> m_c.DefListInt() << {
                'as' >> m_c.DefValue(iv_default='?')},
            'complex' >> m_c.DefValue() << {
                'kind' >> m_c.DefValue()}}})
    v_ret.load_d(fv_conf_dict)
    return v_ret


def test_config_values(fv_conf_object):
    assert fv_conf_object['/main/lost'] == 'default'
    assert fv_conf_object['/main/lost_list'] == list('default')
    assert fv_conf_object['/main/bool']  # == True
    assert fv_conf_object['/main/int'] == 42
    assert fv_conf_object['/main/bigint'] == (2 * 1024)
    assert fv_conf_object['/main/int_list'] == [1, 2, 3]
    assert fv_conf_object['/main/complex_list'] == [1, 5, 10, 42]
    assert fv_conf_object['/main/complex_list/as'] == ['I', 'V', 'X', '?']
    assert fv_conf_object['/main/float'] == 3.141592
    assert fv_conf_object['/main/complex'] == 'ok'
    assert fv_conf_object['/main/complex/kind'] == 'nice'


def test_subconfig_values(fv_conf_object):
    v_sconf_object = fv_conf_object.node('/main/complex')
    assert v_sconf_object.v == 'ok'
    assert v_sconf_object['/kind'] == 'nice'
    assert [v.v for v in fv_conf_object.slice('/main/complex_list')] == [1, 5, 10, 42]
    assert [v['/as'] for v in fv_conf_object.slice('/main/complex_list')] == ['I', 'V', 'X', '?']
    assert [v.v for v in fv_conf_object.slice('/main/complex')] == ['ok']
    assert [v['/kind'] for v in fv_conf_object.slice('/main/complex')] == ['nice']


def test_config_errors(fv_conf_object):
    with pytest.raises(TypeError) as x:
        v = fv_conf_object['/main']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['main/int']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['/main/dummy']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['/main/l_int']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['/main//int']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['/main/z_int']
    with pytest.raises(KeyError) as x:
        v = fv_conf_object['']


def test_subconfig_errors(fv_conf_object):
    with pytest.raises(TypeError) as x:
        v = fv_conf_object.node('/main').v
    v_sconf_object = fv_conf_object.node('/main/complex')
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['/dummy']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['/l_kind']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['/z_kind']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['kind']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['']
    with pytest.raises(KeyError) as x:
        v = v_sconf_object['/']


def test_config_kind_values(fv_conf_object):
    assert fv_conf_object['/s_main/v_lost'] == 'default'
    assert fv_conf_object['/s_main/l_lost_list'] == list('default')
    assert fv_conf_object['/s_main/v_bool']  # == True
    assert fv_conf_object['/s_main/v_int'] == 42
    assert fv_conf_object['/s_main/v_bigint'] == (2 * 1024)
    assert fv_conf_object['/s_main/l_int_list'] == [1, 2, 3]
    assert fv_conf_object['/s_main/l_complex_list'] == [1, 5, 10, 42]
    assert fv_conf_object['/s_main/l_complex_list/v_as'] == ['I', 'V', 'X', '?']
    assert fv_conf_object['/s_main/v_float'] == 3.141592
    assert fv_conf_object['/s_main/v_complex'] == 'ok'
    assert fv_conf_object['/s_main/v_complex/v_kind'] == 'nice'


def test_subconfig_kind_values(fv_conf_object):
    v_sconf_object = fv_conf_object.node('/s_main/v_complex')
    assert v_sconf_object.v == 'ok'
    assert v_sconf_object['/v_kind'] == 'nice'
    v_sconf_object = fv_conf_object.node('/s_main/l_complex_list')
    assert v_sconf_object.v == [1, 5, 10, 42]
    assert v_sconf_object['/v_as'] == ['I', 'V', 'X', '?']
    assert [v.v for v in fv_conf_object.slice('/s_main/l_complex_list')] == [1, 5, 10, 42]
    assert [v['/v_as'] for v in fv_conf_object.slice('/s_main/l_complex_list')] == ['I', 'V', 'X', '?']
    assert [v.v for v in fv_conf_object.slice('/s_main/v_complex')] == ['ok']
    assert [v['/v_kind'] for v in fv_conf_object.slice('/s_main/v_complex')] == ['nice']


def test_config_kind_errors(fv_conf_object):
    with pytest.raises(TypeError):
        v = fv_conf_object['/s_main']
    with pytest.raises(KeyError):
        v = fv_conf_object['s_main/v_int']
    with pytest.raises(KeyError):
        v = fv_conf_object['/s_main/v_dummy']
    with pytest.raises(KeyError):
        v = fv_conf_object['/s_main/l_int']
    with pytest.raises(KeyError):
        v = fv_conf_object['/s_main//v_int']
    with pytest.raises(KeyError):
        v = fv_conf_object['/s_main/z_int']
    with pytest.raises(KeyError):
        v = fv_conf_object['']
    with pytest.raises(AssertionError):
        v = fv_conf_object[None]


def test_config_iter(fv_conf_object):
    l_option = \
        { '/main/lost': 'default'
        , '/main/lost_list': list('default')
        , '/main/bool': True
        , '/main/int': 42
        , '/main/bigint': 2 * 1024
        , '/main/float': 3.141592
        , '/main/int_list': [1, 2, 3]
        , '/main/complex_list': [1, 5, 10, 42]
        , '/main/complex_list/as': ['I', 'V', 'X', '?']
        , '/main/complex': 'ok'
        , '/main/complex/kind': 'nice'}
    v_idx = -1
    for v_option, v_content in fv_conf_object:
        assert v_content == l_option[v_option]
        v_idx += 1
    assert v_idx >= 0
    assert len(fv_conf_object) == len(l_option)


def test_opt_manager_errors():
    with pytest.raises(ValueError):
        v = ' spaces ' >> m_c.DefValue()
    with pytest.raises(ValueError):
        v = 'path/sep' >> m_c.DefValue()
    with pytest.raises(ValueError):
        m_c.DefValue().name_set('')
    with pytest.raises(ValueError):
        m_c.DefValue().name_set('l_bad')
    with pytest.raises(ValueError):
        v = m_c.DefValue()
        v.name_set('main')
        v.name_set('niam')
    with pytest.raises(SyntaxError):
        v = m_c.DefValue() << 'wrong_side'
    with pytest.raises(SyntaxError):
        v = {'wrong', 'side'} >> m_c.DefValue()
    with pytest.raises(KeyError):
        v = ('main' >> m_c.DefValue()) == ('main' >> m_c.DefValue())
    with pytest.raises(KeyError):
        v = ('main' == ('main' >> m_c.DefValue()))
    with pytest.raises(TypeError):
        v = (42 == m_c.DefValue())
    with pytest.raises(TypeError):
        v = (m_c.DefValue() == 42)
    with pytest.raises(KeyError):
        v = (('main' >> m_c.DefValue()) == 'main')
    with pytest.raises(AssertionError):
        v = m_c.DefValue(iv_default={})
    with pytest.raises(ValueError):
        v = m_c.DefValueInt(iv_default='bad')
    with pytest.raises(ValueError):
        v = m_c.DefValueInt().value_parse('bad')
    with pytest.raises(ValueError):
        v = m_c.DefValueFloat(iv_default='bad')
    with pytest.raises(ValueError):
        v = m_c.DefValueInt().value_parse('bad')
    with pytest.raises(ValueError):
        v = m_c.DefValueChoise({})


def test_opt_manager():
    v = m_c.def_opt('main')
    assert v.name == 'main'
    assert v.kind == 's'
    assert not v.required
    assert type(v) == m_c.DefSection

    v = m_c.def_opt('v_main')
    assert v.name == 'main'
    assert v.kind == 'v'
    assert v.required
    assert type(v) == m_c.DefValue

    v = m_c.def_opt('l_main')
    assert v.name == 'main'
    assert v.kind == 'l'
    assert v.required
    assert type(v) == m_c.DefList

    v = 'main' >> m_c.DefSection()
    assert v.name == 'main'
    assert v.kind == 's'
    assert not v.required
    assert v != 'niam'

    v = 'main' >> m_c.DefValue(iv_default='ok')
    assert v.name == 'main'
    assert v.kind == 'v'
    assert v.default == 'ok'
    assert not v.required
    assert v.value_parse('ok') == 'ok'

    v = 'main' >> m_c.DefValueInt(iv_default='1')
    assert v.name == 'main'
    assert v.kind == 'v'
    assert v.default == 1
    assert not v.required
    assert v.value_parse('42') == 42
    assert v.value_parse('1KB') == 1024

    v = 'main' >> m_c.DefValueFloat(iv_default='1')
    assert v.name == 'main'
    assert v.default == 1.0
    assert not v.required
    assert v.value_parse('42') == 42.0

    v = 'main' >> m_c.DefValueChoise(il_mapping={'Yes': 1, 'No': -1}, iv_default='Yes')
    assert v.name == 'main'
    assert v.default == 1
    assert not v.required
    assert v.value_parse('No') == -1
    assert v.value_parse('Yes') == 1

    v = m_c.DefValueChoise(il_mapping=[('Yes', 1), ('No', -1)], iv_default='Yes')
    assert v.value_parse('No') == -1
    assert v.value_parse('Yes') == 1

    v = 'main' >> m_c.DefList(iv_default=None)
    assert v.name == 'main'
    assert v.kind == 'l'
    assert v.default == []
    assert v.required
    assert v.value_parse('ok') == 'ok'

    v = m_c.DefList(iv_default=[])
    assert v.default == []
    assert not v.required

    v = 'main' >> m_c.DefListInt(iv_default='42')
    assert v.name == 'main'
    assert v.kind == 'l'
    assert v.default == [4, 2]
    assert not v.required
    assert v.value_parse('42') == 42
    assert v.value_parse('1KB') == 1024

    v = m_c.DefListInt(iv_default=range(0, 2))
    assert v.default == [0, 1]

    v = m_c.DefListInt(iv_default=[0, 1])
    assert v.default == [0, 1]

    v = 'main' >> m_c.DefListFloat(iv_default='42')
    assert v.name == 'main'
    assert v.kind == 'l'
    assert not v.required
    assert v.default == [4.0, 2.0]
    assert v.value_parse('42') == 42.0

    v = m_c.DefListFloat(iv_default=range(0, 2))
    assert v.default == [0.0, 1.0]

    v = m_c.DefListFloat(iv_default=[0, 1])
    assert v.default == [0.0, 1.0]

    v = m_c.DefListFloat(iv_default=[27.01, 16.09])
    assert v.default == [27.01, 16.09]


def test_conf_load():
    v = m_c.Config(
        {'s' >> m_c.DefSection() <<
            {'v_a',
             'v_b',
             'l_c',
             'l' >> m_c.DefList(),
             'v' >> m_c.DefValue()}
         })
    v.load_d({'s': {'a': 1, 'b': 2}})
    assert v._walker_l[0].node_curr_l[0]['s']['a'] == 1
    assert v._walker_l[0].node_curr_l[0]['s']['b'] == 2
    assert v._parser_l['/s'].kind == 's'
    assert v._parser_l['/s'].name == 's'
    assert not v._parser_l['/s'].required
    assert v._parser_l['/s/a'].kind == 'v'
    assert v._parser_l['/s/a'].name == 'a'
    assert v._parser_l['/s/a'].required
    assert v._parser_l['/s/b'].kind == 'v'
    assert v._parser_l['/s/b'].name == 'b'
    assert v._parser_l['/s/b'].required
    assert v._parser_l['/s/c'].kind == 'l'
    assert v._parser_l['/s/c'].name == 'c'
    assert v._parser_l['/s/c'].required
    assert v._parser_l['/s/l'].kind == 'l'
    assert v._parser_l['/s/l'].name == 'l'
    assert v._parser_l['/s/l'].required
    assert v._parser_l['/s/v'].kind == 'v'
    assert v._parser_l['/s/v'].name == 'v'
    assert v._parser_l['/s/v'].required
    with pytest.raises(KeyError):
        print(v['/s/v'])
    with pytest.raises(KeyError):
        print(v['/s/l'])
    assert len([_ for _ in v._parser_l.keys() if _ not in {'/s', '/s/a', '/s/b', '/s/c', '/s/l', '/s/v'}]) == 0
    v = m_c.Config({'v_0' >> m_c.DefValue(iv_required=False) << {'v_00' >> m_c.DefValue() << {'v_000' >> m_c.DefValue(iv_default='42')}}})
    v.load_d({})
    with pytest.raises(KeyError):
        print(v['/0/00'])
    assert v['/0'] is None
    assert v['/0/00/000'] == '42'
    v.load_d([('s', {'a': 1, 'b': 2})])
    assert v._walker_l[0].node_curr_l[0]['s']['a'] == 1
    assert v._walker_l[0].node_curr_l[0]['s']['b'] == 2


def test_subconf_load():
    v_c = m_c.Config(
        {'s' >> m_c.DefSection() <<
            {'v_a' >> m_c.DefValue() <<
                {'v_aa', 'v_ab'}
            }
        })
    v_c.load_d({'s': {'a': {'v': 'a0', 'aa': 0, 'ab': 1}}})
    v_sc = v_c.node('/s/a')
    v_sc.load_d({'s': {'a': {'v': 'a1', 'aa': 42, 'ab': 24}}})
    assert v_sc.v == 'a1'
    assert v_sc['/aa'] == 42
    v_sc.load_d([('s', {'a': {'v': 'a1'}})])


def test_abc():
    v = m_c.DefOptAbc('_')
    assert v.kind == '_'
    assert v.name == ''

    v = 'main' >> m_c.DefOptAbc('_')
    assert v.name == 'main'

    with pytest.raises(NotImplementedError):
        v = m_c.DefItemAbc('_').value_parse('dummy')
    with pytest.raises(NotImplementedError):
        v = m_c.DefItemAbc('_').default_get('dummy')


def test_conf_errors():
    with pytest.raises(AssertionError):
        v = m_c.Config(42)
    with pytest.raises(KeyError):
        v = m_c.Config({
            'main' >> m_c.DefSection() << {
                'twin' >> m_c.DefValue(iv_default='default'),
                'twin' >> m_c.DefValueInt()
            }
        })
