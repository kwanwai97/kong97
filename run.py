#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
from backend.api.main import app
import os
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5678")), log_level="info")
