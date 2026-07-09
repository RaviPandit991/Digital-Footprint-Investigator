# Digital Footprint Investigator — Viva Preparation Guide

**Author:** Ravi Pandit (12401796)
**Project:** Digital Footprint Investigator — OSINT toolkit

---

## 1. ELEVATOR PITCH (30 seconds — memorize this!)

> "Sir/Ma'am, Digital Footprint Investigator is an **OSINT toolkit** I built that helps security professionals investigate digital identities across the web. It has **22 tools** organized into **Active reconnaissance** (direct interaction like port scanning) and **Passive intelligence** (public data gathering like username lookups). The frontend is a **modern responsive web UI** with dark/light themes, and the backend is a **Python Flask API** that persists investigations in **SQLite**, auto-extracts entities across tools, generates **professional PDF reports**, and deploys with **one Docker command**."

---

## 2. WHAT IS OSINT?

**OSINT = Open Source Intelligence**

Gathering information from **publicly available sources** — social media, WHOIS records, DNS, breach databases, search engines, certificate transparency logs, etc.

**Key point:** No hacking, no unauthorized access. Just clever use of public data.

### Real-world use cases
- Cybersecurity teams during authorized penetration testing
- Digital forensics investigations
- Journalists tracing sources
- Law enforcement missing persons cases
- Corporate due diligence

---

## 3. ACTIVE vs PASSIVE RECONNAISSANCE (IMPORTANT!)

| Aspect | Active | Passive |
| --- | --- | --- |
| **Interaction** | Directly contacts target | Uses third-party public data |
| **Detection risk** | Target's IDS/firewall may notice | Invisible to target |
| **Legality** | Needs authorization | Generally safe |
| **Example** | Port scan, directory brute force | WHOIS, username lookup |
| **Speed** | Fast, direct | Depends on external APIs |

**Viva tip:** If asked "why two categories?" — say: *"To make investigators aware of the legal and stealth implications of each tool before running it."*

---

## 4. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────┐
│  Browser (HTML + CSS + Vanilla JS)      │  ← Frontend
│  index.html, style.css, script.js       │
└────────────────┬────────────────────────┘
                 │ HTTP/JSON
┌────────────────┴────────────────────────┐
│  Flask REST API (backend/app.py)        │  ← Backend
│  Routes: /api/run/<tool>, /api/cases    │
└────────┬──────────────┬─────────────────┘
         │              │
    ┌────▼────┐    ┌───▼──────────┐
    │ 22 Tool │    │ SQLite DB     │
    │ modules │    │ (dfi.db)      │
    └─────────┘    └──────────────┘
         │
    ┌────▼─────────────┐
    │ correlation.py   │  ← Entity extraction & suggestions
    │ report_generator │  ← PDF via reportlab
    └──────────────────┘
```

**Data flow when you click "Port Scan":**

1. Frontend collects target + options into JSON
2. `POST /api/run/port-scan` sent to Flask
3. Flask resolves or creates a case in SQLite
4. `tools/port_scan.py::run()` executes (threaded socket scan)
5. Result saved to `results` table
6. `correlation.py` extracts entities (open ports, IPs) → `entities` table
7. Suggestion engine builds "next tool" recommendations
8. JSON response includes result + `_meta` with case_id + suggestions
9. Frontend renders the result and shows suggestion chips

---

## 5. TECHNOLOGY STACK — WHY EACH CHOICE?

### Backend: Python 3.12 + Flask
- **Why Python?** Best ecosystem for OSINT libraries (dnspython, whois, phonenumbers, Pillow).
- **Why Flask (not Django)?** Django is overkill — we don't need admin UI, migrations, or templates. Flask keeps the backend under 250 lines.

### Database: SQLite (WAL mode)
- **Why SQLite?** Zero setup, single file, perfect for a single-user desktop tool. WAL (Write-Ahead Logging) lets us read while writing → better for multi-threaded Flask.
- **Why not PostgreSQL/MySQL?** No need. If we scale to multi-user later, migrating is straightforward.

### Frontend: Vanilla HTML/CSS/JS
- **Why no React/Vue?** No build step means anyone can run it. Also demonstrates fundamental JS skills.
- **CSS custom properties** for theme switching (`:root[data-theme="dark|light"]`).

### PDF: ReportLab
- **Why?** Most mature Python PDF library. Full control over layout, tables, styles.

### Concurrency: ThreadPoolExecutor
- **Why threads not async?** Python's GIL doesn't hurt I/O-bound work. Threads keep the tool modules simple synchronous code.

### Deployment: Docker + Docker Compose
- **Why?** One command deploys the whole stack. Cross-platform.

---

## 6. THE 22 TOOLS — HOW EACH WORKS

### ACTIVE TOOLS (8)

#### 1. Port Scan
- **How:** Python `socket` module does TCP connect scan (SYN+ACK check).
- **Concurrency:** `ThreadPoolExecutor` with 100–200 workers.
- **Modes:** Basic (35 common ports) → Advanced (top 1000) → Full (all 65535) → Custom range.
- **Timing:** Fast (0.3s timeout), Normal (1s), Thorough (2.5s).
- **Banner option:** After finding open port, send tiny probe to fingerprint the service.

**Viva Q:** *"How is this different from nmap?"* → *"nmap uses raw sockets and SYN scanning which needs root. My tool uses TCP connect (three-way handshake), which is slower but works from userspace on any OS."*

#### 2. DNS Enumeration
- **How:** `dnspython` library queries A, AAAA, MX, NS, TXT, CNAME, SOA (and CAA, DNSKEY, DS in Advanced).
- **Zone Transfer (AXFR):** Attempts `dig axfr @nameserver domain` equivalent — dangerous misconfiguration if it succeeds.
- **DNSSEC check:** Presence of DNSKEY records.
- **SPF/DMARC:** Extracted from TXT records at root and `_dmarc.` subdomain.

**Records explained:**
- `A` → IPv4 address
- `AAAA` → IPv6
- `MX` → Mail server (with priority)
- `NS` → Authoritative nameservers
- `TXT` → Arbitrary text (SPF, DKIM, verification)
- `CNAME` → Alias to another domain
- `SOA` → Start Of Authority (admin contact, refresh times)

#### 3. Subdomain Enumeration
- **How:** Queries **crt.sh** which indexes **Certificate Transparency logs** — every SSL cert issued by a CA is publicly logged.
- **Advanced mode:** Adds DNS bruteforce with a wordlist of ~150 common subdomain prefixes.
- **Live check:** After finding subdomains, resolves each and probes HTTPS.

**Viva Q:** *"What is Certificate Transparency?"* → *"CT is a public, append-only log of every SSL certificate ever issued. Google mandated it after fraudulent Symantec certs were issued in 2015. Since certs include all covered domains in the SAN field, we can discover subdomains by querying these logs."*

#### 4. WHOIS Lookup
- **How:** `python-whois` library queries the WHOIS registry.
- **Extracts:** Registrar, creation/expiration dates, name servers, admin/tech emails.
- **Caveat:** Many registries (Europe under GDPR) redact personal info now.

#### 5. Directory Bruteforce
- **How:** Sends HTTP HEAD requests to guess URL paths from a built-in wordlist.
- **Wordlists:** Small (25 common), Medium (130), Large (250 including CI/CD paths, actuator endpoints).
- **Extensions:** Optionally appends `.php`, `.bak`, `.old` etc.
- **Interesting status codes:** 200, 201, 301, 302, 307, 401, 403.

**Viva Q:** *"Why HEAD not GET?"* → *"HEAD returns headers only, no body. Much faster and lower bandwidth. We still get the status code and Content-Length header."*

#### 6. Web Crawler
- **How:** BeautifulSoup parses HTML, BFS crawl with configurable depth/pages.
- **Extracts:** Internal links, external hosts, emails (regex), phones, social profile URLs, JS files, forms.
- **Respects robots.txt:** Uses `RobotFileParser`.

#### 7. SSL/TLS Scanner
- **How:** Python `ssl` module wraps a socket, calls `getpeercert()`.
- **Grade calculation:** A+ to F based on:
  - TLS version (SSLv3 = major deduction)
  - Cipher strength (RC4/DES/MD5 = weak)
  - Certificate expiry (< 30 days = deduction)
  - Self-signed = deduction
- **Advanced mode:** Tests each TLS version (1.0, 1.1, 1.2, 1.3) individually.

**Viva Q:** *"Why is TLS 1.0 bad?"* → *"Vulnerable to BEAST attack. Deprecated by IETF in 2020. TLS 1.2 minimum, TLS 1.3 preferred."*

#### 8. Banner Grabbing
- **How:** Opens TCP socket, reads first bytes.
- **Fingerprinting:** Signature matching for SSH, FTP, SMTP, HTTP, MySQL, etc.
- **Multi-port:** Can scan multiple ports at once.

---

### PASSIVE TOOLS (14)

#### 1. Authentication (API Key Manager)
- **Purpose:** Configure API keys for external services (HIBP, Shodan, VirusTotal, etc.).
- **Storage:** Local JSON file `backend/data/api_keys.json` (gitignored, never leaves user's machine).

#### 2. Username Lookup
- **How:** Sends parallel HTTP GET to 90+ platform profile URLs, checks status codes.
- **Categories:** Social, dev, gaming, creative, professional, forum, misc.
- **Concurrency:** 15–20 threads for speed.
- **Special cases:** Some platforms return 200 with "no such user" text — we check the response body.

**Viva Q:** *"How do you know if a username exists?"* → *"For most platforms, `HTTP 200 = exists`. For platforms like HackerNews or Steam that return 200 for missing users, we scan the response body for specific error text like 'No such user'."*

#### 3. Email Investigation
- **Layers:**
  1. **Syntax check** — regex `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
  2. **MX record** — via dnspython (proves deliverability)
  3. **Disposable domain check** — hardcoded set of temp email domains
  4. **Free provider check** — Gmail/Outlook/Yahoo list
  5. **Gravatar profile** — MD5(email) → Gravatar API
  6. **HIBP breaches** — HaveIBeenPwned API (needs key)
  7. **Hunter.io verification** — deep verification (optional)

#### 4. Domain Investigation
- **Combines:** WHOIS + full DNS + VirusTotal reputation.
- **One-stop analysis** of any domain.

#### 5. IP Investigation
- **Geolocation:** `ip-api.com` (free, 45 req/min).
- **Reverse DNS:** `socket.gethostbyaddr()`.
- **Advanced:** Shodan (open ports/vulns), VirusTotal, AbuseIPDB.
- **Detects:** Proxy/VPN, hosting provider, Tor exit node.

#### 6. Phone Investigation
- **Library:** `phonenumbers` (Google's port).
- **Extracts:** Country code, region, carrier, line type (mobile/VoIP/fixed), timezones.
- **OSINT links:** Auto-builds search URLs for TrueCaller, Sync.me, NumLookup, BeenVerified.

#### 7. Metadata Extraction
- **Images:** `Pillow` extracts EXIF tags. **GPS is the big prize** — coordinates embedded in photos!
- **PDFs:** `PyPDF2` for metadata + text preview.
- **DMS → Decimal conversion** for GPS coords, then linked to Google Maps + OpenStreetMap.

**Viva Q:** *"What is EXIF?"* → *"Exchangeable Image File Format. Metadata embedded in JPEGs/TIFFs by cameras — camera model, timestamp, and often GPS coordinates from phones. Major privacy leak if not stripped before sharing."*

#### 8. Website Analysis
- **Tech fingerprinting:** Regex matches against 60+ signatures (WordPress, React, Cloudflare, Google Analytics, etc.).
- **Security header audit:** Checks presence of CSP, HSTS, X-Frame-Options, etc.
- **Tracker isolation:** Separates trackers (Facebook Pixel, GA, Hotjar) from other tech.
- **robots.txt + sitemap.xml** parsing.

#### 9. Social Media Search
- Builds parallel search URLs for Twitter, Facebook, LinkedIn, Instagram, etc.
- Also runs Username Lookup if input looks like a handle.

#### 10. Data Breach Check
- **Two modes:**
  1. **Password check** — Pwned Passwords API using **k-anonymity** (no key needed).
  2. **Account check** — Full HIBP account lookup (needs paid key).

**Viva Q:** *"What is k-anonymity in Pwned Passwords?"* → *"We compute SHA-1 of the password locally. Then we send **only the first 5 hex chars** of the hash to the API. The API returns all hashes matching that prefix (usually ~500). We check our full hash against the returned list locally. This way, the API never sees the actual password hash or the password."*

#### 11. Reverse Image Search
- Generates upload URLs for Google Images, Yandex, TinEye, Bing Visual, Baidu, Google Lens.
- No API needed — user opens the links.

#### 12. Google Dorking
- 18 pre-built dork templates: `site:target filetype:pdf`, `intitle:"index of"`, `intext:password`, etc.
- Live search via Google Custom Search API (optional).

#### 13. Public Records
- Multi-jurisdiction registry URLs: SEC EDGAR (US), Companies House (UK), MCA (India), OpenCorporates (global), OFAC sanctions, etc.

#### 14. Dark Web Monitor
- Searches **Ahmia.fi** — a public Tor search engine that indexes clearnet-accessible mirrors of onion sites.
- **We don't touch Tor directly** — Ahmia does the indexing.

---

## 7. PROFESSIONAL FEATURES

### Investigation Cases (SQLite)
- Every tool run belongs to a case.
- Cases persist across restarts.
- Auto-creates a case if none selected.
- **Schema:** 3 tables — `cases`, `results`, `entities` with FK cascade.

### Entity Correlation
- After each successful tool run, `correlation.py::extract_entities()` extracts structured data.
- **Entity types:** email, ip, domain, subdomain, username, phone, url, coordinate, port, tech, cve.
- **Suggestion engine:** Maps entity type → next tool.
  - Found email → suggest Email Investigation + Breach Check
  - Found IP → suggest Port Scan + SSL Scan
  - Found domain → suggest Subdomain Enum + Website Analysis

### PDF Reports
- Multi-page A4 format via ReportLab.
- Cover page, executive summary, entity index, per-tool findings, chain-of-custody.
- **SHA-256 hash** of the PDF returned in `X-Report-SHA256` HTTP header (evidence integrity).

### Command Palette (Ctrl+K)
- Fuzzy search across 22 tools + all cases + 8 quick actions.
- Arrow keys navigate, Enter selects, Esc closes.

### Theme Toggle
- Dark and light modes.
- CSS custom properties on `:root[data-theme="dark|light"]`.
- Persists in `localStorage`, respects `prefers-color-scheme` OS setting.

---

## 8. LIKELY VIVA QUESTIONS + MODEL ANSWERS

### Q1: "Tell me about your project."
**A:** *"Digital Footprint Investigator is an OSINT toolkit with 22 tools for investigating digital identities. It has a Python Flask backend serving a modern web UI. It splits tools into active reconnaissance and passive intelligence, auto-correlates entities like emails and IPs across tools, saves everything to SQLite as investigation cases, and generates professional PDF reports with SHA-256 chain-of-custody."*

### Q2: "Why did you build this?"
**A:** *"OSINT investigators use dozens of scattered tools with inconsistent outputs. My goal was a **single-window platform** that unifies these tools, correlates findings automatically, and generates professional reports — turning what's usually a manual, error-prone process into a structured workflow."*

### Q3: "What's the difference between active and passive OSINT?"
**A:** *"Active tools directly interact with the target — port scans, directory brute force. They can be detected and may have legal implications. Passive tools use only public data — WHOIS, breach databases, certificate logs. They're invisible to the target and generally safe to use."*

### Q4: "How does port scanning work in your project?"
**A:** *"I use Python's `socket` module for TCP connect scanning — attempting a three-way handshake on each port. If `connect_ex()` returns 0, the port is open. I use `ThreadPoolExecutor` with 100–200 workers for concurrency. Users can pick Basic mode (35 common ports), Advanced (top 1000), Full (65535), or a custom range, and configure timing from fast to thorough."*

### Q5: "Why did you use Flask?"
**A:** *"Flask is a lightweight micro-framework. My backend is basically a JSON API serving 22 tools plus case management. Django would bring templates, ORM, and admin UI — features I don't need. Flask keeps the backend under 250 lines and is easy to extend."*

### Q6: "Why SQLite?"
**A:** *"It's zero-configuration — just a file. Perfect for a single-user desktop-style application. I enabled WAL journaling so concurrent reads work while writing. If we scaled to multiple users, migrating to PostgreSQL is straightforward — I designed the schema to be portable."*

### Q7: "Explain Certificate Transparency."
**A:** *"CT is a public, append-only log of every SSL certificate issued by a Certificate Authority. It was mandated by Google after fraudulent Symantec certificates in 2015. Since certs include a Subject Alternative Name field listing all covered domains, we can enumerate subdomains by querying CT logs — I use crt.sh which indexes all major logs."*

### Q8: "What is k-anonymity?"
**A:** *"It's a privacy technique. In my breach check, I compute SHA-1 of a password locally, then send **only the first 5 characters** of the hash to HaveIBeenPwned. Their API returns all hashes with that prefix — usually hundreds. I check locally whether my full hash is in the returned list. This way, my password's hash — let alone the password itself — never leaves my machine."*

### Q9: "How do you extract GPS coordinates from photos?"
**A:** *"Using Pillow — I open the image and read its EXIF metadata. GPS data is stored in DMS format: degrees, minutes, seconds. I convert to decimal using the formula `deg + min/60 + sec/3600`, apply direction (S/W make it negative), and generate Google Maps and OpenStreetMap URLs."*

### Q10: "How does entity correlation work?"
**A:** *"After each successful tool run, an extractor function pulls structured entities — emails, IPs, domains, GPS coordinates. These go into an `entities` table with a case foreign key. My suggestion engine maps entity types to relevant next tools. So if DNS Enum finds an IP, we suggest running Port Scan on it. Users see these as clickable chips."*

### Q11: "How does the PDF report work?"
**A:** *"I use ReportLab. When a user clicks Export PDF, the backend fetches the full case with all results and entities, then builds an A4 document with a branded cover page, executive summary with entity counts, an entity index grouped by type, and detailed per-tool findings using 14 specialized renderers. I compute SHA-256 of the final PDF for chain-of-custody integrity."*

### Q12: "How does Docker deployment work?"
**A:** *"I wrote a Dockerfile based on `python:3.12-slim` with system deps for Pillow, installs Python requirements, and runs the app via gunicorn with 2 workers and 8 threads. `docker-compose.yml` mounts `backend/data/` as a volume so the SQLite database and API keys persist across container restarts. One command — `docker compose up` — and the whole stack is running."*

### Q13: "Is this legal?"
**A:** *"Passive tools use only public data and are legal everywhere. Active tools like port scanning can be considered unauthorized access in many jurisdictions if used against systems you don't own. My README explicitly states it's for authorized security research and educational use only, and I recommend testing only on your own systems or authorized targets like scanme.nmap.org."*

### Q14: "What if someone misuses this?"
**A:** *"Every powerful tool can be misused. This is standard for OSINT toolkits — sherlock, theHarvester, Maltego, all have similar potential. What matters is user responsibility. I could add rate limiting or authentication if it were hosted publicly, but as a self-hosted tool, the user takes responsibility for lawful use."*

### Q15: "What would you improve?"
**A:** *"Three things: **First**, multi-user authentication with role-based permissions for team investigations. **Second**, a background job queue like Celery for long-running scans so the UI stays responsive. **Third**, machine learning for automatic anomaly detection and target classification based on collected entities."*

### Q16: "How do you handle failures?"
**A:** *"Every tool wraps its logic in try/except. Errors are returned as JSON with an `error` field, not raised. In the backend, failed runs are still saved to the case with `status='error'` and the traceback in the `error` column, so users can see what went wrong."*

### Q17: "What about scalability?"
**A:** *"Currently designed for single-user or small-team use. To scale, I'd migrate SQLite to PostgreSQL, add Redis for caching, use Celery for background jobs, add horizontal scaling via multiple gunicorn workers behind a load balancer, and cache OSINT lookups since many results — like WHOIS — don't change often."*

### Q18: "How do you extract 60+ technologies from a website?"
**A:** *"I built a signature dictionary with regex patterns for common frameworks and services. For each site, I fetch the HTML plus all response headers into a single blob and run every pattern. Matches like `wp-content` mean WordPress, `__NEXT_DATA__` means Next.js, `googletagmanager` means GTM. I isolate trackers separately so users see privacy trackers clearly."*

### Q19: "Explain your suggestion engine."
**A:** *"After entities are extracted, the suggestion engine looks at each entity type and maps to relevant tools. I built a `SUGGESTION_MAP` dictionary — email → email-investigation, breach-check, username-lookup on the local part. IP → port scan, ssl scan, ip investigation. Users see these as clickable chips; clicking one opens that tool with the target pre-filled."*

### Q20: "Why did you separate the frontend from the backend?"
**A:** *"Separation of concerns. The Flask backend is a pure JSON API — no HTML rendering. The frontend is static files served by the same Flask app. This means the backend could serve any client — a CLI, a mobile app, a Slack bot — without changes. It's also easier to test each layer independently."*

---

## 9. LIVE DEMO SCRIPT (5 minutes)

**Step 1:** Open http://localhost:5000. Point to header:
- *"Modern dark UI with theme toggle, case selector in header, and Ctrl+K palette."*

**Step 2:** Press **Ctrl+K**, type "user", hit Enter.
- *"The command palette provides fuzzy search across all tools and cases."*

**Step 3:** Enter "torvalds" in Username Lookup, select category "dev", click Run.
- *"It checks 20+ developer platforms in parallel and finds Linus Torvalds on GitHub, GitLab, Stack Overflow…"*

**Step 4:** Point to the suggestion chips at the bottom of the result.
- *"Notice how the system extracted URLs and suggests next tools. Let me click one."*

**Step 5:** Show the entity chips in the case info bar.
- *"All extracted entities across all tools are shown here — automatic correlation."*

**Step 6:** Click PDF Report button.
- *"One click generates a professional multi-page PDF report with cover page, entity index, and SHA-256 chain of custody."*

**Step 7:** Show the downloaded PDF.
- *"Ready to hand to a client or attach to a case file."*

**Step 8:** Toggle theme (moon/sun icon).
- *"Full light mode support with smooth transitions."*

---

## 10. QUICK-RECALL CHEAT SHEET

| Fact | Value |
| --- | --- |
| Total tools | **22** (8 active + 14 passive) |
| Backend language | **Python 3.12** |
| Framework | **Flask 3.0** |
| Database | **SQLite** with WAL mode |
| PDF library | **ReportLab 4.2** |
| Concurrency | **ThreadPoolExecutor** (100–200 workers) |
| Username Lookup platforms | **90+** across 7 categories |
| Website tech signatures | **60+** |
| Google dork templates | **18** |
| DNS record types | **7 basic, 12 advanced** |
| SSL grading tiers | **A+ / A / B / C / D / F** |
| Wordlist sizes (dir brute) | Small 25 / Medium 130 / Large 250 |
| Docker workers | **2 gunicorn workers, 8 threads each** |
| Frontend framework | **None (vanilla JS)** — no build step |
| Theme storage | **localStorage** `dfi-theme` |
| Case storage | **localStorage** `dfi-current-case` |
| PDF hash | **SHA-256** in `X-Report-SHA256` header |
| Password check | **k-anonymity** (first 5 chars of SHA-1) |
| Subdomain source | **crt.sh** (Certificate Transparency) |
| GPS from photos | **EXIF via Pillow** |
| Phone parsing | **phonenumbers** (Google's port) |

---

## 11. ETHICS STATEMENT (for the closing question)

*"This tool is designed for **authorized security research and educational use**. The README explicitly states this. Every active tool includes a warning that unauthorized use may violate laws like the Computer Fraud and Abuse Act. It's the user's responsibility to only test targets they own or have explicit permission to test — such as `scanme.nmap.org` which is publicly authorized for testing. Passive tools use only publicly available data and are generally safe to use."*

---

## 12. FINAL TIPS

### Before the viva
- Have the project running on `http://localhost:5000` for the demo
- Prepare **scanme.nmap.org** as a safe port scan target
- Prepare **torvalds** or **googletest** as safe username lookup targets
- Have `google.com` ready for DNS/subdomain demos
- Test the PDF export beforehand — make sure it downloads cleanly

### During the viva
- **Speak slowly**, use technical terms confidently but explain them if asked
- If you don't know an answer, say *"I haven't explored that specifically, but based on X, I'd approach it Y way"*
- Use the whiteboard to draw the architecture diagram if allowed
- Show enthusiasm — projects you built with passion are the ones you can defend best

### If asked about future work
Mention three things:
1. **Multi-user authentication** for team collaboration
2. **Background job queue** (Celery + Redis) for long scans
3. **Machine learning** for anomaly detection and target classification

---

Good luck, Ravi! You built a real, working, professional-grade tool. Own it in the viva. 🚀
