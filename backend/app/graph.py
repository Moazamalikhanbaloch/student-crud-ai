import os
from typing import TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.db import db_create_student, db_get_students, db_update_student, db_delete_student

# Initialize Gemini Flash (fast, reliable, and available on free tier)
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# 1. State Definition
class AgentState(TypedDict):
    user_query: str
    operation: Optional[str]        # CREATE, READ, UPDATE, DELETE, UNKNOWN
    name: Optional[str]
    roll_number: Optional[str]
    tech_info: Optional[str]
    is_complete: bool
    missing_fields: Optional[str]
    response: Optional[str]

# --- Node 1: Classifier ---
class ClassificationResult(BaseModel):
    operation: str = Field(description="Must be CREATE, READ, UPDATE, DELETE, or UNKNOWN")

classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify the user prompt into one CRUD operation: CREATE, READ, UPDATE, or DELETE. If unrelated, return UNKNOWN."),
    ("human", "{query}")
])

def classify_node(state: AgentState):
    chain = classifier_prompt | llm.with_structured_output(ClassificationResult)
    result = chain.invoke({"query": state["user_query"]})
    return {"operation": result.operation.upper()}

# --- Node 2: Field Validator & Extractor ---
class ValidationResult(BaseModel):
    name: Optional[str] = Field(default=None)
    roll_number: Optional[str] = Field(default=None)
    tech_info: Optional[str] = Field(default=None)
    is_complete: bool = Field(description="True if all necessary fields for this operation are present, False otherwise")
    missing_fields: Optional[str] = Field(default=None, description="Explanation or names of missing fields if incomplete")

validator_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an extractor and validator for a student database.
Required rules:
- CREATE requires all three: name, roll_number, and tech_info (e.g., 'Web dev', 'App dev').
- READ can take an optional roll_number or fetch all records (is_complete is always True for READ).
- UPDATE requires: roll_number, plus at least one of (name or tech_info).
- DELETE requires: roll_number.

Extract the fields. If any required field is missing for the operation, mark is_complete=False and list the missing fields."""),
    ("human", "Operation: {operation}\nUser Query: {query}")
])

def validate_node(state: AgentState):
    chain = validator_prompt | llm.with_structured_output(ValidationResult)
    res = chain.invoke({"operation": state["operation"], "query": state["user_query"]})
    return {
        "name": res.name,
        "roll_number": str(res.roll_number) if res.roll_number else None,
        "tech_info": res.tech_info,
        "is_complete": res.is_complete,
        "missing_fields": res.missing_fields
    }

# --- Node 3: Execution Node ---
def execute_node(state: AgentState):
    op = state["operation"]
    try:
        if op == "CREATE":
            data = db_create_student(state["name"], state["roll_number"], state["tech_info"])
            return {"response": f"Successfully created record: {data}"}
        elif op == "READ":
            data = db_get_students(state["roll_number"])
            return {"response": f"Records retrieved: {data}"}
        elif op == "UPDATE":
            data = db_update_student(state["roll_number"], state["name"], state["tech_info"])
            return {"response": f"Successfully updated record: {data}"}
        elif op == "DELETE":
            data = db_delete_student(state["roll_number"])
            return {"response": f"Successfully deleted record with roll number: {state['roll_number']}"}
        else:
            return {"response": "Could not identify an action to perform."}
    except Exception as e:
        return {"response": f"Database error: {str(e)}"}

def incomplete_node(state: AgentState):
    return {"response": f"Request incomplete. Missing information: {state['missing_fields']}"}

# --- Router ---
def route_validation(state: AgentState):
    if state["is_complete"]:
        return "execute"
    return "ask_missing"

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("classifier", classify_node)
builder.add_node("validator", validate_node)
builder.add_node("execute", execute_node)
builder.add_node("ask_missing", incomplete_node)

builder.set_entry_point("classifier")
builder.add_edge("classifier", "validator")
builder.add_conditional_edges("validator", route_validation, {
    "execute": "execute",
    "ask_missing": "ask_missing"
})
builder.add_edge("execute", END)
builder.add_edge("ask_missing", END)

crud_app = builder.compile()