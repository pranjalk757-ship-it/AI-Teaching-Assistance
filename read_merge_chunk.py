import requests
import json
import os
def create_embeddings(text_list):
    r = requests.post("http://localhost:11434/api/embed",json={
        "model":"bge-m3",
        "input":text_list
    })
    r.raise_for_status()
    embedding = r.json()["embeddings"]
    return embedding

jsons = os.listdir("merge_Transcripts")
os.makedirs("merge_embeddings",exist_ok=True)
chunk_id = 0

for json_file in jsons:
    my_dict = []
    with open(f"merge_Transcripts/{json_file}","r") as f:
        content = json.load(f)
    print(f"Creating embedding for {json_file}")
    # print(content)
    video_title = content["video_title"]
    video_id = content["video_id"]
    embeddings = create_embeddings([c["text"] for c in content["chunks"]])
    for i,chunk_el in enumerate(content["chunks"]):
        chunk_el["chunk_id"] = chunk_id
        chunk_el["video_title"] = video_title
        chunk_el["video_id"] = video_id
        chunk_el["embedding"] = embeddings[i]
        chunk_id += 1
        my_dict.append(chunk_el)
    print(f"Writing embedding in {json_file}")
    with open(f"merge_embeddings/{json_file}","w") as f:
        json.dump(my_dict,f,indent=4)
    
