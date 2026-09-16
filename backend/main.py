from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from simulator_bridge import bridge

from ai_engine.router import router as ai_router

class FaultRequest(BaseModel):
    machine_id: str = "M03"
    fault_type: str = "DISRUPTION_01_COOLING_SYSTEM_DEGRADATION"
    severity: str = "critical"

class RecoveryExecuteRequest(BaseModel):
    machine_id: str
    action_id: str

class RecoveryExecuteResult(BaseModel):
    machine_id: str
    action_id: str
    execution_status: str
    previous_state: str
    resulting_state: str
    timestamp: str
    message: str
    state_changed: bool

app = FastAPI(title="CAUSEN AI Backend API")
app.include_router(ai_router)

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://causen-beta.vercel.app",
        "https://causen-h36s.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background task loop
async def simulation_loop():
    while True:
        bridge.tick()
        await asyncio.sleep(1) # 1 tick per second

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

@app.get("/api/state")
def get_state():
    return bridge.get_frontend_state()

@app.post("/api/fault/inject")
def inject_fault(request: FaultRequest = None):
    if request:
        bridge.inject_fault(machine_id=request.machine_id, fault_type=request.fault_type, severity=request.severity)
    else:
        bridge.inject_fault()
    return {"status": "success", "message": "Fault injection initiated"}

@app.post("/api/fault/reset")
def reset_fault():
    bridge.reset()
    return {"status": "success", "message": "Simulator reset to baseline"}

@app.post("/api/recovery/execute", response_model=RecoveryExecuteResult)
def execute_recovery(request: RecoveryExecuteRequest):
    result = bridge.execute_recovery(request.machine_id, request.action_id)
    return result

class ApprovalPendingRequest(BaseModel):
    machine_id: str
    approval_url: str
    rejection_url: str
    severity: str
    recommended_action: str
    reason: str
    confidence: float

@app.post("/api/approval/pending")
def set_pending_approval(request: ApprovalPendingRequest):
    bridge.pending_approval = request.dict()
    return {"status": "success"}

class ApprovalResolveRequest(BaseModel):
    machine_id: str
    action: str

import requests

@app.post("/api/approval/resolve")
def resolve_approval(request: ApprovalResolveRequest):
    if not bridge.pending_approval or bridge.pending_approval["machine_id"] != request.machine_id:
        return {"status": "error", "message": "No pending approval found for this machine."}
    
    url = bridge.pending_approval["approval_url"] if request.action == "approved" else bridge.pending_approval["rejection_url"]
    
    try:
        # Trigger the n8n Wait node via HTTP GET
        requests.get(url, timeout=5)
    except Exception as e:
        print(f"Failed to trigger n8n resume url: {e}")
        # Even if it times out (n8n might take time), we assume it triggered.

    # Clear pending approval
    bridge.pending_approval = None
    return {"status": "success"}

@app.get("/api/vapi/token")
def get_vapi_token():
    # Web SDK requires the Public Key, not the Private API Key
    vapi_key = os.getenv("VAPI_API_KEY")
    assistant_id = os.getenv("VAPI_ASSISTANT_ID")
    
    if not vapi_key or not assistant_id:
        return {"status": "error", "message": "VAPI environment variables are not configured."}
    
    # We will pass the key securely at runtime to the frontend 
    # to avoid hardcoding it in the React bundle.
    return {
        "status": "success",
        "assistant_id": assistant_id,
        "vapi_response": {
            "token": vapi_key
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
