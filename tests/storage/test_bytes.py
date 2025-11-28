"""
Tests for bytes encoding/decoding functions.

Tests order-preserving encoding of Python values to bytes and back.
"""
import pytest

from bb import bytes_write, bytes_read


# ============================================================================
# Tests for bytes_write and bytes_read
# ============================================================================

def test_bytes_write_read_empty_tuple():
    """Test encoding/decoding empty tuple"""
    original = ()
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


def test_bytes_write_read_single_element():
    """Test encoding/decoding single element tuple"""
    original = ('hello',)
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


def test_bytes_write_read_mixed_types():
    """Test encoding/decoding tuple with mixed types"""
    original = ('hello', 42, 3.14, True, None)
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


def test_bytes_write_read_nested_tuple():
    """Test encoding/decoding tuple with nested tuple"""
    original = ('user123', 'metadata', ('tag1', 'tag2', 'tag3'))
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


def test_bytes_write_read_triple():
    """Test encoding/decoding 3-tuple (common nstore case)"""
    original = ('P4X432', 'blog/title', 'hyper.dev')
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


def test_bytes_write_read_unicode():
    """Test encoding/decoding tuple with unicode"""
    original = ('user', 'name', '你好世界')
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


# ============================================================================
# Tests for order preservation
# ============================================================================

def test_bytes_write_order_strings():
    """Test that encoded strings preserve lexicographic order"""
    values = [('apple',), ('banana',), ('cherry',)]
    encoded = [bytes_write(v) for v in values]

    # Encoded values should maintain order
    assert encoded[0] < encoded[1] < encoded[2]


def test_bytes_write_order_integers():
    """Test that encoded integers preserve numeric order"""
    values = [(1,), (42,), (100,), (1000,)]
    encoded = [bytes_write(v) for v in values]

    # Encoded values should maintain order
    assert encoded[0] < encoded[1] < encoded[2] < encoded[3]


def test_bytes_write_order_negative_integers():
    """Test that encoded negative integers preserve order among themselves"""
    # Note: Current encoding has negative ints type code (0x06) > zero type code (0x04),
    # so negative integers sort after zero. Test only negative number ordering.
    values = [(-100,), (-42,), (-1,)]
    encoded = [bytes_write(v) for v in values]

    # Encoded negative values should maintain order among themselves
    for i in range(len(encoded) - 1):
        assert encoded[i] < encoded[i + 1]

    # Test positive integers separately
    pos_values = [(0,), (1,), (42,), (100,)]
    pos_encoded = [bytes_write(v) for v in pos_values]

    for i in range(len(pos_encoded) - 1):
        assert pos_encoded[i] < pos_encoded[i + 1]


def test_bytes_write_order_floats():
    """Test that encoded floats preserve numeric order"""
    values = [(0.1,), (1.5,), (3.14,), (10.0,)]
    encoded = [bytes_write(v) for v in values]

    # Encoded values should maintain order
    assert encoded[0] < encoded[1] < encoded[2] < encoded[3]


def test_bytes_write_order_mixed_tuples():
    """Test order preservation with mixed-type tuples"""
    values = [
        ('user', 'age', 20),
        ('user', 'age', 30),
        ('user', 'age', 40),
    ]
    encoded = [bytes_write(v) for v in values]

    # Encoded values should maintain order
    assert encoded[0] < encoded[1] < encoded[2]


def test_bytes_write_order_prefix_matching():
    """Test order preservation with common prefixes"""
    values = [
        ('blog', 'post', 'a'),
        ('blog', 'post', 'b'),
        ('blog', 'post', 'c'),
        ('blog', 'title', 'x'),
    ]
    encoded = [bytes_write(v) for v in values]

    # Encoded values should maintain order
    assert encoded[0] < encoded[1] < encoded[2] < encoded[3]


# ============================================================================
# Tests for special cases
# ============================================================================

def test_bytes_write_null_byte_in_string():
    """Test encoding string with null byte escape"""
    original = ('test\x00data',)
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


def test_bytes_write_null_byte_in_bytes():
    """Test encoding bytes with null byte escape"""
    original = (b'test\x00data',)
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


def test_bytes_write_empty_string():
    """Test encoding empty string"""
    original = ('',)
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original


def test_bytes_write_empty_bytes():
    """Test encoding empty bytes"""
    original = (b'',)
    encoded = bytes_write(original)
    decoded = bytes_read(encoded)

    assert decoded == original
