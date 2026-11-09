#!/usr/bin/env python3
"""Fail loudly when a published price contradicts itself.

Written because the reprice on 2026-08-20 shipped fifteen wrong figures. The
sweep that produced them looked for the OLD values and replaced them globally,
which both missed survivors and introduced new errors — a blanket
"$1,200 -> $300" also rewrote the phone agent, whose new floor is $1,000.

So this checks PER SERVICE, not per value: every figure that appears on a
service's own page must be that service's floor, or an explicitly allowed
cross-reference. Prices live on several surfaces that nothing syncs. Those
surfaces are checked here, and social/listing generators are separately
required to stay free of hard-coded dollar amounts.

    python3 tools/check_prices.py     # exit 1 on any contradiction
"""

import glob
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The published floors. This dict is the single source of truth for the check.
FLOORS = {
    'small fixes': 75,
    'websites': 300,
    'seo': 450,
    'business-automation': 500,
    'booking-systems': 600,
    'websites-backend': 625,
    'business-dashboards': 750,
    'ai-chatbots': 750,
    'ai-phone-agents': 1000,
    'custom-software': 1500,
    'mobile-apps': 3500,
    'ongoing': 400,
}

# Prices on offers outside the generated /services/* fleet. Keeping these
# separate preserves the historical service-floor fingerprint used by the
# off-site publication ledger while still making every public amount auditable.
PUBLIC_OFFERS = {
    'one-page-website-starter': 199,
    'technical-build-partner-plan': 199,
    'technical-build-partner-ongoing': 2000,
    'annual-personal-developer': 2499,
    'annual-monthly-equivalent': 208.25,
    'ai-search-pass': 1350,          # the AI search (GEO) pass on /services/seo; anchored in research/2026-09-08-seo-geo-market-prices.md
    'search-ongoing-monthly': 450,   # ongoing search or AI-visibility work, per month
}

# Figures a given service page may legitimately mention besides its own floor,
# because the copy deliberately points at a neighbouring service.
CROSS = {
    'websites': {625, 600, 75, 300, 199}, # backend, booking/ordering, small fixes, separately scoped starter
    'booking-systems': {600, 300},       # ordering sits with booking
    'custom-software': {1500, 3500},     # apps are the bigger sibling
    'business-automation': {500, 600},   # integrations quoted alongside booking
    'seo': {450, 1350},             # its own floor and the AI search (GEO) pass
    'ai-chatbots': {750, 600},
    'ai-phone-agents': {1000, 600, 500},
    'business-dashboards': {750, 500},
    'mobile-apps': {3500, 1500},
}

# Legacy card-processing constants are named explicitly rather than allowed by a
# blanket "small numbers are fine" rule — a stray "$50 website" must still fail.
# Public copy must keep third-party fees provider- and plan-dependent.
FEE_CONSTANTS = {0.30}


ALL = set(FLOORS.values()) | set(PUBLIC_OFFERS.values()) | FEE_CONSTANTS
# budget brackets on the quote form are ranges, not prices
IGNORE_FILES = {'quote.html'}

# Social and classified cards are intentionally evergreen. A valid site floor
# is still invalid here: putting even a current amount back into either source
# would recreate a second rate card that can silently go stale.
PRICE_FREE_CREATIVE_SOURCES = (
    'tools/make_social.py',
    'tools/make_listing_images.py',
    'tools/make_fb.py',
)

CREATIVE_ASSET_CHECKS = tuple(
    (sys.executable, path, '--check') for path in PRICE_FREE_CREATIVE_SOURCES
)


def figures(text):
    """Every dollar amount, decimals included.

    The first version stopped at the decimal point, so "$0.30" read as $0 and
    tripped the check on correct copy, while a European-style "$1.500" meant to
    say fifteen hundred read as $1 and tripped it for the wrong reason. Both are
    the same bug: a price parser that cannot see a decimal is not reading prices.
    """
    out = []
    for m in re.finditer(r'\$([0-9][0-9,]*(?:\.[0-9]+)?)', text):
        v = float(m.group(1).replace(',', ''))
        out.append(int(v) if v == int(v) else v)
    return out

def main():
    os.chdir(ROOT)
    errors = []

    # 1. every service page may only show its own floor + declared cross-refs
    for path in sorted(glob.glob('services/*.html')):
        slug = os.path.basename(path)[:-5]
        if slug == 'index':
            continue
        allowed = CROSS.get(slug, {FLOORS.get(slug)}) | {FLOORS.get(slug)}
        allowed.discard(None)
        s = io.open(path, encoding='utf-8').read()
        for v in set(figures(s)):
            if v not in allowed:
                errors.append(f'{path}: ${v:,} is not this service\'s floor '
                              f'({FLOORS.get(slug)}) nor a declared cross-reference')

    # 2. no surface anywhere may show a figure that is not a published floor
    others = ([p for p in glob.glob('industries/*.html')]
              + ['index.html', 'about.html', 'call.html', 'missed-lead-recovery.html',
                 'technical-build-partner.html', 'llms.txt']
              + glob.glob('es/*.html') + glob.glob('pt/*.html')
              + glob.glob('zh/*.html'))
    for path in others:
        if not os.path.exists(path) or os.path.basename(path) in IGNORE_FILES:
            continue
        s = io.open(path, encoding='utf-8').read()
        for v in set(figures(s)):
            if v not in ALL:
                errors.append(f'{path}: ${v:,} is not a published floor')

    # 3. a range must ascend — "$600-$300" shipped live once
    for path in glob.glob('services/*.html') + glob.glob('industries/*.html') + ['llms.txt']:
        if not os.path.exists(path):
            continue
        s = io.open(path, encoding='utf-8').read()
        for m in re.finditer(r'\$([0-9][0-9,]*)\s*[–—-]\s*\$([0-9][0-9,]*)', s):
            lo = int(m.group(1).replace(',', ''))
            hi = int(m.group(2).replace(',', ''))
            if hi < lo:
                errors.append(f'{path}: descending range ${lo:,}-${hi:,}')

    # 4. a linked card must never promise less than the page it opens.
    # The industry cards are the highest-intent element on the site and they now
    # carry the reader to a priced service page. "from $600" opening a page that
    # starts at $1,500 is a bait-and-switch the visitor discovers one click in,
    # which is worse than the dead end this replaced. Direction only: a card may
    # quote ABOVE its target's floor, because an industry-shaped build legitimately
    # starts higher than the generic service.
    card = re.compile(
        r'<a class="fixcard link" href="/services/([a-z-]+)"[^>]*>.*?</a>', re.S)
    for path in sorted(glob.glob('industries/*.html')):
        s_html = io.open(path, encoding='utf-8').read()
        for m in card.finditer(s_html):
            slug = m.group(1)
            floor = FLOORS.get(slug)
            if floor is None:
                errors.append(f'{path}: card links to /services/{slug}, which has no floor')
                continue
            vals = figures(m.group(0))
            for v in vals:
                if v < floor:
                    errors.append(
                        f'{path}: a card promising ${v:,} opens /services/{slug}, '
                        f'which starts at ${floor:,}')

    # 5. the assistant quotes prices too, and it has its own copy of the list
    prompt = io.open('server/prompt.js', encoding='utf-8').read()
    for v in set(figures(prompt)):
        if v not in ALL:
            errors.append(f'server/prompt.js: ${v:,} is not a published floor')

    # 6. Generated creatives are evergreen, so any dollar amount is wrong even
    # when it happens to match today's site floor. PNGs are not reliably
    # searchable; their canonical copy dictionaries are.
    for path in PRICE_FREE_CREATIVE_SOURCES:
        source = io.open(path, encoding='utf-8').read()
        for v in set(figures(source)):
            errors.append(
                f'{path}: ${v:,} is embedded in evergreen creative source; '
                'social and listing images must not publish prices')

    social_source = io.open('tools/make_social.py', encoding='utf-8').read()
    for output in ('ig_01_prices.png', 'ig_02_pricing.png', 'ig_03_work.png'):
        if output not in social_source:
            errors.append(f'tools/make_social.py: canonical output missing: {output}')

    # A safe generator is not enough if an old PNG was committed beside it.
    # Byte-for-byte fresh renders make source/asset drift a normal test failure.
    # Old social/listing campaigns are archived and absent from the current
    # public manifest (enforced by check_subscription_public.py). Keep their
    # original byte checks available explicitly for any future reuse.
    for command in (CREATIVE_ASSET_CHECKS if "--include-legacy-creatives" in sys.argv else ()):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            detail = (result.stdout + result.stderr).strip().replace('\n', '; ')
            errors.append(f'{command[1]} --check failed: {detail}')

    if errors:
        print('PRICE CHECK FAILED')
        for e in errors:
            print('  -', e)
        return 1
    print(f'price check ok — {len(FLOORS)} service floors, every surface agrees')
    return 0


if __name__ == '__main__':
    sys.exit(main())
