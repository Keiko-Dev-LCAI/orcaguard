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
import json, os, threading, time, secrets, base64, re
from urllib.parse import urlparse, parse_qs, quote as url_quote

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
# AIVM CLIENT — Lightchain v2 Decentralized Inference
# ════════════════════════════════════════════════════════════════════════

AIVM_GATEWAY  = "https://chat-api.mainnet.lightchain.ai"
AIVM_RELAY    = "wss://relay.mainnet.lightchain.ai/ws"
AIVM_RPC      = "https://rpc.mainnet.lightchain.ai"
AIVM_JOB_REG  = "0xfB15F90298e4CcD7106E76fFB5e520315cC42B0b"
AIVM_JOB_FEE  = 20_000_000_000_000_000   # 0.02 LCAI in wei
AIVM_CHAIN_ID = 9200

AIVM_ABI = [
    {
        "name": "createSession", "type": "function", "stateMutability": "payable",
        "inputs": [
            {"name": "paramsHash",     "type": "bytes32"},
            {"name": "worker",         "type": "address"},
            {"name": "encWorkerKey",   "type": "bytes"},
            {"name": "ephemeralPubKey","type": "bytes"},
            {"name": "initState",      "type": "bytes"},
            {"name": "expiry",         "type": "uint256"},
        ],
        "outputs": [{"name": "sessionId", "type": "uint256"}],
    },
    {
        "name": "submitJob", "type": "function", "stateMutability": "payable",
        "inputs": [
            {"name": "sessionId",  "type": "uint256"},
            {"name": "promptHash", "type": "bytes32"},
        ],
        "outputs": [{"name": "jobId", "type": "uint256"}],
    },
    {
        "anonymous": False, "name": "SessionCreated", "type": "event",
        "inputs": [
            {"indexed": True,  "name": "sessionId",     "type": "uint256"},
            {"indexed": True,  "name": "user",           "type": "address"},
            {"indexed": True,  "name": "paramsHash",     "type": "bytes32"},
            {"indexed": False, "name": "worker",         "type": "address"},
            {"indexed": False, "name": "encWorkerKey",   "type": "bytes"},
            {"indexed": False, "name": "ephemeralPubKey","type": "bytes"},
        ],
    },
    {
        "anonymous": False, "name": "JobSubmitted", "type": "event",
        "inputs": [
            {"indexed": True,  "name": "jobId",     "type": "uint256"},
            {"indexed": True,  "name": "sessionId", "type": "uint256"},
            {"indexed": False, "name": "worker",    "type": "address"},
        ],
    },
    {
        "anonymous": False, "name": "JobCompleted", "type": "event",
        "inputs": [
            {"indexed": True,  "name": "jobId",          "type": "uint256"},
            {"indexed": True,  "name": "worker",          "type": "address"},
            {"indexed": False, "name": "responseHash",    "type": "bytes32"},
            {"indexed": False, "name": "ciphertextHash",  "type": "bytes32"},
        ],
    },
]


def _decode_pubkey(s):
    """Accept hex (with/without 0x) or base64; return 65-byte uncompressed P-256 point."""
    if isinstance(s, (bytes, bytearray)):
        return bytes(s)
    s = s.strip()
    if s.startswith('0x') or s.startswith('0X'):
        b = bytes.fromhex(s[2:])
    elif len(s) == 130 and all(c in '0123456789abcdefABCDEF' for c in s):
        b = bytes.fromhex(s)
    else:
        b = base64.b64decode(s)
    if len(b) != 65:
        raise ValueError(f"pubkey decode: expected 65 bytes, got {len(b)}")
    return b


def _ecdh_wrap(session_key: bytes, peer_pub_bytes: bytes) -> bytes:
    """ECDH-wrap session_key for peer P-256 pubkey."""
    from cryptography.hazmat.primitives.asymmetric.ec import (
        generate_private_key, ECDH, EllipticCurvePublicNumbers, SECP256R1
    )
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.backends import default_backend

    x = int.from_bytes(peer_pub_bytes[1:33], 'big')
    y = int.from_bytes(peer_pub_bytes[33:65], 'big')
    peer_pub = EllipticCurvePublicNumbers(x, y, SECP256R1()).public_key(default_backend())

    ephem_priv = generate_private_key(SECP256R1(), default_backend())
    shared = ephem_priv.exchange(ECDH(), peer_pub)

    pub_nums = ephem_priv.public_key().public_numbers()
    ephem_pub_bytes = (b'\x04' +
                       pub_nums.x.to_bytes(32, 'big') +
                       pub_nums.y.to_bytes(32, 'big'))

    nonce  = secrets.token_bytes(12)
    ct_tag = AESGCM(shared).encrypt(nonce, session_key, None)
    return ephem_pub_bytes + nonce + ct_tag


def _aes_encrypt(key: bytes, plaintext: bytes) -> bytes:
    """AES-256-GCM encrypt. Returns nonce(12) || ct || tag(16)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, None)


def _aes_decrypt(key: bytes, blob: bytes) -> bytes:
    """AES-256-GCM decrypt nonce(12) || ct || tag(16)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if len(blob) < 28:
        raise ValueError("ciphertext too short")
    return AESGCM(key).decrypt(blob[:12], blob[12:], None)


class AIVMClient:
    """Runs LLM inference through the Lightchain v2 decentralized worker network."""

    def __init__(self, private_key: str):
        import requests as _req
        from web3 import Web3
        from eth_account import Account

        self._req      = _req
        self._w3       = Web3(Web3.HTTPProvider(AIVM_RPC))
        self._account  = Account.from_key(private_key)
        self._registry = self._w3.eth.contract(
            address=Web3.to_checksum_address(AIVM_JOB_REG),
            abi=AIVM_ABI,
        )
        self._jwt     = None
        self._jwt_exp = 0
        print(f"  [AIVM] wallet: {self._account.address}")

    def _get_jwt(self) -> str:
        from eth_account.messages import encode_defunct
        if self._jwt and time.time() < self._jwt_exp - 30:
            return self._jwt
        r = self._req.get(
            f"{AIVM_GATEWAY}/api/auth/challenge",
            params={"address": self._account.address}, timeout=15,
        )
        r.raise_for_status()
        message = r.json()["message"]
        sig = self._account.sign_message(encode_defunct(text=message))
        r2 = self._req.post(
            f"{AIVM_GATEWAY}/api/auth/verify",
            json={"message": message, "signature": "0x" + sig.signature.hex()},
            timeout=15,
        )
        r2.raise_for_status()
        v = r2.json()
        self._jwt = v["token"]
        exp_str = v["expiresAt"][:19].replace("T", " ")
        self._jwt_exp = time.mktime(time.strptime(exp_str, "%Y-%m-%d %H:%M:%S"))
        return self._jwt

    def _auth_headers(self):
        return {
            "Authorization": f"Bearer {self._get_jwt()}",
            "Accept":        "application/json",
            "Content-Type":  "application/json",
        }

    def run_inference(self, prompt: str, timeout_secs: int = 360) -> str:
        import websocket as _ws
        from web3 import Web3

        req = self._req
        print(f"  [AIVM] starting inference ({len(prompt)} chars)")

        # 1-2. Auth + pick model
        r = req.get(f"{AIVM_GATEWAY}/api/models", timeout=15)
        r.raise_for_status()
        models = r.json().get("models", [])
        model  = next((m for m in models if m["name"] == "llama3-8b"), models[0] if models else None)
        if not model:
            raise RuntimeError("No models available from AIVM gateway")
        model_id = model["id"]
        print(f"  [AIVM] model: {model['name']} id={model_id[:10]}...")

        # 3. Select worker
        r = req.post(
            f"{AIVM_GATEWAY}/api/sessions/select",
            json={"modelId": model_id},
            headers=self._auth_headers(), timeout=15,
        )
        r.raise_for_status()
        sel = r.json()
        print(f"  [AIVM] worker: {sel['worker']}")

        # 4-5. Session key + ECDH wrap
        session_key  = secrets.token_bytes(32)
        enc_worker   = _ecdh_wrap(session_key, _decode_pubkey(sel["workerEncryptionKey"]))
        enc_disputer = _ecdh_wrap(session_key, _decode_pubkey(sel["disputerEncryptionKey"]))

        # 6. Prepare (get dispatcher signature)
        r = req.post(
            f"{AIVM_GATEWAY}/api/sessions/prepare",
            json={
                "modelId":        model_id,
                "encWorkerKey":   base64.b64encode(enc_worker).decode(),
                "encDisputerKey": base64.b64encode(enc_disputer).decode(),
            },
            headers=self._auth_headers(), timeout=15,
        )
        r.raise_for_status()
        prep = r.json()

        # 7. createSession on-chain
        def _h(s): return s[2:] if isinstance(s, str) and s[:2].lower() == '0x' else s
        params_hash = bytes.fromhex(_h(model_id).zfill(64))
        sig_bytes   = bytes.fromhex(_h(prep["signature"]))
        gas_price = self._w3.eth.gas_price
        nonce_val = self._w3.eth.get_transaction_count(self._account.address)

        tx = self._registry.functions.createSession(
            params_hash,
            Web3.to_checksum_address(prep["worker"]),
            enc_worker,
            enc_disputer,
            sig_bytes,
            prep["expiry"],
        ).build_transaction({
            "from":     self._account.address,
            "nonce":    nonce_val,
            "gas":      1_000_000,
            "gasPrice": gas_price,
            "value":    0,
            "chainId":  AIVM_CHAIN_ID,
        })
        signed  = self._account.sign_transaction(tx)
        tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"  [AIVM] createSession tx: {tx_hash.hex()}")
        receipt1 = self._w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)
        if receipt1.status != 1:
            raise RuntimeError("createSession reverted on-chain")

        session_id = None
        for log in receipt1.logs:
            try:
                evt = self._registry.events.SessionCreated().process_log(log)
                session_id = evt["args"]["sessionId"]
                break
            except Exception:
                pass
        if session_id is None:
            raise RuntimeError("SessionCreated event not found in receipt")
        print(f"  [AIVM] sessionId: {session_id}")

        # 8. Get relay token
        relay_token = None
        deadline = time.time() + 120
        while time.time() < deadline:
            r = req.get(
                f"{AIVM_GATEWAY}/api/sessions/{session_id}/token",
                headers=self._auth_headers(), timeout=10,
            )
            if r.status_code == 200:
                d = r.json()
                if d.get("token"):
                    relay_token = d["token"]
                    break
            time.sleep(1)
        if not relay_token:
            raise RuntimeError("Relay token not ready within 120s")

        chunks   = []
        ws_ready = threading.Event()
        ws_err   = [None]

        def _on_message(ws_obj, message):
            try:
                frame = json.loads(message)
                payload = frame.get("payload")
                if not payload:
                    return
                blob = base64.b64decode(payload)
                try:
                    pt = _aes_decrypt(session_key, blob)
                    chunks.append(pt.decode("utf-8", errors="replace"))
                except Exception:
                    pass
            except Exception:
                pass

        def _on_open(ws_obj):
            ws_ready.set()

        def _on_error(ws_obj, err):
            ws_err[0] = err
            ws_ready.set()

        ws = _ws.WebSocketApp(
            f"{AIVM_RELAY}?token={url_quote(relay_token)}",
            on_message=_on_message,
            on_open=_on_open,
            on_error=_on_error,
        )
        ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
        ws_thread.start()
        ws_ready.wait(timeout=15)
        if ws_err[0]:
            raise RuntimeError(f"WebSocket failed: {ws_err[0]}")
        print("  [AIVM] relay connected")

        # 9. Encrypt prompt + upload blob
        # Build full prompt with system context
        full_prompt = f"[SYSTEM]\n{SYSTEM_PROMPT}\n\n[USER]\n{prompt}"
        cipher = _aes_encrypt(session_key, full_prompt.encode("utf-8"))
        r = req.post(
            f"{AIVM_GATEWAY}/api/blobs",
            json={"data": base64.b64encode(cipher).decode()},
            headers=self._auth_headers(), timeout=15,
        )
        r.raise_for_status()
        blob_hashes = r.json().get("blobHashes", [])
        if not blob_hashes:
            raise RuntimeError("No blob hash returned from gateway")
        prompt_hash = bytes.fromhex(_h(blob_hashes[0]).zfill(64))

        # 10. submitJob (pay 0.02 LCAI)
        nonce_val2 = self._w3.eth.get_transaction_count(self._account.address)
        tx2 = self._registry.functions.submitJob(
            session_id,
            prompt_hash,
        ).build_transaction({
            "from":     self._account.address,
            "nonce":    nonce_val2,
            "gas":      500_000,
            "gasPrice": gas_price,
            "value":    AIVM_JOB_FEE,
            "chainId":  AIVM_CHAIN_ID,
        })
        signed2  = self._account.sign_transaction(tx2)
        tx_hash2 = self._w3.eth.send_raw_transaction(signed2.raw_transaction)
        print(f"  [AIVM] submitJob tx: {tx_hash2.hex()}")
        receipt2 = self._w3.eth.wait_for_transaction_receipt(tx_hash2, timeout=90)
        if receipt2.status != 1:
            raise RuntimeError("submitJob reverted — check LCAI balance")

        job_id = None
        for log in receipt2.logs:
            try:
                evt = self._registry.events.JobSubmitted().process_log(log)
                job_id = evt["args"]["jobId"]
                break
            except Exception:
                pass
        if job_id is None:
            raise RuntimeError("JobSubmitted event not found in receipt")
        print(f"  [AIVM] jobId: {job_id}")

        # 11. Poll for JobCompleted
        job_completed_topic = "0x" + Web3.keccak(
            text="JobCompleted(uint256,address,bytes32,bytes32)"
        ).hex()
        job_id_topic = "0x" + hex(job_id)[2:].zfill(64)

        done     = False
        deadline = time.time() + timeout_secs
        while time.time() < deadline and not done:
            time.sleep(5)
            if chunks:
                print(f"  [AIVM] relay data arrived ({len(chunks)} chunks), returning early")
                done = True
                break
            try:
                head = self._w3.eth.block_number
                logs = self._w3.eth.get_logs({
                    "address":   Web3.to_checksum_address(AIVM_JOB_REG),
                    "fromBlock": receipt2.blockNumber,
                    "toBlock":   head,
                    "topics":    [job_completed_topic, job_id_topic],
                })
                if logs:
                    done = True
                    print(f"  [AIVM] JobCompleted on-chain!")
            except Exception as e:
                print(f"  [AIVM] log poll error (retrying): {e}")

        time.sleep(4)  # grace period for final relay frames
        ws.close()

        result = "".join(chunks)
        if result:
            print(f"  [AIVM] inference done, {len(result)} chars")
            return result

        if not done:
            raise RuntimeError(f"Timeout after {timeout_secs}s waiting for JobCompleted")

        return result or "Sorry, the AI completed the job but returned no response. Please try again."


_aivm_client = None

def get_aivm_client():
    global _aivm_client
    pk = os.environ.get("LIGHTCHAIN_PRIVATE_KEY", "").strip()
    if not pk:
        return None
    if _aivm_client is None:
        try:
            _aivm_client = AIVMClient(pk)
        except Exception as e:
            print(f"  [AIVM] init failed: {e}")
            return None
    return _aivm_client

def run_inference(prompt: str) -> str:
    client = get_aivm_client()
    if client:
        try:
            return client.run_inference(prompt)
        except Exception as e:
            print(f"  [AIVM] failed: {e}")
            return f"AI error: {e}"
    return "AI assistant unavailable — LIGHTCHAIN_PRIVATE_KEY not set."

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
# AI RATE LIMITER — 5 AIVM calls per IP per day
# ════════════════════════════════════════════════════════════════════════

AI_DAILY_LIMIT = 5
_ip_usage      = {}   # { ip: {"count": N, "date": "YYYY-MM-DD"} }
_ip_lock       = threading.Lock()

def _get_client_ip(handler) -> str:
    """Get real IP, respecting Railway's X-Forwarded-For proxy header."""
    forwarded = handler.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return handler.client_address[0]

def _check_ai_limit(ip: str) -> tuple[bool, int]:
    """Returns (allowed, remaining). Deducts 1 on success."""
    today = time.strftime("%Y-%m-%d")
    with _ip_lock:
        rec = _ip_usage.get(ip)
        if rec is None or rec["date"] != today:
            _ip_usage[ip] = {"count": 0, "date": today}
            rec = _ip_usage[ip]
        remaining = AI_DAILY_LIMIT - rec["count"]
        if remaining <= 0:
            return False, 0
        rec["count"] += 1
        return True, remaining - 1

def _peek_ai_remaining(ip: str) -> int:
    """Check remaining without deducting."""
    today = time.strftime("%Y-%m-%d")
    with _ip_lock:
        rec = _ip_usage.get(ip)
        if rec is None or rec["date"] != today:
            return AI_DAILY_LIMIT
        return max(0, AI_DAILY_LIMIT - rec["count"])

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
                             "aivm": bool(get_aivm_client())})
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

        if path == "/api/check-bot":
            self._handle_check_bot()
            return

        if path == "/api/scan-airdrops":
            self._handle_scan_airdrops()
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

        ip = _get_client_ip(self)
        allowed, remaining = _check_ai_limit(ip)
        if not allowed:
            self._send_json({"ok": False, "limitReached": True,
                             "error": f"You've used all {AI_DAILY_LIMIT} free AI questions for today. Come back tomorrow!"}, 429)
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
        self._send_json({"ok": True, "jobId": job_id, "remaining": remaining})

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

        # Unknown contract — check rate limit before using AIVM
        ip = _get_client_ip(self)
        allowed, remaining = _check_ai_limit(ip)
        if not allowed:
            self._send_json({"ok": False, "limitReached": True,
                             "error": f"You've used all {AI_DAILY_LIMIT} free AI questions for today. Come back tomorrow!"}, 429)
            return

        # Use AIVM for analysis
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

        # Unknown URL — check rate limit before using AIVM
        ip = _get_client_ip(self)
        allowed, remaining = _check_ai_limit(ip)
        if not allowed:
            self._send_json({"ok": False, "limitReached": True,
                             "error": f"You've used all {AI_DAILY_LIMIT} free AI questions for today. Come back tomorrow!"}, 429)
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

    def _handle_check_bot(self):
        body    = self._read_body()
        address = body.get("address", "").strip()
        if not address:
            self._send_error("address is required")
            return
        if not re.match(r'^0x[0-9a-fA-F]{40}$', address):
            self._send_error("invalid address format")
            return

        # Rate limit check
        ip = _get_client_ip(self)
        allowed, remaining = _check_ai_limit(ip)
        if not allowed:
            self._send_json({"ok": False, "limitReached": True,
                             "error": f"You've used all {AI_DAILY_LIMIT} free AI questions for today. Come back tomorrow!"}, 429)
            return

        # On-chain lookup — parallel threads to avoid sequential timeout
        import urllib.request as _ur

        def _rpc_call(rpc_url, method, params):
            try:
                payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
                req = _ur.Request(rpc_url, data=payload, headers={"Content-Type": "application/json"})
                with _ur.urlopen(req, timeout=7) as r:
                    return json.loads(r.read()).get("result", None)
            except Exception:
                return None

        ETH_RPC  = "https://eth.llamarpc.com"
        LCAI_RPC = "https://rpc.mainnet.lightchain.ai"

        # Known DEX router contracts on Ethereum
        DEX_ROUTERS = {
            "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
            "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router",
            "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap Universal Router",
            "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap V3 Router 2",
            "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch V5",
            "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch V4",
            "0xdef1c0ded9bec7f1a1670819833240f027b25eff": "0x Exchange Proxy",
            "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "SushiSwap Router",
            # ERC-4337 Account Abstraction EntryPoints — bots use these to submit automated UserOperations
            "0x0000000071727de22e5e9d8baf0edac6f37da032": "ERC-4337 EntryPoint v0.7 (AA Bot)",
            "0x5ff137d4b0fdcd49dcd4dc17ae2aa8f821b42f34": "ERC-4337 EntryPoint v0.6 (AA Bot)",
        }

        results = {
            "eth_code": None, "eth_tx": None,
            "lcai_code": None, "lcai_tx": None,
            "txlist": None, "tokentx": None,
        }

        def _fetch(key, rpc, method, params):
            results[key] = _rpc_call(rpc, method, params)

        ETHERSCAN_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
        key_param = f"&apikey={ETHERSCAN_KEY}" if ETHERSCAN_KEY else ""

        def _etherscan_fetch(action, key):
            """Fetch txlist or tokentx from Etherscan into results[key]."""
            try:
                url = (
                    "https://api.etherscan.io/v2/api"
                    "?chainid=1"
                    f"&module=account&action={action}"
                    f"&address={address}"
                    "&startblock=0&endblock=99999999"
                    f"&page=1&offset=50&sort=desc{key_param}"
                )
                req = _ur.Request(url, headers={"User-Agent": "OrcaGuard/1.0"})
                with _ur.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read())
                msg = data.get("message", "")
                if data.get("status") == "1":
                    results[key] = data.get("result", [])
                elif "No transactions" in msg or "No records" in msg:
                    results[key] = []   # confirmed empty, not an error
                else:
                    print(f"  [Etherscan/{action}] status={data.get('status')} msg={msg}")
                    results[key] = None
            except Exception as e:
                print(f"  [Etherscan/{action}] exception: {e}")
                results[key] = None

        # Start all threads in parallel — RPC and both Etherscan fetches at the same time
        rpc_threads = [
            threading.Thread(target=_fetch, args=("eth_code",  ETH_RPC,  "eth_getCode",             [address, "latest"]), daemon=True),
            threading.Thread(target=_fetch, args=("eth_tx",    ETH_RPC,  "eth_getTransactionCount", [address, "latest"]), daemon=True),
            threading.Thread(target=_fetch, args=("lcai_code", LCAI_RPC, "eth_getCode",             [address, "latest"]), daemon=True),
            threading.Thread(target=_fetch, args=("lcai_tx",   LCAI_RPC, "eth_getTransactionCount", [address, "latest"]), daemon=True),
        ]
        es_txlist  = threading.Thread(target=_etherscan_fetch, args=("txlist",  "txlist"),  daemon=True)
        es_tokentx = threading.Thread(target=_etherscan_fetch, args=("tokentx", "tokentx"), daemon=True)

        for t in rpc_threads: t.start()
        es_txlist.start()
        es_tokentx.start()
        # Wait only for fast RPC calls before responding to user
        for t in rpc_threads: t.join(timeout=8)

        eth_contract  = bool(results["eth_code"]  and len(results["eth_code"])  > 4)
        eth_tx        = int(results["eth_tx"],  16) if results["eth_tx"]  else 0
        lcai_contract = bool(results["lcai_code"] and len(results["lcai_code"]) > 4)
        lcai_tx       = int(results["lcai_tx"], 16) if results["lcai_tx"] else 0

        import uuid
        job_id = str(uuid.uuid4())[:12]
        with _jobs_lock:
            _jobs[job_id] = {"status": "pending", "ts": time.time(), "type": "bot", "address": address}

        # Send jobId immediately — Etherscan + AIVM run fully in background
        self._send_json({
            "ok": True, "jobId": job_id,
            "etherscanUrl": f"https://etherscan.io/address/{address}",
            "remaining":    remaining,
        })

        # Capture locals for background thread
        _es_txlist  = es_txlist
        _es_tokentx = es_tokentx
        _results    = results
        _eth_tx     = eth_tx
        _lcai_tx    = lcai_tx
        _eth_c      = eth_contract
        _lcai_c     = lcai_contract
        _DEX        = DEX_ROUTERS

        def _run():
            # Wait for both Etherscan fetches to finish
            _es_txlist.join(timeout=12)
            _es_tokentx.join(timeout=12)

            txlist  = _results.get("txlist")  or []
            tokentx = _results.get("tokentx") or []

            # Analyze txlist: which DEX routers did this wallet call?
            dex_hits = {}
            for tx in txlist:
                to = (tx.get("to") or "").lower()
                if to in _DEX:
                    name = _DEX[to]
                    dex_hits[name] = dex_hits.get(name, 0) + 1

            # Analyze tokentx: token transfer patterns (received vs sent per token)
            token_summary = {}
            for tx in tokentx:
                symbol   = tx.get("tokenSymbol", "?")
                is_in    = (tx.get("to", "").lower() == address.lower())
                contract = tx.get("contractAddress", "").lower()
                if contract not in token_summary:
                    token_summary[contract] = {"symbol": symbol, "in": 0, "out": 0}
                if is_in:
                    token_summary[contract]["in"] += 1
                else:
                    token_summary[contract]["out"] += 1

            # Build human-readable lines for the AI prompt
            if dex_hits:
                dex_line = "DEX router calls in last {} normal txns: {}".format(
                    len(txlist), ", ".join(f"{v}x {k}" for k, v in dex_hits.items()))
            elif _results.get("txlist") is not None:
                dex_line = f"Last {len(txlist)} normal transactions checked: zero DEX router calls detected"
            else:
                dex_line = "Etherscan normal transaction data unavailable"

            if token_summary:
                top = sorted(token_summary.items(), key=lambda x: x[1]["in"] + x[1]["out"], reverse=True)[:5]
                token_line = "ERC-20 token activity (last 50 token txns): " + ", ".join(
                    f"{v['symbol']} ({v['in']} received / {v['out']} sent)" for _, v in top)
            elif _results.get("tokentx") is not None:
                token_line = "No ERC-20 token transfers found"
            else:
                token_line = "Etherscan token transfer data unavailable"

            chain_s = (
                f"Ethereum: {'Smart contract' if _eth_c else 'Regular wallet'}, "
                f"{_eth_tx:,} outbound transactions (nonce)\n"
                f"Lightchain: {'Smart contract' if _lcai_c else 'Regular wallet'}, "
                f"{_lcai_tx:,} outbound transactions\n"
                f"{dex_line}\n"
                f"{token_line}"
            )

            prompt = f"""Analyze this Ethereum wallet address and determine if it is a trading bot or a human trader.

Address: {address}

On-chain data collected from Etherscan and RPC nodes:
{chain_s}

RULES you must follow:
1. Zero transactions is NOT evidence of a bot. A wallet with 0 transactions is new or unused — answer UNCLEAR.
2. Base your verdict only on the data shown above. Do not invent facts.
3. BOT verdict requires solid evidence: the address is a smart contract, OR nonce is over 1000, OR 5+ of the last transactions go to the same DEX router repeatedly.
4. If data is missing or unavailable, acknowledge it and lean toward UNCLEAR.

What makes a bot:
- Address deployed as a smart contract (not a regular wallet)
- Extremely high transaction count (1000+) concentrated on one or two DEX routers
- Rapid repeated swaps through the same router with no other activity

What makes a human:
- Moderate transaction count with a mix of activity types
- Token approvals, NFTs, governance votes, transfers — not just swaps
- Activity spread across multiple protocols and token types

Verdict must be exactly one of: BOT / LIKELY BOT / UNCLEAR / LIKELY HUMAN / HUMAN

Format your response as:
VERDICT: [label]
[2-3 sentences citing the specific numbers from the data above]
What to watch for: [one practical note for someone interacting with this address]"""

            try:
                answer = run_inference(prompt)
                with _jobs_lock:
                    _jobs[job_id] = {"status": "done", "ts": time.time(), "answer": answer, "type": "bot"}
            except Exception as e:
                with _jobs_lock:
                    _jobs[job_id] = {"status": "error", "ts": time.time(), "error": str(e)}

        threading.Thread(target=_run, daemon=True).start()


    def _handle_scan_airdrops(self):
        import urllib.request as _ur, urllib.parse as _up

        body    = self._read_body()
        address = body.get("address", "").strip()
        if not address:
            self._send_error("address is required")
            return
        if not re.match(r'^0x[0-9a-fA-F]{40}$', address):
            self._send_error("invalid address format")
            return

        ip = _get_client_ip(self)

        # ── Scam name patterns ────────────────────────────────────────────
        SCAM_NAME_PATTERNS = [
            r'claim', r'reward', r'airdrop', r'bonus', r'free',
            r'prize', r'win', r'gift', r'voucher', r'cashback',
            r'refund', r'compensation', r'dividend',
            r'visit.*to', r'go to', r'www\.', r'\.com', r'\.io', r'\.net',
            r'\$\d+', r'usd', r'usdt', r'earn',
        ]

        def _name_looks_suspicious(name, symbol):
            combined = (name + ' ' + symbol).lower()
            return any(re.search(p, combined) for p in SCAM_NAME_PATTERNS)

        # ── Fetch token transfers from Etherscan (free, no key needed) ────
        eth_tokens = []
        try:
            url = (
                "https://api.etherscan.io/v2/api"
                "?chainid=1"
                "&module=account&action=tokentx"
                f"&address={address}"
                "&startblock=0&endblock=99999999"
                "&sort=desc&offset=200&page=1"
            )
            req = _ur.Request(url, headers={"User-Agent": "OrcaGuard/1.0"})
            with _ur.urlopen(req, timeout=12) as r:
                data = json.loads(r.read())
            if data.get("status") == "1":
                seen = {}
                for tx in data.get("result", []):
                    to_addr = tx.get("to", "").lower()
                    contract = tx.get("contractAddress", "").lower()
                    name     = tx.get("tokenName", "")
                    symbol   = tx.get("tokenSymbol", "")
                    # Only tokens RECEIVED (not sent by the user)
                    if to_addr == address.lower() and contract not in seen:
                        seen[contract] = True
                        suspicious = _name_looks_suspicious(name, symbol)
                        eth_tokens.append({
                            "contract": contract,
                            "name":     name,
                            "symbol":   symbol,
                            "chain":    "Ethereum",
                            "suspicious": suspicious,
                        })
        except Exception as e:
            pass  # Etherscan unavailable — return what we have

        # ── Quick result: flag obviously named scams without burning AI ───
        flagged  = [t for t in eth_tokens if t["suspicious"]]
        clean    = [t for t in eth_tokens if not t["suspicious"]]

        # If nothing suspicious by name, return immediately (no AI cost)
        if not flagged:
            self._send_json({
                "ok": True,
                "flagged": [],
                "clean": len(clean),
                "total": len(eth_tokens),
                "aiUsed": False,
                "message": (
                    f"Scanned {len(eth_tokens)} tokens your wallet received on Ethereum. "
                    "None of them have names that match common airdrop scam patterns. "
                    "That's a good sign — but always be cautious about interacting with tokens you didn't buy."
                    if eth_tokens else
                    "No ERC-20 token transfers found for this address on Ethereum."
                )
            })
            return

        # ── For suspicious tokens: check rate limit then run AI ──────────
        allowed, remaining = _check_ai_limit(ip)
        if not allowed:
            # Return pattern-flagged results without AI explanation
            self._send_json({
                "ok": True,
                "flagged": flagged[:10],
                "clean": len(clean),
                "total": len(eth_tokens),
                "aiUsed": False,
                "limitReached": True,
                "message": (
                    f"Found {len(flagged)} suspicious token(s) by name pattern. "
                    f"AI daily limit reached — showing name-based flags only. Come back tomorrow for AI verdicts."
                )
            })
            return

        # Build AI prompt for the flagged tokens (cap at 8 to keep prompt short)
        to_analyze = flagged[:8]
        token_list = "\n".join(
            f"- {t['name']} ({t['symbol']}) — contract: {t['contract']}"
            for t in to_analyze
        )
        prompt = f"""A crypto wallet has received the following ERC-20 tokens it likely never bought — they were airdropped in.
Analyze each one and say whether it is likely a SCAM AIRDROP or POSSIBLY LEGITIMATE.

Wallet: {address}
Tokens received:
{token_list}

For each token, give:
TOKEN: [name/symbol]
VERDICT: SCAM AIRDROP or POSSIBLY LEGITIMATE
REASON: [1 sentence — what's suspicious or why it might be okay]

After the list, add a SUMMARY section:
SUMMARY: [2-3 sentences total — overall danger level, and one key warning about what these scam tokens try to get you to do (e.g. visit a website, connect wallet, approve a contract)]"""

        import uuid
        job_id = str(uuid.uuid4())[:12]
        with _jobs_lock:
            _jobs[job_id] = {
                "status": "pending", "ts": time.time(),
                "type": "airdrop_scan",
                "flagged": flagged, "clean": len(clean), "total": len(eth_tokens),
            }

        def _run():
            try:
                answer = run_inference(prompt)
                with _jobs_lock:
                    _jobs[job_id] = {
                        "status": "done", "ts": time.time(),
                        "answer": answer,
                        "type": "airdrop_scan",
                        "flagged": flagged[:10],
                        "clean": len(clean),
                        "total": len(eth_tokens),
                    }
            except Exception as e:
                with _jobs_lock:
                    _jobs[job_id] = {"status": "error", "ts": time.time(), "error": str(e)}

        threading.Thread(target=_run, daemon=True).start()
        self._send_json({
            "ok": True,
            "jobId": job_id,
            "flaggedCount": len(flagged),
            "total": len(eth_tokens),
            "remaining": remaining,
        })


# ════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import socketserver
    print(f"OrcaGuard backend starting on port {PORT}...")

    class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        daemon_threads = True

    server = ThreadedHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"  Ready: http://0.0.0.0:{PORT}")

    def _init_aivm():
        aivm = get_aivm_client()
        if aivm:
            print(f"  AI: Lightchain AIVM (wallet {aivm._account.address})")
        else:
            print("  AI: UNAVAILABLE — set LIGHTCHAIN_PRIVATE_KEY to enable")
    threading.Thread(target=_init_aivm, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
