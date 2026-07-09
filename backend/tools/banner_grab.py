"""Banner grabbing - connect to service and read initial response."""
import socket


def run(target: str) -> dict:
    target = (target or "").strip()
    if not target or ":" not in target:
        return {"error": "Format: host:port (e.g. example.com:80)"}

    host, _, port_s = target.partition(":")
    try:
        port = int(port_s)
    except ValueError:
        return {"error": "Invalid port."}

    banner = ""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, port))
            # For HTTP-ish ports, send a minimal request
            if port in (80, 8080, 8000, 8888):
                s.sendall(b"HEAD / HTTP/1.0\r\nHost: " + host.encode() + b"\r\n\r\n")
            elif port in (443, 8443):
                return {"error": "For HTTPS ports use SSL Scanner instead."}
            data = s.recv(2048)
            banner = data.decode("utf-8", errors="replace").strip()
    except socket.gaierror:
        return {"error": f"Could not resolve host: {host}"}
    except (socket.timeout, ConnectionRefusedError) as e:
        return {"error": f"Connection failed: {e}"}

    # Detect common services
    service = "Unknown"
    lower = banner.lower()
    if "ssh" in lower[:20]:
        service = "SSH"
    elif "ftp" in lower[:20]:
        service = "FTP"
    elif "smtp" in lower[:20]:
        service = "SMTP"
    elif "http" in lower[:20]:
        service = "HTTP"
    elif "mysql" in lower[:20]:
        service = "MySQL"

    return {
        "target": f"{host}:{port}",
        "detected_service": service,
        "banner": banner[:1500],
        "summary": f"{service} service detected on {host}:{port}"
    }
