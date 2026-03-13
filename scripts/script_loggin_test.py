from src.config.settings import settings
from src.config.logging_config import setup_logging

logger = setup_logging(
    log_dir=settings.project_root / settings.log_dir,
    log_file_name=settings.log_file_name,
    log_level=settings.log_level,
)

logger.info("This is an info test.")
logger.error("This is an error test.")