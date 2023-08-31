import random

from pdr_backend.util.strutil import StrMixin, dictStr


def testStrMixin():
    class Foo(StrMixin):
        def __init__(self):
            self.x = 1
            self.y = 2
            self.d = {"a": 3, "b": 4}
            self.d2 = {}
            self.__ignoreVal = "ignoreVal"  # pylint: disable=unused-private-member

        def ignoreMethod(self):
            pass

    f = Foo()
    s = str(f)
    s2 = s.replace(" ", "")
    assert "Foo={" in s
    assert "x=1" in s2
    assert "y=2" in s2
    assert "d=dict={" in s2
    assert "d2={}" in s2
    assert "'a':3" in s2
    assert "'b':4" in s2
    assert "Foo}" in s
    assert "ignoreVal" not in s
    assert "ignoreMethod" not in s


def testDictStr():
    d = {"a": 3, "b": 4}
    s = dictStr(d)
    s2 = s.replace(" ", "")
    assert "dict={" in s
    assert "'a':3" in s2
    assert "'b':4" in s2
    assert "dict}" in s


def testEmptyDictStr():
    d = {}
    s = dictStr(d)
    assert s == ("{}")
