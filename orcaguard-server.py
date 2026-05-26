#!/usr/bin/env python3
"""
OrcaGuard — AI Crypto Safety Assistant
Port 8186 | Powered by Lightchain AIVM

Protects non-technical crypto users from scams:
- Contract address verification
- Airdrop safety checks
- Fake DEX/site detection
- Wallet address validation
- Plain-English AI explanations
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, threading, time, secrets, base64, re, socketserver
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("PORT", 8186))

# ════════════════════════════════════════════════════════════════════════
# KNOWN VERIFIED CONTRACTS & SITES
# ════════════════════════════════════════════════════════════════════════

VERIFIED_CONTRACTS = {
    # LCAI
    "0x9ca8530ca349c966fe9ef903df17a75b8a778927": {
        "name": "LCAI Token (Ethereum Mainnet)",
        "safe": True,
        "note": "This is the official Lightchain AI token contract on Ethereum. Verified on CoinMarketCap and CoinGecko.",
        "links": ["https://coinmarketcap.com/currencies/lightchain-ai/", "https://etherscan.io/token/0x9cA8530CA349c966Fe9ef903Df17a75B8A778927"]
    },
}

VERIFIED_SITES = {
    "lightchain.ai": {"name": "Lightchain AI — Official Site", "safe": True},
    "bridge.lightchain.ai": {"name": "Lightchain Bridge — Official", "safe": True},
    "workers.lightchain.ai": {"name": "Lightchain Worker Explorer — Official", "safe": True},
    "docs.lightchain.ai": {"name": "Lightchain Documentation — Official", "safe": True},
    "dao.lightchain.ai": {"name": "Lightchain Governance — Official", "safe": True},
    "dex-testnet.lightchain.ai": {"name": "Lightchain DEX (Testnet) — Official", "safe": True},
    "forum.lightchain.ai": {"name": "Lightchain Forum — Official", "safe": True},
    "deploy.lightchain.ai": {"name": "Lightchain IDE — Official", "safe": True},
    "mainnet.lightscan.app": {"name": "Lightchain Explorer — Official", "safe": True},
    "app.uniswap.org": {"name": "Uniswap — Official DEX", "safe": True},
    "uniswap.org": {"name": "Uniswap — Official", "safe": True},
}

KNOWN_SCAM_PATTERNS = [
    r"lightchain-ai\.com",
    r"lightchain\.io",
    r"lcai-token\.",
    r"lightchainprotocol\.",
    r"lightchain-protocol\.",
    r"free.*lcai",
    r"lcai.*airdrop.*claim",
    r"lightchain.*presale",
    r"uniswap\.(io|net|app\.io|exchange)",
    r"uninswap\.",
    r"uniswvap\.",
    r"pancakeswap\.(org|net|io)",
]

# ════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are OrcaGuard, an AI crypto safety assistant built to protect non-technical crypto users from scams. You have deep knowledge of crypto scams, phishing attacks, honeypot contracts, and how to verify legitimate projects.

Your job is to give CLEAR, PLAIN-ENGLISH verdicts. Never use technical jargon without explaining it. Always end with a clear recommendation: SAFE, CAUTION, or DANGER.

== LIGHTCHAIN AI (LCAI) — VERIFIED FACTS ==

Official LCAI contract (Ethereum Mainnet): 0x9cA8530CA349c966Fe9ef903Df17a75B8A778927
CoinMarketCap: https://coinmarketcap.com/currencies/lightchain-ai/
CoinGecko: (search LCAI)
Official site: lightchain.ai

WHERE TO BUY LCAI SAFELY:
- Uniswap (app.uniswap.org) — search for the official contract address above
- Bridge to Lightchain Mainnet: bridge.lightchain.ai (after buying on Ethereum)
- Any exchange that shows the exact contract 0x9cA8530CA349c966Fe9ef903Df17a75B8A778927

WHERE LCAI IS NOT LISTED (anything claiming LCAI there is a SCAM):
- Coinbase — NOT LISTED. Any "LCAI" on Coinbase is a fake scam token.
- Binance — NOT LISTED as of 2026. Verify before buying.
- Any exchange not showing the official contract address above

Official Lightchain sites (ONLY these are real):
- lightchain.ai, bridge.lightchain.ai, workers.lightchain.ai
- docs.lightchain.ai, dao.lightchain.ai, forum.lightchain.ai
- mainnet.lightscan.app, deploy.lightchain.ai

== COMMON CRYPTO SCAMS TO WATCH FOR ==

HONEYPOT CONTRACTS:
- You can buy but cannot sell
- Red flags: sell function is disabled, transfer has hidden conditions, owner can change rules
- Verdict: ALWAYS DANGER — never interact

AIRDROP SCAMS:
- Random tokens appear in your wallet you didn't buy
- NEVER interact with, approve, or try to sell unknown airdropped tokens
- Interacting often triggers approval for scammers to drain your wallet
- Verdict: ALWAYS DANGER — do not touch, do not approve

FAKE EXCHANGE LISTINGS:
- Scammers create tokens with the same name/ticker as real projects
- ALWAYS verify by the contract address, never by name or ticker alone
- If someone says "buy LCAI on Coinbase" — it's a scam (LCAI is not on Coinbase)

PHISHING SITES:
- Fake Uniswap: look for misspellings (uninswap, uniswap.io vs app.uniswap.org)
- Always check the URL carefully before connecting your wallet
- Bookmark official sites, never use Google search links for DeFi

WALLET DRAINER TRANSACTIONS:
- Asks you to "approve" spending unlimited tokens
- "setApprovalForAll" — gives complete control of your NFTs
- Any transaction with a very high gas fee for a simple action
- Verdict: NEVER approve what you don't understand

FAKE SUPPORT SCAMS:
- Someone DMs you on Discord/Telegram offering to help
- Real support NEVER asks for your seed phrase or private key
- Verdict: Block immediately, your seed phrase = your entire wallet

SEED PHRASE / PRIVATE KEY:
- NEVER share with anyone, ever, for any reason
- Anyone asking is always a scammer
- Not even Lightchain support, not even MetaMask support

== HOW TO VERIFY ANY CONTRACT ==
1. Go to CoinMarketCap or CoinGecko, search the project name
2. Find the official contract address on their page
3. Compare character by character with what you have
4. If they don't match exactly — it's a fake

== YOUR RESPONSE FORMAT ==
Always structure your response as:
1. VERDICT: 🟢 SAFE / 🟡 CAUTION / 🔴 DANGER
2. Plain English explanation (2-3 sentences max)
3. What to do next (specific action)

Be direct. Be clear. These are people who may lose real money."""

# ════════════════════════════════════════════════════════════════════════
# AIVM CLIENT (copied from orcalearn-server.py with bug fixes)
# ════════════════════════════════════════════════════════════════════════

def get_aivm_client():
    try:
        from web3 import Web3
        import websockets, asyncio
        from cryptography.hazmat.primitives.asymmetric.ec import (
            generate_private_key, ECDH, EllipticCurvePublicKey
        )
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.backends import default_backend
        from eth_account import Account
        import hashlib, struct

        pk = os.environ.get("LIGHTCHAIN_PRIVATE_KEY", "")
        if not pk:
            return None
        return AIVMClient(pk)
    except Exception as e:
        print(f"  AIVM init error: {e}")
        return None

class AIVMClient:
    GATEWAY     = "https://chat-api.mainnet.lightchain.ai"
    RELAY_WS    = "wss://relay.mainnet.lightchain.ai/ws"
    REGISTRY    = "0x0000000000000000000000000000000000001001"
    JOB_FEE     = 20_000_000_000_000_000   # 0.02 LCAI
    CHAIN_ID    = 9200
    RPC         = "https://rpc.mainnet.lightchain.ai"
    MODEL_ID    = "0xf4a414fa2a9a98ce97839f1cc87520a7c07fff92c27c7b16a9d7e3a8d32bfbc0"

    def __init__(self, private_key: str):
        from web3 import Web3
        from eth_account import Account
        self._w3      = Web3(Web3.HTTPProvider(self.RPC))
        self._account = Account.from_key(private_key)
        print(f"  AIVM wallet: {self._account.address}")

    def _h(self, s):
        """Strip 0x prefix safely — lstrip('0x') is buggy for hex with leading zeros."""
        return s[2:] if isinstance(s, str) and s[:2].lower() == '0x' else s

    def run_inference(self, prompt: str) -> str:
        import requests, asyncio, websockets, json as _json
        from cryptography.hazmat.primitives.asymmetric.ec import generate_private_key, ECDH
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.backends import default_backend
        from web3 import Web3
        import hashlib, struct, secrets as _secrets

        # 1. Get JWT
        nonce_resp = requests.get(f"{self.GATEWAY}/auth/nonce?address={self._account.address}", timeout=10)
        nonce = nonce_resp.json()["nonce"]
        msg   = f"Sign this message to authenticate with Lightchain AIVM\nNonce: {nonce}"
        sig   = self._account.sign_message(
            Web3.solidity_keccak(["string"], [f"\x19Ethereum Signed Message:\n{len(msg)}{msg}"]) if False
            else __import__("eth_account").messages.encode_defunct(text=msg)
        )
        jwt_resp = requests.post(f"{self.GATEWAY}/auth/login",
                                 json={"address": self._account.address, "signature": sig.signature.hex()},
                                 timeout=10)
        token = jwt_resp.json()["token"]

        # 2. ECDH key exchange
        ephemeral_key = generate_private_key(__import__("cryptography.hazmat.primitives.asymmetric.ec",
                                              fromlist=["SECP256R1"]).SECP256R1(), default_backend())
        pub_bytes     = ephemeral_key.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        pub_hex = pub_bytes.hex()

        prep_resp = requests.post(f"{self.GATEWAY}/api/prepare-job",
                                  headers={"Authorization": f"Bearer {token}"},
                                  json={"modelId": self.MODEL_ID, "clientPublicKey": pub_hex},
                                  timeout=15)
        prep = prep_resp.json()

        # 3. Derive shared secret → AES-GCM encrypt prompt
        from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
        peer_pub_bytes = bytes.fromhex(self._h(prep["serverPublicKey"]))
        from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1
        peer_pub = __import__("cryptography.hazmat.primitives.asymmetric.ec", fromlist=["EllipticCurvePublicNumbers"])\
                   .EllipticCurvePublicKey  # just for type ref
        from cryptography.hazmat.primitives.asymmetric import ec as _ec
        peer_pub_obj = _ec.EllipticCurvePublicKey.from_encoded_point(_ec.SECP256R1(), peer_pub_bytes)
        shared = ephemeral_key.exchange(ECDH(), peer_pub_obj)
        aes_key = hashlib.sha256(shared).digest()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ]
        plaintext  = _json.dumps({"messages": messages}).encode()
        nonce_aes  = _secrets.token_bytes(12)
        ciphertext = AESGCM(aes_key).encrypt(nonce_aes, plaintext, None)
        encrypted  = (nonce_aes + ciphertext).hex()

        # 4. Submit on-chain job
        params_hash = bytes.fromhex(self._h(self.MODEL_ID).zfill(64))
        sig_bytes   = bytes.fromhex(self._h(prep["signature"]))

        registry_abi = [{"inputs":[{"type":"bytes32"},{"type":"bytes"},{"type":"bytes"},{"type":"string"}],
                          "name":"createAndSubmitJob","outputs":[{"type":"uint256"}],
                          "stateMutability":"payable","type":"function"}]
        contract = self._w3.eth.contract(address=self.REGISTRY, abi=registry_abi)
        tx = contract.functions.createAndSubmitJob(
            params_hash, sig_bytes, bytes.fromhex(encrypted), prep["relayTopic"]
        ).build_transaction({
            "from":     self._account.address,
            "value":    self.JOB_FEE,
            "chainId":  self.CHAIN_ID,
            "nonce":    self._w3.eth.get_transaction_count(self._account.address),
            "gas":      300000,
            "gasPrice": self._w3.eth.gas_price,
        })
        signed = self._account.sign_transaction(tx)
        tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"  [AIVM] job tx: {tx_hash.hex()}")

        # 5. Wait for relay response
        relay_topic = prep["relayTopic"]
        job_completed_topic = "0x" + Web3.keccak(
            text="JobCompleted(uint256,address,bytes32,bytes32)"
        ).hex()

        import asyncio, websockets as _ws

        async def listen_relay():
            uri = f"{self.RELAY_WS}?topic={relay_topic}"
            deadline = time.time() + 360
            async with _ws.connect(uri, ping_interval=30) as ws:
                while time.time() < deadline:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=5)
                        msg = _json.loads(raw)
                        chunks = msg.get("data") or msg.get("chunks") or []
                        if chunks:
                            print(f"  [AIVM] relay data arrived, returning early")
                            return chunks
                    except asyncio.TimeoutError:
                        pass
                    except Exception as e:
                        print(f"  [AIVM] relay error: {e}")
                        break
            return []

        loop = asyncio.new_event_loop()
        try:
            chunks = loop.run_until_complete(listen_relay())
        finally:
            loop.close()

        if not chunks:
            # Fallback: poll logs
            print("  [AIVM] relay gave nothing, polling logs...")
            job_id = None
            for _ in range(60):
                time.sleep(6)
                try:
                    logs = self._w3.eth.get_logs({
                        "fromBlock": "latest",
                        "address":   self.REGISTRY,
                        "topics":    [job_completed_topic],
                    })
                    if logs:
                        job_id = int(logs[-1]["topics"][1].hex(), 16)
                        break
                except Exception as e:
                    print(f"  [AIVM] log poll error: {e}")
            if not job_id:
                return "Sorry, the AI took too long to respond. Please try again."

        # 6. Decrypt response
        try:
            raw_data = bytes.fromhex(self._h("".join(chunks))) if chunks else b""
            if not raw_data:
                return "No response data received."
            nonce_r    = raw_data[:12]
            cipher_r   = raw_data[12:]
            decrypted  = AESGCM(aes_key).decrypt(nonce_r, cipher_r, None)
            result     = _json.loads(decrypted)
            content    = result.get("content") or result.get("message") or str(result)
            return content
        except Exception as e:
            return f"Error decrypting response: {e}"


_aivm_client = None
_aivm_lock   = threading.Lock()

def get_aivm_client_cached():
    global _aivm_client
    with _aivm_lock:
        if _aivm_client is None:
            _aivm_client = get_aivm_client()
        return _aivm_client

def run_inference(prompt: str) -> str:
    client = get_aivm_client_cached()
    if not client:
        return "AI assistant unavailable — LIGHTCHAIN_PRIVATE_KEY not set."
    return client.run_inference(prompt)

# ════════════════════════════════════════════════════════════════════════
# QUICK CHECK LOGIC (instant, no AIVM needed)
# ════════════════════════════════════════════════════════════════════════

def quick_contract_check(address: str) -> dict:
    """Instant check against known contracts before using AIVM."""
    addr_lower = address.lower().strip()
    if addr_lower in VERIFIED_CONTRACTS:
        c = VERIFIED_CONTRACTS[addr_lower]
        return {"verdict": "safe", "known": True, "name": c["name"], "note": c["note"], "links": c.get("links", [])}
    if not re.match(r'^0x[0-9a-f]{40}$', addr_lower):
        return {"verdict": "invalid", "known": True, "note": "This doesn't look like a valid contract address. A valid address starts with 0x followed by exactly 40 characters."}
    return {"verdict": "unknown", "known": False}

def quick_url_check(url: str) -> dict:
    """Instant check against known safe/scam sites."""
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        domain = parsed.netloc.lower().lstrip("www.")
    except Exception:
        domain = url.lower().strip()

    if domain in VERIFIED_SITES:
        s = VERIFIED_SITES[domain]
        return {"verdict": "safe", "known": True, "name": s["name"]}

    for pattern in KNOWN_SCAM_PATTERNS:
        if re.search(pattern, url.lower()):
            return {"verdict": "danger", "known": True,
                    "note": f"This URL matches a known scam pattern. Do NOT connect your wallet to this site."}

    # Suspicious patterns
    warnings = []
    if re.search(r'lightchain', domain) and domain not in VERIFIED_SITES:
        warnings.append("Claims to be Lightchain but is not an official domain")
    if re.search(r'uniswap', domain) and "uniswap.org" not in domain:
        warnings.append("Claims to be Uniswap but is not app.uniswap.org")
    if re.search(r'(free|claim|airdrop|bonus|reward)', domain):
        warnings.append("Domain contains words commonly used in crypto scams")

    if warnings:
        return {"verdict": "caution", "known": True, "warnings": warnings,
                "note": "This site shows suspicious patterns. Do NOT connect your wallet without verifying further."}

    return {"verdict": "unknown", "known": False}

# ════════════════════════════════════════════════════════════════════════
# HTTP SERVER
# ════════════════════════════════════════════════════════════════════════

SERVER_START = time.time()
_jobs        = {}
_jobs_lock   = threading.Lock()


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, msg, code=400):
        self._send_json({"error": msg}, code)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")

        if path == "" or path == "/":
            html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
            try:
                with open(html_path, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self._send_error("index.html not found", 404)
            return

        # Serve static assets (icon, favicon, etc.) from the same directory
        STATIC_TYPES = {
            ".png": "image/png", ".ico": "image/x-icon",
            ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        }
        _, ext = os.path.splitext(path)
        if ext.lower() in STATIC_TYPES:
            static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       os.path.basename(path))
            if os.path.isfile(static_path):
                with open(static_path, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", STATIC_TYPES[ext.lower()])
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(body)
                return
            self._send_error("Not found", 404)
            return

        if path == "/api/health":
            uptime = int(time.time() - SERVER_START)
            h, rem = divmod(uptime, 3600)
            m = rem // 60
            self._send_json({"ok": True, "uptime": uptime, "uptimeLabel": f"{h}h {m}m",
                             "aivm": bool(get_aivm_client_cached())})
            return

        if path == "/api/job":
            qs     = parse_qs(parsed.query)
            job_id = qs.get("id", [""])[0].strip()
            with _jobs_lock:
                job = _jobs.get(job_id)
            if not job:
                self._send_error("Job not found", 404)
                return
            self._send_json(job)
            return

        self._send_error("Not found", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")

        if path == "/api/ask":
            self._handle_ask()
            return

        if path == "/api/check-contract":
            self._handle_check_contract()
            return

        if path == "/api/check-url":
            self._handle_check_url()
            return

        self._send_error("Not found", 404)

    def _handle_ask(self):
        body     = self._read_body()
        question = body.get("question", "").strip()
        if not question:
            self._send_error("question is required")
            return
        if len(question) > 3000:
            self._send_error("question too long (max 3000 chars)")
            return

        import uuid
        job_id = str(uuid.uuid4())[:12]
        with _jobs_lock:
            _jobs[job_id] = {"status": "pending", "ts": time.time()}

        def _run():
            try:
                answer = run_inference(question)
                with _jobs_lock:
                    _jobs[job_id] = {"status": "done", "ts": time.time(), "answer": answer}
            except Exception as e:
                with _jobs_lock:
                    _jobs[job_id] = {"status": "error", "ts": time.time(), "error": str(e)}
            with _jobs_lock:
                if len(_jobs) > 50:
                    oldest = sorted(_jobs.items(), key=lambda x: x[1].get("ts", 0))
                    for k, _ in oldest[:-50]:
                        del _jobs[k]

        threading.Thread(target=_run, daemon=True).start()
        self._send_json({"ok": True, "jobId": job_id})

    def _handle_check_contract(self):
        body    = self._read_body()
        address = body.get("address", "").strip()
        if not address:
            self._send_error("address is required")
            return

        quick = quick_contract_check(address)
        if quick["known"] and quick["verdict"] != "unknown":
            self._send_json({"ok": True, "quick": True, **quick})
            return

        # Unknown contract — use AIVM for analysis
        prompt = f"""A user wants to know if this contract address is safe to interact with:

Contract address: {address}

Please analyze this address. Check if it matches any known legitimate projects. Explain what you know about it and give a clear SAFE / CAUTION / DANGER verdict with specific instructions on what the user should do next. If you don't recognize it, explain how they can verify it themselves."""

        import uuid
        job_id = str(uuid.uuid4())[:12]
        with _jobs_lock:
            _jobs[job_id] = {"status": "pending", "ts": time.time(), "type": "contract", "address": address}

        def _run():
            try:
                answer = run_inference(prompt)
                with _jobs_lock:
                    _jobs[job_id] = {"status": "done", "ts": time.time(), "answer": answer, "type": "contract"}
            except Exception as e:
                with _jobs_lock:
                    _jobs[job_id] = {"status": "error", "ts": time.time(), "error": str(e)}

        threading.Thread(target=_run, daemon=True).start()
        self._send_json({"ok": True, "quick": False, "jobId": job_id})

    def _handle_check_url(self):
        body = self._read_body()
        url  = body.get("url", "").strip()
        if not url:
            self._send_error("url is required")
            return

        quick = quick_url_check(url)
        if quick["known"] and quick["verdict"] != "unknown":
            self._send_json({"ok": True, "quick": True, **quick})
            return

        prompt = f"""A user wants to know if this website is safe to connect their crypto wallet to:

URL: {url}

Please analyze this URL carefully. Check for:
- Is it an official site or a known phishing/scam site?
- Any suspicious patterns in the domain name?
- Is it claiming to be a legitimate service (Uniswap, Lightchain, etc.) when it isn't?

Give a clear SAFE / CAUTION / DANGER verdict and specific instructions."""

        import uuid
        job_id = str(uuid.uuid4())[:12]
        with _jobs_lock:
            _jobs[job_id] = {"status": "pending", "ts": time.time(), "type": "url", "url": url}

        def _run():
            try:
                answer = run_inference(prompt)
                with _jobs_lock:
                    _jobs[job_id] = {"status": "done", "ts": time.time(), "answer": answer, "type": "url"}
            except Exception as e:
                with _jobs_lock:
                    _jobs[job_id] = {"status": "error", "ts": time.time(), "error": str(e)}

        threading.Thread(target=_run, daemon=True).start()
        self._send_json({"ok": True, "quick": False, "jobId": job_id})


# ════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"OrcaGuard backend starting on port {PORT}...")

    # Start HTTP server FIRST so Railway health check passes immediately
    class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        daemon_threads = True
    server = ThreadedHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"  Ready: http://0.0.0.0:{PORT}")

    # Init AIVM in background thread — don't block startup
    def _init_aivm():
        aivm = get_aivm_client_cached()
        if aivm:
            print(f"  AI: Lightchain AIVM (wallet {aivm._account.address})")
        else:
            print("  AI: UNAVAILABLE — set LIGHTCHAIN_PRIVATE_KEY to enable")
    threading.Thread(target=_init_aivm, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
