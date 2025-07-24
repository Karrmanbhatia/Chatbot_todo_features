# actions/fetch_core.py
import os
import json
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.auth import HTTPBasicAuth

# Read ARM_API (username:apiKey)
ARM_API = os.environ.get("ARM_API", "")
if ":" not in ARM_API:
    raise ValueError("❌ ARM_API must be set as 'username:apiKey' in environment variables.")

USERNAME, API_KEY = ARM_API.split(":", 1)
AUTH = HTTPBasicAuth(USERNAME, API_KEY)

def fetch_arm_json(server, products, releases, platforms,
                   min_failing_builds, owner, output_path=None,
                   print_enabled=False, max_workers=50):
    """
    Fetch CDCARM errors, filter by product/release/platform/owner/min_builds,
    include failure messages and investigation details in parallel, and return JSON.
    """

    base = server.rstrip('/') + '/api'

    # Helper: perform authenticated GET requests
    def auth_get(url):
        resp = requests.get(url, auth=AUTH, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # Fetch metadata
    products_data = auth_get(f"{base}/Product")
    releases_data = auth_get(f"{base}/Release")
    platforms_data = auth_get(f"{base}/Platform")

    # Filter by input
    prods = [p for p in products_data if p['Name'] in products]
    rels = [r for r in releases_data if r['Name'] in releases]
    plats = [p for p in platforms_data if p['Name'] in platforms]

    # Helper to process a single error record
    def process_error(e, p, r, pl):
        msg_url = f"{base}/TestResultXML/{e['TestResultId']}"
        raw_msg = auth_get(msg_url)
        raw = raw_msg.get('message', '') if isinstance(raw_msg, dict) else str(raw_msg)
        cleaned = re.sub(r"[\r\n]+", ' ', raw).strip()

        inv_url = f"{base}/Investigation/Test/{e['TestId']}/Release/{r['Id']}/Platform/{pl['Id']}"
        inv_list = auth_get(inv_url) or []

        record = {
            'Product': p['Name'],
            'Release': r['Name'],
            'Platform': pl['Name'],
            'TestName': e.get('TestName'),
            'Result': e.get('Result'),
            'FailureMessage': cleaned,
            'Owner': e.get('Owner'),
            'HasInvestigation': bool(inv_list)
        }

        if inv_list:
            inv = inv_list[0]
            work_item = re.sub(r'\D', '', str(inv.get('WorkItemId', '')) or "")
            record['InvestigationReport'] = inv.get('Name', '')
            record['WorkItemId'] = work_item
            
        return record

    # Collect error records
    tasks = []
    for p in prods:
        for r in rels:
            for pl in plats:
                url = f"{base}/ErrorSummary/Product/{p['Id']}/Release/{r['Id']}/Platform/{pl['Id']}"
                errors = auth_get(url) or []

                for e in errors:
                    if e.get('Result') == 'PASS':
                        continue
                    if owner.lower() != 'all' and e.get('Owner') != owner:
                        continue
                    if not any(f.get('NumFailingBuilds', 0) >= min_failing_builds for f in e.get('FailureInfo', [])):
                        continue
                    tasks.append((e, p, r, pl))

    # Execute in parallel
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_error, e, p, r, pl): (e, p, r, pl) for e, p, r, pl in tasks}
        for future in as_completed(futures):
            try:
                rec = future.result()
                if rec:
                    results.append(rec)
            except Exception:
                continue

    # ✅ DEBUG OUTPUT
    print(f"✅ DEBUG: Total records fetched = {len(results)}")
    if results:
        print("📝 Sample record:")
        print(json.dumps(results[0], indent=2))
    else:
        print("⚠️ No data fetched. Check filter values or connectivity.")

    # Write to output file if needed
    if output_path:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    return results
