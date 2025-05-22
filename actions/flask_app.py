from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import base64
import json
import uuid
from datetime import datetime

from fetch_core import fetch_arm_json

app = Flask(__name__)
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
        owner = data.get("owner", "all")

        # Generate unique output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        file_name = f"cdcarm_results_{timestamp}_{unique_id}.json"
        output_path = os.path.join(tempfile.gettempdir(), file_name)

        print("📥 CDCARM API Request Parameters:")
        print(f"    Products: {products}")
        print(f"    Releases: {releases}")
        print(f"    Platforms: {platforms}")
        print(f"    Min Failing Builds: {min_failing}")
        print(f"    Owner: {owner}")
        print(f"    Output Path: {output_path}")

        # Fetch data
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

        # Read the written file
        with open(output_path, 'r', encoding='utf-8') as f:
            json_data = f.read()

        base64_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

        return jsonify({
            "data_type": "json_download",
            "filename": file_name,
            "content": base64_data,
            "record_count": len(results)
        })

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
