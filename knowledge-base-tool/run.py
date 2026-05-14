import os
import uvicorn

os.environ.setdefault("KNOWLEDGE_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge.db"))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, timeout_keep_alive=30, log_level="info")
