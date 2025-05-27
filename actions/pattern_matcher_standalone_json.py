# file: pattern_matcher_standalone_json.py

import os
import json
import re
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN

# Load NLP embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_error_messages_from_json(json_data):
    error_msgs = []
    if isinstance(json_data, list):
        for entry in json_data:
            if 'FailureMessage' in entry and entry.get("Result") == "ERROR":
                test_name = entry.get("TestName", "Unknown Test")
                owner = entry.get("Owner", "Unknown Owner")
                raw_xml = entry['FailureMessage']
                matches = re.findall(r'<MESSAGE RESULT="ERROR">(.*?)</MESSAGE>', raw_xml, re.DOTALL)
                for msg in matches:
                    msg_clean = msg.replace('\t', ' ').replace('\n', ' ')
                    msg_clean = re.sub(r'\s+', ' ', msg_clean).strip()
                    investigation = None
                    if entry.get("HasInvestigation"):
                        investigation = {
                            "InvestigationReport": entry.get("InvestigationReport", "N/A"),
                            "WorkItemId": entry.get("WorkItemId", "N/A")
                        }
                    error_msgs.append({
                        "TestName": test_name,
                        "Owner": owner,
                        "Message": msg_clean,
                        "Investigation": investigation
                    })
    return error_msgs

def cluster_errors(error_msgs):
    if not error_msgs:
        print("No error messages found.")
        return [], []
    
    texts = [entry['Message'] for entry in error_msgs]
    embeddings = model.encode(texts)
    clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
    labels = clustering.fit_predict(embeddings)
    
    clusters = {}
    for label, msg_data in zip(labels, error_msgs):
        clusters.setdefault(label, []).append(msg_data)
    
    # Unmerged table (each error msg separately)
    unmerged_summary = []
    
    # Merged table (one row per test)
    merged_summary = {}
    
    for cluster_id, entries in clusters.items():
        print(f"\n=== Cluster {cluster_id} ({len(entries)} messages) ===")
        investigations = [e for e in entries if e['Investigation']]
        if investigations:
            print("\n🔍 Investigations in this cluster:")
            for inv in investigations:
                print(f" - {inv['TestName']} (Owner: {inv['Owner']}): {inv['Investigation']}")
        else:
            print("\n🔍 No investigation data in this cluster.")
        
        for entry in entries:
            test_name = entry['TestName']
            owner = entry['Owner']
            investigation_report = entry['Investigation']['InvestigationReport'] if entry['Investigation'] else "None"
            work_item_id = entry['Investigation']['WorkItemId'] if entry['Investigation'] else "None"
            
            # Add to unmerged summary
            unmerged_summary.append({
                "ClusterId": cluster_id,
                "TestName": test_name,
                "Owner": owner,
                "InvestigationReport": investigation_report,
                "WorkItemId": work_item_id
            })
            
            # Merge by test name
            key = (cluster_id, test_name)
            if key not in merged_summary:
                merged_summary[key] = {
                    "ClusterId": cluster_id,
                    "TestName": test_name,
                    "Owner": owner,
                    "InvestigationReport": investigation_report,
                    "WorkItemId": work_item_id
                }

    return unmerged_summary, list(merged_summary.values())

def main():
    json_dir = "test_data"
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    all_error_msgs = []

    for file in json_files:
        file_path = os.path.join(json_dir, file)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_data = f.read()
            def escape_control_chars(match):
                content = match.group(1)
                content = content.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                return f'"{content}"'
            raw_data = re.sub(r'"([^"]*?)"', escape_control_chars, raw_data, flags=re.DOTALL)
            print(f"🔎 Cleaned (escaped) content preview of {file}: {raw_data[:200]}")

            try:
                json_data = json.loads(raw_data)
                extracted_errors = extract_error_messages_from_json(json_data)
                filtered_errors = [e for e in extracted_errors if 'PASSED' not in e['Message']]
                all_error_msgs.extend(filtered_errors)
            except json.JSONDecodeError as e:
                print(f"⚠️ Skipping {file}: JSONDecodeError: {e}")

    print(f"Total error messages extracted (excluding PASSED): {len(all_error_msgs)}")
    unmerged, merged = cluster_errors(all_error_msgs)
    
    # Show final investigation summaries
    df_unmerged = pd.DataFrame(unmerged)
    df_merged = pd.DataFrame(merged)
    
    print("\n📊 Unmerged Investigation Summary (all error messages shown):")
    print(df_unmerged.to_string(index=False))
    
    print("\n📊 Merged Investigation Summary (one row per test):")
    print(df_merged.to_string(index=False))
    
    # Ask user which view to save
    choice = input("\n💾 Do you want to save (u)nmerged, (m)erged, or (b)oth? (u/m/b/n): ").strip().lower()
    if choice == 'u' or choice == 'b':
        df_unmerged.to_csv("investigation_summary_unmerged.csv", index=False)
        print("✅ Saved unmerged summary to investigation_summary_unmerged.csv")
    if choice == 'm' or choice == 'b':
        df_merged.to_csv("investigation_summary_merged.csv", index=False)
        print("✅ Saved merged summary to investigation_summary_merged.csv")
    if choice == 'n':
        print("❌ CSV export skipped.")
        
if __name__ == "__main__":
    main()
