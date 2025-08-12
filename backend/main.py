# Step1: Setup FastAPI backend
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from ai_agent import graph, SYSTEM_PROMPT, parse_response

app = FastAPI()

# Step2: Receive and validate request from Frontend
class Query(BaseModel):
    message: str



@app.post("/ask")
async def ask(query: Query):
    try:
        inputs = {"messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query.message}
        ]}
        stream = graph.stream(inputs, stream_mode="updates")
        tool_called_name, final_response = parse_response(stream)
        return {"response": final_response,
                "tool_called": tool_called_name}
    except Exception as e:
        print(f"Error in /ask endpoint: {e}")
        return {"response": "I'm having trouble connecting. Please try again shortly.",
                "tool_called": None}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)







