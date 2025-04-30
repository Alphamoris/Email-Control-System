

import uvicorn
import argparse
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True) -> None:
    """Run the development server with hot reload. There is a differnece"""
    try:
        logger.info(f"Starting development server at http://{host}:{port}")
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            reload_dirs=["app"],
            log_level="info",
            workers=1,
            limit_concurrency=settings.MAX_CONNECTIONS_COUNT,
            limit_max_requests=settings.MAX_CONNECTIONS_COUNT * 1000,
        )
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise e

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run development server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    
    args = parser.parse_args()
    run_server(args.host, args.port, not args.no_reload)
