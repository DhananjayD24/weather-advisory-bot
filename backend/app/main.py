from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.graph.graph import graph


app = FastAPI(
    title="Weather Advisory Support Bot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    response: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    config = {
        "configurable": {
            "thread_id": request.session_id,
        }
    }

    try:
        result = await graph.ainvoke(
            {
                "current_query": request.message,
            },
            config=config,
        )

        response = result.get("response")

        if not response:
            raise HTTPException(
                status_code=500,
                detail="The agent did not produce a response.",
            )

        return ChatResponse(
            session_id=request.session_id,
            response=response,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process the request: {str(exc)}",
        )