import os
import sys
import logging
import argparse
from alembic.config import Config
from alembic import command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations(direction: str = "upgrade") -> None:
    """Run database migrations.
    
    Args:
        direction: Either "upgrade" or "downgrade"
    """
    try:
        # Get the directory containing this script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Get the project root directory (one level up)
        project_root = os.path.dirname(current_dir)
        
        # Create Alembic configuration
        alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))
        
        if direction == "upgrade":
            logger.info("Running database migrations (upgrade)...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully!")
        elif direction == "downgrade":
            logger.info("Running database migrations (downgrade)...")
            command.downgrade(alembic_cfg, "base")
            logger.info("Database downgrade completed successfully!")
        else:
            raise ValueError(f"Invalid direction: {direction}")
            
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--direction",
        type=str,
        choices=["upgrade", "downgrade"],
        default="upgrade",
        help="Direction of migration (upgrade or downgrade)",
    )
    args = parser.parse_args()
    run_migrations(args.direction)
