from flask import Flask, request, jsonify
from flask_cors import CORS  # Must be before routes
import tempfile
import os
import base64
import json

from fetch_core import fetch_arm_json  # Make sure this points to the right location

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend -> backend calls

@app.route("/fetch_cdcarm", methods=["POST"])
def fetch_cdcarm():
    try:
        data = request.get_json()

        # Extract params with defaults
        products = data.get("products", ["DISCO"])
        releases = data.get("releases", ["25.2"])
        platforms = data.get("platforms", ["Windows"])
        min_failing = int(data.get("min_failing_builds", 2))
        owner = data.get("owner", "all")

        # Create a temp output path
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "web_cdcarm_results.json")

        # Fetch data using core logic
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

        # Read and encode results
        with open(output_path, 'r', encoding='utf-8') as f:
            json_data = f.read()

        base64_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

        return jsonify({
            "data_type": "json_download",
            "filename": "web_cdcarm_results.json",
            "content": base64_data,
            "record_count": len(results)
        })


    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
