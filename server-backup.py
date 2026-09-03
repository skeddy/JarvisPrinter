from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from printer import print_receipt


HOST = "0.0.0.0"
PORT = 8080


def print_shopping_list(items):
    lines = [
        "SHOPPING LIST",
        "",
    ]

    for item in items:
        lines.append("[ ] " + item)

    message = "\n".join(lines)

    print_receipt(message, "SHOPPING")


class PrintHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        try:
            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(content_length)
            request = json.loads(body)

            # -----------------------------
            # Standard print
            # -----------------------------

            if self.path == "/print":

                message = request.get("text", "")
                title = request.get("title", "JARVIS")

                if not message:
                    self.send_error(400, "Missing 'text'")
                    return

                print_receipt(message, title)

                self.send_json({
                    "success": True,
                    "message": "Printed successfully"
                })

                return

            # -----------------------------
            # Shopping list
            # -----------------------------

            if self.path == "/shopping":

                items = request.get("items", [])

                if not items:
                    self.send_error(
                        400,
                        "Missing 'items'"
                    )
                    return

                print_shopping_list(items)

                self.send_json({
                    "success": True,
                    "message": "Shopping list printed"
                })

                return

            # -----------------------------
            # Unknown endpoint
            # -----------------------------

            self.send_error(404, "Not Found")

        except Exception as e:

            self.send_json({
                "success": False,
                "error": str(e)
            }, status=500)

    def send_json(self, data, status=200):

        response = json.dumps(data).encode()

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json"
        )
        self.send_header(
            "Content-Length",
            str(len(response))
        )
        self.end_headers()

        self.wfile.write(response)

    def log_message(self, format, *args):

        print(
            f"[SERVER] {self.address_string()} - "
            f"{format % args}"
        )


print("================================")
print("       JARVIS PRINT SERVER")
print("================================")
print()
print(f"Listening on port {PORT}")
print("Printer: 192.168.1.200:9100")
print()
print("Endpoints:")
print("  POST /print")
print("  POST /shopping")
print()
print("Press CTRL+C to stop.")
print()

server = HTTPServer((HOST, PORT), PrintHandler)
server.serve_forever()