"""Launch the Freshroots app: API plus the built web UI at http://127.0.0.1:8000"""
import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    if not (ROOT / "web" / "dist" / "index.html").exists():
        print("web/dist is missing. Build the UI first:  cd web && npm install && npm run build")
    port = int(os.environ.get("FRESHROOTS_PORT", "8000"))
    uvicorn.run("freshroots.api:app", host="127.0.0.1", port=port, log_level="info")
