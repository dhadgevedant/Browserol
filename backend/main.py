from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent import AgentExecutor
from backend.browser_controller import BrowserController
from backend.llm_interface import OllamaLLM
from backend.utils import init_logger, save_log
from backend.vision_module import VisionModule

app = FastAPI(
    title="Local AI Browser Agent",
    description="A local browser automation agent powered by Ollama and Playwright.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

browser_controller = BrowserController(headless=False)
llm = OllamaLLM()
vision = VisionModule()
agent = AgentExecutor(browser_controller=browser_controller, llm=llm, vision=vision)


class TaskRequest(BaseModel):
    instruction: str


@app.on_event("startup")
async def on_startup():
    init_logger()
    save_log("Starting Local AI Browser Agent")
    await browser_controller.start()
    save_log("Browser controller started")


@app.on_event("shutdown")
async def on_shutdown():
    save_log("Shutting down Local AI Browser Agent")
    await browser_controller.close()


@app.post("/run-task")
async def run_task(request: TaskRequest):
    instruction = request.instruction.strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")

    save_log(f"Received instruction: {instruction}")
    result = await agent.run_instruction(instruction)
    return result


@app.get("/history")
async def get_history():
    return {"history": agent.history}


@app.get("/status")
async def get_status():
    return {"status": "running", "history_count": len(agent.history)}
