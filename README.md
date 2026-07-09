# Digital Footprint Investigator

A full-featured OSINT toolkit with a modern web UI and Python Flask backend.
Investigate digital identities across 22 tools spanning **active reconnaissance** and **passive intelligence gathering**.

> **For authorized security research and educational use only.**

---

## Features

### Active (8 tools) — direct target interaction
| Tool | Description |
| --- | --- |
| Port Scanning | Concurrent TCP connect scan (common ports or custom range) |
| DNS Enumeration | A, AAAA, MX, NS, TXT, CNAME, SOA records |
| Subdomain Enumeration | Certificate Transparency logs via crt.sh |
| WHOIS Lookup | Domain registration & ownership |
| Directory Bruteforce | Built-in wordlist of 50+ common paths |
| Web Crawler | Links, forms, emails, external hosts |
| SSL/TLS Scanner | Cert details, cipher, expiry, SANs |
| Banner Grabbing | Service fingerprinting via TCP banner |

### Passive (14 tools) — non-intrusive intelligence
| Tool | Description | API Key Needed |
| --- | --- | --- |
| Authentication | Manage API keys for external services | — |
| Username Lookup | Check username across 40+ platforms | No |
| Email Investigation | Syntax, MX, disposable, Gravatar, breaches | Optional (HIBP) |
| Domain Investigation | WHOIS + DNS + reputation | Optional (VirusTotal) |
| IP Investigation | Geolocation, ASN, abuse reports | Optional (AbuseIPDB) |
| Phone Investigation | Carrier, region, line type, timezone | No |
| Metadata Extraction | EXIF/GPS from images, PDF metadata | No |
| Website Analysis | Tech stack, headers, cookies, security | No |
| Social Media Search | Aggregated search links + username lookup | No |
| Data Breach Check | Password (k-anonymity) + email breaches | Optional (HIBP) |
| Reverse Image Search | Search links for 6 engines | No |
| Google Dorking | 18 dork templates + optional live search | Optional (Google CSE) |
| Public Records | Multi-jurisdiction registry search | No |
| Dark Web Monitor | Ahmia.fi Tor index search | No |

---

## Professional Features

- **Investigation Cases** — All tool results are grouped under a persistent case (SQLite). Switch, rename, delete cases from the header.
- **Entity Correlation** — Every tool auto-extracts entities (emails, IPs, domains, subdomains, usernames, GPS coordinates, ports, tech, CVEs) and suggests next tools to run against them.
- **PDF Report Export** — One-click professional multi-page PDF with cover page, executive summary, entity index, per-tool findings, and SHA-256 chain-of-custody.
- **Command Palette (Ctrl+K)** — VS Code style quick launcher for tools, cases, and actions with fuzzy search + keyboard navigation.
- **Dark / Light Theme** — Toggle in header, respects OS preference, persists across sessions.
- **Docker Ready** — Single `docker compose up` launches the entire stack.

## Setup

### Option A: Docker (one command)
```bash
docker compose up
```
Then open http://localhost:5000. Data (cases, keys) persists in `./backend/data/`.

### Option B: Manual Python install
```bash
cd Digital-Footprint-Investigator
pip install -r backend/requirements.txt
python -m backend.app
```

You should see:
```
============================================================
  Digital Footprint Investigator
  Starting on http://localhost:5000
  Tools loaded: 22
============================================================
```

### 3. Open the UI
Visit **http://localhost:5000** in any modern browser.

---

## Optional: Configure API keys

Some tools return richer data with API keys. Open the **Passive → Authentication** card to configure:

| Service | Free tier | Get key |
| --- | --- | --- |
| HaveIBeenPwned | $3.95/month | https://haveibeenpwned.com/API/Key |
| VirusTotal | Free (500 req/day) | https://www.virustotal.com/gui/join-us |
| AbuseIPDB | Free (1000 req/day) | https://www.abuseipdb.com/register |
| Google Custom Search | Free (100 req/day) | https://developers.google.com/custom-search |
| Shodan / Hunter.io / TinEye | Free tiers | — |

Keys are stored locally in `backend/data/api_keys.json` and never leave your machine.

---

## Project Structure

```
Digital-Footprint-Investigator/
├── index.html              # Frontend
├── style.css
├── script.js
├── backend/
│   ├── app.py              # Flask entrypoint (python -m backend.app)
│   ├── config.py           # API key storage
│   ├── requirements.txt
│   ├── data/               # Auto-created: api_keys.json
│   └── tools/              # One module per tool
│       ├── port_scan.py
│       ├── dns_enum.py
│       ├── ...
│       └── dark_web.py
└── README.md
```

---

## Legal & Ethics

Active tools (port scanning, directory bruteforcing, etc.) can be considered
unauthorized computer access in many jurisdictions. **Only use them against
systems you own or have explicit written permission to test.**

Passive tools rely on publicly available data but should still be used
responsibly and in compliance with local privacy laws (GDPR, CCPA, etc.).

---

## License

Educational / research use.
