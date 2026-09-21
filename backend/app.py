from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

app = FastAPI()


# ==============================
# CORS
# ==============================

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================
# REQUEST FORMAT
# ==============================

class ChatRequest(BaseModel):
    question: str


# ==============================
# GEMINI CLIENT
# ==============================

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found!")

client = genai.Client(api_key=api_key)


# ==============================
# QDRANT CLIENT
# ==============================

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("Qdrant environment variables not found!")

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=120
)

COLLECTION_NAME = "ai_teaching_assistant"


# ==============================
# QUERY EMBEDDING
# ==============================

def create_query_embedding(question):

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768
        )
    )

    if hasattr(result, "embeddings") and result.embeddings:
        return result.embeddings[0].values

    return result.embedding.values


# ==============================
# GEMINI RESPONSE
# ==============================

def generate_response(prompt):

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print("Gemini error:", e)

        return "Sorry! Gemini is temporarily unavailable."


# ==============================
# QDRANT RETRIEVAL
# ==============================

def search_qdrant(question_embedding, limit=5):

    search_result = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=limit,
        with_payload=True
    )

    return search_result.points


# ==============================
# CHAT HISTORY
# ==============================

chat_history = []


# ==============================
# HOME
# ==============================

@app.get("/")
def home():

    return {
        "message": "AI Teaching Assistant is running"
    }


# ==============================
# CHAT
# ==============================

@app.post("/chat")
def chat(request: ChatRequest):

    question = request.question


    # ==============================
    # QUESTION EMBEDDING
    # ==============================

    question_embedding = create_query_embedding(question)


    # ==============================
    # QDRANT SEARCH
    # ==============================

    results = search_qdrant(
        question_embedding,
        limit=5
    )


    # ==============================
    # COURSE MATERIAL
    # ==============================

    course_chunks = []

    for result in results:

        payload = result.payload

        course_chunks.append(
            f"""
Video: {payload["video_title"]}
Timestamp: {payload["start"]} - {payload["end"]}

Content:
{payload["text"]}
"""
        )

    course_material = "\n\n".join(course_chunks)


    # ==============================
    # HISTORY
    # ==============================

    history_text = ""

    for previous_chat in chat_history:

        history_text += f"""
Student: {previous_chat["question"]}
Assistant: {previous_chat["answer"]}
"""


    # ==============================
    # PROMPT
    # ==============================

    prompt = f"""
You are an AI Teaching Assistant for a Computer Networks course.

Your job is to answer the student's question using ONLY the
provided course material.

========================
STRICT KNOWLEDGE RULES
========================

1. The provided course material is your ONLY factual source.

2. Do NOT use your pretrained knowledge, general knowledge,
or outside information.

3. Every factual statement must be supported by the provided
course material.

4. You may simplify explanations, rephrase sentences,
summarize, or organize information.

5. Do NOT invent facts, examples, definitions, or technical details.

6. If the material doesn't contain enough information, respond exactly:

"I could not find enough information about this topic in the provided course material."

7. Conversation history may ONLY be used to understand references
like "it", "this", or "that".

========================
PREVIOUS CONVERSATION
========================

{history_text}

========================
CURRENT COURSE MATERIAL
========================

{course_material}

========================
CURRENT QUESTION
========================

{question}

========================
FINAL INSTRUCTION
========================

Answer the student's question using ONLY the provided course material
in clean Markdown.
"""


    # ==============================
    # GENERATE ANSWER
    # ==============================

    answer = generate_response(prompt)


    # ==============================
    # SAVE HISTORY
    # ==============================

    chat_history.append({
        "question": question,
        "answer": answer
    })


    # ==============================
    # RESPONSE
    # ==============================

    return {
        "answer": answer,
        "sources": [
            {
                "video_title": result.payload["video_title"],
                "video_id": result.payload["video_id"],
                "start": result.payload["start"],
                "end": result.payload["end"],
                "chunk_id": result.payload["chunk_id"]
            }
            for result in results
        ]
    }