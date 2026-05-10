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

# `devha` — One CLI to Scan Them All 🛡️

**Port scanner · Username lookup · Subdomain enum · Directory bruteforce · OSINT crawler · Cipher tools — in one beautiful terminal.**

[![PyPI version](https://img.shields.io/pypi/v/devha?color=cyan&style=flat-square)](https://pypi.org/project/devha/)
[![Python](https://img.shields.io/pypi/pyversions/devha?color=blue&style=flat-square)](https://pypi.org/project/devha/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/YOUR-USERNAME/devha/ci.yml?style=flat-square&label=ci)](https://github.com/YOUR-USERNAME/devha/actions)
[![Downloads](https://img.shields.io/pypi/dm/devha?color=magenta&style=flat-square)](https://pypi.org/project/devha/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

[Install](#-installation) · [Commands](#-commands) · [Examples](#-examples) · [Contributing](#-contributing) · [Ethics](#%EF%B8%8F-ethical-use)

</div>

---

## 🚀 What is `devha`?

`devha` (short for **Dev**eloper & **Ha**cking) is an all-in-one Python CLI that bundles **10 essential security and developer tools** into one beautiful, beginner-friendly interface — heavily inspired by classics like [Sherlock](https://github.com/sherlock-project/sherlock), [Sublist3r](https://github.com/aboul3la/Sublist3r), [dirsearch](https://github.com/maurosoria/dirsearch), [Photon](https://github.com/s0md3v/Photon), [theHarvester](https://github.com/laramies/theHarvester) and [Scapy](https://github.com/secdev/scapy).

Instead of installing six different tools and learning six different syntaxes, you get **one binary**, **one syntax**, **one beautiful Rich-powered output**.

```bash
$ devha username coolkid42
$ devha portscan scanme.nmap.org
$ devha subdomains example.com
$ devha cipher encode "hello world" --type caesar --key 13
```

Built for **learners**, **CTF players**, and **developers** who think their terminal should look as good as their IDE.

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
docker run --rm -it ghcr.io/YOUR-USERNAME/devha:latest --help
```

### From source
```bash
git clone https://github.com/YOUR-USERNAME/devha.git
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
devha portscan <target> [--ports 1-1024] [--threads 100] [--timeout 1.0]
```

```
$ devha portscan scanme.nmap.org --ports 20-100

⚠️  Scanning external host. Permission confirmed for scanme.nmap.org.

┏━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ PORT ┃ STATUS  ┃ SERVICE  ┃
┡━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ 22   │ ✅ OPEN │ ssh      │
│ 80   │ ✅ OPEN │ http     │
└──────┴─────────┴──────────┘

Scanned 81 ports in 2.4s · 2 open · 79 closed
```
</details>

<details>
<summary><b>👤 username — Find usernames across 50+ sites</b></summary>

```bash
devha username <name> [--sites github,reddit,...] [--timeout 5]
```

```
$ devha username coolkid42

┏━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ SITE        ┃ STATUS    ┃ URL                                ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ GitHub      │ ✅ taken  │ https://github.com/coolkid42       │
│ Reddit      │ ❌ free   │ —                                  │
│ Twitch      │ ✅ taken  │ https://twitch.tv/coolkid42        │
│ Roblox      │ ❌ free   │ —                                  │
└─────────────┴───────────┴────────────────────────────────────┘
```
</details>

<details>
<summary><b>📡 wifi — List nearby WiFi networks</b></summary>

```bash
devha wifi
```

```
$ devha wifi

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┓
┃ SSID               ┃ SIGNAL  ┃ SECURITY   ┃ CHANNEL ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━┩
│ HomeNetwork-5G     │ ▰▰▰▰▰   │ WPA3       │ 36      │
│ Coffee_Shop_Free   │ ▰▰▰▱▱   │ Open       │ 6       │
│ Neighbor_2.4       │ ▰▰▱▱▱   │ WPA2       │ 11      │
└────────────────────┴─────────┴────────────┴─────────┘

🔒 Read-only mode. devha never connects to or attacks networks.
```
</details>

<details>
<summary><b>🔐 cipher — Classic ciphers (encode/decode/crack)</b></summary>

```bash
devha cipher encode <text> --type [caesar|vigenere|rot13|atbash] --key <key>
devha cipher decode <text> --type ...
devha cipher crack  <text> --type caesar
devha cipher tui    # interactive Textual interface
```

```
$ devha cipher crack "Khoor Zruog"

┏━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ KEY ┃ RESULT       ┃ SCORE  ┃
┡━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 3   │ Hello World  │ 0.98 ✅│
│ 7   │ Daddk Sknhc  │ 0.12   │
│ 13  │ Xubbe Mehbt  │ 0.21   │
└─────┴──────────────┴────────┘

Best guess: shift 3 → "Hello World"
```
</details>

<details>
<summary><b>🌐 subdomains — Find subdomains (3 methods combined)</b></summary>

```bash
devha subdomains <domain> [--method wordlist|crt|hackertarget|all]
```

Combines:
- 📚 Wordlist DNS brute-force (top 1000)
- 📜 Certificate Transparency logs (crt.sh)
- 🌍 HackerTarget public API

</details>

<details>
<summary><b>📁 dirscan — Discover hidden paths</b></summary>

```bash
devha dirscan <url> [--threads 50] [--extensions php,html,txt]
```

⚠️ Asks for permission confirmation before scanning. Rate-limited to 10 req/s by default.

</details>

<details>
<summary><b>🕸️ crawl — Extract emails, links, secrets</b></summary>

```bash
devha crawl <url> [--depth 2] [--ignore-robots]
```

Respects `robots.txt` by default. Extracts emails, social links, phone numbers, and potential API-key patterns.

</details>

<details>
<summary><b>📧 harvest — OSINT email/subdomain harvester</b></summary>

```bash
devha harvest <domain>
```

Gathers public information from search engines and certificate logs. **Public data only** — does not attempt logins, brute-force, or anything intrusive.

</details>

<details>
<summary><b>🛡️ headers — Security header audit</b></summary>

```bash
devha headers <url>
```

```
$ devha headers https://example.com

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ HEADER                     ┃ VALUE                                ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Content-Type               │ text/html; charset=UTF-8             │
│ Strict-Transport-Security  │ max-age=63072000                     │
│ X-Frame-Options            │ DENY                                 │
└────────────────────────────┴──────────────────────────────────────┘

╭─ Security Score: 4/6 ⚠️  ──────────────────────────────╮
│ ✅ Strict-Transport-Security                          │
│ ✅ X-Content-Type-Options                             │
│ ✅ X-Frame-Options                                    │
│ ✅ Referrer-Policy                                    │
│ ❌ Content-Security-Policy   (missing)                │
│ ❌ Permissions-Policy        (missing)                │
╰────────────────────────────────────────────────────────╯
```
</details>

<details>
<summary><b>🏓 ping — Educational packet-level ICMP</b></summary>

```bash
devha ping <host> [--count 4] [--show-packet]
```

Built on Scapy. Shows you what an ICMP packet actually *looks like* — perfect for learning networking.

> Requires root/admin privileges on most systems.
</details>

---

## ⚙️ Configuration

`devha` reads optional defaults from `~/.config/devha/config.toml`:

```toml
[defaults]
threads = 100
timeout = 5.0
user_agent = "devha/0.1.0"

[colors]
banner = "cyan"
success = "bright_green"
warning = "yellow"
error = "bright_red"
```

You can also use `devha --no-banner` to hide the ASCII banner for cleaner output in CI/scripting contexts.

---

## ⚖️ Ethical Use

> **`devha` is a learning tool. Use it to understand networks and security — not to break things.**

✅ **Allowed**
- Your own systems and networks
- Legal practice ranges: `scanme.nmap.org`, [HackTheBox](https://hackthebox.com), [TryHackMe](https://tryhackme.com), [PicoCTF](https://picoctf.org)
- Targets where you have **explicit written permission** (bug bounties, pentesting contracts)
- Public APIs that openly allow it (GitHub, crt.sh, etc.)

❌ **Not allowed**
- Scanning, crawling, or harvesting systems you don't own without permission
- Any activity that violates [the Computer Fraud and Abuse Act (US)](https://www.law.cornell.edu/uscode/text/18/1030), [Computer Misuse Act (UK)](https://www.legislation.gov.uk/ukpga/1990/18/contents), [Wet computercriminaliteit (NL)](https://wetten.overheid.nl/), or your local equivalent

Every active-scan command in `devha` shows a confirmation prompt before sending traffic. **You waive your right to claim ignorance the moment you press `y`.** Don't be that person.

The maintainers are not responsible for misuse. Be smart, be legal, be kind.

---

## 🤝 Contributing

Contributions are very welcome — especially:
- 🌐 New sites for the `username` checker (just edit `devha/data/sites.json`)
- 📝 Better wordlists for `subdomains` and `dirscan`
- 🎨 New ciphers (Playfair, Hill, Enigma?)
- 🐛 Bug fixes & test coverage
- 📖 Translations of the README

Quick start:
```bash
git clone https://github.com/YOUR-USERNAME/devha.git
cd devha
poetry install
poetry run pytest
poetry run pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details. By contributing, you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🗺️ Roadmap

- [ ] `devha tui` — Textual super-interface combining all commands
- [ ] `devha update-data` — refresh wordlists from SecLists
- [ ] Shell completions (bash, zsh, fish, PowerShell)
- [ ] More cipher types (Enigma, Playfair, Hill)
- [ ] Plugin system for community-contributed commands
- [ ] Integration with Have-I-Been-Pwned for `username` checks

Vote for features in [Discussions](https://github.com/YOUR-USERNAME/devha/discussions) or open an [issue](https://github.com/YOUR-USERNAME/devha/issues).

---

## 🙏 Acknowledgements

`devha` stands on the shoulders of giants:

- 🦸 [Sherlock](https://github.com/sherlock-project/sherlock) — for proving one CLI can have 60k+ stars
- 🌐 [Sublist3r](https://github.com/aboul3la/Sublist3r) — subdomain enum done right
- 📁 [dirsearch](https://github.com/maurosoria/dirsearch) — directory discovery
- 🕷️ [Photon](https://github.com/s0md3v/Photon) — fast crawler
- 🌾 [theHarvester](https://github.com/laramies/theHarvester) — OSINT classic
- 📦 [Scapy](https://github.com/secdev/scapy) — packet magic in Python
- 🎨 [Rich](https://github.com/Textualize/rich) — for making Python terminals beautiful
- ⌨️ [Typer](https://github.com/tiangolo/typer) — for the cleanest CLI framework around

---

## 📜 License

MIT © [YOUR-NAME](https://github.com/YOUR-USERNAME) — see [LICENSE](LICENSE).

---

<div align="center">

**⭐ If `devha` saved you a few `pip install`s, consider giving it a star — it really helps!**

Made with 🐍 and a healthy obsession with terminal aesthetics.

</div>
