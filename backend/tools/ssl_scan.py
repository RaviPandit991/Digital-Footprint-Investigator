"""SSL/TLS certificate inspection."""
import socket
import ssl
from datetime import datetime, timezone


def run(target: str) -> dict:
    target = (target or "").strip()
    if not target:
        return {"error": "Host required (e.g. example.com or example.com:443)."}

    if ":" in target:
        host, _, port_s = target.partition(":")
        try:
            port = int(port_s)
        except ValueError:
            return {"error": "Invalid port."}
    else:
        host, port = target, 443

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((host, port), timeout=8) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version()
    except (socket.gaierror, socket.timeout, ConnectionRefusedError) as e:
        return {"error": f"Connection failed: {e}"}
    except ssl.SSLError as e:
        return {"error": f"SSL error: {e}"}
    except Exception as e:
        return {"error": f"Scan failed: {e}"}

    def _parse_dt(s):
        try:
            return datetime.strptime(s, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            return s

    subject = dict(x[0] for x in cert.get("subject", []))
    issuer = dict(x[0] for x in cert.get("issuer", []))
    not_before = _parse_dt(cert.get("notBefore", ""))
    not_after = _parse_dt(cert.get("notAfter", ""))

    # Days remaining
    days_left = None
    try:
        exp = datetime.strptime(cert.get("notAfter", ""), "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        days_left = (exp - datetime.now(timezone.utc)).days
    except Exception:
        pass

    sans = [x[1] for x in cert.get("subjectAltName", [])]

    return {
        "target": f"{host}:{port}",
        "tls_version": version,
        "cipher_suite": cipher[0] if cipher else None,
        "cipher_bits": cipher[2] if cipher else None,
        "subject": subject,
        "issuer": issuer,
        "not_before": not_before,
        "not_after": not_after,
        "days_until_expiry": days_left,
        "serial_number": cert.get("serialNumber"),
        "san": sans,
        "summary": f"TLS {version} | Issued by {issuer.get('organizationName', 'Unknown')} | Expires in {days_left} days"
    }
