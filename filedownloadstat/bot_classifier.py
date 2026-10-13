"""
Bot classification module using DeepLogBot.

Classifies download traffic into three categories:
- Bots: Automated scrapers and coordinated botnets
- Hubs: Legitimate institutional bulk downloaders (research facilities, mirrors)
- Organic users: Independent individual researchers
"""
import contextlib
import logging
import os
import re
from unittest import mock

import duckdb
from deeplogbot import run_bot_annotator

from exceptions import BotClassificationError

logger = logging.getLogger(__name__)

# deeplogbot hardcodes "SET memory_limit='4GB'" / "SET threads=2" /
# "PRAGMA max_temp_directory_size='30GiB'" on its DuckDB connection, which
# OOMs on the full merged parquet. These env vars (set by the Nextflow
# process from task.memory / task.cpus) override those settings.
_DUCKDB_ENV_OVERRIDES = {
    "memory_limit": "DEEPLOGBOT_DUCKDB_MEMORY_LIMIT",
    "threads": "DEEPLOGBOT_DUCKDB_THREADS",
    "max_temp_directory_size": "DEEPLOGBOT_DUCKDB_MAX_TEMP_SIZE",
}
_DUCKDB_SETTING_RE = re.compile(
    r"^\s*(SET|PRAGMA)\s+(memory_limit|threads|max_temp_directory_size)\s*=",
    re.IGNORECASE,
)


class _DuckDBConnectionOverride:
    """Proxy for a DuckDB connection that applies env-var resource overrides."""

    def __init__(self, conn, overrides: dict) -> None:
        self._conn = conn
        self._overrides = overrides

    def apply_overrides(self) -> None:
        for setting in self._overrides:
            self._conn.execute(self._override_query(setting))

    def _override_query(self, setting: str) -> str:
        value = self._overrides[setting]
        return f"SET {setting}={value}" if setting == "threads" else f"SET {setting}='{value}'"

    def execute(self, query, *args, **kwargs):
        match = _DUCKDB_SETTING_RE.match(query) if isinstance(query, str) else None
        if match and match.group(2).lower() in self._overrides:
            query = self._override_query(match.group(2).lower())
            logger.info(f"DuckDB override: {query}")
        return self._conn.execute(query, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)


@contextlib.contextmanager
def _duckdb_resource_overrides():
    overrides = {
        setting: os.environ[env]
        for setting, env in _DUCKDB_ENV_OVERRIDES.items()
        if os.environ.get(env)
    }
    if not overrides:
        yield
        return

    real_connect = duckdb.connect

    def connect(*args, **kwargs):
        conn = _DuckDBConnectionOverride(real_connect(*args, **kwargs), overrides)
        # Apply up front too, in case deeplogbot stops setting them itself
        conn.apply_overrides()
        return conn

    with mock.patch.object(duckdb, "connect", connect):
        yield


class BotClassifier:
    """Wraps DeepLogBot to classify download traffic in parquet files."""

    def __init__(
        self,
        method: str = "rules",
        contamination: float = 0.15,
        provider: str = "ebi",
    ) -> None:
        self.method = method
        self.contamination = contamination
        self.provider = provider

    def classify(
        self,
        input_parquet: str,
        output_dir: str,
        output_parquet: str,
    ) -> dict:
        """
        Run bot classification on a merged parquet file.

        Args:
            input_parquet: Path to the merged parquet file.
            output_dir: Directory for classification reports and outputs.
            output_parquet: Path for the annotated parquet file.

        Returns:
            dict with classification statistics.

        Raises:
            BotClassificationError: If classification fails.
        """
        if not os.path.exists(input_parquet):
            raise BotClassificationError(
                f"Input parquet file not found: {input_parquet}",
                input_path=input_parquet,
                method=self.method,
            )

        os.makedirs(output_dir, exist_ok=True)

        try:
            logger.info(
                "Starting bot classification",
                extra={
                    "input_parquet": input_parquet,
                    "method": self.method,
                    "contamination": self.contamination,
                    "provider": self.provider,
                },
            )

            with _duckdb_resource_overrides():
                result_stats = run_bot_annotator(
                    input_parquet=input_parquet,
                    output_dir=output_dir,
                    output_parquet=output_parquet,
                    classification_method=self.method,
                    contamination=self.contamination,
                    output_strategy="new_file",
                    provider=self.provider,
                )

            logger.info(
                "Bot classification completed",
                extra={
                    "output_parquet": output_parquet,
                    "result_stats": str(result_stats),
                },
            )

            return result_stats

        except Exception as e:
            error = BotClassificationError(
                f"Bot classification failed: {str(e)}",
                input_path=input_parquet,
                method=self.method,
                original_error=str(e),
            )
            logger.error(
                "Bot classification failed",
                extra={"input_parquet": input_parquet, "error": str(e)},
                exc_info=True,
            )
            raise error
