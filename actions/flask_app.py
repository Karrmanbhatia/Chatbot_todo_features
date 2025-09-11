# actions/flask_app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import tempfile
import os
import json
import uuid
from datetime import datetime
import requests

from fetch_core import fetch_arm_json
from pattern_matcher_level_1 import run_prediction
from pattern_matcher_level_2 import run_bug_fallback


app = Flask(
    __name__,
    template_folder="../web",     # Relative to flask_app.py
    static_folder="../web"
)
CORS(app)  # Enable CORS for frontend access

BASE_API_URL = "https://cdcarm.win.ansys.com"

# ===================== AUTH HANDLER ===================== #
def get_basic_auth():
    """Parses ARM_API env var (username:apiKey) and returns (username, apiKey) tuple."""
    arm_api = os.environ.get("ARM_API", "")
    if ":" not in arm_api:
        raise ValueError("ARM_API must be set as username:apiKey")
    username, api_key = arm_api.split(":", 1)
    return (username, api_key)

# ===================== FETCH CDCARM ===================== #
@app.route("/fetch_cdcarm", methods=["POST"])
def fetch_cdcarm():
    try:
        data = request.get_json()

        # Extract params
        products = data.get("products", ["DISCO"])
        releases = data.get("releases", ["25.2"])
        platforms = data.get("platforms", ["Windows"])
        min_failing = int(data.get("min_failing_builds", 2))
        owner = "all"  # Always fetch ALL owners

        # Generate unique output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        file_name = f"cdcarm_results_{timestamp}_{unique_id}.json"
        output_path = os.path.join(tempfile.gettempdir(), file_name)

        # Log parameters
        print("📥 CDCARM API Request Parameters:")
        print(f"    Products: {products}")
        print(f"    Releases: {releases}")
        print(f"    Platforms: {platforms}")
        print(f"    Min Failing Builds: {min_failing}")
        print(f"    Output Path: {output_path}")

        # Fetch data from ARM
        results = fetch_arm_json(
            server="https://cdcarm.win.ansys.com",
            products=products,
            releases=releases,
            platforms=platforms,
            min_failing_builds=min_failing,
            owner=owner,
            output_path=output_path,
            print_enabled=False
        )

        print(f"✅ Records fetched: {len(results)}")

        # Run level-1 prediction (ARM)
        merged_summary = run_prediction(output_path)

        predicted = []
        unpredicted = []

        if isinstance(merged_summary, dict):
            mode = merged_summary.get("mode")
            print(f"🔄 Prediction Mode: {mode}")

            if mode == "predicted_with_clusters":
                predicted = merged_summary.get("predicted", [])
                unpredicted = merged_summary.get("clusters", [])
            elif mode in ("clustered_only", "clustered"):
                print("⚠ No predictions found. Returning all tests as 'unpredicted'.")
                unpredicted = results

        elif isinstance(merged_summary, list):
            predicted = merged_summary

        # Tag source = ARM for all level 1 predictions
        for test in predicted:
            test["Source"] = "ARM"
            test["MatchedSource"] = "LEVEL_1"

        # Ensure HasInvestigation is present
        for test in predicted + unpredicted:
            if "HasInvestigation" not in test:
                test["HasInvestigation"] = False

        # Run level-2 prediction (TFS bug match)
        level2_matches = run_bug_fallback(unpredicted, product_name=products[0] if products else "default")

        for test in level2_matches:
            test["Source"] = "TFS"
            test["MatchedSource"] = "TFS_BUG"
            test["HasInvestigation"] = False

        # Merge predictions — prefer higher confidence if duplicate test names
        final_predicted = []
        used_test_names = {}

        for test in predicted + level2_matches:
            test_name = test.get("TestName")
            score = float(test.get("ConfidenceScore", 0.0))

            if test_name not in used_test_names:
                used_test_names[test_name] = test
            else:
                existing_score = float(used_test_names[test_name].get("ConfidenceScore", 0.0))
                if score > existing_score:
                    used_test_names[test_name] = test

        final_predicted = list(used_test_names.values())

        # Identify unpredicted tests
        predicted_names = set(t["TestName"] for t in final_predicted)
        final_unpredicted = [t for t in results if t.get("TestName") not in predicted_names]

        for test in final_unpredicted:
            test["HasInvestigation"] = False

        return jsonify({
            "data_type": "prediction_table",
            "predicted": final_predicted,
            "unpredicted": final_unpredicted
        })

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return jsonify({"error": str(e)}), 500




# ===================== PROXY ENDPOINTS ===================== #
@app.route("/api/products", methods=["GET"])
def get_products():
    try:
        auth = get_basic_auth()
        url = f"{BASE_API_URL}/api/Product"
        response = requests.get(url, auth=auth, headers={"Content-Type": "application/json"}, timeout=15)
        response.raise_for_status()
        products = response.json()
        print(f"✅ Products fetched: {len(products)}")
        return jsonify(products)
    except Exception as e:
        print(f"❌ Error fetching products: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/releases", methods=["GET"])
def get_releases():
    try:
        auth = get_basic_auth()
        url = f"{BASE_API_URL}/api/Release"
        response = requests.get(url, auth=auth, headers={"Content-Type": "application/json"}, timeout=15)
        response.raise_for_status()
        releases = response.json()
        print(f"✅ Releases fetched: {len(releases)}")
        return jsonify(releases)
    except Exception as e:
        print(f"❌ Error fetching releases: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/platforms", methods=["GET"])
def get_platforms():
    try:
        auth = get_basic_auth()
        url = f"{BASE_API_URL}/api/Platform"
        response = requests.get(url, auth=auth, headers={"Content-Type": "application/json"}, timeout=15)
        response.raise_for_status()
        platforms = response.json()
        print(f"✅ Platforms fetched: {len(platforms)}")
        return jsonify(platforms)
    except Exception as e:
        print(f"❌ Error fetching platforms: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 for local
    app.run(host="0.0.0.0", port=port)
