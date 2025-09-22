# actions/flask_app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import tempfile
import os
import json
import uuid
from datetime import datetime
import requests
import re
from concurrent.futures import ThreadPoolExecutor

from fetch_core import fetch_arm_json               # ← unchanged
from pattern_matcher_level_1 import run_prediction, extract_error_messages
from pattern_matcher_level_2 import run_bug_fallback

app = Flask(
    __name__,
    template_folder="../web",     # Relative to flask_app.py
    static_folder="../web"
)
CORS(app)  # Enable CORS for frontend access

# Single API base (host is same for Unified & Standalone; only UI path differs)
BASE_API_URL = "https://cdcarm.win.ansys.com"

# -----------------------------------------------------------------------------
# ✅ Hardcoded product map for items that don't appear in your usual catalog
#    (e.g., PRIME is shown under "Standalone" in the UI, but shares the same API host)
#    Extend this dict later if you find more special products.
# -----------------------------------------------------------------------------
# ✅ Products that need special handling.
# Add new ones here; set area="Standalone" if they use the Standalone report route.
PRODUCT_SOURCE_MAP = {
    "PRIME": {
        "server": BASE_API_URL,
        "product_id": 53,
        "area": "Standalone",
        "aliases": ["PRIME", "PRIME"],
    },
    # "CoolProduct": {"server": BASE_API_URL, "product_id": 777, "area": "Unified", "aliases": ["COOLPRODUCT"]}
}


# If you ever want to search multiple bases by default, add them here.
DEFAULT_CDCARM_SERVERS = [BASE_API_URL]


# ===================== AUTH HANDLER ===================== #
def get_basic_auth():
    """Parses ARM_API env var (username:apiKey) and returns (username, apiKey) tuple."""
    arm_api = os.environ.get("ARM_API", "")
    if ":" not in arm_api:
        raise ValueError("ARM_API must be set as username:apiKey")
    username, api_key = arm_api.split(":", 1)
    return (username, api_key)


# ===================== DIRECT FETCH FOR MAPPED PRODUCTS ===================== #
def fetch_errors_by_product_id(server,
                               product_id,
                               product_name,
                               releases,
                               platforms,
                               min_failing_builds,
                               owner,
                               *,
                               area: str = "Unified",
                               application_id: int = 4,
                               timeout: int = 30):
    """
    Fetch CDCARM failures for a product by ProductId, supporting Unified or Standalone 'area'.

    - Unified:   /api/ErrorSummary/Product/{pid}/Release/{rid}/Platform/{plid}
    - Standalone: same endpoint but requires extra query params (mirrors the Reports link you shared)

    Returns a list of records in the same shape as fetch_core.fetch_arm_json() returns.
    """
    username, api_key = get_basic_auth()
    auth = (username, api_key)
    base = server.rstrip('/') + '/api'

    def get_json(url):
        resp = requests.get(url, auth=auth, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    # Resolve release/platform objects by name on this server
    try:
        rel_all = get_json(f"{base}/Release") or []
        pl_all  = get_json(f"{base}/Platform") or []
    except Exception:
        rel_all, pl_all = [], []

    rel_objs = [r for r in rel_all if r.get('Name') in releases]
    pl_objs  = [p for p in pl_all  if p.get('Name') in platforms]

    # Pre-encoded pieces from your working Standalone URL
    # filterCollection=MatchType=All&Filter0=Type:...RunTypeFilter,Operator:NOT_EQUAL,Value:7
    FILTER_COLLECTION = (
        "MatchType%3DAll%26"
        "Filter0%3DType%3AARM.WebFilters.TestResults.Filters.RunTypeFilter%2C"
        "Operator%3ANOT_EQUAL%2CValue%3A7"
    )
    # highlighterCollection=MatchType=All&Filter0=Type:...RunAgeHighlighter,Operator:GREATER_THAN_OR_EQUAL,Value:7
    HIGHLIGHTER_COLLECTION = (
        "MatchType%3DAll%26"
        "Filter0%3DType%3AARM.WebFilters.TestResults.Highlighters.RunAgeHighlighter%2C"
        "Operator%3AGREATER_THAN_OR_EQUAL%2CValue%3A7"
    )

    results = []
    for r in rel_objs:
        for pl in pl_objs:
            if area.lower() == "standalone":
                # 👇 Mirrors your updated Standalone Reports link semantics
                url = (
                    f"{base}/ErrorSummary/Product/{product_id}"
                    f"?applicationId={application_id}"
                    f"&releaseId={r['Id']}"
                    f"&platformId={pl['Id']}"
                    f"&officialOnly=False"
                    f"&filterCollection={FILTER_COLLECTION}"
                    f"&highlighterCollection={HIGHLIGHTER_COLLECTION}"
                    f"&chronicFailureThreshold=0"
                    f"&errorReport=True"
                    f"&noCache=False"
                    f"&showNonChronicFailures=True"
                    f"&releaseChanged=True"
                    f"&allPackages=True"
                )
            else:
                # Default Unified path
                url = f"{base}/ErrorSummary/Product/{product_id}/Release/{r['Id']}/Platform/{pl['Id']}"

            try:
                es = get_json(url) or []
            except Exception:
                es = []

            for e in es:
                if e.get('Result') == 'PASS':
                    continue
                if owner.lower() != 'all' and e.get('Owner') != owner:
                    continue
                if not any(f.get('NumFailingBuilds', 0) >= min_failing_builds for f in e.get('FailureInfo', [])):
                    continue

                # Failure message
                try:
                    msg_json = get_json(f"{base}/TestResultXML/{e['TestResultId']}") or {}
                except Exception:
                    msg_json = {}
                raw = msg_json.get('message', '') if isinstance(msg_json, dict) else str(msg_json)
                cleaned = re.sub(r"[\r\n]+", ' ', raw).strip()

                # Investigation (optional)
                try:
                    inv_list = get_json(
                        f"{base}/Investigation/Test/{e['TestId']}/Release/{r['Id']}/Platform/{pl['Id']}"
                    ) or []
                except Exception:
                    inv_list = []

                rec = {
                    'Product':  product_name,
                    'Release':  r['Name'],
                    'Platform': pl['Name'],
                    'TestName': e.get('TestName'),
                    'Result':   e.get('Result'),
                    'FailureMessage': cleaned,
                    'Owner': e.get('Owner'),
                    'HasInvestigation': bool(inv_list)
                }
                if inv_list:
                    inv0 = inv_list[0]
                    work_item = re.sub(r'\D', '', str(inv0.get('WorkItemId', '')) or "")
                    rec['InvestigationReport'] = inv0.get('Name', '')
                    rec['WorkItemId'] = work_item

                results.append(rec)

    return results



# ===================== FETCH CDCARM ===================== #
@app.route("/fetch_cdcarm", methods=["POST"])
def fetch_cdcarm():
    try:
        data = request.get_json()

        # Extract params (unchanged)
        products    = data.get("products", ["DISCO"])
        releases    = data.get("releases", ["25.2"])
        platforms   = data.get("platforms", ["Windows"])
        min_failing = int(data.get("min_failing_builds", 2))
        owner       = "all"  # Always fetch ALL owners

        # Unique output path (unchanged)
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id   = uuid.uuid4().hex[:6]
        file_name   = f"cdcarm_results_{timestamp}_{unique_id}.json"
        output_path = os.path.join(tempfile.gettempdir(), file_name)

        # Classify products: normal (Unified) vs mapped (e.g., PRIME)
        mapped = [p for p in products if p in PRODUCT_SOURCE_MAP]
        normal = [p for p in products if p not in PRODUCT_SOURCE_MAP]

        print("📥 CDCARM API Request Parameters:")
        print(f"    Products: {products}  (normal={normal}, mapped={mapped})")
        print(f"    Releases: {releases}")
        print(f"    Platforms: {platforms}")
        print(f"    Min Failing Builds: {min_failing}")
        print(f"    Output Path: {output_path}")

        # ---- Fetch phase: preserve original behavior for normal products ----
        all_results = []

        if normal:
            # Original code path using fetch_core.fetch_arm_json (no signature changes)
            normal_results = fetch_arm_json(
                server=BASE_API_URL,
                products=normal,
                releases=releases,
                platforms=platforms,
                min_failing_builds=min_failing,
                owner=owner,
                output_path=None,      # we'll write after merging
                print_enabled=False
            )
            all_results.extend(normal_results or [])

        # Direct-by-ProductId path for mapped products (e.g., PRIME in Standalone UI)
        for pname in mapped:
            cfg = PRODUCT_SOURCE_MAP[pname]
            pid = cfg["product_id"]
            srv = cfg.get("server", BASE_API_URL)
            area = cfg.get("area", "Unified")
            mapped_results = fetch_errors_by_product_id(
                server=srv,
                product_id=pid,
                product_name=pname,
                releases=releases,
                platforms=platforms,
                min_failing_builds=min_failing,
                owner=owner,
                area=area,            # 👈 new
                application_id=4      # stays 4 (from your working URL); make configurable if needed
            )
            all_results.extend(mapped_results or [])

        print(f"✅ Records fetched: {len(all_results)}")

        # Write merged JSON for downstream steps
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        # ---------- Run ARM (L1) and TFS (L2) in parallel ----------
        with open(output_path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)
        _, targets_for_l2 = extract_error_messages(raw_json)

        product_name = products[0] if products else "default"
        tfs_matches_all = []

        with ThreadPoolExecutor(max_workers=2) as ex:
            fut_l1 = ex.submit(run_prediction, output_path)                      # ARM L1
            fut_l2 = ex.submit(run_bug_fallback, targets_for_l2, product_name)   # TFS L2

            merged_summary = fut_l1.result()
            try:
                tfs_matches_all = fut_l2.result() or []
            except FileNotFoundError as e:
                print(f"⚠️ Skipping Level-2: {e}")
                tfs_matches_all = []
            except Exception as e:
                print(f"⚠️ Level-2 error (continuing without TFS): {e}")
                tfs_matches_all = []

        # ---------- Unpack ARM L1 result (and flatten clusters) ----------
        predicted = []
        unpredicted_flat = []

        if isinstance(merged_summary, dict):
            mode = merged_summary.get("mode")
            print(f"🔄 Prediction Mode: {mode}")
            if mode == "predicted_with_clusters":
                predicted = merged_summary.get("predicted", [])
                clusters  = merged_summary.get("clusters", [])  # list[list[dict]]
                unpredicted_flat = [item for grp in clusters for item in grp]  # flatten
            elif mode in ("clustered_only", "clustered"):
                print("⚠ No predictions found. Returning all tests as 'unpredicted'.")
                unpredicted_flat = all_results
        elif isinstance(merged_summary, list):
            predicted = merged_summary

        # Tag + flags (preserve existing behavior)
        for t in predicted:
            t["Source"] = "ARM"
            t["MatchedSource"] = "LEVEL_1"
            t.setdefault("HasInvestigation", False)

        for t in unpredicted_flat:
            t.setdefault("HasInvestigation", False)

        for t in tfs_matches_all:
            t["Source"] = "TFS"
            t.setdefault("MatchedSource", "TFS_BUG")
            t.setdefault("HasInvestigation", False)

        # ---------- Build side-by-side choices per TestName (no auto-merge) ----------
        def score_of(x):
            try:
                return float(x.get("ConfidenceScore", 0.0))
            except Exception:
                return 0.0

        best_arm_by_name = {}
        for t in predicted:
            name = t.get("TestName")
            if not name:
                continue
            if name not in best_arm_by_name or score_of(t) > score_of(best_arm_by_name[name]):
                best_arm_by_name[name] = t

        best_tfs_by_name = {}
        for t in tfs_matches_all:
            name = t.get("TestName")
            if not name:
                continue
            if name not in best_tfs_by_name or score_of(t) > score_of(best_tfs_by_name[name]):
                best_tfs_by_name[name] = t

        # universe = every original test name we fetched from ARM
        all_names = {t.get("TestName") for t in all_results if t.get("TestName")}
        side_by_side = []
        for name in sorted(all_names):
            side_by_side.append({
                "TestName": name,
                "ARM": best_arm_by_name.get(name),
                "TFS": best_tfs_by_name.get(name)
            })

        # ---------- Keep your original "merged best" for backward-compat ----------
        used_test_names = {}
        for test in (list(best_arm_by_name.values()) + list(best_tfs_by_name.values())):
            tn = test.get("TestName")
            sc = score_of(test)
            if tn not in used_test_names or sc > score_of(used_test_names[tn]):
                used_test_names[tn] = test
        final_predicted = list(used_test_names.values())

        # Unpredicted list = those with no ARM or TFS suggestion
        predicted_names = set(t["TestName"] for t in final_predicted if t.get("TestName"))
        final_unpredicted = [t for t in all_results if t.get("TestName") not in predicted_names]
        for t in final_unpredicted:
            t.setdefault("HasInvestigation", False)

        # ---------- Response: keep old keys, add new keys for UI choice ----------
        return jsonify({
            "data_type": "prediction_table",
            # legacy keys (no feature loss)
            "predicted": final_predicted,
            "unpredicted": final_unpredicted,
            # new: show both sources so user can choose
            "side_by_side": side_by_side,
            # optional: full source lists if UI wants separate tabs
            "arm_predicted": predicted,
            "tfs_matches": tfs_matches_all,
            "sources_used": ["ARM"] + (["TFS"] if tfs_matches_all else [])
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
