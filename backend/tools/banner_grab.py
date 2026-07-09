"""Banner grabbing - single or multi-port with service detection."""
import socket
from concurrent.futures import ThreadPoolExecutor


def _grab(host: str, port: int, timeout: float = 5.0) -> dict:
    banner = ""
    error = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            if port in (80, 8080, 8000, 8888, 8081, 3000, 5000, 9000):
                s.sendall(b"HEAD / HTTP/1.0\r\nHost: " + host.encode() + b"\r\n\r\n")
            data = s.recv(2048)
            banner = data.decode("utf-8", errors="replace").strip()
    except socket.gaierror:
        error = "Could not resolve host"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        error = str(e)

    service = _detect_service(banner)
    return {
        "port": port,
        "service": service,
        "banner": banner[:1500] if banner else "",
        "error": error,
    }


def _detect_service(banner: str) -> str:
    if not banner:
        return "Unknown"
    lower = banner.lower()
    signatures = {
        "SSH":    ["ssh-"],
        "FTP":    ["220 ", "ftp"],
        "SMTP":   ["smtp", "postfix", "exim", "sendmail"],
        "HTTP":   ["http/", "server:"],
        "POP3":   ["pop3", "+ok"],
        "IMAP":   ["imap"],
        "MySQL":  ["mysql", "mariadb"],
        "PostgreSQL": ["postgresql"],
        "Redis":  ["redis"],
        "MongoDB":["mongodb"],
        "VNC":    ["rfb "],
        "Telnet": ["telnet"],
        "RDP":    ["mstshash"],
        "NetBIOS":["smb", "netbios"],
    }
    for service, patterns in signatures.items():
        for p in patterns:
            if p in lower[:100]:
                return service
    return "Unknown"


def run(target: str, ports: str = "") -> dict:
    """Grab service banners.

    target: host or host:port
    ports: comma-separated list of ports (overrides port in target)
    """
    target = (target or "").strip()
    if not target:
        return {"error": "Target required."}

    host = target
    port_list = []
    if ":" in target and not ports:
        host, _, port_s = target.partition(":")
        try:
            port_list = [int(port_s)]
        except ValueError:
            return {"error": "Invalid port."}

    if ports:
        try:
            port_list = [int(p.strip()) for p in ports.split(",") if p.strip()]
        except ValueError:
            return {"error": "Invalid port list."}

    if not port_list:
        return {"error": "Provide port in target (host:port) or in ports option."}

    results = []
    with ThreadPoolExecutor(max_workers=min(10, len(port_list))) as ex:
        for r in ex.map(lambda p: _grab(host, p), port_list):
            results.append(r)

    successful = [r for r in results if r.get("banner")]
    return {
        "target": host,
        "ports_tested": len(port_list),
        "results": results,
        "summary": f"Grabbed {len(successful)}/{len(port_list)} banners from {host}"
    }
