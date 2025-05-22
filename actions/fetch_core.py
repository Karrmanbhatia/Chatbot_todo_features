import os
import json
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_arm_json(server, products, releases, platforms,
                   min_failing_builds, owner, output_path=None,
                   print_enabled=False, max_workers=50):
    """
    Fetch CDCARM errors, filter by product/release/platform/owner/min_builds,
    include failure messages and investigation details in parallel, and return JSON.
    """

    base = server.rstrip('/') + '/api'

    # Fetch metadata
    products_data = requests.get(f"{base}/Product", timeout=30).json()
    releases_data = requests.get(f"{base}/Release", timeout=30).json()
    platforms_data = requests.get(f"{base}/Platform", timeout=30).json()

    # Filter by input
    prods = [p for p in products_data if p['Name'] in products]
    rels = [r for r in releases_data if r['Name'] in releases]
    plats = [p for p in platforms_data if p['Name'] in platforms]

    # Helper to process a single error record
    def process_error(e, p, r, pl):
        msg_url = f"{base}/TestResultXML/{e['TestResultId']}"
        raw_msg = requests.get(msg_url, timeout=30).json()
        raw = raw_msg.get('message', '') if isinstance(raw_msg, dict) else str(raw_msg)
        cleaned = re.sub(r"[\r\n]+", ' ', raw).strip()

        inv_url = f"{base}/Investigation/Test/{e['TestId']}/Release/{r['Id']}/Platform/{pl['Id']}"
        inv_list = requests.get(inv_url, timeout=30).json() or []

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
                errors = requests.get(url, timeout=30).json() or []

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
