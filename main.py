from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.agent import AutalicAgent
import json # Added missing import for json

app = FastAPI()

# --- App Setup ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
agent = AutalicAgent() # Create a single, long-lived agent instance
chat_history = [] # In-memory chat history (will reset on server restart)

class ChatRequest(BaseModel):
    message: str

# --- API Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat", response_class=JSONResponse)
async def chat(chat_request: ChatRequest):
    global chat_history
    
    try:
        # Add user message to history
        chat_history.append({"role": "user", "content": chat_request.message})
        
        # Run the agent with the full history
        response_content = agent.run(chat_history)
        
        # Add bot response to history
        chat_history.append({"role": "assistant", "content": response_content})

        # The agent can return a JSON string (for analysis) or a plain text string (for conversation)
        try:
            # Try to parse as JSON for analysis results
            json_response = json.loads(response_content)
            return JSONResponse(content={"type": "analysis", "data": json_response})
        except (json.JSONDecodeError, TypeError):
            # If it's not JSON, it's a conversational response
            return JSONResponse(content={"type": "conversation", "data": response_content})

    except Exception as e:
        print(f"--- SERVER ERROR --- \n{e}")
        return JSONResponse(status_code=500, content={"error": "An internal error occurred."})

@app.post("/reset")
async def reset_chat():
    global chat_history
    chat_history = []
    return JSONResponse(content={"message": "Chat history has been reset."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 