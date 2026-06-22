#!/usr/bin/env python3
"""Build complete i18n-ui.js — Binai pattern, matches current index.html IDs."""
import ast
import copy
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(name):
    with open(os.path.join(DIR, 'translations', name), encoding='utf-8') as f:
        return json.load(f)


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def merge_pack(base, overlay, html_overlay=None):
    p = copy.deepcopy(base)
    p.update(overlay)
    if html_overlay:
        p.update(html_overlay)
    return p


def tr_html(html, pairs):
    s = html
    for old, new in pairs:
        s = s.replace(old, new)
    return s


# ── English base ─────────────────────────────────────────────────────────────
en = load_json('en.json')
en.update(load_json('en_html.json'))
en.setdefault('lang_sub', 'Change the whole app — navigation, guides, and buttons.')

# Fix scams_list_html — index uses <ul id="scamsList">, inner <li> only
if en.get('scams_list_html', '').startswith('<ul'):
    en['scams_list_html'] = re.sub(r'^<ul[^>]*>|</ul>$', '', en['scams_list_html'])

# ── Spanish overlay (from finalize_i18n.py) ──────────────────────────────────
fin = open(os.path.join(DIR, 'finalize_i18n.py'), encoding='utf-8').read()
es_overlay = ast.literal_eval(re.search(r'^es = (\{.*?\n\})\n', fin, re.M | re.S).group(1))
es_overlay.setdefault('lang_sub', 'Cambia toda la app — navegación, guías y botones.')
es_html = {k: tr_html(v, [
    ("Got a token address?", "¿Tienes una dirección de token?"),
    ("Contract Checker", "Comprobador de contratos"),
    ("Not sure about a website?", "¿No estás seguro de un sitio web?"),
    ("Website Checker", "Comprobador de sitios web"),
    ("Want to see what's in your wallet?", "¿Quieres ver qué hay en tu billetera?"),
    ("Wallet Audit", "Auditoría de billetera"),
    ("New to crypto?", "¿Nuevo en cripto?"),
    ("Common Scams", "Estafas comunes"),
    ("Airdrop Scams", "Estafas de airdrop"),
    ("Honeypot Tokens", "Tokens honeypot"),
    ("Official site", "Sitio oficial"),
    ("Use the built-in browser", "Usa el navegador integrado"),
    ("Understanding Gas Fees", "Entender las comisiones de gas"),
    ("Signs you're probably safe", "Señales de que probablemente estás seguro"),
]) for k, v in load_json('en_html.json').items()}
if es_html.get('scams_list_html', '').startswith('<ul'):
    es_html['scams_list_html'] = re.sub(r'^<ul[^>]*>|</ul>$', '', es_html['scams_list_html'])

# ── French overlay (inline subset from generate_overlays.py) ─────────────────
fr_overlay = {
    "lang_title": "Langue", "lang_sub": "Changez toute l'app — navigation, guides et boutons.",
    "server_checking": "● Vérification...", "server_online": "● Serveur en ligne", "server_offline": "● Serveur hors ligne",
    "sidebar_safety_checks": "Vérifications", "sidebar_resources": "Ressources", "sidebar_ai_assistant": "Assistant IA",
    "nav_contract": "Vérifier un contrat", "nav_url": "Vérifier un site", "nav_wallet": "Vérifier un portefeuille",
    "nav_audit": "Audit portefeuille", "nav_breach": "Fuites de données", "nav_buylcai": "Acheter LCAI",
    "nav_scams": "Arnaques courantes", "nav_tips": "Conseils", "nav_ask": "Demander à OrcaGuard",
    "mnav_home": "Accueil", "mnav_contract": "Contrat", "mnav_url": "Site", "mnav_wallet": "Portefeuille",
    "mnav_audit": "Audit", "mnav_breach": "Fuites", "mnav_buylcai": "LCAI", "mnav_scams": "Arnaques",
    "mnav_tips": "Conseils", "mnav_ask": "IA",
    "home_title": "🛡️ Bienvenue sur OrcaGuard",
    "home_sub": "Votre compagnon de sécurité crypto pour la communauté Lightchain AI (LCAI). Avant d'acheter, de vous connecter ou d'envoyer des fonds — passez par ici d'abord.",
    "contract_btn": "Vérifier", "url_btn": "Vérifier", "wallet_btn": "Vérifier", "wallet_bot_btn": "Vérifier bot",
    "audit_connect_btn": "Connecter le portefeuille", "audit_disconnect": "Déconnecter",
    "audit_airdrop_btn": "Scanner les tokens arnaque", "breach_btn": "Vérifier les fuites",
    "ask_send": "Envoyer", "terms_close": "Fermer", "ask_welcome": "Salut ! Je suis OrcaGuard. Je protège les détenteurs de crypto des arnaques, du phishing et des mauvais contrats.\n\nPosez-moi vos questions en langage simple. 🛡️",
    "footer_orca_link": "🐬 Autres dApps Orca →", "terms_footer_link": "📋 Conditions et avis",
    "verdict_safe": "🟢 SÛR", "verdict_danger": "🔴 DANGER", "verdict_caution": "🟡 PRUDENCE",
    "btn_checking": "Vérification...", "btn_connecting": "Connexion...", "btn_switching": "Changement...",
    "btn_scanning": "Analyse…", "btn_scan_again": "Analyser à nouveau",
    "msg_server_unavailable": "Assistant IA temporairement indisponible. Réessayez dans 30 secondes.",
    "msg_connect_wallet_first": "Connectez d'abord votre portefeuille.",
    "msg_audit_no_wallet": "Aucun portefeuille détecté. Installez une extension ou utilisez WalletConnect.",
    "msg_audit_wc_failed": "WalletConnect a échoué. Essayez un autre portefeuille.",
    "msg_audit_cancelled": "Connexion annulée.",
    "net_eth": "Ethereum Mainnet", "net_lcai": "Lightchain Mainnet",
    "audit_switch_eth": "↔ Passer à Ethereum", "audit_switch_lcai": "↔ Passer à Lightchain",
}

# ── Chinese overlay (from translations/zh.json + zh_html.json) ───────────────
zh_overlay = load_json('zh.json')
zh_overlay.setdefault('lang_sub', '切换整个应用 — 导航、指南和按钮。')
zh_html = load_json('zh_html.json')
if zh_html.get('scams_list_html', '').startswith('<ul'):
    zh_html['scams_list_html'] = re.sub(r'^<ul[^>]*>|</ul>$', '', zh_html['scams_list_html'])

# ── Japanese overlay ─────────────────────────────────────────────────────────
ja_overlay = {
    "lang_title": "言語", "lang_sub": "アプリ全体を切り替え — ナビ、ガイド、ボタンすべて。",
    "sidebar_safety_checks": "安全チェック", "sidebar_resources": "リソース", "sidebar_ai_assistant": "AIアシスタント",
    "nav_contract": "コントラクト確認", "nav_url": "ウェブサイト確認", "nav_wallet": "ウォレット確認",
    "nav_audit": "ウォレット監査", "nav_breach": "漏洩チェック", "nav_buylcai": "LCAI安全購入",
    "nav_scams": "よくある詐欺", "nav_tips": "ヒントとヘルプ", "nav_ask": "OrcaGuardに質問",
    "mnav_home": "ホーム", "mnav_contract": "契約", "mnav_url": "サイト", "mnav_wallet": "ウォレット",
    "mnav_audit": "監査", "mnav_breach": "漏洩", "mnav_buylcai": "LCAI", "mnav_scams": "詐欺",
    "mnav_tips": "ヒント", "mnav_ask": "AI",
    "home_title": "🛡️ OrcaGuardへようこそ",
    "home_sub": "Lightchain AI（LCAI）コミュニティの暗号資産安全コンパニオン。トークン購入、サイト接続、送金の前に — まずここで確認してください。",
    "contract_btn": "確認", "url_btn": "確認", "wallet_btn": "確認", "audit_connect_btn": "ウォレット接続",
    "audit_disconnect": "切断", "ask_send": "送信", "terms_close": "閉じる",
    "ask_welcome": "こんにちは！OrcaGuardです。詐欺、フィッシング、危険なコントラクトから暗号資産ホルダーを守ります。\n\n何でも平易な日本語でお答えします。🛡️",
    "footer_orca_link": "🐬 他のOrca dApps →", "terms_footer_link": "📋 利用規約",
    "verdict_safe": "🟢 安全", "verdict_danger": "🔴 危険", "verdict_caution": "🟡 注意",
    "btn_checking": "確認中...", "btn_connecting": "接続中...", "btn_switching": "切替中...",
    "msg_server_unavailable": "AIアシスタントは一時的に利用できません。30秒後に再試行してください。",
    "msg_connect_wallet_first": "まずウォレットを接続してください。",
    "net_eth": "Ethereumメインネット", "net_lcai": "Lightchainメインネット",
    "audit_switch_eth": "↔ Ethereumに切替", "audit_switch_lcai": "↔ Lightchainに切替",
}

# Portuguese / German — nav + buttons
pt_overlay = {
    "lang_title": "Idioma", "lang_sub": "Mude o app inteiro — navegação, guias e botões.",
    "nav_contract": "Verificar contrato", "nav_url": "Verificar site", "nav_wallet": "Verificar carteira",
    "nav_audit": "Auditoria da carteira", "nav_breach": "Vazamentos", "nav_buylcai": "Comprar LCAI",
    "nav_scams": "Golpes comuns", "nav_tips": "Dicas e ajuda", "nav_ask": "Perguntar ao OrcaGuard",
    "home_title": "🛡️ Bem-vindo ao OrcaGuard",
    "contract_btn": "Verificar", "ask_send": "Enviar", "audit_connect_btn": "Conectar carteira",
    "ask_welcome": "Olá! Sou o OrcaGuard. Protejo holders de cripto de golpes, phishing e contratos ruins.\n\nPergunte o que quiser em linguagem simples. 🛡️",
    "footer_orca_link": "🐬 Outros dApps Orca →", "terms_footer_link": "📋 Termos e aviso",
}
de_overlay = {
    "lang_title": "Sprache", "lang_sub": "Ganze App umstellen — Navigation, Anleitungen und Buttons.",
    "nav_contract": "Vertrag prüfen", "nav_url": "Website prüfen", "nav_wallet": "Wallet prüfen",
    "nav_audit": "Wallet-Audit", "nav_breach": "Datenlecks", "nav_buylcai": "LCAI sicher kaufen",
    "nav_scams": "Betrugsmaschen", "nav_tips": "Tipps & Hilfe", "nav_ask": "OrcaGuard fragen",
    "home_title": "🛡️ Willkommen bei OrcaGuard",
    "contract_btn": "Prüfen", "ask_send": "Senden", "audit_connect_btn": "Wallet verbinden",
    "ask_welcome": "Hallo! Ich bin OrcaGuard. Ich schütze Krypto-Inhaber vor Betrug, Phishing und schlechten Verträgen.\n\nFragen Sie mich in einfacher Sprache. 🛡️",
    "footer_orca_link": "🐬 Weitere Orca dApps →", "terms_footer_link": "📋 Nutzungsbedingungen",
}

packs = {
    'en': en,
    'es': merge_pack(en, es_overlay, es_html),
    'fr': merge_pack(en, fr_overlay),
    'pt': merge_pack(en, pt_overlay),
    'de': merge_pack(en, de_overlay),
    'ja': merge_pack(en, ja_overlay),
    'zh': merge_pack(en, zh_overlay, zh_html),
}

APPLY_I18N = r'''
window.applyI18n = function() {
  const lang = localStorage.getItem('orcaguard_lang') || 'en';
  const htmlLang = { en:'en', es:'es', fr:'fr', pt:'pt', de:'de', ja:'ja', zh:'zh-CN' };
  document.documentElement.lang = htmlLang[lang] || 'en';

  const set = (id, key, vars) => { const el = document.getElementById(id); if (el) el.textContent = t(key, vars); };
  const setPh = (id, key) => { const el = document.getElementById(id); if (el) el.placeholder = t(key); };
  const setHTML = (id, key, vars) => { const el = document.getElementById(id); if (el) el.innerHTML = t(key, vars); };

  set('langTitle', 'lang_title');
  set('langSub', 'lang_sub');
  set('mobileLangTitle', 'lang_title');
  set('mobileLangSub', 'lang_sub');
  set('sidebarLabelChecks', 'sidebar_safety_checks');
  set('sidebarLabelResources', 'sidebar_resources');
  set('sidebarLabelAi', 'sidebar_ai_assistant');
  set('navContract', 'nav_contract'); set('navUrl', 'nav_url'); set('navWallet', 'nav_wallet');
  set('navAudit', 'nav_audit'); set('navBreach', 'nav_breach'); set('navBuylcai', 'nav_buylcai');
  set('navScams', 'nav_scams'); set('navTips', 'nav_tips'); set('navAsk', 'nav_ask');
  set('mnavHome', 'mnav_home'); set('mnavContract', 'mnav_contract'); set('mnavUrl', 'mnav_url');
  set('mnavWallet', 'mnav_wallet'); set('mnavAudit', 'mnav_audit'); set('mnavBreach', 'mnav_breach');
  set('mnavBuylcai', 'mnav_buylcai'); set('mnavScams', 'mnav_scams'); set('mnavTips', 'mnav_tips'); set('mnavAsk', 'mnav_ask');
  set('androidDownload', 'android_download'); set('androidHint', 'android_hint');
  set('homeTitle', 'home_title'); set('homeSub', 'home_sub'); set('homeIntro', 'home_intro');
  set('cardContractT', 'home_card_contract_title'); set('cardContractD', 'home_card_contract_desc');
  set('cardUrlT', 'home_card_url_title'); set('cardUrlD', 'home_card_url_desc');
  set('cardWalletT', 'home_card_wallet_title'); set('cardWalletD', 'home_card_wallet_desc');
  set('cardAuditT', 'home_card_audit_title'); set('cardAuditD', 'home_card_audit_desc');
  set('cardBreachT', 'home_card_breach_title'); set('cardBreachD', 'home_card_breach_desc');
  set('cardBuylcaiT', 'home_card_buylcai_title'); set('cardBuylcaiD', 'home_card_buylcai_desc');
  set('cardScamsT', 'home_card_scams_title'); set('cardScamsD', 'home_card_scams_desc');
  set('cardTipsT', 'home_card_tips_title'); set('cardTipsD', 'home_card_tips_desc');
  set('cardAskT', 'home_card_ask_title'); set('cardAskD', 'home_card_ask_desc');
  set('homeGuideTitle', 'home_start_title'); setHTML('homeGuideBody', 'home_start_html');
  set('contractTitle', 'contract_title'); set('contractSub', 'contract_sub');
  set('contractLabel', 'contract_label'); set('contractHint', 'contract_hint');
  set('contractBtn', 'contract_btn'); setPh('contractInput', 'contract_ph');
  set('contractInfo1Title', 'contract_info_why_title'); setHTML('contractInfo1Body', 'contract_info_why_html');
  set('contractInfo2Title', 'contract_info_official_title'); setHTML('contractInfo2Body', 'contract_info_official_html');
  set('contractInfo3Title', 'contract_info_native_title'); setHTML('contractInfo3Body', 'contract_info_native_html');
  set('urlTitle', 'url_title'); set('urlSub', 'url_sub'); set('urlLabel', 'url_label'); set('urlHint', 'url_hint');
  set('urlBtn', 'url_btn'); setPh('urlInput', 'url_ph');
  set('urlWarnTitle', 'url_warning_title'); set('urlWarnBody', 'url_warning_p');
  set('urlOfficialTitle', 'url_official_title'); setHTML('urlOfficialBody', 'url_official_html');
  set('walletTitle', 'wallet_title'); set('walletSub', 'wallet_sub');
  set('walletLabel', 'wallet_label'); set('walletHint', 'wallet_hint'); set('walletBtn', 'wallet_btn');
  setPh('walletInput', 'wallet_ph'); setPh('botInput', 'wallet_bot_ph');
  set('walletBotLabel', 'wallet_bot_label'); set('walletBotDesc', 'wallet_bot_desc'); set('botBtn', 'wallet_bot_btn');
  set('walletInfoTitle', 'wallet_info_title'); setHTML('walletInfoBody', 'wallet_info_html');
  set('walletWarnTitle', 'wallet_warning_title'); set('walletWarnBody', 'wallet_warning_p');
  set('auditTitle', 'audit_title'); set('auditSub', 'audit_sub');
  set('auditConnectTitle', 'audit_connect_title'); set('auditConnectDesc', 'audit_connect_sub');
  set('auditConnectBtn', 'audit_connect_btn');
  set('auditConnectedLabel', 'audit_connected_label'); set('auditDisconnectBtn', 'audit_disconnect');
  set('auditNetworkLabel', 'audit_network_label'); set('auditEthLabel', 'audit_eth_label'); set('auditLcaiLabel', 'audit_lcai_label');
  set('auditSwitchEth', 'audit_switch_eth'); set('auditSwitchLcai', 'audit_switch_lcai');
  set('auditAirdropLabel', 'audit_airdrop_label'); set('auditAirdropDesc', 'audit_airdrop_desc');
  set('airdropScanBtn', 'audit_airdrop_btn');
  set('auditRevokeTitle', 'audit_approvals_title'); setHTML('auditRevokeBody', 'audit_approvals_html');
  set('auditRevokeBtn', 'audit_approvals_btn');
  set('auditWhatTitle', 'audit_what_title'); set('auditWhatBody', 'audit_what_p');
  set('auditTrustTitle', 'audit_trust_title'); setHTML('auditTrustBody', 'audit_trust_html');
  set('buylcaiTitle', 'buylcai_title'); set('buylcaiSub', 'buylcai_sub');
  set('buylcaiSafeTitle', 'buylcai_safe_title'); setHTML('buylcaiSafeBody', 'buylcai_safe_html');
  set('buylcaiWaysTitle', 'buylcai_ways_title'); setHTML('buylcaiWaysBody', 'buylcai_ways_html');
  set('buylcaiWarn1Title', 'buylcai_coinbase_title'); set('buylcaiWarn1Body', 'buylcai_coinbase_p');
  set('buylcaiWarn2Title', 'buylcai_uniswap_title'); set('buylcaiWarn2Body', 'buylcai_uniswap_p');
  set('buylcaiVerifyTitle', 'buylcai_verify_title'); setHTML('buylcaiVerifyBody', 'buylcai_verify_html');
  set('scamsTitle', 'scams_title'); set('scamsSub', 'scams_sub');
  setHTML('scamsList', 'scams_list_html');
  set('tipsTitle', 'tips_title'); set('tipsSub', 'tips_sub');
  set('tipsWalletTitle', 'tips_wallet_title'); set('tipsWalletIntro', 'tips_wallet_intro');
  setHTML('tipsWalletContent', 'tips_wallet_html');
  set('tipsGasTitle', 'tips_gas_title'); set('tipsGasIntro', 'tips_gas_intro');
  setHTML('tipsGasContent', 'tips_gas_html');
  set('tipsSlippageTitle', 'tips_slippage_title'); set('tipsSlippageIntro', 'tips_slippage_intro');
  setHTML('tipsSlippageContent', 'tips_slippage_html');
  set('tipsTrustTitle', 'tips_trust_title');
  setHTML('tipsTrustContent', 'tips_trust_html');
  set('tipsGeneralTitle', 'tips_general_title');
  setHTML('tipsGeneralContent', 'tips_general_html');
  set('tipsTxTitle', 'tips_sign_title'); set('tipsTxIntro', 'tips_sign_intro');
  setHTML('tipsTxContent', 'tips_sign_html');
  set('breachTitle', 'breach_title'); set('breachSub', 'breach_sub');
  set('breachLabel', 'breach_label'); set('breachHint', 'breach_hint'); set('breachBtn', 'breach_btn');
  setPh('breachInput', 'breach_ph');
  set('breachAboutTitle', 'breach_about_title'); setHTML('breachAboutBody', 'breach_about_html');
  set('breachActionTitle', 'breach_action_title'); setHTML('breachActionBody', 'breach_action_html');
  set('askTitle', 'ask_title'); set('askSub', 'ask_sub'); setPh('aiInput', 'ask_ph');
  set('aiSend', 'ask_send'); set('askPowered', 'ask_powered');
  set('footerTerms', 'terms_footer_link'); set('footerPod', 'footer_orca_link');
  set('footerContact', 'footer_contact'); set('footerContactLink', 'footer_contact_link');
  set('toastCopiedText', 'footer_contact_toast');
  set('termsModalTitle', 'terms_modal_title'); set('termsCloseBtn', 'terms_close');
  set('termsUpdated', 'terms_updated');
  set('termsS1Title', 'terms_s1_title'); set('termsS1Body', 'terms_s1_p');
  set('termsS2Title', 'terms_s2_title'); set('termsS2Body', 'terms_s2_p');
  set('termsS3Title', 'terms_s3_title'); set('termsS3Body', 'terms_s3_p');
  set('termsS4Title', 'terms_s4_title'); set('termsS4Body', 'terms_s4_p');
  set('termsS5Title', 'terms_s5_title'); set('termsS5Body', 'terms_s5_p');
  set('termsS6Title', 'terms_s6_title'); set('termsS6Body', 'terms_s6_p');
  const welcome = document.getElementById('aiWelcome');
  if (welcome) welcome.textContent = t('ask_welcome');
  if (typeof updateServerBadge === 'function') updateServerBadge();
  if (typeof resetActionButtons === 'function') resetActionButtons();
};
'''

lines = ['/* OrcaGuard UI strings — full app localization (Binai pattern) */', 'window.ORCAGUARD_I18N = {']
for li, lang in enumerate(packs):
    lines.append(f'  {lang}: {{')
    items = sorted(packs[lang].items())
    for i, (k, v) in enumerate(items):
        comma = ',' if i < len(items) - 1 else ''
        lines.append(f'    {k}: {js_str(v)}{comma}')
    lines.append('  }' + (',' if li < len(packs) - 1 else ''))
lines.append('};')
lines.append('')
lines.append('''window.t = function(key, vars) {
  const lang = localStorage.getItem('orcaguard_lang') || 'en';
  const pack = window.ORCAGUARD_I18N[lang] || window.ORCAGUARD_I18N.en;
  let s = pack[key] || window.ORCAGUARD_I18N.en[key] || key;
  if (vars) Object.keys(vars).forEach(k => { s = s.replace('{' + k + '}', vars[k]); });
  return s;
};

window.currentLang = function() {
  return localStorage.getItem('orcaguard_lang') || 'en';
};
''')
lines.append(APPLY_I18N.strip())

out_path = os.path.join(DIR, 'i18n-ui.js')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

for lang in packs:
    print(f'{lang}: {len(packs[lang])} keys')
print(f'Wrote {out_path}')