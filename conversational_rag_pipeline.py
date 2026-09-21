import requests
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import numpy as np
import pandas as pd
from google import genai
def create_embedding(text_list):
    r = requests.post("http://localhost:11434/api/embed",json={
        "model":"bge-m3",
        "input":text_list
    })
    r.raise_for_status()
    embedding = r.json()["embeddings"]
    return embedding

client = genai.Client(
    api_key = os.getenv("GOOGLE_API_KEY")
)

def generate_response(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Sorry ! Gemini is temporary unavailable Please Try again with another model \n Error : {e}"

all_data = []
embeddings = os.listdir("merge_embeddings")
for embed_file in embeddings:
    with open(f"merge_embeddings/{embed_file}","r") as f:
        data = json.load(f)
    all_data.extend(data)

embedding = [chunk["embedding"] for chunk in all_data]
embedding_metrics = np.vstack(embedding)


chat_history = []
df = pd.DataFrame(all_data)

while True:
    question = input("You : ")
    if question.lower() == "exit":
        break
    
    question_embedding = create_embedding(question)
    question_metrics = np.vstack(question_embedding)

    similarity = cosine_similarity(embedding_metrics,question_metrics)
    similarity = similarity.flatten()
    max_index = 5
    top_indices = np.argsort(similarity)[::-1][0:max_index]
    new_df = df.loc[top_indices].copy()
    new_df["similarities"] = similarity[top_indices]

    course_material = "\n\n".join(
        new_df["text"].to_list()
    )

    history_text = ""

    for chat in chat_history:
        history_text += f"""
            Student:{chat["question"]},
            Assistant:{chat["answer"]}
        """
    
    prompt = f"""
    You are an AI Teaching Assistant for a Computer Networks course.

    Your job is to teach the student using ONLY the provided course
    material.

    ========================
    STRICT RULES
    ========================

    1. The course material is your ONLY source of factual information.

    2. Do NOT use pretrained knowledge, general knowledge, internet
    knowledge, or information from outside the provided course material.

    3. Every factual statement in your answer must be supported by the
    provided course material.

    4. You may simplify, rephrase, summarize, and organize information
    from the course material.

    5. Do NOT invent facts, examples, definitions, formulas, advantages,
    disadvantages, or explanations.

    6. If the course material does not contain enough information to
    answer the question, say:

    "I could not find enough information about this topic in the
    provided course material."

    7. Use conversation history ONLY to understand what the student is
    referring to.

    8. Conversation history is NOT a factual knowledge source.

    9. Answer the current question directly and clearly.

    10. Do not generate sources or timestamps.

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

    Answer the current question using ONLY the current course material.

    Now answer the student.
    """
    answer = generate_response(prompt)
    print("\nAssistant : ",answer)

    chat_history.append({
        "question":question,
        "answer":answer
    })