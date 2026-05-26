# OrcaGuard 🛡️

AI-powered crypto wallet safety assistant for the Lightchain community.

Protects non-technical crypto users from scams, phishing, and bad contracts — with plain-English answers, not technical jargon.

## What it does

- **Check a Contract** — paste any contract address and get a verdict before buying or interacting
- **Check a Website** — verify a site is legitimate before connecting your wallet
- **Verify a Wallet** — format-check a destination address before sending crypto
- **Buy LCAI Safely** — official guide with verified sources and known scams
- **Common Scams** — plain-English guide to 9 common crypto scam types
- **Ask OrcaGuard** — AI chat powered by Lightchain AIVM

## Running locally

```bash
cd ~/Desktop/orcaguard
python3 orcaguard-server.py
```

Then open: http://localhost:8186

## Installing as a service

```bash
sudo cp orcaguard-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable orcaguard-server
sudo systemctl start orcaguard-server
```

Add your Lightchain wallet private key to the service file to enable AI responses:

```
Environment=LIGHTCHAIN_PRIVATE_KEY=0x...
```

## Built for the Lightchain community

Free to use. Powered by Lightchain AIVM — every AI check supports the network.

Built by Keiko — because too many community members have been hurt by scams that plain-English explanations could have prevented.

Official LCAI contract (Ethereum Mainnet): `0x9cA8530CA349c966Fe9ef903Df17a75B8A778927`
