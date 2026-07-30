"""Tests for hve.protocol — HVE1 framing, BASE15/CHI40/CHI39 profiles."""

import pytest

from hve.core import HVEState, HVEError, encode_base
from hve.chromatic import HVEColor
from hve.protocol import (
    pack_base15,
    unpack_base15,
    base15_packed_size,
    pack_chi40,
    unpack_chi40,
    pack_chi39,
    unpack_chi39,
    make_frame,
    parse_frame,
    PROFILE_BASE15,
    PROFILE_CHI40,
)


class TestBase15Packing:
    @pytest.mark.parametrize("count", [0, 1, 2, 7, 8, 9, 31, 257])
    def test_roundtrip(self, count):
        indices = [(i * 7919 + 17) % 32400 for i in range(count)]
        packed = pack_base15(indices)
        assert len(packed) == base15_packed_size(count)
        unpacked = unpack_base15(packed, count)
        assert unpacked == indices

    def test_reserved_word_rejected(self):
        with pytest.raises(HVEError, match="invalid or reserved"):
            pack_base15([32400])

    def test_nonzero_padding_rejected(self):
        # Pack 1 word (15 bits → 2 bytes, 1 padding bit)
        packed = bytearray(pack_base15([100]))
        # Set padding bit
        packed[-1] |= 1
        with pytest.raises(HVEError, match="padding"):
            unpack_base15(bytes(packed), 1)

    def test_empty_stream(self):
        assert pack_base15([]) == b""
        assert unpack_base15(b"", 0) == []

    def test_length_mismatch(self):
        with pytest.raises(HVEError, match="length"):
            unpack_base15(b"\x00", 2)


class TestChi40:
    def test_roundtrip_no_color(self):
        state = HVEState(45, 0, 2, 3)
        color = HVEColor.no_color()
        packed = pack_chi40(state, color)
        assert len(packed) == 5
        dec_state, dec_color = unpack_chi40(packed)
        assert dec_state == state
        assert dec_color == color

    def test_roundtrip_rgb(self):
        state = HVEState(359, 1, 4, 8)
        color = HVEColor.rgb(128, 64, 32)
        packed = pack_chi40(state, color)
        dec_state, dec_color = unpack_chi40(packed)
        assert dec_state == state
        assert dec_color == color

    def test_invalid_no_color_rejected(self):
        # P=0 but R=1 → invalid
        data = bytes([0, 0, 1, 0, 0])
        with pytest.raises(HVEError):
            unpack_chi40(data)

    def test_wrong_length(self):
        with pytest.raises(HVEError, match="5 bytes"):
            unpack_chi40(b"\x00\x00\x00\x00")


class TestChi39:
    def test_roundtrip(self):
        from hve.chromatic import encode_chi, CHI_MAX_INDEX
        for idx in [0, 1, 100000, CHI_MAX_INDEX]:
            packed = pack_chi39(idx)
            assert len(packed) == 5
            unpacked = unpack_chi39(packed)
            assert unpacked == idx

    def test_bit39_rejected(self):
        data = bytes([0x80, 0, 0, 0, 0])
        with pytest.raises(HVEError, match="bit 39"):
            unpack_chi39(data)

    def test_out_of_range(self):
        from hve.chromatic import CHI_MAX_INDEX
        with pytest.raises(HVEError):
            pack_chi39(CHI_MAX_INDEX + 1)


class TestFraming:
    def test_base15_frame_roundtrip(self):
        indices = [0, 100, 200, 300, 400, 500, 600, 700, 800]
        payload = pack_base15(indices)
        frame = make_frame(PROFILE_BASE15, len(indices), payload, flags=0x1234)
        profile, flags, count, dec_payload = parse_frame(frame)
        assert profile == PROFILE_BASE15
        assert flags == 0x1234
        assert count == 9
        assert dec_payload == payload

    def test_chi40_frame_roundtrip(self):
        state = HVEState(10, 0, 1, 2)
        color = HVEColor.rgb(100, 200, 50)
        payload = pack_chi40(state, color)
        frame = make_frame(PROFILE_CHI40, 1, payload)
        profile, flags, count, dec_payload = parse_frame(frame)
        assert profile == PROFILE_CHI40
        assert count == 1
        assert dec_payload == payload

    def test_crc_corruption_detected(self):
        payload = pack_base15([0, 1, 2])
        frame = bytearray(make_frame(PROFILE_BASE15, 3, payload))
        frame[-1] ^= 0x01  # corrupt last byte
        with pytest.raises(HVEError, match="CRC"):
            parse_frame(bytes(frame))

    def test_truncated_frame(self):
        with pytest.raises(HVEError, match="truncated"):
            parse_frame(b"\x00" * 10)

    def test_bad_magic(self):
        with pytest.raises(HVEError, match="magic"):
            parse_frame(b"XXXX" + b"\x00" * 12)

    def test_bad_version(self):
        frame = b"HVE1" + bytes([99]) + b"\x00" * 11
        with pytest.raises(HVEError, match="version"):
            parse_frame(frame)

    def test_payload_size_mismatch(self):
        with pytest.raises(HVEError, match="exactly"):
            make_frame(PROFILE_BASE15, 5, b"\x00")

    def test_crc32_known_vector(self):
        """CRC-32/ISO-HDLC of '123456789' = 0xCBF43926."""
        import binascii
        assert binascii.crc32(b"123456789") & 0xFFFFFFFF == 0xCBF43926
