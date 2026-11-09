"""Build the public subscription surfaces without altering historical source or records.

Old inbound routes stay reachable, but their competing packages are retired. Source
ledgers remain historical evidence; this overlay is validated separately at build time.
"""
from pathlib import Path, PurePosixPath
import html
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://leonbuilds.org'
RETAIN = {'about.html', 'privacy.html', 'work.html', 'reviews.html',
    'work/allcpr-site-intelligence.html', 'work/curio-app.html',
    'work/beastypages-website.html', 'work/loqol-seller-portal.html',
    'guides/contractor-inquiry-workflow.html', 'guides/website-builder-or-custom-software.html'}
CSS = '''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#faf9f6;color:#202422;font:16px/1.8 system-ui,sans-serif}a{color:#304f3f;text-underline-offset:4px}a:focus-visible,summary:focus-visible{outline:3px solid #557d37;outline-offset:4px}header,footer,main{max-width:900px;width:calc(100% - 40px);margin:auto}header{display:flex;align-items:center;justify-content:space-between;padding:25px 0;border-bottom:1px solid #dedfd8;font-size:13px}.brand{font-size:20px;font-weight:650;letter-spacing:-1px;text-decoration:none}main{padding:65px 0 80px}h1{font-size:clamp(35px,6vw,62px);line-height:1.1;letter-spacing:-2px;font-weight:550}h2{font-size:29px;line-height:1.25;letter-spacing:-1px;font-weight:550;margin-top:40px}h3{font-size:20px;line-height:1.4}p,li{color:#626761}p{max-width:760px}img{max-width:100%;height:auto;border-radius:8px}svg{max-width:22px;max-height:22px}figure{margin:35px 0}figcaption{font-size:12px;color:#626761}section,article{margin-top:30px}.eyebrow{font-size:11px;letter-spacing:.1em;color:#657455}.button{display:inline-block;text-decoration:none;background:#304f3f;color:white;padding:13px 22px;border-radius:5px;font-size:14px;margin:12px 10px 12px 0}.offer{padding:24px 28px;background:#eff2e6;border:1px solid #dce2d1;border-radius:8px;margin-top:35px}.offer h2{margin:0;font-size:28px}.offer p{font-size:14px}.offer strong{color:#344b3b}.card,.evidence-grid,.work-row,.case-deliverables,.proof-grid{padding:15px 0;border-bottom:1px solid #dedfd8}footer{border-top:1px solid #dedfd8;padding:25px 0;font-size:12px;display:flex;justify-content:space-between;gap:15px;flex-wrap:wrap}details{border-bottom:1px solid #dedfd8;padding:16px 0}summary{cursor:pointer}details p{font-size:14px}blockquote{border-left:3px solid #c5d1b5;padding:5px 20px;margin:25px 0}.ctarow,.assist-fallback,.site-orbit,.hero-visual,.scroll-cue,.service-price,.pricing-grid,.price-grid,.partner-packages,.quoteform,.cal-embed,.mobile-cta,.site-footer,.site-nav{display:none!important}.claim-boundary{background:#f0f1ea;padding:20px;border-radius:5px}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}@media(max-width:580px){main{padding:45px 0}h1{letter-spacing:-1.5px}.offer{padding:22px}header{font-size:11px}p,li{font-size:14px}h2{font-size:25px}figure{margin-inline:0}}'''


def offer_block():
    return '''<section class="offer" aria-label="Current membership"><p class="eyebrow">THE CURRENT LEONBUILDS OFFER</p><h2>Your Personal Developer</h2><p><strong>$2,499/year</strong> · Equivalent to $208.25/month, billed annually.</p><p>24 hours over 12 months, released as 2 hours each month. One active request. Estimates approved before work. Planning, calls, design, development, testing, revisions, and support use this allowance.</p><p>Unused hours carry forward within the membership year and expire at its end or cancellation. Hosting, tools, AI usage, and large projects cost extra. I aim to reply within two business days; delivery is scheduled per request.</p><p>Manual renewal, with no automatic charge. Cancel by email; unused future full months are refunded at $208.25 each. Completed and current months are not refundable. Paid custom deliverables are yours; existing tools retain their licenses. Full written terms and fit are confirmed before payment.</p><a class="button" href="/#start">Start Building ↗</a><a href="/#scope">Read the full service details</a></section>'''


def route_for(relative):
    name = str(relative)
    if name == 'index.html': return '/'
    if name.endswith('/index.html'): return '/' + name[:-10].rstrip('/')
    return '/' + name[:-5]


def page(title, description, path, body, noindex=False, language='en'):
    schema = {'@context':'https://schema.org','@type':'WebPage','name':title,'url':BASE+path,'isPartOf':{'@id':BASE+'/#business'}}
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ''
    return '<!doctype html><html lang="'+language+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+' | LeonBuilds</title><meta name="description" content="'+html.escape(description, quote=True)+'"><link rel="canonical" href="'+BASE+path+'">'+robots+'<link rel="icon" href="/favicon.svg"><style>'+CSS+'</style><script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script></head><body><header><a class="brand" href="/">LeonBuilds.</a><a href="/#start">Tell me your idea ↗</a></header>'+body+'<footer><a href="/">Your Idea. I’ll Build It.</a><a href="/#scope">Service details</a><a href="/privacy">Privacy</a><span>© 2026 LeonBuilds</span></footer></body></html>\n'


def retained_page(relative, original):
    title = re.search(r'<title>(.*?)</title>', original, re.S | re.I)
    title = html.unescape(title.group(1)).split('|')[0].strip() if title else 'Selected work'
    desc = re.search(r'<meta\b[^>]*name="description"[^>]*content="([^"]+)"', original, re.I)
    description = html.unescape(desc.group(1)) if desc else 'Selected work and practical software development with Leon Kelvin Li. Learn about the current LeonBuilds membership.'
    main = re.search(r'<main\b[^>]*>(.*?)</main>', original, re.S | re.I)
    if not main: raise ValueError(f'{relative}: missing main content')
    body = main.group(1)
    # Preserve actual portfolio evidence, privacy disclosures, and educational text.
    # Replace old conversion/footer blocks; do not convert historical case results.
    body = re.sub(r'<script\b[^>]*>.*?</script>', '', body, flags=re.S | re.I)
    body = re.sub(r'<section\b[^>]*class="[^"]*(?:cta-section|final-cta)[^"]*"[^>]*>.*?</section>', '', body, flags=re.S | re.I)
    body = body.replace('/quote', '/#start').replace('/call', '/#start')
    body = re.sub(r'/#start\?[^\"#\s<>]*', '/#start', body)
    body = re.sub(r'get a fixed quote|Get a fixed quote|Request a quote|request a quote', 'Discuss your idea', body)
    body = re.sub(r'book a free 15-minute call|Book a free 15-minute call', 'Start with a scope discussion', body)
    body = re.sub(r'(<a\b[^>]*href="/services/[^>]+>).*?(</a>)', r'\1Explore the current membership →\2', body, flags=re.S)
    return page(title, description, route_for(relative), '<main id="main">'+body+offer_block()+'</main><script src="/site-motion.js" defer></script>')


def bridge_page(relative, original):
    path = route_for(relative)
    title_match = re.search(r'<h1\b[^>]*>(.*?)</h1>', original, re.S | re.I)
    former_title = html.unescape(re.sub('<[^>]+>',' ',title_match.group(1))).strip() if title_match else 'A place to start'
    former_title = re.sub(r'\s+',' ',former_title)
    body = '<main id="main"><p class="eyebrow">A SIMPLER WAY TO BUILD TOGETHER</p><h1>Your Idea. I’ll Build It.</h1><p>This page now leads to the LeonBuilds personal developer membership. The previous standalone packages and prices have been retired.</p><p>Whether you need a website, a focused automation, or a small custom tool, start by telling me what you want to build. We confirm the first deliverable fits your available hours before you pay.</p>'+offer_block()+'</main>'
    return page(former_title+' — current membership', 'LeonBuilds now offers one personal developer membership: $2,499/year with 24 scoped hours. Review the details and discuss your idea before payment.', path, body, noindex=True)


def generate(pages, write=False):
    directory = ROOT / 'content/subscription-public'
    out = {}
    indexable = ['/']
    for relative in pages:
        if str(relative) == 'index.html': continue
        original = (ROOT / relative).read_text()
        if str(relative) in RETAIN:
            content = retained_page(relative, original)
            indexable.append(route_for(relative))
        else:
            content = bridge_page(relative, original)
        target = directory / relative
        save(target, content, write)
        out[relative] = target
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('<url><loc>'+BASE+path+'</loc></url>\n' for path in indexable)+'</urlset>\n'
    sm = directory/'sitemap.xml'
    save(sm, sitemap, write)
    out[PurePosixPath('sitemap.xml')] = sm
    llms = '''# LeonBuilds
Your Idea. I’ll Build It. A personal developer membership with Leon Kelvin Li.
Price: $2,499/year, paid annually; $208.25/month equivalent.
Allowance: 24 hours/year, released 2 hours monthly, one active request, estimates approved before work. All planning, calls, design, development, testing, revisions, and support count. Hours carry within the year and expire at end/cancellation.
No unlimited work. Complex applications and large projects need separate quotes. Hosting, domains, AI usage, and other third-party costs are extra.
Fit and written terms confirmed before payment. Response target two business days, not an SLA. Manual renewal; cancel by email. Unused future full months refunded at $208.25 each; current/completed months not refundable.
Paid custom deliverables belong to the customer, subject to pre-existing and third-party licenses.
Start: https://leonbuilds.org/#start
Service scope and FAQ: https://leonbuilds.org/#scope
Public proof you can inspect: /work/curio-app, /work/beastypages-website, /work/allcpr-site-intelligence, /work/loqol-seller-portal.
The Home Screen historical demo checkout: payments and kitchen operations are not live. Portfolio work does not establish that a whole app fits the membership.
Old service and industry URLs are noindex transition pages. Only the current membership should be quoted. Never invent reviews, ratings, revenue, or a guaranteed delivery date.
'''
    lp = directory/'llms.txt'
    save(lp, llms, write)
    out[PurePosixPath('llms.txt')] = lp
    return out


def save(target, content, write):
    if target.is_symlink() or ROOT not in target.resolve().parents:
        raise ValueError('unsafe subscription source path: ' + str(target))
    if target.exists() and target.read_text() == content: return
    if not write: raise ValueError('Subscription public pages need regeneration: run python3 tools/subscription_public.py')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)

if __name__ == '__main__':
    from build_static import sitemap_pages
    generated = generate(sitemap_pages(), write=True)
    print(f'Prepared {len(generated)} subscription public surfaces; no deployment.')
