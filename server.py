from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import os
import time
import threading
import urllib.request
import urllib.error

from printer import print_receipt


# ============================================================
# CONFIGURATION
# ============================================================

HOST = "0.0.0.0"
PORT = 8080

# Always locate files relative to server.py.
BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"
RESTART_FLAG = BASE_DIR / "restart.flag"


# ============================================================
# OPENAI CONFIGURATION
# ============================================================

OPENAI_KEY_FILE = BASE_DIR / "openai_key.txt"
OPENAI_MODEL = "gpt-5.6-luna"


def get_openai_key():

    if not OPENAI_KEY_FILE.exists():
        raise Exception(
            "OpenAI API key file not found."
        )

    key = OPENAI_KEY_FILE.read_text(
        encoding="utf-8"
    ).strip()

    if not key:
        raise Exception(
            "OpenAI API key file is empty."
        )

    return key


def ask_jarvis(question):

    api_key = get_openai_key()

    prompt = f"""
You are Jarvis, a friendly family AI assistant.

Answer the following question clearly and accurately.

The answer will be printed on a small thermal receipt, so:
- Keep it concise.
- Use short paragraphs.
- Avoid tables.
- Avoid markdown.
- Use simple language where possible.
- For questions from children, make the answer friendly and fun.
- Do not include a greeting unless appropriate.
- Aim for around 100-180 words maximum.

Question:
{question}
"""

    payload = {
        "model": OPENAI_MODEL,
        "input": prompt
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            response_data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="replace"
        )

        print(
            f"[OPENAI ERROR] {e.code}: {error_body}"
        )

        raise Exception(
            f"OpenAI returned HTTP {e.code}"
        )

    except Exception as e:

        print(
            f"[OPENAI CONNECTION ERROR] {e}"
        )

        raise Exception(
            "Could not connect to OpenAI."
        )


    # Extract the text from the Responses API.
    answer_parts = []

    for output in response_data.get(
        "output",
        []
    ):

        for content in output.get(
            "content",
            []
        ):

            if content.get(
                "type"
            ) == "output_text":

                text = content.get(
                    "text",
                    ""
                )

                if text:
                    answer_parts.append(
                        text
                    )


    answer = "\n".join(
        answer_parts
    ).strip()


    if not answer:

        raise Exception(
            "Jarvis received an empty answer."
        )


    return answer


# ============================================================
# SHOPPING LIST
# ============================================================

def print_shopping_list(items):

    lines = [
        "Don't forget to buy:",
        ""
    ]

    for item in items:
        lines.append(
            "[ ] " + str(item)
        )

    message = "\n".join(
        lines
    )

    print_receipt(
        message,
        "Shopping list"
    )


# ============================================================
# RESTART
# ============================================================

def restart_jarvis():

    print(
        "[JARVIS] Restart requested."
    )

    try:

        # Create a flag for jarvis.sh to detect.
        RESTART_FLAG.touch()

        print(
            f"[JARVIS] Restart flag created: "
            f"{RESTART_FLAG}"
        )

        return True

    except Exception as e:

        print(
            f"[JARVIS] Restart failed: {e}"
        )

        return False


# ============================================================
# HTTP HANDLER
# ============================================================

class PrintHandler(BaseHTTPRequestHandler):


    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def do_GET(self):

        if self.path != "/":

            self.send_error(
                404,
                "Not Found"
            )

            return

        try:

            with open(
                HTML_FILE,
                "rb"
            ) as file:

                content = file.read()


            self.send_response(
                200
            )

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(content))
            )

            # Prevent Edge from caching the page while we
            # are developing Jarvis.
            self.send_header(
                "Cache-Control",
                "no-cache, no-store, must-revalidate"
            )

            self.send_header(
                "Pragma",
                "no-cache"
            )

            self.send_header(
                "Expires",
                "0"
            )

            self.end_headers()

            self.wfile.write(
                content
            )

            self.wfile.flush()


        except Exception as e:

            print(
                f"[WEB ERROR] {e}"
            )

            self.send_error(
                500,
                str(e)
            )


    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    def do_POST(self):

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(
                content_length
            )

            request = json.loads(
                body
            )


            # =================================================
            # PRINT
            # =================================================

            if self.path == "/print":

                message = request.get(
                    "text",
                    ""
                )

                title = request.get(
                    "title",
                    "JARVIS"
                )

                if not message:

                    self.send_json(
                        {
                            "success": False,
                            "error": "Missing text"
                        },
                        400
                    )

                    return


                print_receipt(
                    message,
                    title
                )


                self.send_json(
                    {
                        "success": True,
                        "message": "Printed successfully"
                    }
                )

                return


            # =================================================
            # SHOPPING LIST
            # =================================================

            if self.path == "/shopping":

                items = request.get(
                    "items",
                    []
                )

                if not items:

                    self.send_json(
                        {
                            "success": False,
                            "error": "Missing items"
                        },
                        400
                    )

                    return


                print_shopping_list(
                    items
                )


                self.send_json(
                    {
                        "success": True,
                        "message": "Shopping list printed"
                    }
                )

                return


            # =================================================
            # ASK JARVIS
            # =================================================

            if self.path == "/ask":

                question = request.get(
                    "question",
                    ""
                ).strip()

                if not question:

                    self.send_json(
                        {
                            "success": False,
                            "error": "Please enter a question."
                        },
                        400
                    )

                    return


                print(
                    f"[JARVIS] Question: {question}"
                )


                try:

                    answer = ask_jarvis(
                        question
                    )


                    # Print the question and answer.
                    print_text = (
                        "Question:\n"
                        + question
                        + "\n\n"
                        + "Jarvis:\n"
                        + answer
                    )


                    print_receipt(
                        print_text,
                        "Ask Jarvis"
                    )


                    self.send_json(
                        {
                            "success": True,
                            "question": question,
                            "answer": answer
                        }
                    )


                except Exception as e:

                    print(
                        f"[JARVIS] Ask failed: {e}"
                    )

                    self.send_json(
                        {
                            "success": False,
                            "error": str(e)
                        },
                        500
                    )

                return


            # =================================================
            # RESTART JARVIS
            # =================================================

            if self.path == "/restart":

                success = restart_jarvis()


                if not success:

                    self.send_json(
                        {
                            "success": False,
                            "error": "Unable to restart Jarvis"
                        },
                        500
                    )

                    return


                self.send_json(
                    {
                        "success": True,
                        "message": "Jarvis is restarting"
                    }
                )


                # Shut down the HTTP server cleanly.
                def shutdown_server():

                    time.sleep(
                        0.5
                    )

                    server.shutdown()


                threading.Thread(
                    target=shutdown_server,
                    daemon=True
                ).start()

                return


            # =================================================
            # UNKNOWN ENDPOINT
            # =================================================

            self.send_error(
                404,
                "Not Found"
            )


        except json.JSONDecodeError:

            self.send_json(
                {
                    "success": False,
                    "error": "Invalid JSON"
                },
                400
            )


        except Exception as e:

            print(
                f"[REQUEST ERROR] {e}"
            )

            try:

                self.send_json(
                    {
                        "success": False,
                        "error": str(e)
                    },
                    500
                )

            except Exception:

                pass


    # --------------------------------------------------------
    # JSON RESPONSE
    # --------------------------------------------------------

    def send_json(
        self,
        data,
        status=200
    ):

        response = json.dumps(
            data
        ).encode("utf-8")


        self.send_response(
            status
        )

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.send_header(
            "Cache-Control",
            "no-cache"
        )

        self.end_headers()


        self.wfile.write(
            response
        )

        self.wfile.flush()


    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    def log_message(
        self,
        format,
        *args
    ):

        print(
            f"[SERVER] "
            f"{self.address_string()} - "
            f"{format % args}"
        )


# ============================================================
# START SERVER
# ============================================================

print(
    "================================"
)

print(
    "       JARVIS PRINT CENTRE"
)

print(
    "================================"
)

print()

print(
    f"Web interface: http://localhost:{PORT}"
)

print(
    f"Server directory: {BASE_DIR}"
)

print(
    "Printer: 192.168.1.200:9100"
)

print()

print(
    "Endpoints:"
)

print(
    "  GET  /"
)

print(
    "  POST /print"
)

print(
    "  POST /shopping"
)

print(
    "  POST /ask"
)

print(
    "  POST /restart"
)

print()

print(
    "Press CTRL+C to stop."
)

print()


# ============================================================
# HTTP SERVER
# ============================================================

server = HTTPServer(
    (HOST, PORT),
    PrintHandler
)

try:

    server.serve_forever()

finally:

    server.server_close()