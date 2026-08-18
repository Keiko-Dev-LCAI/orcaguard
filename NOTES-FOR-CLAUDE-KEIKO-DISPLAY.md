# OrcaGuard — KEIKO / Filament display gap (2026-08-18)

**Handoff:** `~/Desktop/Importantant stuff/SESSION-169-KEIKO-DISPLAY-HANDOFF.md`

## Facts
- KEIKO = Filament memecoin on **Lightchain** (not Ethereum). Contract `0x93eD20e33e7C88CFa73348086ed1f2c7a2B50854`.
- Lightscan shows ~825.6M KEIKO on Ledger `0x69DEd8…7156`.
- Wallet Audit Connect shows native LCAI for that address but **not KEIKO**.

## Code causes (do not blame Ledger)
1. `index.html` → `connectWalletAudit()` only `eth_getBalance` (native). No Filament/token balance list.
2. `scanAirdrops` / `_handle_scan_airdrops` **can** load KEIKO from Lightscan `addresses/{addr}/tokens`.
3. `_renderScanResult` when `flagged.length === 0` shows “clean” summary only — **does not render `data.tokens`** (so knownSafe KEIKO never named).

## Fix direction (needs Keiko **go**)
- On audit results: list Lightchain held tokens (at least knownSafe / KEIKO) with balances.
- On clean airdrop scan: render known + clean token names, not only a green banner.
