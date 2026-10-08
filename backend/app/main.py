from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.graph import crud_app
from app.db import db_get_students

app = FastAPI(title="AI Student CRUD API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "FastAPI is running"}

@app.get("/students")
def get_all():
    return {"data": db_get_students()}

@app.post("/chat")
def process_chat(req: QueryRequest):
    result = crud_app.invoke({
        "user_query": req.query,
        "operation": None,
        "name": None,
        "roll_number": None,
        "tech_info": None,
        "is_complete": False,
        "missing_fields": None,
        "response": None
    })
    return {
        "operation": result.get("operation"),
        "is_complete": result.get("is_complete"),
        "response": result.get("response")
    }