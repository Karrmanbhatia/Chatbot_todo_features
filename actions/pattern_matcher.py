# pattern_matcher.py

import json
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering

def clean_failure_message(msg):
    """Basic cleaning of failure messages."""
    msg = msg.lower()
    msg = re.sub(r'\d+', '', msg)  # remove numbers
    msg = re.sub(r'\W+', ' ', msg)  # remove non-word chars
    return msg.strip()

def cluster_failures(input_json, output_csv):
    # Load JSON data
    with open(input_json, "r") as f:
        data = json.load(f)

    # Clean messages
    messages = [clean_failure_message(item["FailureMessage"]) for item in data]

    # Vectorize
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(messages)

    # Cluster
    clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=0.3, linkage="average", affinity="cosine")
    clusters = clustering.fit_predict(tfidf_matrix.toarray())

    # Add cluster labels
    for i, item in enumerate(data):
        item["ClusterID"] = int(clusters[i])

    # Save to CSV
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)
    print(f"✅ Results saved to {output_csv}")

if __name__ == "__main__":
    # Example usage
    input_json = "your_fetched_file.json"
    output_csv = "clustered_failures.csv"
    cluster_failures(input_json, output_csv)
