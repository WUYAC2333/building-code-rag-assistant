from fastapi import FastAPI
from pydantic import BaseModel
from rag import qa_chain

app = FastAPI(title="Building Code RAG API")

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    answer: str
    references: list

@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    answer, docs = qa_chain(request.question)

    return {
        "answer": answer,
        "references": docs
    }