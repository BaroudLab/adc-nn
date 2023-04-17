from .. import io
from pytest import fixture
import numpy as np

SIZE = (256, 256)


@fixture
def make_bf():
    return np.random.randint((2**16), size=SIZE, dtype="uint16")


@fixture
def make_fluo():
    return np.random.randint((850), size=SIZE, dtype="uint16") + 400


def test_to8bits(make_bf):
    out = io.to8bits(make_bf)
    assert out.dtype == np.uint8


def test_uint16_to_base64(make_bf):
    out = io.encode_base64(make_bf)
    assert isinstance(out, str)


def test_uint8_to_base64(make_bf):
    out = io.encode_base64(io.to8bits(make_bf))
    assert isinstance(out, str)


def test_rgb(make_bf, make_fluo):
    out = io.bf_fluo_2rgb(io.to8bits(make_bf), io.to8bits(make_fluo))
    assert out.dtype == np.uint8
    assert list(out.shape) == list(SIZE) + [3]
    assert isinstance(io.encode_base64(out), str)
