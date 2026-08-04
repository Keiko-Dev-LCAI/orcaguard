#!/usr/bin/env python3
"""Build i18n-ui.js from translations/{lang}.json + translations/{lang}_html.json."""
import json
import os
import re
from datetime import datetime, timezone

DIR = os.path.dirname(os.path.abspath(__file__))
TRANS = os.path.join(DIR, 'translations')
LANGS = ['en', 'es', 'fr', 'pt', 'de', 'ja', 'zh']


def load_json(name):
    with open(os.path.join(TRANS, name), encoding='utf-8') as f:
        return json.load(f)


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def bump_index_cache_buster():
    """Force clients (especially Android TWA) to fetch fresh i18n-ui.js — Binai pattern."""
    index_path = os.path.join(DIR, 'index.html')
    version = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')
    with open(index_path, encoding='utf-8') as f:
        html = f.read()
    new_tag = f'<script src="i18n-ui.js?v={version}"></script>'
    if re.search(r'<script src="i18n-ui\.js\?v=[^"]+"></script>', html):
        html = re.sub(r'<script src="i18n-ui\.js\?v=[^"]+"></script>', new_tag, html)
    else:
        html = html.replace('<script src="i18n-ui.js"></script>', new_tag)
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  cache buster → i18n-ui.js?v={version}')
    return version


def load_pack(lang):
    strings = load_json(f'{lang}.json')
    html = load_json(f'{lang}_html.json')
    pack = {**strings, **html}
    raw = pack.get('scams_list_html', '')
    if raw.startswith('<ul'):
        pack['scams_list_html'] = re.sub(r'^<ul[^>]*>|</ul>$', '', raw)
    return pack


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
  set('buylcaiBridgeTitle', 'buylcai_bridge_title'); setHTML('buylcaiBridgeBody', 'buylcai_bridge_html');
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


def main():
    packs = {}
    for lang in LANGS:
        path = os.path.join(TRANS, f'{lang}.json')
        if not os.path.exists(path):
            print(f'ERROR: missing {path} — run build_translations.py first')
            raise SystemExit(1)
        packs[lang] = load_pack(lang)

    lines = [
        '/* OrcaGuard UI strings — full app localization (Binai pattern) */',
        'window.ORCAGUARD_I18N = {',
    ]
    for li, lang in enumerate(LANGS):
        lines.append(f'  {lang}: {{')
        items = sorted(packs[lang].items())
        for i, (k, v) in enumerate(items):
            comma = ',' if i < len(items) - 1 else ''
            lines.append(f'    {k}: {js_str(v)}{comma}')
        lines.append('  }' + (',' if li < len(LANGS) - 1 else ''))
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
    bump_index_cache_buster()

    en = packs['en']
    for lang in LANGS:
        p = packs[lang]
        missing = [k for k in en if k not in p]
        same = [k for k in en if k in p and p[k] == en[k]
                and k not in ('contract_ph', 'url_ph', 'wallet_ph', 'wallet_bot_ph', 'msg_airdrop_limit')]
        print(f'{lang}: {len(p)} keys, missing={len(missing)}, same_as_en={len(same)}')
    print(f'Wrote {out_path}')


if __name__ == '__main__':
    main()