import json
import os
import math

jsons = os.listdir("transcripts")
n = 5
for file_name in jsons:
    if file_name.endswith(".json"):
        file_path = os.path.join("transcripts",file_name)
        with open(file_path,'r',encoding="utf-8") as f:
            data = json.load(f)
            new_chunks = []
            num_chunks = len(data["chunk"])
            num_group = math.ceil(num_chunks/n)
            video_id = data["video_id"]
            video_title = data["video_name"]
            for i in range(num_group):
                start_index = i*n
                end_index = min((i+1)*n,num_chunks)
                chunk_group = data["chunk"][start_index:end_index]

                new_chunks.append({
                    "video_id":video_id,
                    "start":chunk_group[0]["start"],
                    "end":chunk_group[-1]["end"],
                    "video_title":video_title,
                    "text":" ".join(c["text"] for c in chunk_group)
                })
            os.makedirs("merge_Transcripts",exist_ok=True)
            with open(f"merge_Transcripts/{file_name}",'w',encoding="utf-8") as f:
                json.dump({"video_id":video_id,"video_title":video_title,"chunks":new_chunks,"text":data["text"]},f,indent=4)