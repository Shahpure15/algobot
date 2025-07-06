# src/api/health.py
from fastapi import FastAPI
from datetime import datetime
import uvicorn
import threading
import time

app = FastAPI()

class HealthServer:
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.start_time = datetime.now()
        
    def start_server(self):
        """Start health check server in background"""
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": str(datetime.now() - health_server.start_time) if 'health_server' in globals() else "unknown"
    }

@app.get("/status")
async def bot_status():
    """Bot status endpoint"""
    if 'health_server' in globals() and health_server.bot:
        return health_server.bot.get_status()
    return {"status": "bot not available"}

# Global health server instance
health_server = HealthServer()
