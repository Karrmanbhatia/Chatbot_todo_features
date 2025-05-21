#!/usr/bin/env python3
import os
import json
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_arm_json(server, products, releases, platforms,
                   min_failing_builds, owner, output_path,
                   print_enabled=True, max_workers=50):
    """
    Fetch CDCARM errors, filter by product/release/platform/owner/min_builds,
    include failure messages and investigation details in parallel, and save as JSON.
    """
    if print_enabled:
        print(f"→ Fetching metadata from {server}/api/... ")

    # 1) fetch metadata lists
    base = server.rstrip('/') + '/api'
    products_data = requests.get(f"{base}/Product").json()
    releases_data = requests.get(f"{base}/Release").json()
    platforms_data = requests.get(f"{base}/Platform").json()

    # 2) filter metadata by user choices
    prods = [p for p in products_data if p['Name'] in products]
    rels = [r for r in releases_data if r['Name'] in releases]
    plats = [p for p in platforms_data if p['Name'] in platforms]

    # helper to process a single error record
    def process_error(e, p, r, pl):
        # fetch and clean failure message
        msg_url = f"{base}/TestResultXML/{e['TestResultId']}"
        if print_enabled:
            print(f"→ GET {msg_url}")
        raw_msg = requests.get(msg_url).json()
        raw = raw_msg.get('message', '') if isinstance(raw_msg, dict) else str(raw_msg)
        cleaned = re.sub(r"[\r\n]+", ' ', raw).strip()

        # fetch investigation info
        inv_url = f"{base}/Investigation/Test/{e['TestId']}/Release/{r['Id']}/Platform/{pl['Id']}"
        if print_enabled:
            print(f"→ GET {inv_url}")
        inv_list = requests.get(inv_url).json() or []

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
            work_item = re.sub(r'\D', '', str(inv.get('WorkItemId', '')))
            record['InvestigationReport'] = inv.get('Name', '')
            record['WorkItemId'] = work_item
        return record

    # 3) collect all tasks
    tasks = []
    for p in prods:
        for r in rels:
            for pl in plats:
                summary_url = f"{base}/ErrorSummary/Product/{p['Id']}/Release/{r['Id']}/Platform/{pl['Id']}"
                if print_enabled:
                    print(f"→ GET {summary_url}")
                errors = requests.get(summary_url).json() or []

                for e in errors:
                    if e.get('Result') == 'PASS':
                        continue
                    if owner.lower() != 'all' and e.get('Owner') != owner:
                        continue
                    if not any(f.get('NumFailingBuilds', 0) >= min_failing_builds for f in e.get('FailureInfo', [])):
                        continue
                    tasks.append((e, p, r, pl))

    # 4) execute in parallel
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(process_error, e, p, r, pl): (e, p, r, pl)
            for e, p, r, pl in tasks
        }
        for future in as_completed(future_to_task):
            try:
                rec = future.result()
                results.append(rec)
            except Exception as ex:
                e, p, r, pl = future_to_task[future]
                if print_enabled:
                    print(f"Error processing {e['TestName']} in {p['Name']}/{r['Name']}/{pl['Name']}: {ex}")

    # 5) write results to JSON
    dir_name = os.path.dirname(output_path) or '.'
    os.makedirs(dir_name, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    if print_enabled:
        print(f"✔ Wrote {len(results)} records (with+without investigation) to {output_path}")


def main():
    # interactive inputs
    server = input("Server URL [https://cdcarm.win.ansys.com]: ").strip() or "https://cdcarm.win.ansys.com"
    prods_input = input("Products (comma-separated) [DISCO]: ").strip() or "DISCO"
    rels_input = input("Releases (comma-separated) [25.2]: ").strip() or "25.2"
    plats_input = input("Platforms (comma-separated) [Windows]: ").strip() or "Windows"
    min_input = input("Min failing builds [2]: ").strip() or "2"
    owner = input("Owner filter [all]: ").strip() or "all"
    output_path = input("Output JSON path [./filtered_errors.json]: ").strip() or "./filtered_errors.json"
    print_choice = input("Show console prints? [Y/n]: ").strip().lower()
    print_enabled = (print_choice != 'n')

    # parse inputs
    products = [x.strip() for x in prods_input.split(',') if x.strip()]
    releases = [x.strip() for x in rels_input.split(',') if x.strip()]
    platforms = [x.strip() for x in plats_input.split(',') if x.strip()]
    try:
        min_failing_builds = int(min_input)
    except ValueError:
        min_failing_builds = 2

    fetch_arm_json(
        server, products, releases, platforms,
        min_failing_builds, owner, output_path,
        print_enabled
    )

if __name__ == "__main__":
    main()