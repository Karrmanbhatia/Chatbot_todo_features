#file: flask_app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import base64
import json
import uuid
from datetime import datetime
import requests  # 🔥 Add requests to fetch data from remote APIs

from fetch_core import fetch_arm_json

app = Flask(__name__,
    template_folder="../web",     # Relative to flask_app.py
    static_folder="../web" )
CORS(app)  # Enable CORS for frontend access

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
        print(f"    Owner: {owner}")
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

        # Run prediction on the saved JSON
        from pattern_matcher_level_1 import run_prediction
        merged_summary = run_prediction(output_path)

        if isinstance(merged_summary, dict):
            mode = merged_summary.get("mode")
            print(f"🔄 Prediction Mode: {mode}")

            if mode in ("clustered_only", "clustered"):
                return jsonify({
                    "data_type": "clustered_groups_only",
                    "clustered_summary": merged_summary["clusters"]
                })

            elif mode == "predicted_with_clusters":
                return jsonify({
                    "data_type": "hybrid",
                    "predicted": merged_summary["predicted"],
                    "clustered_summary": merged_summary["clusters"]
                })

        # If it's a plain list (legacy behavior)
        return jsonify({
            "data_type": "prediction_table",
            "merged_summary": merged_summary
        })

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


# 🔥 Proxy endpoints for dynamic data lists
@app.route("/api/products", methods=["GET"])
def get_products():
    try:
        response = requests.get("https://cdcarm.win.ansys.com/api/Product")
        response.raise_for_status()
        products = response.json()
        print(f"✅ Products fetched: {len(products)}")  # 🔥 Log count
        return jsonify(products)
    except Exception as e:
        print(f"❌ Error fetching products: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/releases", methods=["GET"])
def get_releases():
    try:
        response = requests.get("https://cdcarm.win.ansys.com/api/Release")
        response.raise_for_status()
        releases = response.json()
        print(f"✅ Releases fetched: {len(releases)}")  # 🔥 Log count
        return jsonify(releases)
    except Exception as e:
        print(f"❌ Error fetching releases: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/platforms", methods=["GET"])
def get_platforms():
    try:
        response = requests.get("https://cdcarm.win.ansys.com/api/Platform")
        response.raise_for_status()
        platforms = response.json()
        print(f"✅ Platforms fetched: {len(platforms)}")  # 🔥 Log count
        return jsonify(platforms)
    except Exception as e:
        print(f"❌ Error fetching platforms: {e}")
        return jsonify({"error": str(e)}), 500
from flask import render_template

@app.route("/")
def home():
    return render_template("index.html")

# Example for owners if needed
# @app.route("/api/owners", methods=["GET"])
# def get_owners():
#     try:
#         response = requests.get("https://cdcarm.win.ansys.com/api/Owners")
#         response.raise_for_status()
#         owners = response.json()
#         print(f"✅ Owners fetched: {len(owners)}")  # 🔥 Log count
#         return jsonify(owners)
#     except Exception as e:
#         print(f"❌ Error fetching owners: {e}")
#         return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 for local
    app.run(host="0.0.0.0", port=port)
