# OrcaGuard

AI-powered crypto wallet safety assistant for the Lightchain community.

## What it does
- **Check a Contract** — paste any contract address; get a plain-English verdict before buying or interacting
- **Check a Website** — verify a DEX or site is legitimate before connecting your wallet
- **Verify a Wallet** — check a destination address before sending crypto
- **Buy LCAI Safely** — official guide to verified sources and known scams
- **Common Scams** — plain-English guide to the most common crypto scams
- **Ask OrcaGuard** — AI chat powered by Lightchain AIVM

## Known gap (2026-08-18 / session 169) — for Claude
**KEIKO** (Filament memecoin on **Lightchain**, `0x93eD20…`) shows on **Lightscan** for the Ledger bag but **not** on MetaMask Assets and **not** named on OrcaGuard Wallet Audit.

- Connect audit = native LCAI only (`eth_getBalance`).
- Airdrop scan can detect KEIKO via Lightscan but clean UI doesn’t list token names.
- See `NOTES-FOR-CLAUDE-KEIKO-DISPLAY.md` and `~/Desktop/Importantant stuff/SESSION-169-KEIKO-DISPLAY-HANDOFF.md`.
- Do **not** call KEIKO an Ethereum ERC-20. Fix UI only with Keiko **go**.

## Running locally
```bash
python3 orcaguard-server.py
```
Then open http://localhost:8186

Built with love for the Lightchain community. Free to use.
