"""Port scanning - TCP connect scan with modes, service detection, banner grabbing."""
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

# Top 1000 most common ports (nmap top-1000 style, subset for space)
TOP_1000_PORTS = sorted(set(list(COMMON_PORTS.keys()) + [
    7, 9, 13, 17, 19, 20, 26, 37, 42, 43, 49, 70, 79, 81, 82, 83, 84, 85, 88, 89,
    106, 113, 119, 123, 129, 137, 138, 144, 161, 179, 199, 211, 264, 306, 311,
    340, 389, 406, 407, 416, 417, 425, 427, 444, 458, 481, 497, 500, 512, 513,
    514, 515, 524, 541, 543, 544, 545, 548, 554, 555, 563, 585, 591, 593, 616,
    617, 631, 636, 646, 648, 666, 667, 668, 683, 687, 691, 700, 705, 711, 714,
    720, 722, 726, 749, 765, 777, 783, 787, 800, 801, 808, 843, 873, 880, 888,
    898, 900, 901, 902, 903, 911, 912, 981, 987, 990, 992, 999, 1000, 1001,
    1002, 1007, 1009, 1010, 1011, 1021, 1022, 1023, 1024, 1025, 1026, 1027,
    1028, 1029, 1030, 1050, 1080, 1099, 1100, 1214, 1234, 1241, 1300, 1311,
    1352, 1417, 1434, 1494, 1533, 1600, 1720, 1723, 1755, 1761, 1801, 1900,
    1935, 1998, 2000, 2001, 2002, 2005, 2020, 2100, 2103, 2105, 2106, 2107,
    2121, 2144, 2160, 2161, 2170, 2179, 2200, 2222, 2251, 2260, 2288, 2301,
    2323, 2366, 2381, 2382, 2383, 2393, 2394, 2399, 2401, 2492, 2500, 2522,
    2525, 2557, 2601, 2602, 2604, 2605, 2607, 2608, 2701, 2717, 2718, 2725,
    2800, 2809, 2811, 2869, 2875, 2909, 2910, 2920, 2967, 2968, 2998, 3000,
    3001, 3003, 3005, 3006, 3007, 3011, 3013, 3017, 3030, 3031, 3052, 3071,
    3128, 3168, 3211, 3221, 3260, 3261, 3268, 3269, 3283, 3300, 3301, 3306,
    3322, 3323, 3324, 3325, 3333, 3351, 3367, 3369, 3370, 3371, 3372, 3389,
    3390, 3404, 3476, 3493, 3517, 3527, 3546, 3551, 3580, 3659, 3689, 3690,
    3703, 3737, 3766, 3784, 3800, 3801, 3809, 3814, 3826, 3827, 3828, 3851,
    3869, 3871, 3878, 3880, 3889, 3905, 3914, 3918, 3920, 3945, 3971, 3986,
    3995, 3998, 4000, 4001, 4002, 4003, 4004, 4005, 4006, 4045, 4111, 4125,
    4126, 4129, 4224, 4242, 4279, 4321, 4343, 4443, 4444, 4445, 4446, 4449,
    4550, 4567, 4662, 4848, 4899, 4900, 4998, 5000, 5001, 5002, 5003, 5004,
    5009, 5030, 5033, 5050, 5051, 5054, 5060, 5061, 5080, 5087, 5100, 5101,
    5102, 5120, 5190, 5200, 5214, 5221, 5222, 5225, 5226, 5269, 5280, 5298,
    5357, 5405, 5414, 5431, 5440, 5500, 5510, 5544, 5550, 5555, 5560, 5566,
    5631, 5633, 5666, 5678, 5679, 5718, 5730, 5800, 5801, 5802, 5810, 5811,
    5815, 5822, 5825, 5850, 5859, 5862, 5877, 5901, 5902, 5903, 5904, 5906,
    5907, 5910, 5911, 5915, 5922, 5925, 5950, 5952, 5959, 5960, 5961, 5962,
    5963, 5987, 5988, 5989, 5998, 5999, 6000, 6001, 6002, 6003, 6004, 6005,
    6006, 6007, 6009, 6025, 6059, 6100, 6101, 6106, 6112, 6123, 6129, 6156,
    6346, 6389, 6502, 6510, 6543, 6547, 6565, 6566, 6580, 6646, 6666, 6667,
    6668, 6669, 6689, 6692, 6699, 6779, 6788, 6789, 6792, 6839, 6881, 6901,
    6969, 7000, 7001, 7002, 7004, 7007, 7019, 7025, 7070, 7100, 7103, 7106,
    7200, 7201, 7402, 7435, 7443, 7496, 7512, 7625, 7627, 7676, 7741, 7777,
    7778, 7800, 7911, 7920, 7921, 7937, 7938, 7999, 8000, 8001, 8002, 8007,
    8008, 8009, 8010, 8011, 8021, 8022, 8031, 8042, 8045, 8080, 8081, 8082,
    8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090, 8093, 8099, 8100, 8180,
    8181, 8192, 8193, 8194, 8200, 8222, 8254, 8290, 8291, 8292, 8300, 8333,
    8383, 8400, 8402, 8443, 8500, 8600, 8649, 8651, 8652, 8654, 8701, 8800,
    8873, 8888, 8899, 8994, 9000, 9001, 9002, 9003, 9009, 9010, 9011, 9040,
    9050, 9071, 9080, 9081, 9090, 9091, 9099, 9100, 9101, 9102, 9103, 9110,
    9111, 9200, 9207, 9220, 9290, 9415, 9418, 9485, 9500, 9502, 9503, 9535,
    9575, 9593, 9594, 9595, 9618, 9666, 9876, 9877, 9878, 9898, 9900, 9917,
    9929, 9943, 9944, 9968, 9998, 9999, 10000, 10001, 10002, 10003, 10004,
    10009, 10010, 10012, 10024, 10025, 10082, 10180, 10215, 10243, 10566,
    10616, 10617, 10621, 10626, 10628, 10629, 10778, 11110, 11111, 11967,
    12000, 12174, 12265, 12345, 13456, 13722, 13782, 13783, 14000, 14238,
    14441, 14442, 15000, 15002, 15003, 15004, 15660, 15742, 16000, 16001,
    16012, 16016, 16018, 16080, 16113, 16992, 16993, 17877, 17988, 18040,
    18101, 18988, 19101, 19283, 19315, 19350, 19780, 19801, 19842, 20000,
    20005, 20031, 20221, 20222, 20828, 21571, 22939, 23502, 24444, 24800,
    25734, 25735, 26214, 27000, 27352, 27353, 27355, 27356, 27715, 28201,
    30000, 30718, 30951, 31038, 31337, 32768, 32769, 32770, 32771, 32772,
    32773, 32774, 32775, 32776, 32777, 32778, 32779, 32780, 32781, 32782,
    32783, 32784, 32785, 33354, 33899, 34571, 34572, 34573, 35500, 38292,
    40193, 40911, 41511, 42510, 44176, 44442, 44443, 44501, 45100, 48080,
    49152, 49153, 49154, 49155, 49156, 49157, 49158, 49159, 49160, 49161,
    49163, 49165, 49167, 49175, 49176, 49400, 49999, 50000, 50001, 50002,
    50003, 50006, 50300, 50389, 50500, 50636, 50800, 51103, 51493, 52673,
    52822, 52848, 52869, 54045, 54328, 55055, 55056, 55555, 55600, 56737,
    56738, 57294, 57797, 58080, 60020, 60443, 61532, 61900, 62078, 63331,
    64623, 64680, 65000, 65129, 65389
]))


def _check_port(host: str, port: int, timeout: float, grab_banner: bool):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            if result != 0:
                return None
            banner = ""
            if grab_banner:
                try:
                    s.settimeout(1.5)
                    # HTTP-like ports need a request
                    if port in (80, 8080, 8000, 8888, 8081, 8088, 3000, 5000):
                        s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                    banner = s.recv(512).decode("utf-8", errors="replace").strip()
                    banner = banner.split("\n")[0][:200]  # first line only
                except (socket.timeout, OSError):
                    pass
            return {
                "port": port,
                "service": COMMON_PORTS.get(port, "Unknown"),
                "banner": banner
            }
    except OSError:
        return None


def run(target: str, mode: str = "basic", timing: str = "normal",
        grab_banners: bool = False, custom_ports: str = "") -> dict:
    """Scan a target.

    mode: 'basic' (common ~35 ports), 'advanced' (top 1000), 'full' (1-65535), 'custom'
    timing: 'fast' (0.3s), 'normal' (1s), 'thorough' (2.5s)
    grab_banners: also grab service banner on open ports
    custom_ports: comma-separated list, e.g. "22,80,443,8000-8100"
    """
    target = (target or "").strip()
    if not target:
        return {"error": "Target required."}

    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        return {"error": f"Could not resolve host: {target}"}

    timeout_map = {"fast": 0.3, "normal": 1.0, "thorough": 2.5}
    timeout = timeout_map.get(timing, 1.0)

    # Build port list
    if mode == "basic":
        port_list = sorted(COMMON_PORTS.keys())
    elif mode == "advanced":
        port_list = TOP_1000_PORTS
    elif mode == "full":
        port_list = list(range(1, 65536))
    elif mode == "custom":
        port_list = _parse_ports(custom_ports)
        if not port_list:
            return {"error": "Invalid custom port list. Use comma-separated or ranges like 22,80,8000-8100"}
    else:
        return {"error": f"Unknown mode: {mode}"}

    workers = 200 if len(port_list) > 500 else 100
    open_ports = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_check_port, ip, p, timeout, grab_banners) for p in port_list]
        for f in as_completed(futures):
            r = f.result()
            if r:
                open_ports.append(r)

    open_ports.sort(key=lambda x: x["port"])

    return {
        "target": target,
        "ip": ip,
        "mode": mode,
        "timing": timing,
        "banners_enabled": grab_banners,
        "ports_scanned": len(port_list),
        "open_ports": open_ports,
        "summary": f"{len(open_ports)} open port(s) found / {len(port_list)} scanned "
                   f"({mode} mode, {timing} timing)"
    }


def _parse_ports(spec: str) -> list:
    if not spec:
        return []
    ports = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            try:
                a, b = chunk.split("-")
                for p in range(int(a), int(b) + 1):
                    if 1 <= p <= 65535:
                        ports.add(p)
            except ValueError:
                return []
        else:
            try:
                p = int(chunk)
                if 1 <= p <= 65535:
                    ports.add(p)
            except ValueError:
                return []
    return sorted(ports)
