import sys
from pathlib import Path

SCRAPER = Path(__file__).resolve().parents[1]
ROOT = SCRAPER.parent
sys.path.insert(0, str(SCRAPER))
sys.path.insert(0, str(ROOT / "shared-config"))
