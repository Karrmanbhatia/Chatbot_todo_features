import os
import json
import re
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')


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
        print("⚠️ No investigated anchors found. Cannot anchor prediction.")
        return []

    # encode
    anchor_texts = [a['Message'] for a in anchors]
    anchor_embeddings = model.encode(anchor_texts)

    results = []

    for target in targets:
        target_embedding = model.encode([target['Message']])[0]
        similarities = cosine_similarity(
            [target_embedding], anchor_embeddings
        )[0]
        # find best matching anchor
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        if best_score < 1 - threshold:
            predicted_workitem = "-"
        else:
            predicted_workitem = anchors[best_idx]['Investigation']['WorkItemId']
        results.append({
            "TestName": target['TestName'],
            "Owner": target['Owner'],
            "PredictedWorkItemId": predicted_workitem
        })

    # add anchors themselves
    for a in anchors:
        results.append({
            "TestName": a['TestName'],
            "Owner": a['Owner'],
            "PredictedWorkItemId": a['Investigation']['WorkItemId']
        })

    return results


if __name__ == "__main__":
    file = input("Path to JSON file: ").strip()
    res = run_prediction(file)
    df = pd.DataFrame(res)
    print(df.to_string(index=False))
