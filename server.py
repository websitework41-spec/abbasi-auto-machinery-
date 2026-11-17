import os
import sys
import json
import re
import mimetypes
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

os.makedirs(DATA_DIR, exist_ok=True)

VK = ["id","stockId","make","model","year","mileage","engine","transmission","fuel","drive","steering","color","doorsSeats","origin","category","status","description"]

def sync_index_html(inventory=None, company=None):
    try:
        if not os.path.exists(INDEX_PATH):
            return
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            html = f.read()

        if inventory is not None:
            # Build VR array
            vr_rows = []
            pool_tags = []
            for item in inventory:
                row = [
                    item.get("id", ""),
                    item.get("stockId", ""),
                    item.get("make", ""),
                    item.get("model", ""),
                    int(item.get("year", 2024)),
                    item.get("mileage", ""),
                    item.get("engine", ""),
                    item.get("transmission", ""),
                    item.get("fuel", ""),
                    item.get("drive", ""),
                    item.get("steering", ""),
                    item.get("color", ""),
                    item.get("doorsSeats", ""),
                    item.get("origin", "Japan"),
                    item.get("category", "cars"),
                    item.get("status", "Available"),
                    item.get("description", "")
                ]
                vr_rows.append(row)
                img_src = item.get("image", "hero.jpg")
                pool_tags.append(f'        <img data-id="{item.get("id")}" src="{img_src}" alt="{item.get("make")} {item.get("model")}" />')

            vr_json = json.dumps(vr_rows, ensure_ascii=False)
            html = re.sub(r"var VR\s*=\s*\[[\s\S]*?\];\s*</script>", f"var VR={vr_json};\n    </script>", html, count=1)
            
            # Update #x-pool
            pool_block = '<div id="x-pool" hidden>\n' + '\n'.join(pool_tags) + '\n      </div>'
            html = re.sub(r'<div id="x-pool" hidden>[\s\S]*?</div>\s*</div>', pool_block + '\n    </div>', html, count=1)

        if company is not None:
            cp_json = json.dumps(company, ensure_ascii=False)
            html = re.sub(r"var CP\s*=\s*\{[\s\S]*?\};\s*var LISTS", f"var CP={cp_json};\nvar LISTS", html, count=1)

        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            f.write(html)
        print("[Server] Successfully synced changes to index.html")
    except Exception as e:
        print(f"[Server] Error syncing index.html: {e}")

class AbbasiRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        # Enable CORS for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_json({"status": "online", "mode": "local", "base_dir": BASE_DIR})
            return

        if path == "/api/inventory":
            inv_file = os.path.join(DATA_DIR, "inventory.json")
            if os.path.exists(inv_file):
                with open(inv_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.send_json(data)
            else:
                self.send_json([])
            return

        if path == "/api/company":
            cp_file = os.path.join(DATA_DIR, "company.json")
            if os.path.exists(cp_file):
                with open(cp_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.send_json(data)
            else:
                self.send_json({})
            return

        if path == "/api/inquiries":
            inq_file = os.path.join(DATA_DIR, "inquiries.json")
            if os.path.exists(inq_file):
                with open(inq_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.send_json(data)
            else:
                self.send_json([])
            return

        if path == "/api/employees":
            emp_file = os.path.join(DATA_DIR, "employees.json")
            if os.path.exists(emp_file):
                with open(emp_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.send_json(data)
            else:
                self.send_json([])
            return

        if path == "/api/audit-logs":
            log_file = os.path.join(DATA_DIR, "audit_logs.json")
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.send_json(data)
            else:
                self.send_json([])
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        if path == "/api/inventory":
            try:
                data = json.loads(body.decode("utf-8"))
                inv_file = os.path.join(DATA_DIR, "inventory.json")
                with open(inv_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                sync_index_html(inventory=data)
                self.send_json({"success": True, "count": len(data)})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/company":
            try:
                data = json.loads(body.decode("utf-8"))
                cp_file = os.path.join(DATA_DIR, "company.json")
                with open(cp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                sync_index_html(company=data)
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/inquiries":
            try:
                item = json.loads(body.decode("utf-8"))
                inq_file = os.path.join(DATA_DIR, "inquiries.json")
                items = []
                if os.path.exists(inq_file):
                    with open(inq_file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                
                # Update existing or prepend new
                existing_idx = next((i for i, x in enumerate(items) if x.get("id") == item.get("id")), -1)
                if existing_idx >= 0:
                    items[existing_idx] = item
                else:
                    items.insert(0, item)

                with open(inq_file, "w", encoding="utf-8") as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                self.send_json({"success": True, "id": item.get("id")})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/upload":
            try:
                req = json.loads(body.decode("utf-8"))
                filename = req.get("filename", f"upload_{os.urandom(4).hex()}.jpg")
                # Sanitize filename
                filename = os.path.basename(filename)
                if not filename.startswith("v-"):
                    filename = "v-" + filename
                
                b64_data = req.get("data", "")
                if "," in b64_data:
                    b64_data = b64_data.split(",", 1)[1]

                import base64
                raw_bytes = base64.b64decode(b64_data)
                out_path = os.path.join(BASE_DIR, filename)
                with open(out_path, "wb") as f:
                    f.write(raw_bytes)

                self.send_json({"success": True, "filename": filename, "url": filename})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/employees":
            try:
                emp_data = json.loads(body.decode("utf-8"))
                emp_file = os.path.join(DATA_DIR, "employees.json")
                items = []
                if os.path.exists(emp_file):
                    with open(emp_file, "r", encoding="utf-8") as f:
                        items = json.load(f)

                if isinstance(emp_data, list):
                    items = emp_data
                else:
                    existing_idx = next((i for i, x in enumerate(items) if x.get("id") == emp_data.get("id")), -1)
                    if existing_idx >= 0:
                        items[existing_idx] = emp_data
                    else:
                        items.append(emp_data)

                with open(emp_file, "w", encoding="utf-8") as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                self.send_json({"success": True, "count": len(items)})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/audit-logs":
            try:
                log_entry = json.loads(body.decode("utf-8"))
                log_file = os.path.join(DATA_DIR, "audit_logs.json")
                logs = []
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        logs = json.load(f)

                if isinstance(log_entry, list):
                    logs = log_entry
                else:
                    logs.insert(0, log_entry)

                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
                self.send_json({"success": True, "count": len(logs)})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/api/inquiries":
            inq_id = qs.get("id", [""])[0]
            if not inq_id:
                self.send_json({"error": "id parameter required"}, status=400)
                return
            inq_file = os.path.join(DATA_DIR, "inquiries.json")
            if os.path.exists(inq_file):
                with open(inq_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                items = [x for x in items if x.get("id") != inq_id]
                with open(inq_file, "w", encoding="utf-8") as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
            self.send_json({"success": True})
            return

        if path == "/api/employees":
            emp_id = qs.get("id", [""])[0]
            if not emp_id:
                self.send_json({"error": "id parameter required"}, status=400)
                return
            emp_file = os.path.join(DATA_DIR, "employees.json")
            if os.path.exists(emp_file):
                with open(emp_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                items = [x for x in items if x.get("id") != emp_id]
                with open(emp_file, "w", encoding="utf-8") as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
            self.send_json({"success": True})
            return

        if path == "/api/audit-logs":
            log_file = os.path.join(DATA_DIR, "audit_logs.json")
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
            self.send_json({"success": True})
            return

        self.send_response(404)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

def run():
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    server_address = ("0.0.0.0", port)
    ThreadingHTTPServer.allow_reuse_address = True
    httpd = ThreadingHTTPServer(server_address, AbbasiRequestHandler)
    print(f"==================================================")
    print(f" Abbasi Auto Machinery Local Server Running")
    print(f" Main Site:    http://localhost:{port}/")
    print(f" Admin Panel:  http://localhost:{port}/admin.html")
    print(f"==================================================", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    run()
