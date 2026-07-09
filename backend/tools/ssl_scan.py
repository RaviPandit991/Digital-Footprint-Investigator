"""SSL/TLS scanner with vulnerability checks and grade."""
import socket
import ssl
from datetime import datetime, timezone


WEAK_CIPHERS = ["RC4", "DES", "3DES", "MD5", "NULL", "EXP", "ADH", "AECDH"]
WEAK_PROTOCOLS = ["SSLv2", "SSLv3", "TLSv1", "TLSv1.1"]


def _get_cert(host: str, port: int, verify: bool = False):
    ctx = ssl.create_default_context()
    if not verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=8) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock.getpeercert(), ssock.cipher(), ssock.version()


def _try_protocol(host: str, port: int, protocol) -> bool:
    """Try to establish a connection using a specific TLS version."""
    ctx = ssl.SSLContext(protocol)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return True
    except (ssl.SSLError, OSError, ValueError):
        return False


def _test_protocols(host: str, port: int) -> dict:
    """Test which TLS/SSL versions the server supports."""
    protocols = {}
    version_map = [
        ("SSLv3", getattr(ssl, "PROTOCOL_SSLv3", None)),
        ("TLSv1", getattr(ssl, "PROTOCOL_TLSv1", None)),
        ("TLSv1.1", getattr(ssl, "PROTOCOL_TLSv1_1", None)),
        ("TLSv1.2", getattr(ssl, "PROTOCOL_TLSv1_2", None)),
    ]
    for name, proto in version_map:
        if proto is None:
            protocols[name] = "unavailable"
        else:
            protocols[name] = "supported" if _try_protocol(host, port, proto) else "not supported"
    return protocols


def _grade(days_left, tls_version, cipher_name, protocols, self_signed) -> dict:
    """Calculate a simple A-F grade like SSL Labs."""
    score = 100
    issues = []

    if tls_version in ("SSLv3", "TLSv1"):
        score -= 50; issues.append(f"Uses deprecated {tls_version}")
    elif tls_version == "TLSv1.1":
        score -= 30; issues.append("Uses TLS 1.1 (deprecated)")
    elif tls_version == "TLSv1.2":
        pass
    elif tls_version == "TLSv1.3":
        score += 5

    for weak in WEAK_CIPHERS:
        if cipher_name and weak in cipher_name:
            score -= 20; issues.append(f"Weak cipher: {weak}")

    if protocols.get("SSLv3") == "supported":
        score -= 40; issues.append("SSLv3 enabled (POODLE)")
    if protocols.get("TLSv1") == "supported":
        score -= 20; issues.append("TLS 1.0 enabled")
    if protocols.get("TLSv1.1") == "supported":
        score -= 10; issues.append("TLS 1.1 enabled")

    if days_left is not None:
        if days_left < 0:
            score -= 100; issues.append("EXPIRED certificate")
        elif days_left < 15:
            score -= 30; issues.append(f"Expires in {days_left} days")
        elif days_left < 30:
            score -= 10; issues.append(f"Expires in {days_left} days")

    if self_signed:
        score -= 30; issues.append("Self-signed certificate")

    grade = ("A+" if score >= 100 else "A" if score >= 85 else "B" if score >= 70
             else "C" if score >= 55 else "D" if score >= 40 else "F")
    return {"grade": grade, "score": max(0, min(100, score)), "issues": issues}


def run(target: str, mode: str = "basic") -> dict:
    """SSL/TLS scan.

    mode: 'basic' (cert info + cipher) or 'advanced' (+ protocol enumeration + grade)
    """
    target = (target or "").strip()
    if not target:
        return {"error": "Host required."}
    if ":" in target:
        host, _, port_s = target.partition(":")
        try:
            port = int(port_s)
        except ValueError:
            return {"error": "Invalid port."}
    else:
        host, port = target, 443

    try:
        cert, cipher, version = _get_cert(host, port, verify=False)
    except (socket.gaierror, socket.timeout, ConnectionRefusedError) as e:
        return {"error": f"Connection failed: {e}"}
    except ssl.SSLError as e:
        return {"error": f"SSL error: {e}"}

    # Check if verifies against system CAs
    self_signed = False
    try:
        _get_cert(host, port, verify=True)
    except (ssl.SSLError, ssl.SSLCertVerificationError):
        self_signed = True
    except Exception:
        pass

    def _parse_dt(s):
        try:
            return datetime.strptime(s, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        except Exception:
            return None

    subject = dict(x[0] for x in cert.get("subject", []))
    issuer = dict(x[0] for x in cert.get("issuer", []))
    not_after_dt = _parse_dt(cert.get("notAfter", ""))
    days_left = (not_after_dt - datetime.now(timezone.utc)).days if not_after_dt else None

    result = {
        "target": f"{host}:{port}",
        "tls_version": version,
        "cipher_suite": cipher[0] if cipher else None,
        "cipher_bits": cipher[2] if cipher else None,
        "subject": subject,
        "issuer": issuer,
        "not_before": cert.get("notBefore"),
        "not_after": cert.get("notAfter"),
        "days_until_expiry": days_left,
        "self_signed": self_signed,
        "serial_number": cert.get("serialNumber"),
        "san": [x[1] for x in cert.get("subjectAltName", [])],
        "mode": mode,
    }

    if mode == "advanced":
        protocols = _test_protocols(host, port)
        result["protocols_supported"] = protocols
        result["grade"] = _grade(days_left, version, cipher[0] if cipher else "",
                                  protocols, self_signed)
    else:
        result["grade"] = _grade(days_left, version, cipher[0] if cipher else "",
                                  {}, self_signed)

    grade_str = result["grade"]["grade"]
    result["summary"] = (f"Grade {grade_str} | TLS {version} | "
                         f"Issuer: {issuer.get('organizationName', 'Unknown')} | "
                         f"Expires in {days_left} days")
    return result
