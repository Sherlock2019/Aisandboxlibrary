from fastapi import FastAPI, Request
import yaml
import httpx

app = FastAPI(title="AI Agent Hub")
registry = {}

@app.on_event("startup")
async def load_registry() -> None:
    global registry
    try:
        with open("agent_registry.yaml", "r", encoding="utf-8") as f:
            registry.update(yaml.safe_load(f) or {})
    except FileNotFoundError:
        registry.clear()

@app.get("/health")
async def health() -> dict:
    return {"status": "hub ok"}

@app.post("/run/{agent_name}")
async def run_agent(agent_name: str, request: Request) -> dict:
    if agent_name not in registry.get("agents", {}):
        return {"error": f"Unknown agent: {agent_name}"}
    payload = await request.json()
    agent_cfg = registry["agents"][agent_name]
    url = agent_cfg["url"].rstrip("/") + "/run"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()
