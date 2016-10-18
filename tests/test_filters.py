from marvinbot.filters import RegexpFilter, MultiRegexpFilter
from nose.tools import assert_raises


def test_basic_match():
    filt = RegexpFilter(r't[e]+st', mode='match')
    assert filt('test') is not None
    assert filt('teeeest').group(0) == 'teeeest'


def test_basic_search():
    filt = RegexpFilter(r't[e]+st', mode='search')
    assert filt('somethigntotest') is not None
    assert filt('someteeeest').group(0) == 'teeeest'


def test_basic_no_match():
    filt = RegexpFilter(r't[e]+st', mode='match')
    assert filt('something') is None


def test_wrong_mode():
    assert_raises(ValueError, RegexpFilter, r't[e]+st', mode='unknown')
    assert_raises(ValueError, MultiRegexpFilter, [r't[e]+st'], mode='unknown')


def test_multi_match():
    filt = MultiRegexpFilter({'exp1': r't[e]+st', 'exp2': r's[o]+me'})

    m = filt('test')
    assert m is not None
    assert m.group(0) == 'test' and m.group('exp1') == 'test'
    assert m.group('exp1') == 'test' and m.group('exp2') is None

    m = filt('some')
    assert m is not None
    assert m.group(0) == 'some' and m.group('exp2') == 'some'
    assert m.group('exp1') is None and m.group('exp2') == 'some'

    m = filt('testsome')
    assert m is not None
    assert m.group(0) == 'test' and m.group('exp1') == 'test' and m.group('exp2') is None
