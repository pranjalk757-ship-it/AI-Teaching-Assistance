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
    api_key = os.getenv("GOOGLE_API_KEY")
)
def get_response(prompt):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    print(response)
    return response.text

embedding_folder = os.listdir("merge_embeddings")
all_data = []
for embed_file in embedding_folder:
    with open(f"merge_embeddings/{embed_file}","r") as f:
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
# print(new_df[["chunk_id","text","embedding"]])

# prompt = f'''
# I'm teaching computer networks in this course.Here are video subtitle chunks containing video title,video id,start time in seconds,end time in seconds,the text at that time:

# {new_df[["video_id","video_title","start","end","chunk_id","text"]]}
# ----------------------------------------------
# {question}
# User asked this question related to video chunks,you have to answer where and how much content is taught in which video(in which video and at what timestamp) and guide the user to go to that particular video.If users asked unrelated questions tell him\her that you can answer question related to this course
# '''

context = "\n\n".join(new_df["text"].tolist())
prompt = f"""
You are an AI Teaching Assistant for a Computer Networks course.

Your job is to teach the student using ONLY the course material
provided below.

========================
STRICT KNOWLEDGE RULE
========================

1. The provided course material is your ONLY source of truth.

2. DO NOT use your pretrained knowledge, general knowledge,
   internet knowledge, or information from outside the provided
   course material.

3. Every factual statement in your answer must be supported by
   the provided course material.

4. You MAY:
   - explain concepts in simpler language
   - rephrase sentences
   - summarize the material
   - organize information into bullet points
   - explain the relationship between information explicitly
     present in the material

5. You MUST NOT:
   - invent facts
   - add definitions that are not in the material
   - add examples that are not in the material
   - add advantages or disadvantages that are not in the material
   - add formulas that are not in the material
   - add assumptions from your own knowledge
   - correct or replace the teacher's explanation using outside knowledge

========================
WHEN INFORMATION IS MISSING
========================

If the course material does not contain enough information to
answer the student's question, DO NOT guess.

Respond exactly:

"I could not find enough information about this topic in the
provided course material."

If only part of the question can be answered, answer ONLY the
part supported by the course material and clearly state that the
remaining information was not found.

========================
CONVERSATION CONTEXT
========================

The student may ask follow-up questions such as:

"what about its advantages?"
"why is it used?"
"explain that again"
"what is the difference?"
"give an example"

Use the conversation history only to understand what the student
is referring to.

IMPORTANT:
Conversation history is NOT a knowledge source.

For factual information, you must still rely ONLY on the retrieved
course material.

========================
ANSWER STYLE
========================

Teach like a good Computer Networks professor.

- Use simple and clear language.
- Start with the direct answer.
- Explain step by step when appropriate.
- Use headings and bullet points when useful.
- Avoid unnecessary complexity.
- Do not make the answer unnecessarily long.
- If a technical term is important, explain it simply.
- Do not repeat the same information unnecessarily.

If the student asks for:
- "short answer" → keep it short.
- "explain" → give a clear explanation.
- "difference" → use a comparison/table if supported by the material.
- "advantages/disadvantages" → mention ONLY those present in the material.
- "example" → provide an example ONLY if one exists in the material.
- "exam answer" → structure it clearly for exam writing, but do not
  add information that is not present in the course material.

========================
SOURCE AND TIMESTAMP RULE
========================

The retrieved chunks contain metadata such as:

- video_id
- video_title
- start
- end
- text

Do NOT invent, change, calculate, or modify these values.

Do NOT create a Sources section yourself.

The application will generate the sources and timestamps separately.

========================
COURSE MATERIAL
========================

{context}

========================
STUDENT QUESTION
========================

{question}

========================
FINAL INSTRUCTION
========================

Answer the student's question using ONLY the course material above.

Before answering, internally check:

1. Is the answer supported by the retrieved material?
2. Am I accidentally using outside knowledge?
3. Did I add any fact, example, definition, or explanation that
   is not supported by the material?

If the answer is not sufficiently supported, use the required
"I could not find enough information..." response instead.

Now answer the student.
"""
with open("prompt.txt",'w') as f:
    f.write(prompt)

response = get_response(prompt)
with open("response.txt","w")as f:
    f.write(response)
# for index,item in new_df.iterrows():
#     print(index,item["video_id"],item["video_title"],item["start"],item["end"],item["chunk_id"],item["text"])