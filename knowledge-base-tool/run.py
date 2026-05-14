import subprocess
import sys
import threading
import time
import os

from app.database import init_db


def run_api():
    os.environ.setdefault("KNOWLEDGE_DB_PATH", "knowledge.db")
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


def run_ui():
    import gradio as gr
    from app.ui import create_app
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)


def main():
    init_db()
    print("Database initialized")

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    print("Starting API server on http://0.0.0.0:8000")
    time.sleep(2)

    print("Starting Web UI on http://0.0.0.0:7860")
    run_ui()


if __name__ == "__main__":
    main()
