"""HVE Protocol — framing, stream packing, and serialization profiles.

Profiles:
    BASE15: MSB-first 15-bit stream packing of BASE indices.
    CHI40: Aligned 40-bit [index:15][P:1][R:8][G:8][B:8] per state.
    CHI39: Compact 39-bit monolithic χ index in 5 bytes.

Frame format (HVE1):
    Bytes 0–3:  Magic "HVE1"
    Byte 4:     Version major (1)
    Byte 5:     Profile (0x01=BASE15, 0x02=CHI40)
    Bytes 6–7:  Flags (big-endian uint16)
    Bytes 8–11: State count (big-endian uint32)
    Bytes 12–15: CRC-32/ISO-HDLC of payload (big-endian uint32)
    Bytes 16+:  Payload
"""

from __future__ import annotations

import binascii
import struct

from hve.core import (
    HVEState,
    HVEError,
    encode_base,
    decode_base,
    BASE_CARDINALITY,
)
from hve.chromatic import (
    HVEColor,
    validate_color,
    CHI_MAX_INDEX,
)

# ─── Constants ────────────────────────────────────────────────────────────────

PROFILE_BASE15: int = 0x01
PROFILE_CHI40: int = 0x02
FRAME_HEADER_SIZE: int = 16
FRAME_MAGIC: bytes = b"HVE1"
FRAME_VERSION_MAJOR: int = 1


# ─── BASE15 Stream Packing ───────────────────────────────────────────────────

def base15_packed_size(state_count: int) -> int:
    """Compute the byte size required to pack *state_count* 15-bit words."""
    if state_count < 0:
        raise HVEError("state_count cannot be negative")
    return (state_count * 15 + 7) // 8


def pack_base15(indices: list[int] | tuple[int, ...]) -> bytes:
    """Pack a sequence of BASE indices into an MSB-first 15-bit byte stream.

    Unused trailing bits in the last byte are zero-padded.

    Args:
        indices: A sequence of valid BASE indices in [0, 32399].

    Returns:
        The packed byte string.

    Raises:
        HVEError: If any index is invalid or reserved.
    """
    output = bytearray(base15_packed_size(len(indices)))
    bit_pos = 0
    for word in indices:
        if not (0 <= word < BASE_CARDINALITY):
            raise HVEError(f"invalid or reserved 15-bit word: {word}")
        for bit in range(14, -1, -1):
            byte_index = bit_pos // 8
            bit_in_byte = 7 - (bit_pos % 8)
            output[byte_index] |= ((word >> bit) & 1) << bit_in_byte
            bit_pos += 1
    return bytes(output)


def unpack_base15(data: bytes, state_count: int) -> list[int]:
    """Unpack an MSB-first 15-bit byte stream into BASE indices.

    Validates that:
      - The data length exactly matches the expected packed size.
      - Trailing padding bits are zero.
      - Each decoded word is in [0, 32399].

    Args:
        data: The packed byte string.
        state_count: Number of states encoded in the stream.

    Returns:
        A list of BASE indices.

    Raises:
        HVEError: On length mismatch, nonzero padding, or reserved words.
    """
    required = base15_packed_size(state_count)
    if len(data) != required:
        raise HVEError(f"payload length must be exactly {required} bytes, got {len(data)}")
    result: list[int] = []
    bit_pos = 0
    for _ in range(state_count):
        word = 0
        for bit in range(14, -1, -1):
            byte_index = bit_pos // 8
            bit_in_byte = 7 - (bit_pos % 8)
            word |= ((data[byte_index] >> bit_in_byte) & 1) << bit
            bit_pos += 1
        if word >= BASE_CARDINALITY:
            raise HVEError(f"decoded word {word} belongs to the reserved interval")
        result.append(word)
    # Validate zero padding
    if required and (state_count * 15) % 8:
        padding_bits = 8 - ((state_count * 15) % 8)
        if data[-1] & ((1 << padding_bits) - 1):
            raise HVEError("nonzero padding bits")
    return result


# ─── CHI40 Aligned Profile ───────────────────────────────────────────────────

def pack_chi40(state: HVEState, color: HVEColor) -> bytes:
    """Pack a state and color into the aligned 40-bit CHI40 profile.

    Format: [base_index:15][present:1][R:8][G:8][B:8] = 5 bytes, big-endian.

    Args:
        state: A valid HVE state.
        color: A valid HVE color.

    Returns:
        A 5-byte big-endian representation.
    """
    base_index = encode_base(state)
    validate_color(color)
    word = (
        (base_index << 25)
        | (int(color.present) << 24)
        | (color.r << 16)
        | (color.g << 8)
        | color.b
    )
    return word.to_bytes(5, "big")


def unpack_chi40(data: bytes) -> tuple[HVEState, HVEColor]:
    """Unpack a 5-byte CHI40 representation into state and color.

    Args:
        data: Exactly 5 bytes in big-endian CHI40 format.

    Returns:
        A tuple (state, color).

    Raises:
        HVEError: On invalid data length, invalid index, or color constraint
                  violation (e.g. NoColor with nonzero RGB).
    """
    if len(data) != 5:
        raise HVEError(f"CHI40 state must occupy exactly 5 bytes, got {len(data)}")
    word = int.from_bytes(data, "big")
    base_index = (word >> 25) & 0x7FFF
    present = bool((word >> 24) & 1)
    r = (word >> 16) & 0xFF
    g = (word >> 8) & 0xFF
    b = word & 0xFF
    color = HVEColor(present, r, g, b)
    validate_color(color)
    return decode_base(base_index), color


# ─── CHI39 Compact Profile ───────────────────────────────────────────────────

def pack_chi39(index: int) -> bytes:
    """Pack a monolithic HVE-χ index into 5 bytes (39 significant bits).

    Bit 39 (MSB of byte 0) is reserved and must be zero.

    Args:
        index: A valid HVE-χ index in [0, 543,581,830,799].

    Returns:
        A 5-byte big-endian representation.

    Raises:
        HVEError: If the index is outside the valid interval.
    """
    if not (0 <= index <= CHI_MAX_INDEX):
        raise HVEError(f"HVE-χ index must be in [0, {CHI_MAX_INDEX}], got {index}")
    return index.to_bytes(5, "big")


def unpack_chi39(data: bytes) -> int:
    """Unpack a 5-byte CHI39 representation into a monolithic HVE-χ index.

    Args:
        data: Exactly 5 bytes.

    Returns:
        The HVE-χ index.

    Raises:
        HVEError: On invalid length, reserved bit 39 set, or out-of-range index.
    """
    if len(data) != 5:
        raise HVEError(f"CHI39 representation must occupy 5 bytes, got {len(data)}")
    if data[0] & 0x80:
        raise HVEError("bit 39 is reserved and must be zero")
    index = int.from_bytes(data, "big")
    if index > CHI_MAX_INDEX:
        raise HVEError(f"HVE-χ index {index} outside valid interval")
    return index


# ─── HVE1 Frame Format ───────────────────────────────────────────────────────

def frame_payload_size(profile: int, state_count: int) -> int:
    """Compute the expected payload size for a given profile and state count."""
    if profile == PROFILE_BASE15:
        return base15_packed_size(state_count)
    if profile == PROFILE_CHI40:
        return state_count * 5
    raise HVEError(f"unsupported profile: 0x{profile:02X}")


def make_frame(
    profile: int,
    state_count: int,
    payload: bytes,
    flags: int = 0,
) -> bytes:
    """Construct a deterministic HVE1 frame.

    Args:
        profile: PROFILE_BASE15 (0x01) or PROFILE_CHI40 (0x02).
        state_count: Number of states in the payload.
        payload: The serialized state data.
        flags: Optional 16-bit flags field.

    Returns:
        The complete frame (header + payload).

    Raises:
        HVEError: On payload size mismatch, invalid profile, or flag overflow.
    """
    expected = frame_payload_size(profile, state_count)
    if len(payload) != expected:
        raise HVEError(f"payload must contain exactly {expected} bytes, got {len(payload)}")
    if not (0 <= flags <= 0xFFFF):
        raise HVEError("flags must fit in uint16")
    crc = binascii.crc32(payload) & 0xFFFFFFFF
    header = (
        FRAME_MAGIC
        + bytes((FRAME_VERSION_MAJOR, profile))
        + struct.pack(">HII", flags, state_count, crc)
    )
    assert len(header) == FRAME_HEADER_SIZE
    return header + payload


def parse_frame(frame: bytes) -> tuple[int, int, int, bytes]:
    """Parse and validate an HVE1 frame.

    Checks magic, version, profile, exact length, and CRC-32 integrity.

    Args:
        frame: The raw frame bytes.

    Returns:
        A tuple (profile, flags, state_count, payload).

    Raises:
        HVEError: On any validation failure (truncated, bad magic, bad version,
                  length mismatch, CRC mismatch, unsupported profile).
    """
    if len(frame) < FRAME_HEADER_SIZE:
        raise HVEError("truncated frame")
    if frame[:4] != FRAME_MAGIC:
        raise HVEError("invalid frame magic")
    version = frame[4]
    profile = frame[5]
    if version != FRAME_VERSION_MAJOR:
        raise HVEError(f"unsupported frame version: {version}")
    flags, state_count, stored_crc = struct.unpack(">HII", frame[6:16])
    expected_payload = frame_payload_size(profile, state_count)
    if len(frame) != FRAME_HEADER_SIZE + expected_payload:
        raise HVEError("frame length mismatch")
    payload = frame[FRAME_HEADER_SIZE:]
    actual_crc = binascii.crc32(payload) & 0xFFFFFFFF
    if actual_crc != stored_crc:
        raise HVEError("CRC mismatch")
    return profile, flags, state_count, payload
