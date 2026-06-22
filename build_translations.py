#!/usr/bin/env python3
"""Generate complete translations/{lang}.json and {lang}_html.json for all languages."""
import ast
import json
import os
import re
import time

from deep_translator import GoogleTranslator

DIR = os.path.dirname(os.path.abspath(__file__))
TRANS = os.path.join(DIR, 'translations')

LANG_META = {
    'es': ('es', 'Cambia toda la app — navegación, guías y botones.'),
    'fr': ('fr', "Changez toute l'app — navigation, guides et boutons."),
    'pt': ('pt', 'Mude o app inteiro — navegação, guias e botões.'),
    'de': ('de', 'Ganze App umstellen — Navigation, Anleitungen und Buttons.'),
    'ja': ('ja', 'アプリ全体を切り替え — ナビ、ガイド、ボタンすべて。'),
}

# Keep identical to English (addresses, URLs, template vars)
KEEP_EN = {
    'contract_ph', 'url_ph', 'wallet_ph', 'wallet_bot_ph',
    'msg_airdrop_limit',  # wrapper around dynamic {msg}
}

PLACEHOLDER_LOCALE = {
    'es': {'breach_ph': 'tu@email.com'},
    'fr': {'breach_ph': 'vous@email.com'},
    'pt': {'breach_ph': 'seu@email.com'},
    'de': {'breach_ph': 'ihre@email.com'},
    'ja': {'breach_ph': 'your@email.com'},
}


def load_json(name):
    with open(os.path.join(TRANS, name), encoding='utf-8') as f:
        return json.load(f)


def save_json(name, data):
    path = os.path.join(TRANS, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  wrote {name} ({len(data)} keys)')


def load_es_strings():
    fin = open(os.path.join(DIR, 'finalize_i18n.py'), encoding='utf-8').read()
    return ast.literal_eval(re.search(r'^es = (\{.*?\n\})\n', fin, re.M | re.S).group(1))


def load_fr_strings():
    src = open(os.path.join(DIR, 'generate_overlays.py'), encoding='utf-8').read()
    return ast.literal_eval(
        re.search(r'OVERLAY_FR = (\{.*?\n\})\n\nHTML_FR', src, re.S).group(1)
    )


def translate_text(text, target, retries=3):
    if not text or not text.strip():
        return text
    for attempt in range(retries):
        try:
            # Google Translate limit ~5000 chars; chunk long strings
            if len(text) <= 4500:
                return GoogleTranslator(source='en', target=target).translate(text)
            parts = []
            chunk = ''
            for line in text.split('\n'):
                if len(chunk) + len(line) + 1 > 4500:
                    parts.append(
                        GoogleTranslator(source='en', target=target).translate(chunk)
                    )
                    chunk = line
                else:
                    chunk = f'{chunk}\n{line}' if chunk else line
            if chunk:
                parts.append(GoogleTranslator(source='en', target=target).translate(chunk))
            return '\n'.join(parts)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
            print(f'    retry {attempt + 1}: {e}')


def build_strings(lang, en_strings, overlay=None):
    target, lang_sub = LANG_META[lang]
    out = {}
    for key, val in en_strings.items():
        if overlay and key in overlay:
            out[key] = overlay[key]
        elif key in KEEP_EN:
            out[key] = val
        elif key in PLACEHOLDER_LOCALE.get(lang, {}):
            out[key] = PLACEHOLDER_LOCALE[lang][key]
        else:
            out[key] = translate_text(val, target)
            time.sleep(0.15)
    out['lang_sub'] = lang_sub
    return out


def build_html(lang, en_html, overlay_html=None):
    target, _ = LANG_META[lang]
    out = {}
    for key, val in en_html.items():
        if overlay_html and key in overlay_html:
            out[key] = overlay_html[key]
        else:
            out[key] = translate_text(val, target)
            time.sleep(0.2)
    return out


def main():
    en_strings = load_json('en.json')
    en_html = load_json('en_html.json')
    zh_strings = load_json('zh.json')
    zh_html = load_json('zh_html.json')

    # Spanish — complete strings from finalize_i18n.py
    print('Building es...')
    es_overlay = load_es_strings()
    es_strings = dict(en_strings)
    es_strings.update(es_overlay)
    for k in KEEP_EN:
        es_strings[k] = en_strings[k]
    es_strings.update(PLACEHOLDER_LOCALE.get('es', {}))
    es_strings['lang_sub'] = LANG_META['es'][1]
    save_json('es.json', es_strings)

    print('  es HTML (translating)...')
    save_json('es_html.json', build_html('es', en_html))

    # French — complete strings from generate_overlays.py
    print('Building fr...')
    fr_overlay = load_fr_strings()
    fr_strings = dict(en_strings)
    fr_strings.update(fr_overlay)
    for k in KEEP_EN:
        fr_strings[k] = en_strings[k]
    fr_strings.update(PLACEHOLDER_LOCALE.get('fr', {}))
    fr_strings['lang_sub'] = LANG_META['fr'][1]
    save_json('fr.json', fr_strings)

    print('  fr HTML (translating)...')
    save_json('fr_html.json', build_html('fr', en_html))

    # Portuguese, German, Japanese — translate all
    for lang in ('pt', 'de', 'ja'):
        print(f'Building {lang} strings...')
        save_json(f'{lang}.json', build_strings(lang, en_strings))
        print(f'  {lang} HTML (translating)...')
        save_json(f'{lang}_html.json', build_html(lang, en_html))

    # Chinese already complete — ensure lang_sub present
    if 'lang_sub' not in zh_strings:
        zh_strings['lang_sub'] = '切换整个应用 — 导航、指南和按钮。'
        save_json('zh.json', zh_strings)

    print('Done.')


if __name__ == '__main__':
    main()