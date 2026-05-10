# devha — Developer & Hacking CLI

> ⚠️ **For ethical use only.** Always obtain explicit written permission before scanning systems you don't own.

```
   ╔══════════════════════════════════════════╗
   ║  ██████╗ ███████╗██╗   ██╗██╗  ██╗ █████╗  ║
   ║  ██╔══██╗██╔════╝██║   ██║██║  ██║██╔══██╗ ║
   ║  ██║  ██║█████╗  ██║   ██║███████║███████║ ║
   ║  ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══██║██╔══██║ ║
   ║  ██████╔╝███████╗ ╚████╔╝ ██║  ██║██║  ██║ ║
   ║  ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝ ║
   ║                                            ║
   ║   Developer & Hacking CLI  v0.1.0          ║
   ║   ⚠  For ethical use only                  ║
   ╚══════════════════════════════════════════╝
```

[![PyPI version](https://badge.fury.io/py/devha.svg)](https://badge.fury.io/py/devha)
[![Python versions](https://img.shields.io/pypi/pyversions/devha)](https://pypi.org/project/devha)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/waldex451/devha/actions/workflows/ci.yml/badge.svg)](https://github.com/waldex451/devha/actions)

An open-source Python CLI that bundles 10 ethical-hacking and developer tools into one beautiful, hacker-themed command-line tool — inspired by Sherlock, Sublist3r, dirsearch, Photon, theHarvester, and more, but simplified and in a single package.

---

## Features

| Command | Description |
|---|---|
| 🔌 `portscan` | Mini-nmap — scan open ports with threading + progress bar |
| 👤 `username` | Mini-Sherlock — check username on 55+ platforms |
| 📡 `wifi` | List nearby Wi-Fi networks (read-only, no cracking) |
| 🔐 `cipher` | Encode/decode/crack Caesar, Vigenère, ROT13, Atbash + TUI |
| 🌐 `subdomains` | Wordlist + crt.sh + HackerTarget subdomain discovery |
| 📂 `dirscan` | Mini-dirsearch — brute-force web paths with rate limiting |
| 🕷️ `crawl` | Mini-Photon — extract emails, links, and API key patterns |
| 🌾 `harvest` | Mini-theHarvester — collect public info about a domain |
| 🔍 `headers` | HTTP header inspector + security score audit |
| 🏓 `ping` | Scapy ICMP ping with packet-level educational output |

---

## Quick Start

```bash
pipx install devha
devha --help
devha cipher encode "Hello, World!" --type rot13
devha portscan scanme.nmap.org --ports 1-1000
devha username torvalds
```

---

## Installation

### Via pipx (recommended)

```bash
pipx install devha
```

### Via pip

```bash
pip install devha
```

### Via Docker

```bash
docker build -t devha .
docker run --rm -it devha portscan scanme.nmap.org
docker run --rm devha cipher encode "hello" --type rot13
```

### From source

```bash
git clone https://github.com/waldex451/devha
cd devha
pip install poetry
poetry install
poetry run devha --help
```

---

## Command Reference

### `devha portscan <target>`

Scan open ports on a host using concurrent sockets.

```
$ devha portscan scanme.nmap.org --ports 1-1000

  Scanning scanme.nmap.org (45.33.32.156)  ports 1-1000  threads 100

  Scanning... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:08

  ╭─ Open ports on scanme.nmap.org ─╮
  │ PORT │ STATUS │ SERVICE          │
  │ 22   │ OPEN   │ ssh              │
  │ 80   │ OPEN   │ http             │
  ╰──────────────────────────────────╯

  Found 2 open port(s).
```

Options: `--ports`, `--threads`, `--timeout`, `--yes`, `--json`

---

### `devha username <name>`

Check username existence on 55+ platforms.

```
$ devha username torvalds

  ╭─ Username: torvalds ──────────────────────────────────────────╮
  │ SITE           │ STATUS      │ URL                            │
  │ GitHub         │ ✔  FOUND    │ https://github.com/torvalds   │
  │ Reddit         │ ✘  NOT FOUND│ https://www.reddit.com/...    │
  │ Twitter        │ ✔  FOUND    │ https://twitter.com/torvalds  │
  ╰───────────────────────────────────────────────────────────────╯

  Found on 2 / 55 platform(s).
```

Options: `--sites`, `--timeout`, `--found`, `--json`

---

### `devha cipher encode/decode/crack`

Classical ciphers — Caesar, Vigenère, ROT13, Atbash.

```
$ devha cipher encode "Hello World" --type caesar --key 13
╭─ Encoded (caesar) ─╮
│ Uryyb Jbeyq        │
╰────────────────────╯

$ devha cipher crack "Uryyb Jbeyq" --type caesar
  Caesar Crack — All 25 Shifts
  SHIFT │ SCORE │ PLAINTEXT
  13    │ 5.85  │ Hello World   ← Best guess

$ devha cipher tui    # opens interactive live encode/decode TUI
```

Options for encode/decode: `--type [caesar|vigenere|rot13|atbash]`, `--key`, `--json`

---

### `devha subdomains <domain>`

Discover subdomains via three methods.

```
$ devha subdomains example.com --method crt

  ╭─ Subdomains of example.com ─────────────────────────────────╮
  │ SUBDOMAIN           │ IP            │ METHOD                 │
  │ www.example.com     │ 93.184.216.34 │ crt.sh                 │
  │ dev.example.com     │ 93.184.216.34 │ wordlist               │
  ╰──────────────────────────────────────────────────────────────╯

  Found 2 subdomain(s).
```

Options: `--method [wordlist|crt|hackertarget|all]`, `--json`

---

### `devha dirscan <url>`

Brute-force web paths using HEAD requests.

```
$ devha dirscan https://example.com --extensions php,html

  ╭─ Dirscan results — https://example.com ─────────────────────╮
  │ STATUS │ SIZE  │ PATH                                        │
  │ 200    │ 1256  │ /robots.txt                                 │
  │ 403    │ -     │ /.git                                       │
  ╰──────────────────────────────────────────────────────────────╯
```

Options: `--threads`, `--extensions`, `--user-agent`, `--rate`, `--yes`, `--json`

---

### `devha crawl <url>`

Crawl a website and extract useful information.

```
$ devha crawl https://example.com --depth 2

  Crawled 12 page(s)

  ╭─ Emails (3) ──────╮   ╭─ Social Links (2) ─────────────────╮
  │  • admin@...      │   │  • https://twitter.com/example      │
  │  • info@...       │   │  • https://linkedin.com/company/... │
  ╰───────────────────╯   ╰─────────────────────────────────────╯
```

Options: `--depth`, `--ignore-robots`, `--yes`, `--timeout`, `--json`

---

### `devha harvest <domain>`

Collect publicly available information about a domain.

```
$ devha harvest example.com

  ╭─ Emails (5) ──────────────╮  ╭─ Subdomains (12) ─────────╮
  │  • admin@example.com      │  │  • www.example.com         │
  │  ...                      │  │  • ...                     │
  ╰───────────────────────────╯  ╰────────────────────────────╯
```

Options: `--timeout`, `--json`

---

### `devha headers <url>`

Audit HTTP security headers.

```
$ devha headers https://github.com

  ╭─ Security Audit ───────────────────────────────────────────╮
  │  Security Score: 5/6  ★★★★★☆                              │
  │                                                            │
  │  ✔  Present:                                               │
  │     • content-security-policy                              │
  │     • strict-transport-security                            │
  │     • x-content-type-options                               │
  │                                                            │
  │  ✘  Missing:                                               │
  │     • permissions-policy  — Controls browser feature access│
  ╰────────────────────────────────────────────────────────────╯
```

Options: `--timeout`, `--json`

---

### `devha ping <host>`

ICMP ping with packet-level detail (requires root/admin).

```
$ sudo devha ping 8.8.8.8 --count 4

  [1] Reply  ttl=118  size=28B  rtt=12.34ms
  [2] Reply  ttl=118  size=28B  rtt=11.89ms

  ╭─ Ping Summary — 8.8.8.8 ──────────────────────────────────────────────────╮
  │  Sent: 4  Received: 4  Loss: 0%  RTT: min=11.89ms avg=12.17ms max=12.45ms │
  ╰────────────────────────────────────────────────────────────────────────────╯
```

Options: `--count`, `--show-packet`, `--timeout`, `--json`

---

### `devha wifi`

List nearby Wi-Fi networks (read-only).

```
$ devha wifi

  ╭─ Nearby Wi-Fi Networks ──────────────────────────────────╮
  │ SSID          │ SIGNAL │ SECURITY │ CHANNEL              │
  │ HomeNetwork   │ -42    │ WPA2     │ 6                    │
  │ GuestWifi     │ -68    │ Open     │ 11                   │
  ╰──────────────────────────────────────────────────────────╯
```

Options: `--json`

---

## Global Options

All commands support:

- `--no-banner` — skip the ASCII banner
- `--json` — machine-readable JSON output
- `--help` — detailed help with examples

---

## Ethical Use Policy

`devha` includes mandatory ethics warnings before any active scan. You will always be asked to confirm before scanning external systems.

**Safe targets for testing without permission:**
- `localhost` / `127.0.0.1`
- `scanme.nmap.org` (Nmap's official scan-me host)
- HackTheBox, TryHackMe machines you're authorized on

**Skip the prompt with `--yes` only for systems you own.**

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for new functionality
4. Ensure `ruff check .` and `black --check .` pass
5. Submit a Pull Request

---

## License

MIT — see [LICENSE](LICENSE).

---

> ⚠️ **Disclaimer:** This tool is for educational purposes and authorized security testing only. The authors are not responsible for misuse. Always obtain explicit written permission before scanning systems you don't own.
