#actions/TFS_indexing.py
import os
import json
import logging
import requests
from requests.auth import HTTPBasicAuth
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import faiss

# --------------------------- CONFIG --------------------------- #
TUNING_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "tune_parameter", "tuning_bugmatch_global.json")

FIXED_MODEL_NAME = "bge-small-en-v1.5"  # fallback

TFS_FIELDS = [
    "System.Id", "System.Title", "System.State", "System.AssignedTo",
    "System.CreatedDate", "System.WorkItemType", "System.Description",
    "Microsoft.VSTS.TCM.ReproSteps", "System.Tags", "System.AreaPath", "System.IterationPath"
]

# --------------------------- CLEANING --------------------------- #
def clean_text(text):
    if not text:
        return ""
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\b(FaceID|Node|Part|Surface|Edge)[-_]?\d+\b", "", text)
    text = text.replace("_", " ")
    text = re.sub(r"\b[\w-]+\.(cpp|h|py|cs|log|txt|dll|exe)\b", "", text)
    return re.sub(r"\s+", " ", text.strip())

# --------------------------- TFS FETCH --------------------------- #
def fetch_tfs_bugs(query_id, pat_token, output_jsonl, log, organization_url, project_name):
    url = f"{organization_url}/{project_name}/_apis/wit/wiql/{query_id}?api-version=6.0"
    log.info("Requesting list of work items via WIQL...")
    response = requests.get(url, auth=HTTPBasicAuth('', pat_token))
    response.raise_for_status()
    work_items = response.json().get('workItems', [])
    ids = [str(item['id']) for item in work_items]
    if not ids:
        log.warning("No bugs found for the given query.")
        return []

    bugs = []
    with open(output_jsonl, 'w', encoding='utf-8') as fout:
        for i in range(0, len(ids), 200):
            chunk = ids[i:i+200]
            body = {"ids": chunk, "fields": TFS_FIELDS}
            resp = requests.post(
                f"{organization_url}/_apis/wit/workitemsbatch?api-version=6.0",
                json=body,
                auth=HTTPBasicAuth('', pat_token),
                headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            for item in resp.json().get('value', []):
                fields = item.get('fields', {})
                if fields.get("System.WorkItemType", "").lower() != "bug":
                    continue
                doc = {
                    "id": fields.get("System.Id"),
                    "title": fields.get("System.Title"),
                    "state": fields.get("System.State"),
                    "assigned_to": fields.get("System.AssignedTo", {}).get("displayName", "Unassigned")
                        if isinstance(fields.get("System.AssignedTo"), dict)
                        else fields.get("System.AssignedTo", "Unassigned"),
                    "created_date": fields.get("System.CreatedDate"),
                    "description": fields.get("System.Description", ""),
                    "repro_steps": fields.get("Microsoft.VSTS.TCM.ReproSteps", ""),
                    "tags": fields.get("System.Tags", ""),
                    "area_path": fields.get("System.AreaPath", ""),
                    "iteration_path": fields.get("System.IterationPath", "")
                }
                fout.write(json.dumps(doc, ensure_ascii=False) + '\n')
                bugs.append(doc)
    log.info(f"TFS bugs corpus written to {output_jsonl}")
    return bugs

# --------------------------- EMBED + SAVE --------------------------- #
def embed_and_save(bugs, dir_path, log):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log.info(f"Using device: {device}")
    
    try:
        with open(TUNING_CONFIG_PATH, "r") as f:
            best_config = json.load(f)
            model_name = best_config.get("model_name", FIXED_MODEL_NAME)
            log.info(f"📌 Using model from tuning config: {model_name}")
    except Exception as e:
        model_name = FIXED_MODEL_NAME
        log.warning(f"⚠ Failed to load tuning config. Using fallback model: {model_name}")

    model_path = os.path.join(os.path.dirname(__file__), "..", "models", model_name)
    model = SentenceTransformer(model_path, device=device)
    if device == "cuda":
        model = model.half()

    texts = [
        clean_text(f"{doc['title']}\n{doc['description']}\n{doc['repro_steps']}\n{doc['tags']}")
        for doc in bugs
    ]
    log.info(f"Embedding {len(texts)} bugs using model: {model_name}")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)

    meta = [
        {
            "BugId": doc["id"],
            "Title": doc["title"],
            "State": doc["state"],
            "AssignedTo": doc["assigned_to"],
            "Message": clean_text(f"{doc['title']} {doc['description']} {doc['repro_steps']} {doc['tags']}")
        }
        for doc in bugs
    ]

    embeddings = np.array(embeddings).astype('float32')
    np.save(os.path.join(dir_path, "tfs_bugs_embeddings.npy"), embeddings)
    with open(os.path.join(dir_path, "tfs_bugs_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, os.path.join(dir_path, "tfs_bugs.index"))
    log.info("✅ Bug index and metadata written to disk.")


# --------------------------- MAIN --------------------------- #
def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    log = logging.getLogger()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dir_path = os.path.join(BASE_DIR, "tune_parameter")
    os.makedirs(dir_path, exist_ok=True)

    query_id = "0064473e-7889-463f-83b3-056b66904d0d"
    pat_token = os.getenv("TFS_PAT_TOKEN")
    organization_url = "https://tfs.ansys.com:8443/tfs/ANSYS_Development"
    project_name = "Portfolio"

    output_jsonl = os.path.join(dir_path, "tfs_bugs_corpus.jsonl")

    bugs = fetch_tfs_bugs(query_id, pat_token, output_jsonl, log, organization_url, project_name)
    if bugs:
        embed_and_save(bugs, dir_path, log)
    else:
        log.warning("No bugs were fetched; skipping embedding and saving.")

if __name__ == '__main__':
    main()
