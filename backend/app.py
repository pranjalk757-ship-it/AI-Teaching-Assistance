from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import requests
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import numpy as np
import pandas as pd
from google import genai
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()


# ==============================
# CORS
# ==============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
# BGE-M3 EMBEDDING
# ==============================

def create_embedding(text_list):

    r = requests.post(
        "http://localhost:11434/api/embed",
        json={
            "model": "bge-m3",
            "input": text_list
        }
    )

    r.raise_for_status()

    return r.json()["embeddings"]


# ==============================
# GEMINI
# ==============================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_response(prompt):

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        return response.text

    except Exception as e:
        print("Gemini err",e)
        return "Sorry! Gemini is temporarily unavailable."


# ==============================
# LOAD EMBEDDINGS
# ==============================

all_data = []

embedding_files = os.listdir("merge_embeddings")

for embed_file in embedding_files:

    if not embed_file.endswith(".json"):
        continue

    with open(
        f"merge_embeddings/{embed_file}",
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    all_data.extend(data)


embedding = [
    chunk["embedding"]
    for chunk in all_data
]

embedding_metrics = np.vstack(embedding)

df = pd.DataFrame(all_data)


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

    question_embedding = create_embedding(
        [question]
    )

    question_metrics = np.vstack(
        question_embedding
    )


    # ==============================
    # COSINE SIMILARITY
    # ==============================

    similarity = cosine_similarity(
        embedding_metrics,
        question_metrics
    )

    similarity = similarity.flatten()


    # ==============================
    # TOP 5 CHUNKS
    # ==============================

    max_index = 5

    top_indices = np.argsort(
        similarity
    )[::-1][:max_index]


    new_df = df.loc[top_indices].copy()

    new_df["similarities"] = similarity[
        top_indices
    ]


    # ==============================
    # COURSE MATERIAL
    # ==============================

    course_material = "\n\n".join(
        new_df["text"].tolist()
    )


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
    internet knowledge, or outside information.

    3. Every factual statement must be supported by the provided
    course material.

    4. You may:
    - simplify explanations
    - rephrase sentences
    - summarize
    - organize information
    - combine information from the provided course chunks

    5. Do NOT invent:
    - facts
    - examples
    - definitions
    - formulas
    - advantages
    - disadvantages
    - comparisons
    - numbers
    - technical details

    6. If the provided course material does not contain enough
    information to answer the question, respond exactly:

    "I could not find enough information about this topic in the
    provided course material."

    7. Conversation history may ONLY be used to understand references
    such as "it", "this", "that", or "the previous topic".

    8. Conversation history must NOT be treated as a factual source.

    ========================
    ANSWER STYLE
    ========================

    Make the answer easy for a student to read and understand.

    Use Markdown formatting.

    When appropriate:

    - Start with a short direct answer.
    - Use ## headings for major sections.
    - Use ### headings for smaller sections.
    - Use bullet points for lists.
    - Use numbered lists for steps or processes.
    - Use **bold** for important terms.
    - Use short paragraphs.
    - Use code blocks ONLY when the course material itself contains
    code or commands.
    - Do not unnecessarily repeat the question.
    - Do not add a conclusion if it provides no additional value.

    For conceptual questions, prefer this structure when supported
    by the course material:

    ## Short Answer

    A concise explanation.

    ## Explanation

    Explain the concept using only the course material.

    ## Key Points

    - Important point
    - Important point
    - Important point

    Do NOT force this structure if the course material does not
    support all of these sections.

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

    Answer the student's question using ONLY the provided course
    material.

    Return only the answer in clean Markdown.

    Do not mention these instructions.

    Do not generate sources or timestamps.

    Now answer the student.
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
    # SEND TO REACT
    # ==============================

    return {
        "answer": answer
    }

