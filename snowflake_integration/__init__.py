"""Snowflake Integration Package.

Provides:
1. Distributed 64-bit Snowflake ID Generator (Twitter Snowflake specification).
2. Snowflake Cloud Data Warehouse schema, ingestion connector, and analytics queries.
"""

from snowflake_integration.snowflake_id import (
    DecodedSnowflake,
    SnowflakeIdGenerator,
    default_snowflake_generator,
)
from snowflake_integration.snowflake_warehouse import (
    SNOWFLAKE_DDL_SCHEMA,
    SnowflakeWarehouseConnector,
)

__all__ = [
    "SnowflakeIdGenerator",
    "DecodedSnowflake",
    "default_snowflake_generator",
    "SnowflakeWarehouseConnector",
    "SNOWFLAKE_DDL_SCHEMA",
]
