#actions/tune_bug_match_model.py
import os
import json
import logging
import requests
import numpy as np
import torch
import optuna
from datetime import datetime
from requests.auth import HTTPBasicAuth
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import f1_score

# --------------------------- CONFIG --------------------------- #
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TUNE_DIR = os.path.join(SCRIPT_DIR, "tune_parameter")
TUNING_JSON = os.path.join(TUNE_DIR, "tuning_bugmatch_global.json")

TFS_FIELDS = [
    "System.Id", "System.Title", "System.State", "System.AssignedTo",
    "System.CreatedDate", "System.WorkItemType", "System.Description",
    "Microsoft.VSTS.TCM.ReproSteps", "System.Tags", "System.AreaPath", "System.IterationPath"
]

MODEL_CANDIDATES = [
    "bge-small-en-v1.5",
    "all-MiniLM-L12-v2",
    "e5-small-v2",
    "multi-qa-MiniLM-L6-cos-v1"
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

# --------------------------- FETCH BUGS --------------------------- #
def fetch_tfs_bugs(query_id, pat_token, log, org_url, project):
    url = f"{org_url}/{project}/_apis/wit/wiql/{query_id}?api-version=6.0"
    response = requests.get(url, auth=HTTPBasicAuth('', pat_token))
    response.raise_for_status()
    work_items = response.json().get('workItems', [])
    ids = [str(item['id']) for item in work_items]
    if not ids:
        return []

    bugs = []
    for i in range(0, len(ids), 200):
        chunk = ids[i:i+200]
        body = {"ids": chunk, "fields": TFS_FIELDS}
        resp = requests.post(
            f"{org_url}/_apis/wit/workitemsbatch?api-version=6.0",
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
                "BugId": fields.get("System.Id"),
                "Title": fields.get("System.Title"),
                "State": fields.get("System.State"),
                "AssignedTo": fields.get("System.AssignedTo", {}).get("displayName", "Unassigned")
                    if isinstance(fields.get("System.AssignedTo"), dict)
                    else fields.get("System.AssignedTo", "Unassigned"),
                "Text": clean_text(
                    f"{fields.get('System.Title')} "
                    f"{fields.get('System.Description')} "
                    f"{fields.get('Microsoft.VSTS.TCM.ReproSteps')} "
                    f"{fields.get('System.Tags')}"
                )
            }
            bugs.append(doc)
    return bugs

# --------------------------- EMBED --------------------------- #
def get_embeddings(model, texts):
    return model.encode(texts, batch_size=32)

# --------------------------- EVALUATE --------------------------- #
def evaluate_model(bug_texts, model, threshold):
    emb = get_embeddings(model, bug_texts)
    sims = cosine_similarity(emb, emb)

    y_true = []
    y_pred = []

    for i in range(len(sims)):
        for j in range(i + 1, len(sims)):
            y_true.append(1 if bug_texts[i] == bug_texts[j] else 0)  # identity fallback
            y_pred.append(1 if sims[i][j] >= threshold else 0)

    if sum(y_pred) == 0:
        return 0.0
    return f1_score(y_true, y_pred)

# --------------------------- TUNING --------------------------- #
def tune_model(bugs, log):
    best_overall = {"score": -1}

    bug_texts = [b["Text"] for b in bugs]

    for model_name in MODEL_CANDIDATES:
        try:
            model_path = os.path.join("..", "models", model_name)
            model = SentenceTransformer(model_path, device="cuda" if torch.cuda.is_available() else "cpu")
        except Exception as e:
            log.warning(f"❌ Failed to load {model_name}: {e}")
            continue

        log.info(f"🔍 Tuning model: {model_name}")

        def objective(trial):
            th = trial.suggest_float("threshold", 0.3, 0.9)
            score = evaluate_model(bug_texts, model, th)
            return score

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=20)

        if study.best_value > best_overall["score"]:
            best_overall = {
                "model_name": model_name,
                "threshold": round(study.best_params["threshold"], 3),
                "score": round(study.best_value, 4),
                "timestamp": datetime.now().isoformat()
            }

    log.info(f"✅ Best Config: {best_overall}")
    with open(TUNING_JSON, "w", encoding="utf-8") as f:
        json.dump(best_overall, f, indent=2)
    log.info(f"🧠 Saved best config to {TUNING_JSON}")

# --------------------------- MAIN --------------------------- #
def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    log = logging.getLogger()

    query_id = "0064473e-7889-463f-83b3-056b66904d0d"
    #pat_token = "PAT TOKEN"
    org_url = "https://tfs.ansys.com:8443/tfs/ANSYS_Development"
    project = "Portfolio"
    os.makedirs(TUNE_DIR, exist_ok=True)
    log.info("📡 Fetching TFS bugs...")
    bugs = fetch_tfs_bugs(query_id, pat_token, log, org_url, project)
    if bugs:
        tune_model(bugs, log)
    else:
        log.warning("No bugs returned. Tuning aborted.")

if __name__ == "__main__":
    main()
