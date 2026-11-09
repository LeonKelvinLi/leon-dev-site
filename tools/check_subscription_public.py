"""Validate the actual composed public manifest, including retired inbound routes."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from build_static import build_manifest, StaticBuildError
from check_site import SiteHTMLParser, validate_pages, validate_links, validate_hreflang, ROOT


def main():
    errors, warnings, pages, sources = [], [], [], {}
    try:
        manifest = build_manifest()
    except (ValueError, StaticBuildError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    retired_creatives = [str(relative) for relative in manifest
        if str(relative).startswith(('assets/social/', 'assets/listings/fb_'))
        or str(relative) == 'assets/facebook.png']
    if retired_creatives: errors.append('Retired campaign assets entered public output: ' + ', '.join(retired_creatives))
    for relative, source in manifest.items():
        if relative.suffix != '.html' or re.fullmatch(r'google[a-z0-9]+\.html', relative.name): continue
        content = source.read_text()
        parser = SiteHTMLParser(ROOT / relative)
        parser.feed(content)
        parser.close()
        pages.append(parser.page)
        sources[str(relative)] = content
        visible = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', content, flags=re.S | re.I)
        visible = re.sub(r'<[^>]+>', ' ', visible)
        for obsolete in [r'\$(?:199|300|400|500|625|750|1,500|2,000|3,500)\b', r'Systems Plan', r'Focused Build Sprint']:
            if re.search(obsolete, visible, re.I): errors.append(f'{relative}: retired public offer: {obsolete}')
        if str(relative).startswith(('services/','industries/','es/','pt/','zh/')) or str(relative) in {'quote.html','call.html','technical-build-partner.html','missed-lead-recovery.html'}:
            if 'noindex,follow' not in content: errors.append(f'{relative}: transition page must be noindex')
            if '2,499/year' not in visible: errors.append(f'{relative}: annual membership missing')
    canonicals = validate_pages(pages, errors, warnings)
    validate_links(pages, canonicals, errors)
    validate_hreflang(canonicals, errors)
    sitemap = ET.parse(manifest[Path('sitemap.xml')])
    actual = {(el.text or '').strip() for el in sitemap.getroot().iter() if el.tag.endswith('}loc')}
    expected = {url for url, page in canonicals.items() if 'noindex,follow' not in sources[page.label]}
    if actual != expected: errors.append(f'sitemap differs from indexable public pages: {actual ^ expected}')
    root = sources['index.html']
    for target in ['24 hours over 12 months','before you pay','two business days','renewal is manual']:
        if target.lower() not in root.lower(): errors.append(f'homepage missing {target}')
    if 'Disallow: /images/leon-kelvin-li' not in manifest[Path('robots.txt')].read_text(): errors.append('portrait crawler restriction missing')
    for error in errors: print(error, file=sys.stderr)
    for warning in warnings: print('warning: '+warning)
    if errors: return 1
    print(f'Public subscription check passed: {len(pages)} routes, {len(actual)} indexable, retired offers removed, internal links and metadata valid.')
    return 0

if __name__ == '__main__': raise SystemExit(main())
