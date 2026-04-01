"""
Bot classification module using DeepLogBot.

Classifies download traffic into three categories:
- Bots: Automated scrapers and coordinated botnets
- Hubs: Legitimate institutional bulk downloaders (research facilities, mirrors)
- Organic users: Independent individual researchers
"""
import logging
import os

from deeplogbot import run_bot_annotator

from exceptions import BotClassificationError

logger = logging.getLogger(__name__)


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
