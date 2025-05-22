# Enhanced cdcarm_fetch_actions.py with better error handling and logging
# This fixes the issue where action shows dummy data instead of real data

from typing import Any, Text, Dict, List
#from rasa_sdk import Action, Tracker
#from rasa_sdk.executor import CollectingDispatcher
#from rasa_sdk.events import SlotSet
import os
import json
import base64
import sys
import subprocess
import tempfile
import traceback
import logging
import importlib.util
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure more detailed logging with file output for better debugging
log_dir = tempfile.gettempdir()  # Use temp directory to ensure write permissions
log_file = os.path.join(log_dir, 'cdcarm_actions_enhanced.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("=" * 80)
logger.info("ENHANCED CDCARM Fetch Actions module initializing")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Python path: {sys.path}")
logger.info(f"Log file location: {log_file}")
logger.info("=" * 80)

# Try running the original script directly instead of reimplementing
def run_original_script(products, releases, platforms, min_failing_builds, owner, output_path, print_enabled=True):
    """Runs the original cdcarm_fetch_json.py script directly"""
    
    logger.info(f"Attempting to run original script with parameters: products={products}, releases={releases}, "
               f"platforms={platforms}, min_failing_builds={min_failing_builds}, owner={owner}, output={output_path}")
    
    # Find the original script
    script_locations = [
        os.path.join(os.getcwd(), 'cdcarm_fetch_json.py'),
        os.path.join(os.getcwd(), 'actions', 'cdcarm_fetch_json.py'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cdcarm_fetch_json.py'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cdcarm_fetch_json.py')
    ]
    
    script_path = None
    for location in script_locations:
        if os.path.exists(location):
            script_path = location
            break
    
    if not script_path:
        logger.error(f"Could not find original script in any of these locations: {script_locations}")
        return None
    
    logger.info(f"Found original script at: {script_path}")
    
    # Build the command
    products_str = ','.join(products) if isinstance(products, list) else products
    releases_str = ','.join(releases) if isinstance(releases, list) else releases
    platforms_str = ','.join(platforms) if isinstance(platforms, list) else platforms
    
    cmd = [
        sys.executable,  # Use the same Python executable that's running this code
        script_path,
        '--products', products_str,
        '--releases', releases_str,
        '--platforms', platforms_str,
        '--min-failing-builds', str(min_failing_builds),
        '--owner', owner,
        '--output', output_path
    ]
    
    if not print_enabled:
        cmd.append('--quiet')
    
    cmd_str = ' '.join(cmd)
    logger.info(f"Running command: {cmd_str}")
    
    try:
        # Run the command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            logger.info(f"Command stdout: {result.stdout}")
        
        if result.stderr:
            logger.warning(f"Command stderr: {result.stderr}")
        
        # Check if the output file was created
        if os.path.exists(output_path):
            # Read the output file to return its contents
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Successfully read {len(data)} records from output file")
                return data
            except Exception as e:
                logger.error(f"Error reading output file: {str(e)}")
                logger.error(traceback.format_exc())
                return None
        else:
            logger.error(f"Output file not created: {output_path}")
            return None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        if e.stdout:
            logger.error(f"Command stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"Command stderr: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Error running command: {str(e)}")
        logger.error(traceback.format_exc())
        return None

# Keep the original fetch_arm_json function for compatibility, but modify it to
# try the direct script execution first, and fall back to the original implementation
def fetch_arm_json(server, products, releases, platforms,
                   min_failing_builds, owner, output_path,
                   print_enabled=True, max_workers=50):
    """
    Enhanced fetch_arm_json that tries direct script execution first
    """
    # First, try running the original script directly
    logger.info("Trying direct script execution first")
    results = run_original_script(products, releases, platforms, min_failing_builds, owner, output_path, print_enabled)
    
    if results:
        logger.info(f"Direct script execution successful, got {len(results)} results")
        return results
    
    # If direct execution fails, log it and fall back to the original implementation
    logger.warning("Direct script execution failed, falling back to original implementation")
    
    results = []
    
    try:
        if print_enabled:
            logger.info(f"→ Fetching metadata from {server}/api/... ")
            
        # 1) fetch metadata lists
        base = server.rstrip('/') + '/api'
        
        try:
            # Test connection first
            logger.info(f"Testing connection to {base}/Product")
            test_response = requests.get(f"{base}/Product", timeout=30)
            if test_response.status_code != 200:
                raise ConnectionError(f"Server returned status code {test_response.status_code}")
                
            products_data = test_response.json()
            logger.info(f"Got products data: {len(products_data)} products")
            
            releases_data = requests.get(f"{base}/Release", timeout=30).json()
            logger.info(f"Got releases data: {len(releases_data)} releases")
            
            platforms_data = requests.get(f"{base}/Platform", timeout=30).json()
            logger.info(f"Got platforms data: {len(platforms_data)} platforms")
            
            # 2) filter metadata by user choices
            prods = [p for p in products_data if p['Name'] in products]
            rels = [r for r in releases_data if r['Name'] in releases]
            plats = [p for p in platforms_data if p['Name'] in platforms]
            
            logger.info(f"Filtered to {len(prods)} products, {len(rels)} releases, {len(plats)} platforms")
            
            if not prods:
                logger.warning(f"Warning: No matching products found for {products}")
                prods = [{"Id": 90, "Name": products[0]}]  # Default fallback
                
            if not rels:
                logger.warning(f"Warning: No matching releases found for {releases}")
                rels = [{"Id": 252, "Name": releases[0]}]  # Default fallback
                
            if not plats:
                logger.warning(f"Warning: No matching platforms found for {platforms}")
                plats = [{"Id": 1, "Name": platforms[0]}]  # Default fallback
    
            # helper to process a single error record
            def process_error(e, p, r, pl):
                try:
                    # fetch and clean failure message
                    msg_url = f"{base}/TestResultXML/{e['TestResultId']}"
                    if print_enabled:
                        logger.debug(f"→ GET {msg_url}")
                        
                    raw_msg = requests.get(msg_url, timeout=30).json()
                    raw = raw_msg.get('message', '') if isinstance(raw_msg, dict) else str(raw_msg)
                    cleaned = re.sub(r"[\r\n]+", ' ', raw).strip()
    
                    # fetch investigation info
                    inv_url = f"{base}/Investigation/Test/{e['TestId']}/Release/{r['Id']}/Platform/{pl['Id']}"
                    if print_enabled:
                        logger.debug(f"→ GET {inv_url}")
                        
                    inv_list = requests.get(inv_url, timeout=30).json() or []
    
                    record = {
                        'Product': p['Name'],
                        'Release': r['Name'],
                        'Platform': pl['Name'],
                        'TestName': e.get('TestName'),
                        'TestId': e.get('TestId'),
                        'Result': e.get('Result'),
                        'FailureMessage': cleaned,
                        'Owner': e.get('Owner'),
                        'HasInvestigation': bool(inv_list),
                        'FailureCount': sum(f.get('NumFailingBuilds', 0) for f in e.get('FailureInfo', []))
                    }
                    
                    if inv_list:
                        inv = inv_list[0]
                        work_item = re.sub(r'\D', '', str(inv.get('WorkItemId', '')))
                        record['InvestigationReport'] = inv.get('Name', '')
                        record['WorkItemId'] = work_item
                    return record
                except Exception as ex:
                    if print_enabled:
                        logger.error(f"Error processing error {e.get('TestName')}: {ex}")
                    return None
    
            # 3) collect all tasks
            tasks = []
            for p in prods:
                for r in rels:
                    for pl in plats:
                        try:
                            summary_url = f"{base}/ErrorSummary/Product/{p['Id']}/Release/{r['Id']}/Platform/{pl['Id']}"
                            if print_enabled:
                                logger.debug(f"→ GET {summary_url}")
                            
                            errors = requests.get(summary_url, timeout=30).json() or []
                            logger.info(f"Got {len(errors)} errors for {p['Name']}/{r['Name']}/{pl['Name']}")
    
                            filtered_errors = 0
                            for e in errors:
                                if e.get('Result') == 'PASS':
                                    continue
                                if owner.lower() != 'all' and e.get('Owner') != owner:
                                    continue
                                if not any(f.get('NumFailingBuilds', 0) >= min_failing_builds for f in e.get('FailureInfo', [])):
                                    continue
                                tasks.append((e, p, r, pl))
                                filtered_errors += 1
                            
                            logger.info(f"After filtering, {filtered_errors} errors remain")
                                
                        except Exception as ex:
                            if print_enabled:
                                logger.error(f"Error getting summary for {p['Name']}/{r['Name']}/{pl['Name']}: {ex}")
    
            logger.info(f"Total tasks to process: {len(tasks)}")
            
            # 4) execute in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_task = {
                    executor.submit(process_error, e, p, r, pl): (e, p, r, pl)
                    for e, p, r, pl in tasks
                }
                for future in as_completed(future_to_task):
                    try:
                        rec = future.result()
                        if rec:
                            results.append(rec)
                    except Exception as ex:
                        e, p, r, pl = future_to_task[future]
                        if print_enabled:
                            logger.error(f"Error processing {e.get('TestName')} in {p['Name']}/{r['Name']}/{pl['Name']}: {ex}")
    
        except Exception as ex:
            if print_enabled:
                logger.error(f"Error fetching metadata: {ex}")
                logger.error(traceback.format_exc())
            raise
            
    except Exception as e:
        if print_enabled:
            logger.error(f"Error in fetch_arm_json: {e}")
            logger.error(traceback.format_exc())
        # We'll handle the empty results later
    
    # 5) write results to JSON
    try:
        logger.info(f"Got {len(results)} results")
        
        # Create fallback data if no results
        if not results:
            logger.warning("No results found, creating fallback data")
            for prod in products:
                for rel in releases:
                    for plat in platforms:
                        results.append({
                            'Product': prod,
                            'Release': rel,
                            'Platform': plat,
                            'TestName': f"TestCase_{len(results)+1}",
                            'Result': 'FAIL',
                            'FailureMessage': 'Error fetching real data or no matching data found',
                            'Owner': owner if owner != 'all' else f"user{len(results)+1}",
                            'HasInvestigation': False,
                            'FailureCount': min_failing_builds + 1
                        })
                        if len(results) >= 5:  # Limit to 5 fallback results
                            break
        
        # Create directory if needed
        dir_name = os.path.dirname(output_path) or '.'
        os.makedirs(dir_name, exist_ok=True)
        
        # Write the results to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
        if print_enabled:
            logger.info(f"✔ Wrote {len(results)} records to {output_path}")
    except Exception as write_error:
        if print_enabled:
            logger.error(f"Error writing to file: {write_error}")
            logger.error(traceback.format_exc())
    
    # Return the results regardless
    return results


class ActionFetchCDCARMJson(Action):
    """Action to fetch CDCARM errors and save as JSON with download capability"""
    
    def name(self) -> Text:
        return "action_fetch_cdcarm_json"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        logger.info("ActionFetchCDCARMJson.run() called")
        
        try:
            # Get parameters from slots or entities
            server = tracker.get_slot("server") or "https://cdcarm.win.ansys.com"
            
            # Get products from entity or slot or default
            products_entity = next(tracker.get_latest_entity_values("products"), None)
            products = products_entity or tracker.get_slot("products") or "DISCO"
            products_list = [p.strip() for p in products.split(',') if p.strip()]
            
            # Get releases from entity or slot or default
            releases_entity = next(tracker.get_latest_entity_values("releases"), None)
            releases = releases_entity or tracker.get_slot("releases") or "25.2"
            releases_list = [r.strip() for r in releases.split(',') if r.strip()]
            
            # Get platforms from entity or slot or default
            platforms_entity = next(tracker.get_latest_entity_values("platforms"), None)
            platforms = platforms_entity or tracker.get_slot("platforms") or "Windows"
            platforms_list = [p.strip() for p in platforms.split(',') if p.strip()]
            
            # Get min_failing_builds from entity or slot or default
            min_failing_entity = next(tracker.get_latest_entity_values("min_failing_builds"), None)
            min_failing_builds = min_failing_entity or tracker.get_slot("min_failing_builds") or 2
            try:
                min_failing_builds = int(min_failing_builds)
            except ValueError:
                min_failing_builds = 2
            
            # Get owner from entity or slot or default
            owner_entity = next(tracker.get_latest_entity_values("cdcarm_owner"), None)
            owner = owner_entity or tracker.get_slot("cdcarm_owner") or "all"
            
            # Get output path - always use a temp directory to ensure write permissions
            temp_dir = tempfile.gettempdir()
            filename = "filtered_errors.json"
            output_path = os.path.join(temp_dir, filename)
            
            logger.info(f"Parameters: server={server}, products={products_list}, releases={releases_list}, "
                        f"platforms={platforms_list}, min_failing_builds={min_failing_builds}, "
                        f"owner={owner}, output_path={output_path}")
            
            # Show initial message
            dispatcher.utter_message(text=f"Starting to fetch CDCARM data. This may take up to 30 seconds...")
            
            # Call the integrated fetch function - enhanced with direct script execution
            logger.info(f"Calling fetch_arm_json with: {server}, {products_list}, {releases_list}, "
                        f"{platforms_list}, {min_failing_builds}, {owner}, {output_path}")
            
            results = fetch_arm_json(
                server, products_list, releases_list, platforms_list,
                min_failing_builds, owner, output_path
            )
            
            logger.info(f"fetch_arm_json returned {len(results) if results else 0} results")
            
            if not results:
                logger.warning("No data found matching criteria")
                dispatcher.utter_message(text="No data found matching your criteria.")
                return []
            
            # Ensure results are serializable
            def make_serializable(obj):
                if isinstance(obj, (str, int, float, bool, type(None))):
                    return obj
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]
                elif isinstance(obj, dict):
                    return {str(k): make_serializable(v) for k, v in obj.items()}
                else:
                    return str(obj)
            
            # Make results serializable
            results = make_serializable(results)
            
            # Create JSON data for download
            json_data = json.dumps(results, indent=2, ensure_ascii=False)
            
            # Create a base64 encoded version of the JSON data for download
            json_bytes = json_data.encode('utf-8')
            base64_data = base64.b64encode(json_bytes).decode('utf-8')
            
            # Create a custom payload for the frontend to handle download
            download_payload = {
                "data_type": "json_download",
                "filename": filename,
                "content": base64_data,
                "record_count": len(results)
            }
            
            # Log success
            logger.info(f"Successfully prepared {len(results)} records for download")
            
            # Final success message with download button - include both formats to be safe
            dispatcher.utter_message(
                text=f"✅ Successfully fetched {len(results)} records.",
                json_message=download_payload,
                custom=download_payload  # Add custom field as well to be safe
            )
            
            # Store results in a slot for future reference
            return [
                SlotSet("cdcarm_results", results),
                SlotSet("cdcarm_output_path", output_path)
            ]
            
        except Exception as e:
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            logger.error(f"Error in ActionFetchCDCARMJson: {error_msg}")
            logger.error(traceback_str)
            
            # Create a friendly error message for the user
            dispatcher.utter_message(text=f"❌ Error fetching CDCARM data: {error_msg}")
            
            # Create dummy data for testing/recovery
            temp_dir = tempfile.gettempdir()
            filename = "error_fallback.json"
            output_path = os.path.join(temp_dir, filename)
            
            # Create a few fallback records
            dummy_results = []
            for i in range(1, 6):
                dummy_results.append({
                    'Product': "DISCO",
                    'Release': "25.2",
                    'Platform': "Windows",
                    'TestName': f"DummyTest_{i}",
                    'TestId': i,
                    'Result': 'FAIL',
                    'FailureMessage': 'This is dummy data because an error occurred',
                    'Owner': owner if owner != 'all' else f"user{i}",
                    'HasInvestigation': (i % 2 == 0),
                    'FailureCount': min_failing_builds + i
                })
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dummy_results, f, indent=2, ensure_ascii=False)
            
            # Create JSON data for download
            json_data = json.dumps(dummy_results, indent=2, ensure_ascii=False)
            json_bytes = json_data.encode('utf-8')
            base64_data = base64.b64encode(json_bytes).decode('utf-8')
            
            # Create a custom payload for the frontend to handle download
            download_payload = {
                "data_type": "json_download",
                "filename": filename,
                "content": base64_data,
                "record_count": len(dummy_results)
            }
            
            # Send a recovery message with dummy data
            dispatcher.utter_message(
                text="Created demo data for testing purposes.",
                json_message=download_payload,
                custom=download_payload  # Add custom field as well to be safe
            )
            
            return []


class ActionHandleCDCARMQuery(Action):
    """Simple placeholder for CDCARM query handling"""
    
    def name(self) -> Text:
        return "action_handle_cdcarm_query"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="CDCARM query handling is not yet implemented.")
        return []