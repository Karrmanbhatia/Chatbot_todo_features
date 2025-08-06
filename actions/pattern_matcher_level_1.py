#pattern_matcher_level_1.py
import os
import json
import re
import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score, f1_score
import itertools
import optuna

# -------------------------------
# GPU / Device Configuration
# -------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ Using device: {device.upper()}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CANDIDATES = [
    "bge-small-en-v1.5",
    "all-MiniLM-L12-v2",
    "e5-small-v2",
    "multi-qa-MiniLM-L6-cos-v1"
]

DEFAULT_THRESHOLD = 0.3
DEFAULT_EPS = 0.3
DEFAULT_MIN_SAMPLES = 2

# -------------------------------
# Embedding Model (Lazy load)
# -------------------------------
model = None

def load_model(model_name):
    global model
    model_path = os.path.join(BASE_DIR, '..', 'models', model_name)
    model = SentenceTransformer(model_path, device=device)
    if device == "cuda":
        model = model.half()
    print(f"📦 Loaded model: {model_name}")
    return model

# -------------------------------
# Utility Functions
# -------------------------------
def extract_error_messages(json_data):
    anchors, targets = [], []
    seen_tests = set()
    if isinstance(json_data, list):
        for entry in json_data:
            if entry.get("Result") in ["ERROR", "FAIL", "TIMEOUT"] and "FailureMessage" in entry:
                test_name = entry.get("TestName", "Unknown Test")
                owner = entry.get("Owner", "Unknown Owner")
                product = entry.get("Product", "default")
                raw_xml = entry["FailureMessage"]
                matches = re.findall(r'<MESSAGE RESULT="(?:ERROR|FAIL|TIMEOUT)">(.*?)</MESSAGE>', raw_xml, re.DOTALL)
                full_msg = " ".join([re.sub(r'\s+', ' ', m.replace('\n', ' ').replace('\t', ' ')).strip() for m in matches])
                if (test_name, full_msg) in seen_tests:
                    continue
                seen_tests.add((test_name, full_msg))
                entry_dict = {
                    "TestName": test_name,
                    "Owner": owner,
                    "Message": full_msg,
                    "Product": product
                }
                if entry.get("HasInvestigation"):
                    entry_dict["Investigation"] = {
                        "Report": entry.get("InvestigationReport", "N/A"),
                        "WorkItemId": entry.get("WorkItemId", "N/A")
                    }
                    anchors.append(entry_dict)
                else:
                    targets.append(entry_dict)
    return anchors, targets

def evaluate_prediction(anchors, targets, threshold, model):
    if not anchors or not targets:
        return 0.0
    anchor_texts = [a['Message'] for a in anchors]
    target_texts = [t['Message'] for t in targets]
    anchor_embeddings = model.encode(anchor_texts, batch_size=32, device=device)
    target_embeddings = model.encode(target_texts, batch_size=32, device=device)
    true_labels, pred_labels = [], []
    for idx, target in enumerate(targets):
        similarities = cosine_similarity([target_embeddings[idx]], anchor_embeddings)[0]
        best_score = np.max(similarities)
        true_labels.append(1)
        pred_labels.append(1 if best_score >= threshold else 0)
    return f1_score(true_labels, pred_labels)

def evaluate_clustering(targets, eps, min_samples, model):
    if len(targets) < 2:
        return 0.0
    messages = [t['Message'] for t in targets]
    embeddings = model.encode(messages, batch_size=32, device=device)
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = clustering.fit_predict(embeddings)
    if len(set(labels)) <= 1:
        return 0.0
    return silhouette_score(embeddings, labels, metric='cosine')

def auto_tune(anchors, targets):
    print("🔍 Starting auto-tuning across models using Optuna...")

    best_score = -1
    best_params = {}

    for model_name in MODEL_CANDIDATES:
        try:
            temp_model = load_model(model_name)
        except Exception as e:
            print(f"❌ Failed to load model {model_name}: {e}")
            continue

        def objective(trial):
            th = trial.suggest_float("threshold", 0.2, 0.6)
            eps = trial.suggest_float("eps", 0.1, 0.4)
            ms = trial.suggest_int("min_samples", 2, 5)

            f1_val = evaluate_prediction(anchors, targets, th, temp_model) if len(anchors) >= 5 else 0.0
            cluster_score = evaluate_clustering(targets, eps, ms, temp_model)
            score = 0.7 * f1_val + 0.3 * cluster_score if f1_val > 0 else cluster_score

            trial.set_user_attr("f1", f1_val)
            trial.set_user_attr("silhouette", cluster_score)
            return score

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=25, show_progress_bar=False)

        if study.best_value > best_score:
            best_score = study.best_value
            best_params = {
                "threshold": round(study.best_params["threshold"], 3),
                "eps": round(study.best_params["eps"], 3),
                "min_samples": study.best_params["min_samples"],
                "model_name": model_name
            }

        print(f"🧪 Finished tuning {model_name} → Best Score: {round(study.best_value, 3)}")

    print(f"✅ Best overall tuning: {best_params} (Score: {round(best_score, 3)})")
    return best_params

def get_best_params(anchors, targets, product_name="default"):
    tuning_file = os.path.join(BASE_DIR, f"tuning_config_{product_name}.json")
    if os.path.exists(tuning_file):
        try:
            with open(tuning_file, "r") as f:
                return json.load(f)
        except:
            pass
    if not anchors and not targets:
        return {
            "threshold": DEFAULT_THRESHOLD,
            "eps": DEFAULT_EPS,
            "min_samples": DEFAULT_MIN_SAMPLES,
            "model_name": MODEL_CANDIDATES[0]
        }
    best = auto_tune(anchors, targets)
    with open(tuning_file, "w") as f:
        json.dump(best, f, indent=2)
    return best

def extract_product_name(json_data, default="default"):
    for entry in json_data:
        if entry.get("Product"):
            return entry["Product"].strip()
    return default

def group_similar_failures(targets, model, eps=DEFAULT_EPS, min_samples=DEFAULT_MIN_SAMPLES):
    if not targets:
        return []
    messages = [t['Message'] for t in targets]
    embeddings = model.encode(messages, batch_size=32, device=device)
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = clustering.fit_predict(embeddings)
    clustered = {}
    for i, label in enumerate(labels):
        if label == -1:
            continue
        target_copy = dict(targets[i])
        target_copy["HasInvestigation"] = False
        clustered.setdefault(label, []).append(target_copy)
    return list(clustered.values())

def run_prediction(json_file_path):
    with open(json_file_path, encoding='utf-8') as f:
        raw_data = f.read()
        raw_data = re.sub(
            r'"([^"]*?)"',
            lambda m: m.group(0).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'),
            raw_data,
            flags=re.DOTALL
        )
        json_data = json.loads(raw_data)

    anchors, targets = extract_error_messages(json_data)
    product_name = extract_product_name(json_data)
    best_params = get_best_params(anchors, targets, product_name)

    print(f"🚀 Using model: {best_params['model_name']}, th={best_params['threshold']}, eps={best_params['eps']}, min_samples={best_params['min_samples']}")
    load_model(best_params['model_name'])

    anchor_embeddings = model.encode([a['Message'] for a in anchors], batch_size=32, device=device)
    target_embeddings = model.encode([t['Message'] for t in targets], batch_size=32, device=device)

    predicted_results = []
    for idx, target in enumerate(targets):
        sims = cosine_similarity([target_embeddings[idx]], anchor_embeddings)[0]
        best_idx = np.argmax(sims)
        best_score = sims[best_idx]
        predicted_workitem = anchors[best_idx]['Investigation']['WorkItemId'] if best_score >= best_params['threshold'] else "-"
        predicted_results.append({
            "TestName": target['TestName'],
            "Owner": target['Owner'],
            "PredictedWorkItemId": predicted_workitem,
            "IsPredicted": "Yes" if predicted_workitem and predicted_workitem != "-" else "No",
            "ConfidenceScore": round(float(best_score), 3),
            "HasInvestigation": False,
            "Product": target["Product"]
        })

    for a in anchors:
        predicted_results.append({
            "TestName": a['TestName'],
            "Owner": a['Owner'],
            "PredictedWorkItemId": a['Investigation']['WorkItemId'],
            "IsPredicted": "No",
            "ConfidenceScore": 1.0,
            "HasInvestigation": True,
            "Product": a["Product"]
        })

    unpredicted = [targets[i] for i, t in enumerate(predicted_results[:len(targets)]) if t["PredictedWorkItemId"] == "-"]
    fallback_clusters = group_similar_failures(unpredicted, model, best_params['eps'], best_params['min_samples'])

    return {
        "mode": "predicted_with_clusters",
        "predicted": predicted_results,
        "clusters": fallback_clusters
    }

if __name__ == "__main__":
    file = input("Path to JSON file: ").strip()
    if not os.path.exists(file):
        print(f"❌ File not found: {file}")
        exit(1)
    res = run_prediction(file)
    if 'predicted' in res:
        df = pd.DataFrame(res['predicted'])
        print(df.to_string(index=False))
    else:
        print("⚠️ Only clustering data available.")
        print(res)

