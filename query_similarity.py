import os
from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np
import pandas as pd
import requests
from google import genai
def create_embedding(text):
    r = requests.post("http://localhost:11434/api/embed",
                json={
                    "model":"bge-m3",
                    "input":text
                }
    )
    embedding = r.json()['embeddings']
    return embedding

#  Using Local LLM for generating response 

# def get_response(prompt):
#     r = requests.post("http://localhost:11434/api/generate",
#                 json={
#                     "model":"llama3.2:3b",
#                     "prompt":prompt,
#                     "stream":False
#     })
#     r.raise_for_status()
#     response = r.json()
#     print(response)
#     return response


# Using Gemini  as LLM for generating response
client = genai.Client(
    api_key="REMOVED_SECRET"
    # api_key = os.getenv("GOOGLE_API_KEY")
)
def get_response(prompt):
    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt
    )
    print(response)
    return response.text

embedding_folder = os.listdir("embeddings")
all_data = []
for embed_file in embedding_folder:
    with open(f"embeddings/{embed_file}","r") as f:
        data = json.load(f)
    all_data.extend(data)


embedding = [chunk["embedding"] for chunk in all_data]
embedding_metrics = np.vstack(embedding)


question = input("Ask your question : ")
question_embedding = create_embedding(question)
question_metrics = np.vstack(question_embedding)
# question_shape = question_metrics.shape
# print("q metric",question_metrics)
# print("shape",question_shape)

similarity = cosine_similarity(embedding_metrics,question_metrics)
similarity = similarity.flatten()
max_index = 5
top_indices = np.argsort(similarity)[::-1][0:max_index]
df = pd.DataFrame(all_data)
new_df = df.loc[top_indices].copy()
new_df["similarities"] = similarity[top_indices]


prompt = f"""
You are an AI Teaching Assistant for this Computer Networks course.

IMPORTANT:
Answer ONLY using the provided course transcript chunks.
Do NOT use outside knowledge.

You can:
- explain the retrieved content
- simplify the teacher's explanation
- summarize the teacher's explanation

Do NOT invent information that is not present in the
provided course material.

The student question is:

{question}

The retrieved course chunks are:

{new_df[["video_id","video_title","start","end","chunk_id","text"]].to_string(index=False)}

Instructions:

1. If the student asks a conceptual question such as
   "What is mesh topology?", "Why is it expensive?",
   or "Explain mesh topology", explain the concept using
   the retrieved course content.

2. If the student asks where a topic is taught, identify
   the relevant video and timestamp.

3. If the retrieved content is insufficient, say:
   "I could not find enough information about this topic
   in the provided course material."

4. Never treat chunk_id as video_id.

5. Do not calculate or modify timestamps.
   Use the timestamps exactly as provided.

6. Do not invent video titles or video IDs.

7. For conceptual questions, provide the explanation first,
   followed by the source video title and timestamp.
"""
with open("prompt.txt",'w') as f:
    f.write(prompt)

response = get_response(prompt)
with open("response.txt","w")as f:
    f.write(response)
# for index,item in new_df.iterrows():
#     print(index,item["video_id"],item["video_title"],item["start"],item["end"],item["chunk_id"],item["text"])