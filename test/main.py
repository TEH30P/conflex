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
            super(TestConf, self).__init__(
                { '/main': m_c.OptSection()
                , '/main/missing': m_c.OptValue(iv_default='default')
                , '/main/lost': m_c.OptList(iv_default=list('default'))
                , '/main/bool': m_c.OptValueEnum({'True': True, 'true': True, 'False': False, 'false': False})
                , '/main/int': m_c.OptValueInt()
                , '/main/bigint': m_c.OptValueInt()
                , '/main/float': m_c.OptValueFloat()
                , '/main/int_list': m_c.OptListInt()
                , '/main/complex': m_c.OptValue()
                , '/main/complex/kind': m_c.OptValue()}
            )
            # self._l_parser = \
            #     { 'main':
            #         { 'missing': m_c.OptValue(iv_default='default')
            #         , 'lost': m_c.OptList(iv_default=list('default'))
            #         , 'int': m_c.OptValue(if_value_parser=m_c.value_parser_int)
            #         , 'bigint': m_c.OptValue(if_value_parser=m_c.value_parser_int)
            #         , 'float': m_c.OptValue(if_value_parser=m_c.value_parser_float)
            #         , 'int_list': m_c.OptList(if_item_value_parser=m_c.value_parser_int)
            #         , 'complex': m_c.OptValue({
            #             'kind': m_c.OptValue()
            #             })
            #         }
            #     }

    v_ret: TestConf = TestConf()
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
    with pytest.raises(AttributeError):
        v = fv_conf_object['/main']
    with pytest.raises(KeyError):
        v = fv_conf_object['main/int']
    with pytest.raises(KeyError):
        v = fv_conf_object['/main/dummy']
    with pytest.raises(KeyError):
        v = fv_conf_object['/main/l_int']
    with pytest.raises(KeyError):
        v = fv_conf_object['/main//int']
    with pytest.raises(KeyError):
        v = fv_conf_object['/main/z_int']
    with pytest.raises(KeyError):
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
    with pytest.raises(AttributeError):
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


def test_config_iter(fv_conf_object):
    l_option: list = \
        [ ('/main/missing', 'default')
        , ('/main/lost', list('default'))
        , ('/main/bool', True)
        , ('/main/int', 42)
        , ('/main/bigint', 2 * 1024)
        , ('/main/float', 3.141592)
        , ('/main/int_list', [1, 2, 3])
        , ('/main/complex', 'ok')
        , ('/main/complex/kind', 'nice')]
    v_idx = -1
    for v_idx, l_option_container in enumerate(fv_conf_object):
        assert (l_option_container[0], l_option_container[1]) == l_option[v_idx]
    assert v_idx >= 0
    assert len(fv_conf_object) == len(l_option)


def test_opt_manager_errors():
    with pytest.raises(AttributeError):
        v = m_c.OptValue(iv_default={})
    with pytest.raises(ValueError):
        v = m_c.OptValueInt(iv_default='bad')
    with pytest.raises(ValueError):
        v = m_c.OptValueInt().value_parse('bad')
    with pytest.raises(ValueError):
        v = m_c.OptValueFloat(iv_default='bad')
    with pytest.raises(ValueError):
        v = m_c.OptValueInt().value_parse('bad')
    with pytest.raises(AttributeError):
        v = m_c.OptValueEnum({})


def test_opt_manager():
    v = m_c.OptSection()
    assert v.kind == 's'

    v = m_c.OptValue(iv_default='ok')
    assert v.kind == 'v'
    assert v.default == 'ok'
    assert v.value_parse('ok') == 'ok'

    v = m_c.OptValueInt(iv_default='1')
    assert v.kind == 'v'
    assert v.default == 1
    assert v.value_parse('42') == 42
    assert v.value_parse('1KB') == 1024

    v = m_c.OptValueFloat(iv_default='1')
    assert v.default == 1.0
    assert v.value_parse('42') == 42.0

    v = m_c.OptValueEnum(il_mapping={'Yes': 1, 'No': -1}, iv_default='Yes')
    assert v.default == 1
    assert v.value_parse('No') == -1
    assert v.value_parse('Yes') == 1

    v = m_c.OptValueEnum(il_mapping=[('Yes', 1), ('No', -1)], iv_default='Yes')
    assert v.value_parse('No') == -1
    assert v.value_parse('Yes') == 1

    v = m_c.OptList(iv_default=None)
    assert v.kind == 'l'
    assert v.default == []
    assert v.value_parse('ok') == 'ok'

    v = m_c.OptList(iv_default=[])
    assert v.default == []

    v = m_c.OptListInt(iv_default='42')
    assert v.kind == 'l'
    assert v.default == [4, 2]
    assert v.value_parse('42') == 42
    assert v.value_parse('1KB') == 1024

    v = m_c.OptListInt(iv_default=range(0, 2))
    assert v.default == [0, 1]

    v = m_c.OptListInt(iv_default=[0, 1])
    assert v.default == [0, 1]

    v = m_c.OptListFloat(iv_default='42')
    assert v.kind == 'l'
    assert v.default == [4.0, 2.0]
    assert v.value_parse('42') == 42.0

    v = m_c.OptListFloat(iv_default=range(0, 2))
    assert v.default == [0.0, 1.0]

    v = m_c.OptListFloat(iv_default=[0, 1])
    assert v.default == [0.0, 1.0]

    v = m_c.OptListFloat(iv_default=[27.01, 16.09])
    assert v.default == [27.01, 16.09]


def test_conv_load():
    v = m_c.Config({'a': m_c.OptValue(), 'b': m_c.OptValue()})
    v.load_d({'a': 1, 'b': 2})
    assert v._l_conf['a'] == 1
    assert v._l_conf['b'] == 2
    v.load_d([('a', 1), ('b', 2)])
    assert v._l_conf['a'] == 1
    assert v._l_conf['b'] == 2


def test_abc():
    v = m_c.OptAbc('_')
    assert v.kind == '_'

    with pytest.raises(NotImplementedError):
        v = m_c.OptItemAbc('_').value_parse('dummy')
