import os
import sys
import json
import base64
import logging
import tempfile
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='direct_script_runner.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Path to your script - update this if needed
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cdcarm_fetch_json.py')

class ScriptHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        logging.info("POST request received")
        
        # Set headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get content length
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse form data
        form_data = {}
        for key_value in post_data.split('&'):
            if '=' in key_value:
                key, value = key_value.split('=', 1)
                form_data[key] = value
        
        logging.debug(f"Parsed form data: {form_data}")
        
        # Check action
        if form_data.get('action') != 'run_cdcarm_script':
            self.wfile.write(json.dumps({'error': 'Invalid action'}).encode('utf-8'))
            return
        
        # Get parameters
        products = form_data.get('products', 'DISCO')
        releases = form_data.get('releases', '25.2')
        platforms = form_data.get('platforms', 'Windows')
        min_failing_builds = form_data.get('min_failing_builds', '2')
        owner = form_data.get('owner', 'all')
        
        logging.info(f"Parameters: products={products}, releases={releases}, platforms={platforms}, "
                   f"min_failing_builds={min_failing_builds}, owner={owner}")
        
        # Check if script exists
        if not os.path.exists(SCRIPT_PATH):
            error_msg = f"Script not found at: {SCRIPT_PATH}"
            logging.error(error_msg)
            self.wfile.write(json.dumps({'error': error_msg}).encode('utf-8'))
            return
        
        # Create temp file for output
        output_file = os.path.join(tempfile.gettempdir(), f"cdcarm_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
        
        # Build command
        cmd = [
            sys.executable,  # Python executable
            SCRIPT_PATH,
            '--products', products,
            '--releases', releases,
            '--platforms', platforms,
            '--min-failing-builds', min_failing_builds,
            '--owner', owner,
            '--output', output_file,
            '--quiet'
        ]
        
        logging.info(f"Running command: {' '.join(cmd)}")
        
        try:
            # Run the command
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if process.stdout:
                logging.debug(f"Command stdout: {process.stdout}")
            
            if process.stderr:
                logging.warning(f"Command stderr: {process.stderr}")
            
            # Check if output file exists
            if not os.path.exists(output_file):
                error_msg = f"Output file was not created: {output_file}"
                logging.error(error_msg)
                self.wfile.write(json.dumps({'error': error_msg}).encode('utf-8'))
                return
            
            # Read the output file
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create response
            json_string = json.dumps(data, indent=2)
            base64_data = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
            
            response = {
                'data_type': 'json_download',
                'filename': 'cdcarm_data.json',
                'content': base64_data,
                'record_count': len(data)
            }
            
            logging.info(f"Successfully processed {len(data)} records")
            
            # Send response
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
            # Clean up
            try:
                os.unlink(output_file)
            except:
                pass
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with code {e.returncode}: {e.stderr}"
            logging.error(error_msg)
            self.wfile.write(json.dumps({'error': error_msg}).encode('utf-8'))
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.wfile.write(json.dumps({'error': error_msg}).encode('utf-8'))

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ScriptHandler)
    logging.info(f"Starting server on port {port}")
    print(f"Starting script runner server on port {port}")
    print(f"URL: http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        print("Server stopped")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run CDCARM script via web server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    args = parser.parse_args()
    
    run_server(args.port)