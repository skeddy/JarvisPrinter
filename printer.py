import socket
from datetime import datetime

PRINTER_IP = "192.168.1.200"
PRINTER_PORT = 9100


def send_to_printer(data):
    with socket.create_connection(
        (PRINTER_IP, PRINTER_PORT),
        timeout=5
    ) as sock:
        sock.sendall(data)


def text(value):
    return value.encode("cp437", errors="replace")


def print_receipt(message, title="JARVIS"):
    ESC = b"\x1b"
    GS = b"\x1d"

    data = b""

    # Initialise
    data += ESC + b"@"

    # Centre
    data += ESC + b"a\x01"

    # Bold + double size
    data += ESC + b"E\x01"
    data += ESC + b"!\x30"
    data += text(title)
    data += b"\n"

    # Reset formatting
    data += ESC + b"!\x00"
    data += ESC + b"E\x00"

    data += b"\n"

    # Left aligned
    data += ESC + b"a\x00"
    data += text(message)
    data += b"\n\n"

    # Separator
    data += text("--------------------------------")
    data += b"\n"

    # Date/time
    data += text("Printed: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    data += b"\n"
    # Space before cut
    data += b"\n\n\n\n\n"

    # Full cut
    data += GS + b"V\x01"

    send_to_printer(data)