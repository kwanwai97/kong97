from backend.api.main import app
import uvicorn

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "5678"))
    uvicorn.run(app, host="0.0.0.0", port=port)
