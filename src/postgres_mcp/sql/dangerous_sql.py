from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
from typing import Optional

from typing_extensions import LiteralString

from .sql_driver import SqlDriver

logger = logging.getLogger(__name__)


class DangerousSqlDriver(SqlDriver):
    """A wrapper around any SqlDriver that allows any query but added a timeout."""

    def __init__(self, sql_driver: SqlDriver, timeout: float | None = None):
        """Initialize with an underlying SQL driver and optional timeout.

        Args:
            sql_driver: The underlying SQL driver to wrap
            timeout: Optional timeout in seconds for query execution
        """
        self.sql_driver = sql_driver
        self.timeout = timeout

    async def execute_query(
        self,
        query: LiteralString,
        params: list[Any] | None = None,
        force_readonly: bool = False,
    ) -> Optional[list[SqlDriver.RowResult]]:  # noqa: UP007
        """Execute a query after validating it is safe"""

        # NOTE: Always force readonly=True in SafeSqlDriver regardless of what was passed
        if self.timeout:
            try:
                async with asyncio.timeout(self.timeout):
                    return await self.sql_driver.execute_query(
                        f"/* crystaldba */ {query}",
                        params=params,
                        force_readonly=force_readonly,
                    )
            except asyncio.TimeoutError as e:
                logger.warning(f"Query execution timed out after {self.timeout} seconds: {query[:100]}...")
                raise ValueError(
                    f"Query execution timed out after {self.timeout} seconds in restricted mode. "
                    "Consider simplifying your query or increasing the timeout."
                ) from e
            except Exception as e:
                logger.error(f"Error executing query: {e}")
                raise
        else:
            return await self.sql_driver.execute_query(
                f"/* crystaldba */ {query}",
                params=params,
                force_readonly=force_readonly,
            )
