"""Distributed 64-bit Snowflake ID Generation Framework (Twitter Snowflake Specification).

Generates unique, time-ordered 64-bit transaction identifiers across distributed
banking nodes without centralized coordination or database locking.

Bit Layout (64 bits):
- 1 bit  : Unused sign bit (always 0)
- 41 bits: Timestamp in milliseconds since custom epoch (approx. 69 years lifetime)
- 5 bits : Datacenter ID (0 - 31)
- 5 bits : Worker / Machine ID (0 - 31)
- 12 bits: Sequence counter (up to 4096 unique IDs per millisecond per worker)
"""

import threading
import time
from datetime import datetime, timezone
from typing import Dict, NamedTuple


class DecodedSnowflake(NamedTuple):
    snowflake_id: int
    timestamp_ms: int
    datetime_utc: datetime
    datacenter_id: int
    worker_id: int
    sequence: int


class SnowflakeIdGenerator:
    """Thread-safe 64-bit Distributed Snowflake Identifier Generator."""

    # Custom Banking Epoch: 2026-01-01 00:00:00 UTC
    DEFAULT_EPOCH_MS: int = 1767225600000

    # Bit allocation
    DATACENTER_ID_BITS: int = 5
    WORKER_ID_BITS: int = 5
    SEQUENCE_BITS: int = 12

    # Maximum values
    MAX_DATACENTER_ID: int = -1 ^ (-1 << DATACENTER_ID_BITS)  # 31
    MAX_WORKER_ID: int = -1 ^ (-1 << WORKER_ID_BITS)          # 31
    SEQUENCE_MASK: int = -1 ^ (-1 << SEQUENCE_BITS)           # 4095

    # Bit shift positions
    WORKER_ID_SHIFT: int = SEQUENCE_BITS
    DATACENTER_ID_SHIFT: int = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_LEFT_SHIFT: int = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

    def __init__(
        self,
        datacenter_id: int = 1,
        worker_id: int = 1,
        epoch_ms: int = DEFAULT_EPOCH_MS,
    ) -> None:
        if not (0 <= datacenter_id <= self.MAX_DATACENTER_ID):
            raise ValueError(f"Datacenter ID must be in [0, {self.MAX_DATACENTER_ID}]. Got {datacenter_id}")
        if not (0 <= worker_id <= self.MAX_WORKER_ID):
            raise ValueError(f"Worker ID must be in [0, {self.MAX_WORKER_ID}]. Got {worker_id}")

        self.datacenter_id = datacenter_id
        self.worker_id = worker_id
        self.epoch_ms = epoch_ms

        self.sequence = 0
        self.last_timestamp_ms = -1
        self._lock = threading.Lock()

    def _current_timestamp_ms(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        """Spins until next millisecond is reached."""
        curr = self._current_timestamp_ms()
        while curr <= last_timestamp:
            curr = self._current_timestamp_ms()
        return curr

    def generate_id(self) -> int:
        """Generates a unique, collision-free 64-bit integer Snowflake ID."""
        with self._lock:
            now_ms = self._current_timestamp_ms()

            if now_ms < self.last_timestamp_ms:
                # Clock drift / NTP backward jump protection
                diff = self.last_timestamp_ms - now_ms
                if diff <= 5:
                    time.sleep(diff / 1000.0)
                    now_ms = self._current_timestamp_ms()
                else:
                    raise RuntimeError(f"Clock moved backwards by {diff}ms. Rejecting ID generation.")

            if now_ms == self.last_timestamp_ms:
                # Same millisecond: increment sequence counter
                self.sequence = (self.sequence + 1) & self.SEQUENCE_MASK
                if self.sequence == 0:
                    # Sequence exhausted for this millisecond, wait until next millisecond
                    now_ms = self._wait_next_millis(self.last_timestamp_ms)
            else:
                # New millisecond: reset sequence counter
                self.sequence = 0

            self.last_timestamp_ms = now_ms

            # Compute 64-bit Snowflake ID via bitwise operations
            snowflake_id = (
                ((now_ms - self.epoch_ms) << self.TIMESTAMP_LEFT_SHIFT)
                | (self.datacenter_id << self.DATACENTER_ID_SHIFT)
                | (self.worker_id << self.WORKER_ID_SHIFT)
                | self.sequence
            )
            return snowflake_id

    def generate_id_str(self, prefix: str = "TXN_") -> str:
        """Returns string format with optional prefix (e.g. TXN_72948194829104819)."""
        return f"{prefix}{self.generate_id()}"

    def decode_id(self, snowflake_id: int) -> DecodedSnowflake:
        """Deconstructs a 64-bit Snowflake ID into its constituent components."""
        sequence = snowflake_id & self.SEQUENCE_MASK
        worker_id = (snowflake_id >> self.WORKER_ID_SHIFT) & self.MAX_WORKER_ID
        datacenter_id = (snowflake_id >> self.DATACENTER_ID_SHIFT) & self.MAX_DATACENTER_ID
        timestamp_offset = snowflake_id >> self.TIMESTAMP_LEFT_SHIFT
        actual_timestamp_ms = timestamp_offset + self.epoch_ms
        dt_utc = datetime.fromtimestamp(actual_timestamp_ms / 1000.0, tz=timezone.utc)

        return DecodedSnowflake(
            snowflake_id=snowflake_id,
            timestamp_ms=actual_timestamp_ms,
            datetime_utc=dt_utc,
            datacenter_id=datacenter_id,
            worker_id=worker_id,
            sequence=sequence,
        )


# Global default instance for banking worker node
default_snowflake_generator = SnowflakeIdGenerator(datacenter_id=1, worker_id=1)
