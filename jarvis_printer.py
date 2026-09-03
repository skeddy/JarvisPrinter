import socket
import sys
from datetime import datetime

PRINTER_IP = "192.168.1.200"
PRINTER_PORT = 9100


def send_to_printer(data):
    with socket.create_connection((PRINTER_IP, PRINTER_PORT), timeout=5) as sock:
        sock.sendall(data)


def text(value):
    return value.encode("cp437", errors="replace")


def print_receipt(message):
    ESC = b"\x1b"
    GS = b"\x1d"

    data = b""

    # Initialise printer
    data += ESC + b"@"

    # Centre
    data += ESC + b"a\x01"

    # Bold + double height/width
    data += ESC + b"E\x01"
    data += ESC + b"!\x30"
    data += text("JARVIS")
    data += b"\n"

    # Reset formatting
    data += ESC + b"!\x00"
    data += ESC + b"E\x00"

    data += b"\n"

    # Left aligned message
    data += ESC + b"a\x00"
    data += text(message)
    data += b"\n\n"

    # Separator
    data += text("--------------------------------")
    data += b"\n"

    # Date/time
    data += text(datetime.now().strftime("%d/%m/%Y %H:%M"))
    data += b"\n"

    # Extra space before cutter
    data += b"\n\n\n\n\n"

    # Full cut
    data += GS + b"V\x01"

    send_to_printer(data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python jarvis_printer.py "Message to print"')
        sys.exit(1)

    message = " ".join(sys.argv[1:])

    try:
        print_receipt(message)
        print("Printed successfully.")
    except Exception as e:
        print(f"Printer error: {e}")
        sys.exit(1)