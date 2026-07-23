#!/usr/bin/env python3
from backend.api.main import app
import uvicorn, os
uvicorn.run(app, host="127.0.0.1", port=5678)
