import logging

import uvicorn

from taximetr.settings import settings

# ========== КОНФИГУРАЦИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    uvicorn.run('taximetr.app:app',
                host=settings.server_host,
                port=settings.server_port,
                reload=True,
                log_level="debug")

if __name__ == "__main__":
    main()