import os
import json
import re
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)


def extract_error_messages(json_data):
    """
    Separates:
      - anchors: failures with investigation
      - targets: failures without investigation
    """
    anchors = []
    targets = []

    if isinstance(json_data, list):
        for entry in json_data:
            if entry.get("Result") == "ERROR" and "FailureMessage" in entry:
                test_name = entry.get("TestName", "Unknown Test")
                owner = entry.get("Owner", "Unknown Owner")
                raw_xml = entry["FailureMessage"]
                matches = re.findall(r'<MESSAGE RESULT="ERROR">(.*?)</MESSAGE>', raw_xml, re.DOTALL)
                for msg in matches:
                    cleaned = re.sub(r'\s+', ' ', msg.replace('\n', ' ').replace('\t', ' ')).strip()
                    if entry.get("HasInvestigation"):
                        anchors.append({
                            "TestName": test_name,
                            "Owner": owner,
                            "Message": cleaned,
                            "Investigation": {
                                "Report": entry.get("InvestigationReport", "N/A"),
                                "WorkItemId": entry.get("WorkItemId", "N/A")
                            }
                        })
                    else:
                        targets.append({
                            "TestName": test_name,
                            "Owner": owner,
                            "Message": cleaned
                        })
    return anchors, targets


def run_prediction(json_file_path, threshold=0.3):
    """
    Investigation-anchored prediction:
      - group errors with anchors based on cosine similarity
      - label predicted vs. existing work items
      - include confidence score for predictions
    """

    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"{json_file_path} not found")

    with open(json_file_path, encoding='utf-8') as f:
        raw_data = f.read()

        raw_data = re.sub(
            r'"([^"]*?)"',
            lambda m: m.group(0)
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('\t', '\\t'),
            raw_data,
            flags=re.DOTALL
        )
        try:
            json_data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON decode failed: {e}")
            return []

    # Extract anchors and targets
    anchors = []
    targets = []

    if isinstance(json_data, list):
        for entry in json_data:
            if 'FailureMessage' in entry and entry.get("Result") == "ERROR":
                test_name = entry.get("TestName", "Unknown Test")
                owner = entry.get("Owner", "Unknown Owner")
                raw_xml = entry['FailureMessage']
                matches = re.findall(r'<MESSAGE RESULT="ERROR">(.*?)</MESSAGE>', raw_xml, re.DOTALL)
                for msg in matches:
                    cleaned = re.sub(r'\s+', ' ', msg.replace('\n', ' ').replace('\t', ' ')).strip()
                    if entry.get("HasInvestigation"):
                        anchors.append({
                            "TestName": test_name,
                            "Owner": owner,
                            "Message": cleaned,
                            "Investigation": {
                                "Report": entry.get("InvestigationReport", "N/A"),
                                "WorkItemId": entry.get("WorkItemId", "N/A")
                            }
                        })
                    else:
                        targets.append({
                            "TestName": test_name,
                            "Owner": owner,
                            "Message": cleaned
                        })

    if not anchors:
        print("⚠️ No investigated anchors found. Attempting fallback clustering...")
        fallback_clusters = group_similar_failures(targets)
        return {
            "mode": "clustered",
            "clusters": fallback_clusters
        }

    # Encode anchor messages once
    anchor_texts = [a['Message'] for a in anchors]
    anchor_embeddings = model.encode(anchor_texts)

    results = []

    # Batch encode all target messages
    target_texts = [t['Message'] for t in targets]
    target_embeddings = model.encode(target_texts)

    for idx, target in enumerate(targets):
        target_embedding = target_embeddings[idx]
        similarities = cosine_similarity([target_embedding], anchor_embeddings)[0]

        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]

        if best_score < threshold:
            predicted_workitem = "-"
        else:
            predicted_workitem = anchors[best_idx]['Investigation']['WorkItemId']

        results.append({
            "TestName": target['TestName'],
            "Owner": target['Owner'],
            "PredictedWorkItemId": predicted_workitem,
            "IsPredicted": "Yes" if predicted_workitem != "-" else "No",
            "ConfidenceScore": round(float(best_score), 3),
            "HasInvestigation": False
        })


    # Add known anchors directly
    for a in anchors:
        results.append({
            "TestName": a['TestName'],
            "Owner": a['Owner'],
            "PredictedWorkItemId": a['Investigation']['WorkItemId'],
            "IsPredicted": "No",
            "ConfidenceScore": None,
            "HasInvestigation": True
        })

        # Group unpredicted targets (fallback)
    unpredicted = [
        t for i, t in enumerate(targets)
        if results[i]["PredictedWorkItemId"] == "-"
    ]
    fallback_clusters = group_similar_failures(unpredicted)

    return {
        "mode": "predicted_with_clusters",
        "predicted": results,
        "clusters": fallback_clusters
    }

    return results
def group_similar_failures(targets, eps=0.3, min_samples=2):
    """
    Cluster similar failure messages when no anchors are available.
    Returns list of clusters, each a list of test dicts.
    """
    if not targets:
        return []

    model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
    messages = [t['Message'] for t in targets]
    embeddings = model.encode(messages)

    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = clustering.fit_predict(embeddings)

    clustered = {}
    for i, label in enumerate(labels):
        if label == -1:
            continue  # noise / outliers
        target_with_flag = dict(targets[i])  # copy to avoid mutating original
        target_with_flag["HasInvestigation"] = False
        clustered.setdefault(label, []).append(target_with_flag)
        

    return list(clustered.values())


if __name__ == "__main__":
    file = input("Path to JSON file: ").strip()
    res = run_prediction(file)
    df = pd.DataFrame(res)
    print(df.to_string(index=False))
