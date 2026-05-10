<div align="center">

```
   ╔══════════════════════════════════════════════╗
   ║                                              ║
   ║    ▄▄▄▄  ▄▄▄▄ ▄   ▄ ▄   ▄  ▄▄▄              ║
   ║    █   █ █    █   █ █   █ █   █             ║
   ║    █   █ █▄▄▄ █   █ █▄▄▄█ █▄▄▄█             ║
   ║    █   █ █     █ █  █   █ █   █             ║
   ║    █▄▄█  █▄▄▄▄  █   █   █ █   █             ║
   ║                                              ║
   ║    Developer  &  Hacking  CLI                ║
   ║                                              ║
   ╚══════════════════════════════════════════════╝
```

**devha — One CLI to Scan Them All 🛡️**

*Port scanner · Username lookup · Subdomain enum · Directory bruteforce · OSINT crawler · Cipher tools — in one beautiful terminal.*

[![PyPI version](https://badge.fury.io/py/devha.svg)](https://badge.fury.io/py/devha)
[![Python](https://img.shields.io/pypi/pyversions/devha)](https://pypi.org/project/devha)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/waldex451/devha/actions/workflows/ci.yml/badge.svg)](https://github.com/waldex451/devha/actions)
[![Downloads](https://img.shields.io/pypi/dm/devha)](https://pypi.org/project/devha)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[Install](#-installation) · [Commands](#%EF%B8%8F-commands) · [Examples](#-quick-start) · [Contributing](#-contributing) · [Ethics](#%EF%B8%8F-ethical-use)

</div>

---

## 🚀 What is devha?

**devha** (short for *Developer & Hacking*) is an all-in-one Python CLI that bundles **10 essential security and developer tools** into one beautiful, beginner-friendly interface — heavily inspired by classics like [Sherlock](https://github.com/sherlock-project/sherlock), [Sublist3r](https://github.com/aboul3la/Sublist3r), [dirsearch](https://github.com/maurosoria/dirsearch), [Photon](https://github.com/s0md3v/Photon), [theHarvester](https://github.com/laramies/theHarvester) and [Scapy](https://scapy.net/).

Instead of installing six different tools and learning six different syntaxes, you get **one binary, one syntax, one beautiful Rich-powered output**.

```bash
$ devha username coolkid42
$ devha portscan scanme.nmap.org
$ devha subdomains example.com
$ devha cipher encode "hello world" --type caesar --key 13
```

Built for **learners, CTF players, and developers** who think their terminal should look as good as their IDE.

---

## ✨ Features

| Command | What it does | Inspired by |
|---|---|---|
| 🔍 `portscan` | Scan open ports on a host (threaded, fast) | nmap |
| 👤 `username` | Check if a username exists on 50+ sites | Sherlock |
| 📡 `wifi` | List nearby WiFi networks (read-only) | iwlist / airport |
| 🔐 `cipher` | Encode, decode & crack classic ciphers | — |
| 🌐 `subdomains` | Find subdomains via wordlist + crt.sh + APIs | Sublist3r |
| 📁 `dirscan` | Discover hidden directories on a website | dirsearch |
| 🕸️ `crawl` | Crawl a site for emails, links, secrets | Photon |
| 📧 `harvest` | OSINT: gather emails & names from public sources | theHarvester |
| 🛡️ `headers` | Audit HTTP security headers + score | securityheaders.com |
| 🏓 `ping` | Educational ICMP ping at packet level | Scapy |

All commands support `--json` for scripting, `--no-banner` for clean output, and rich color-coded results out of the box.

---

## 📦 Installation

### 🌟 Recommended: pipx (isolated, global)

```bash
pipx install devha
```

### Via pip

```bash
pip install devha
```

### Via Docker

```bash
docker run --rm -it ghcr.io/waldex451/devha:latest --help
```

### From source

```bash
git clone https://github.com/waldex451/devha.git
cd devha
poetry install
poetry run devha --help
```

> **Requirements:** Python 3.10+ · Works on Linux, macOS, Windows · `wifi` command requires OS-specific tools (`iwlist`, `nmcli`, `airport`, or `netsh`)

---

## ⚡ Quick Start

```bash
# See all commands
devha --help

# Check if your dream username is taken
devha username your_brand_name

# Scan a legal practice range
devha portscan scanme.nmap.org

# Encrypt a message with ROT13
devha cipher encode "meet me at midnight" --type rot13

# Audit a website's security headers
devha headers https://example.com
```

---

## 🛠️ Commands

<details>
<summary><b>🔍 portscan — Mini-nmap port scanner</b></summary>

```bash
devha portscan <target> [--ports 1-1024] [--threads 100] [--timeout 1.0] [--yes] [--json]
```

Scans open ports using concurrent sockets with a live progress bar. Uses `socket.getservbyport()` for service names.

```
$ devha portscan scanme.nmap.org --ports 1-1000

  Scanning scanme.nmap.org  ports 1-1000  threads 100

  Scanning... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:08

  ╭─ Open ports on scanme.nmap.org ───╮
  │ PORT │ STATUS │ SERVICE           │
  │ 22   │ OPEN   │ ssh               │
  │ 80   │ OPEN   │ http              │
  ╰───────────────────────────────────╯
```

</details>

<details>
<summary><b>👤 username — Find usernames across 50+ sites</b></summary>

```bash
devha username <name> [--sites github,reddit] [--timeout 5] [--found] [--json]
```

Checks 55+ platforms in parallel using `httpx.AsyncClient`. Green = found, Red = not found, Yellow = error/timeout.

```
$ devha username torvalds

  ╭─ Username: torvalds ──────────────────────────────────────╮
  │ SITE           │ STATUS       │ URL                       │
  │ GitHub         │ ✔  FOUND     │ https://github.com/...   │
  │ Reddit         │ ✘  NOT FOUND │ ...                       │
  ╰───────────────────────────────────────────────────────────╯

  Found on 12 / 55 platform(s).
```

</details>

<details>
<summary><b>📡 wifi — List nearby WiFi networks</b></summary>

```bash
devha wifi [--json]
```

Read-only. Detects OS automatically and uses `nmcli`/`iwlist` (Linux), `airport` (macOS), or `netsh` (Windows). Sorted by signal strength.

> ⚠️ **Does not connect to or crack any networks.**

</details>

<details>
<summary><b>🔐 cipher — Classic ciphers (encode/decode/crack)</b></summary>

```bash
devha cipher encode <text> --type [caesar|vigenere|rot13|atbash] --key <key>
devha cipher decode <text> --type ... --key ...
devha cipher crack  <text> --type caesar   # tries all 25 shifts + readability score
devha cipher tui                           # live interactive TUI
```

Pure Python — no external crypto library needed.

```
$ devha cipher crack "Uryyb Jbeyq"

  SHIFT │ SCORE │ PLAINTEXT
  13    │ 5.85  │ Hello World  ← best guess
```

</details>

<details>
<summary><b>🌐 subdomains — Find subdomains (3 methods combined)</b></summary>

```bash
devha subdomains <domain> [--method wordlist|crt|hackertarget|all]
```

Combines wordlist DNS brute-force, [crt.sh](https://crt.sh) Certificate Transparency logs, and the HackerTarget API. Results are deduplicated.

</details>

<details>
<summary><b>📁 dirscan — Discover hidden paths</b></summary>

```bash
devha dirscan <url> [--threads 50] [--extensions php,html] [--rate 10] [--yes]
```

Sends async HEAD requests to 500+ common paths. Only shows interesting status codes (200, 301, 401, 403…). Rate-limited by default.

> ⚠️ Always requires ethics confirmation.

</details>

<details>
<summary><b>🕸️ crawl — Extract emails, links, secrets</b></summary>

```bash
devha crawl <url> [--depth 2] [--ignore-robots] [--yes]
```

Crawls internal links up to the specified depth. Extracts emails, phone numbers, social links, external links, and potential API key patterns from JS files. Respects `robots.txt` by default.

</details>

<details>
<summary><b>📧 harvest — OSINT email/subdomain harvester</b></summary>

```bash
devha harvest <domain> [--timeout 15]
```

Collects publicly available emails (DuckDuckGo), subdomains (crt.sh), and employee names (LinkedIn snippets). **Public data only — no credentials accessed.**

</details>

<details>
<summary><b>🛡️ headers — Security header audit</b></summary>

```bash
devha headers <url> [--json]
```

Fetches all response headers and audits the presence of 6 critical security headers:

- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- `Permissions-Policy`

Outputs a `★★★★★☆` score with explanations for missing headers.

</details>

<details>
<summary><b>🏓 ping — Educational packet-level ICMP</b></summary>

```bash
sudo devha ping <host> [--count 4] [--show-packet] [--timeout 2]
```

Uses Scapy to send raw ICMP packets and shows TTL, RTT, and size. `--show-packet` displays the full packet summary for learning purposes.

> ⚠️ Requires root/admin on most systems.

</details>

---

## ⚙️ Configuration

devha reads optional defaults from `~/.config/devha/config.toml`:

```toml
[defaults]
threads = 100
timeout = 5.0
user_agent = "devha/0.1.0"

[colors]
banner  = "cyan"
success = "bright_green"
warning = "yellow"
error   = "bright_red"
```

You can also use `devha --no-banner` to hide the ASCII banner for cleaner output in CI/scripting contexts.

---

## ⚖️ Ethical Use

> devha is a **learning tool**. Use it to understand networks and security — not to break things.

### ✅ Allowed

- Your own systems and networks
- Legal practice ranges: `scanme.nmap.org`, HackTheBox, TryHackMe, PicoCTF
- Targets where you have **explicit written permission** (bug bounties, pentesting contracts)
- Public APIs that openly allow it (GitHub, crt.sh, etc.)

### ❌ Not allowed

- Scanning, crawling, or harvesting systems you don't own without permission
- Any activity that violates the Computer Fraud and Abuse Act (US), Computer Misuse Act (UK), Wet computercriminaliteit (NL), or your local equivalent

Every active-scan command in devha shows a **confirmation prompt** before sending traffic. You waive your right to claim ignorance the moment you press `y`. Don't be that person.

*The maintainers are not responsible for misuse. Be smart, be legal, be kind.*

---

## 🤝 Contributing

Contributions are very welcome — especially:

- 🌐 **New sites** for the username checker (just edit `devha/data/sites.json`)
- 📝 **Better wordlists** for subdomains and dirscan
- 🎨 **New ciphers** (Playfair, Hill, Enigma?)
- 🐛 **Bug fixes & test coverage**
- 📖 **Translations** of the README

```bash
git clone https://github.com/waldex451/devha.git
cd devha
poetry install
poetry run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 🗺️ Roadmap

- [ ] `devha tui` — Textual super-interface combining all commands
- [ ] `devha update-data` — refresh wordlists from SecLists
- [ ] Shell completions (bash, zsh, fish, PowerShell)
- [ ] More cipher types (Enigma, Playfair, Hill)
- [ ] Plugin system for community-contributed commands
- [ ] Integration with Have-I-Been-Pwned for username checks

Vote for features in [Discussions](https://github.com/waldex451/devha/discussions) or open an issue.

---

## 🙏 Acknowledgements

devha stands on the shoulders of giants:

- 🦸 [Sherlock](https://github.com/sherlock-project/sherlock) — for proving one CLI can have 60k+ stars
- 🌐 [Sublist3r](https://github.com/aboul3la/Sublist3r) — subdomain enum done right
- 📁 [dirsearch](https://github.com/maurosoria/dirsearch) — directory discovery
- 🕷️ [Photon](https://github.com/s0md3v/Photon) — fast crawler
- 🌾 [theHarvester](https://github.com/laramies/theHarvester) — OSINT classic
- 📦 [Scapy](https://scapy.net/) — packet magic in Python
- 🎨 [Rich](https://github.com/Textualize/rich) — for making Python terminals beautiful
- ⌨️ [Typer](https://typer.tiangolo.com/) — for the cleanest CLI framework around

---

## 📜 License

MIT © waldex451 — see [LICENSE](LICENSE).

---

<div align="center">

⭐ **If devha saved you a few `pip install`s, consider giving it a star — it really helps!**

*Made with 🐍 and a healthy obsession with terminal aesthetics.*

</div>
