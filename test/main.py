import pytest
import conflex as m_c

l_test_dict: dict = {
    'simple_nulls0': {'s_main': {'v_missing': None, 'l_lost': None, 'v_bool': 'true', 'v_int': '42', 'v_bigint': '2KB', 'v_float': '3.141592', 'l_int_list': ['1', '2', '3'], 'v_complex': {'v': 'ok', 'v_kind': 'nice'}}}
}

@pytest.fixture(scope='module', params=['fl:simple.yaml', 'fl:simple_nopref.yaml', 'fl:simple_fullpath.yaml', 'kv:simple_nulls0'])
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
                , '/main/missing': m_c.DefValue(iv_default='default')
                , '/main/lost': m_c.DefList(iv_default=list('default'))
                , '/main/bool': m_c.DefValueEnum({'True': True, 'true': True, 'False': False, 'false': False})
                , '/main/int': m_c.DefValueInt()
                , '/main/bigint': m_c.DefValueInt()
                , '/main/float': m_c.DefValueFloat()
                , '/main/int_list': m_c.DefListInt()
                , '/main/complex': m_c.DefValue()
                , '/main/complex/kind': m_c.DefValue()}

    v_ret = m_c.Config({
        'main' >> m_c.DefSection() << {
            'missing' >> m_c.DefValue(iv_default='default'),
            'lost' >> m_c.DefList(iv_default=list('default')),
            'bool' >> m_c.DefValueEnum({'True': True, 'true': True, 'False': False, 'false': False}),
            'int' >> m_c.DefValueInt(),
            'bigint' >> m_c.DefValueInt(),
            'float' >> m_c.DefValueFloat(),
            'int_list' >> m_c.DefListInt(),
            'complex' >> m_c.DefValue() << {
                'kind' >> m_c.DefValue()}}})
    v_ret.load_d(fv_conf_dict)
    return v_ret


def test_config_values(fv_conf_object):
    assert fv_conf_object['/main/missing'] == 'default'
    assert fv_conf_object['/main/lost'] == list('default')
    assert fv_conf_object['/main/bool']  # == True
    assert fv_conf_object['/main/int'] == 42
    assert fv_conf_object['/main/bigint'] == (2 * 1024)
    assert fv_conf_object['/main/int_list'] == [1, 2, 3]
    assert fv_conf_object['/main/float'] == 3.141592
    assert fv_conf_object['/main/complex'] == 'ok'
    assert fv_conf_object['/main/complex/kind'] == 'nice'


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


def test_config_kind_values(fv_conf_object):
    assert fv_conf_object['/s_main/v_missing'] == 'default'
    assert fv_conf_object['/s_main/l_lost'] == list('default')
    assert fv_conf_object['/s_main/v_bool']  # == True
    assert fv_conf_object['/s_main/v_int'] == 42
    assert fv_conf_object['/s_main/v_bigint'] == (2 * 1024)
    assert fv_conf_object['/s_main/l_int_list'] == [1, 2, 3]
    assert fv_conf_object['/s_main/v_float'] == 3.141592
    assert fv_conf_object['/s_main/v_complex'] == 'ok'
    assert fv_conf_object['/s_main/v_complex/v_kind'] == 'nice'


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

'''

'''
def test_config_iter(fv_conf_object):
    l_option = \
        { '/main/missing': 'default'
        , '/main/lost': list('default')
        , '/main/bool': True
        , '/main/int': 42
        , '/main/bigint': 2 * 1024
        , '/main/float': 3.141592
        , '/main/int_list': [1, 2, 3]
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
    with pytest.raises(TypeError):
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
        v = m_c.DefValueEnum({})


def test_opt_manager():
    v = m_c.def_opt('main')
    assert v.v_name == 'main'
    assert v.v_kind == 's'
    assert type(v) == m_c.DefSection

    v = m_c.def_opt('v_main')
    assert v.v_name == 'main'
    assert v.v_kind == 'v'
    assert type(v) == m_c.DefValue

    v = m_c.def_opt('l_main')
    assert v.v_name == 'main'
    assert v.v_kind == 'l'
    assert type(v) == m_c.DefList

    v = 'main' >> m_c.DefSection()
    assert v.v_name == 'main'
    assert v.v_kind == 's'
    assert v != 'niam'

    v = 'main' >> m_c.DefValue(iv_default='ok')
    assert v.v_name == 'main'
    assert v.v_kind == 'v'
    assert v.v_default == 'ok'
    assert v.value_parse('ok') == 'ok'

    v = 'main' >> m_c.DefValueInt(iv_default='1')
    assert v.v_name == 'main'
    assert v.v_kind == 'v'
    assert v.v_default == 1
    assert v.value_parse('42') == 42
    assert v.value_parse('1KB') == 1024

    v = 'main' >> m_c.DefValueFloat(iv_default='1')
    assert v.v_name == 'main'
    assert v.v_default == 1.0
    assert v.value_parse('42') == 42.0

    v = 'main' >> m_c.DefValueEnum(il_mapping={'Yes': 1, 'No': -1}, iv_default='Yes')
    assert v.v_name == 'main'
    assert v.v_default == 1
    assert v.value_parse('No') == -1
    assert v.value_parse('Yes') == 1

    v = m_c.DefValueEnum(il_mapping=[('Yes', 1), ('No', -1)], iv_default='Yes')
    assert v.value_parse('No') == -1
    assert v.value_parse('Yes') == 1

    v = 'main' >> m_c.DefList(iv_default=None)
    assert v.v_name == 'main'
    assert v.v_kind == 'l'
    assert v.v_default == []
    assert v.value_parse('ok') == 'ok'

    v = m_c.DefList(iv_default=[])
    assert v.v_default == []

    v = 'main' >> m_c.DefListInt(iv_default='42')
    assert v.v_name == 'main'
    assert v.v_kind == 'l'
    assert v.v_default == [4, 2]
    assert v.value_parse('42') == 42
    assert v.value_parse('1KB') == 1024

    v = m_c.DefListInt(iv_default=range(0, 2))
    assert v.v_default == [0, 1]

    v = m_c.DefListInt(iv_default=[0, 1])
    assert v.v_default == [0, 1]

    v = 'main' >> m_c.DefListFloat(iv_default='42')
    assert v.v_name == 'main'
    assert v.v_kind == 'l'
    assert v.v_default == [4.0, 2.0]
    assert v.value_parse('42') == 42.0

    v = m_c.DefListFloat(iv_default=range(0, 2))
    assert v.v_default == [0.0, 1.0]

    v = m_c.DefListFloat(iv_default=[0, 1])
    assert v.v_default == [0.0, 1.0]

    v = m_c.DefListFloat(iv_default=[27.01, 16.09])
    assert v.v_default == [27.01, 16.09]


def test_conf_load():
    v = m_c.Config({'s' >> m_c.DefSection() << {'v_a', 'v_b'}})
    v.load_d({'s': {'a': 1, 'b': 2}})
    assert v._l_conf['s']['a'] == 1
    assert v._l_conf['s']['b'] == 2
    v.load_d([('s', {'a': 1, 'b': 2})])
    assert v._l_conf['s']['a'] == 1
    assert v._l_conf['s']['b'] == 2


def test_abc():
    v = m_c.DefOptAbc('_')
    assert v.v_kind == '_'
    assert v.v_name == ''

    v = 'main' >> m_c.DefOptAbc('_')
    assert v.v_name == 'main'

    with pytest.raises(NotImplementedError):
        v = m_c.DefItemAbc('_').value_parse('dummy')

def test_conf_errors():
    with pytest.raises(TypeError):
        v = m_c.Config(42)