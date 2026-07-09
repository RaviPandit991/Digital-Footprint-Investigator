"""Port scanning via TCP connect scan (stdlib only)."""
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPC", 135: "MSRPC", 139: "NetBIOS",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS", 587: "SMTP",
    993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
    2049: "NFS", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 5985: "WinRM", 6379: "Redis", 8000: "HTTP-Alt",
    8080: "HTTP-Proxy", 8443: "HTTPS-Alt", 8888: "HTTP-Alt",
    9200: "Elasticsearch", 11211: "Memcached", 27017: "MongoDB"
}


def _check_port(host: str, port: int, timeout: float = 1.0):
    """Return (port, is_open, service_hint)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            return port, result == 0, COMMON_PORTS.get(port, "Unknown")
    except (socket.gaierror, OSError):
        return port, False, COMMON_PORTS.get(port, "Unknown")


def run(target: str, ports: str = "common", timeout: float = 1.0) -> dict:
    """Scan the target host on the given ports.

    ports: 'common' (default), 'top1000', or comma-separated list like '22,80,443'.
    """
    target = (target or "").strip()
    if not target:
        return {"error": "Target required."}

    # Resolve
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        return {"error": f"Could not resolve host: {target}"}

    # Build port list
    if ports == "common":
        port_list = sorted(COMMON_PORTS.keys())
    elif ports == "top1000":
        port_list = list(range(1, 1001))
    else:
        try:
            port_list = sorted({int(p.strip()) for p in ports.split(",") if p.strip()})
        except ValueError:
            return {"error": "Invalid port list. Use 'common', 'top1000', or comma-separated integers."}

    open_ports = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(_check_port, ip, p, timeout) for p in port_list]
        for future in as_completed(futures):
            port, is_open, service = future.result()
            if is_open:
                open_ports.append({"port": port, "service": service})

    open_ports.sort(key=lambda x: x["port"])

    return {
        "target": target,
        "ip": ip,
        "ports_scanned": len(port_list),
        "open_ports": open_ports,
        "summary": f"{len(open_ports)} open port(s) found out of {len(port_list)} scanned."
    }
