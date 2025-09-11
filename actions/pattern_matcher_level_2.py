#actions/pattern_matcher_level_2.py
import os
import json
import re
import numpy as np
import faiss
import torch
import optuna
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import f1_score

# -------------------------------
# Config
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUG_INDEX_PATH = os.path.join(BASE_DIR, "bug_index/tfs_bugs.index")
BUG_META_PATH = os.path.join(BASE_DIR, "bug_index/tfs_bugs_meta.json")
MODEL_CANDIDATES = [
    "bge-small-en-v1.5",
    "all-MiniLM-L12-v2",
    "e5-small-v2",
    "multi-qa-MiniLM-L6-cos-v1"
]
DEFAULT_THRESHOLD = 0.65

device = "cuda" if torch.cuda.is_available() else "cpu"
model = None

# -------------------------------
# Preprocessing
# -------------------------------
def clean_message(msg: str) -> str:
    msg = re.sub(r"<[^>]+>", " ", msg)
    msg = msg.replace("_", " ")
    msg = re.sub(r"\b(FaceID|Node|Part|Surface|Edge)[-_]?\d+\b", "", msg)
    msg = re.sub(r"\b[\w-]+\.(cpp|h|py|cs|log|txt|dll|exe)\b", "", msg)
    msg = re.sub(r"\s+", " ", msg).strip()
    return msg

# -------------------------------
# Loaders
# -------------------------------
def load_embedding_model(name):
    global model
    model_path = os.path.join(BASE_DIR, '..', 'models', name)
    model = SentenceTransformer(model_path, device=device)
    if device == "cuda":
        model = model.half()
    print(f"📦 Loaded embedding model: {name}")

def load_faiss_index():
    return faiss.read_index(BUG_INDEX_PATH)

def load_bug_metadata():
    with open(BUG_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------
# Evaluation
# -------------------------------
def evaluate_bug_matching(unmatched_tests, bug_meta, bug_index, model, threshold):
    cleaned_messages = [clean_message(t['Message']) for t in unmatched_tests]
    test_embeddings = model.encode(cleaned_messages, batch_size=32, device=device)
    bug_messages = [clean_message(b['Message']) for b in bug_meta]
    bug_embeddings = model.encode(bug_messages, batch_size=32, device=device)

    index = faiss.IndexFlatL2(len(bug_embeddings[0]))
    index.add(np.array(bug_embeddings).astype("float32"))

    D, I = index.search(np.array(test_embeddings).astype("float32"), k=1)

    y_true = [1] * len(unmatched_tests)  # Assume all should match for eval
    y_pred = [1 if (1 - D[i][0]) >= threshold else 0 for i in range(len(unmatched_tests))]

    if sum(y_pred) == 0:
        return 0.0

    return f1_score(y_true, y_pred)

# -------------------------------
# Auto-Tuning
# -------------------------------
def auto_tune_bug_matching(unmatched_tests, bug_meta):
    best_score = -1
    best_params = {}

    for model_name in MODEL_CANDIDATES:
        try:
            load_embedding_model(model_name)
        except Exception as e:
            print(f"❌ Failed to load {model_name}: {e}")
            continue

        bug_index = load_faiss_index()

        def objective(trial):
            threshold = trial.suggest_float("threshold", 0.3, 0.9)
            score = evaluate_bug_matching(unmatched_tests, bug_meta, bug_index, model, threshold)
            trial.set_user_attr("f1_score", score)
            return score

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=20, show_progress_bar=False)

        if study.best_value > best_score:
            best_score = study.best_value
            best_params = {
                "model_name": model_name,
                "threshold": round(study.best_params["threshold"], 3)
            }

    print(f"✅ Best model: {best_params['model_name']} | Threshold: {best_params['threshold']} | F1: {best_score:.3f}")
    return best_params

def get_best_params(unmatched_tests, product="default"):
    path = os.path.join(BASE_DIR, f"tuning_bugmatch_{product}.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            pass

    bug_meta = load_bug_metadata()
    best = auto_tune_bug_matching(unmatched_tests, bug_meta)
    with open(path, "w") as f:
        json.dump(best, f, indent=2)
    return best

# -------------------------------
# Matching Logic
# -------------------------------
def match_against_bugs(unmatched_tests, model_name, threshold):
    load_embedding_model(model_name)
    bug_index = load_faiss_index()
    bug_meta = load_bug_metadata()

    cleaned_messages = [clean_message(t['Message']) for t in unmatched_tests]
    test_embeddings = model.encode(cleaned_messages, batch_size=32, device=device)

    D, I = bug_index.search(np.array(test_embeddings).astype("float32"), k=1)

    results = []
    for i, test in enumerate(unmatched_tests):
        score = 1 - D[i][0]
        bug_idx = int(I[i][0])

        if score >= threshold:
            matched_bug = bug_meta[bug_idx]
            results.append({
                "TestName": test["TestName"],
                "Owner": test["Owner"],
                "MatchedBugId": matched_bug["BugId"],
                "BugTitle": matched_bug.get("Title", ""),
                "ConfidenceScore": round(float(score), 3),
                "MatchedSource": "TFS_BUG"
            })
        else:
            results.append({
                "TestName": test["TestName"],
                "Owner": test["Owner"],
                "MatchedBugId": "-",
                "BugTitle": "",
                "ConfidenceScore": round(float(score), 3),
                "MatchedSource": "UNIQUE"
            })

    return results

# -------------------------------
# Flask Entry
# -------------------------------
def run_bug_fallback(unmatched_tests, product_name="default"):
    if not unmatched_tests:
        return []

    print(f"🔄 Matching {len(unmatched_tests)} unpredicted tests to TFS bugs...")
    params = get_best_params(unmatched_tests, product_name)
    return match_against_bugs(unmatched_tests, params["model_name"], params["threshold"])

# -------------------------------
# CLI Debug
# -------------------------------
if __name__ == "__main__":
    path = input("Path to unpredicted JSON file: ").strip()
    if not os.path.exists(path):
        print("❌ File not found.")
        exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    result = run_bug_fallback(data, product_name="DISCO")
    print(json.dumps(result, indent=2))
