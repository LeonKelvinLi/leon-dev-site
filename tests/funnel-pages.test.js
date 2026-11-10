'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const ROOT = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');
const approvedTestimonials = () => JSON.parse(
  read('content/client-success/testimonial-publication.json')
).approved_testimonials;

function inlineScripts(html) {
  const scripts = [];
  const re = /<script([^>]*)>([\s\S]*?)<\/script>/g;
  let match;
  while ((match = re.exec(html))) {
    if (/application\/ld\+json/i.test(match[1])) continue;
    if (match[2].trim()) scripts.push(match[2]);
  }
  return scripts;
}

function mainOnly(html) {
  return html.match(/<main\b[^>]*>[\s\S]*?<\/main>/i)?.[0] || '';
}

test('quote submission waits for a receipt and keeps mailto as a fallback', () => {
  const html = read('quote.html');

  assert.match(html, /<title>Get a Fixed Quote \| Leon Builds<\/title>/i);
  assert.match(html, /<form class="qform" id="qform" method="post" action="\/quote"/);
  assert.match(html, /<noscript>[\s\S]*mailto:leondragon3798@gmail\.com[\s\S]*tel:\+15108267735[\s\S]*<\/noscript>/);
  assert.match(html, /await fetch\(API\+'\/api\/lead'/);
  assert.match(html, /method:'POST'/);
  assert.match(html, /result\.receiptId/);
  assert.match(html, /id="qreceipt"/);
  assert.match(html, /id="qfail" hidden/);
  assert.match(html, /manual\.href=mailtoFor\(d\)/);
  assert.doesNotMatch(html, /window\.location\.href/);
  assert.doesNotMatch(html, /keepalive:true/);
  assert.doesNotMatch(html, /quote_form_submit/);
  assert.match(html, /track\('quote_lead_accepted',\{receipt:receiptId\}\)/);
  for (const field of [
    'utmSource', 'utmMedium', 'utmCampaign', 'utmTerm', 'utmContent',
    'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid',
    'firstPage', 'firstReferrer', 'firstUtmSource', 'firstUtmMedium',
    'firstUtmCampaign', 'firstUtmTerm', 'firstUtmContent', 'firstGclid',
    'firstGbraid', 'firstWbraid', 'firstFbclid', 'firstMsclkid',
    'lastPage', 'lastReferrer', 'lastUtmSource', 'lastUtmMedium',
    'lastUtmCampaign', 'lastUtmTerm', 'lastUtmContent', 'lastGclid',
    'lastGbraid', 'lastWbraid', 'lastFbclid', 'lastMsclkid',
    'analyticsSessionId'
  ]) assert.match(html, new RegExp(`d\\.${field}=`));
  assert.match(html, /sessionStorage\.getItem\('leon_analytics_session'\)/);
  assert.match(html, /sessionStorage\.getItem\(attemptStorage\)/);
  assert.match(html, /sessionStorage\.setItem\(attemptStorage/);
  assert.match(html, /submissionKey=submissionKeyFor\(d\)/);
  assert.match(html, /service==='contractor-lead-recovery'/);
  assert.match(html, /Request the 3-point review/);
  assert.match(html, /name="package" type="hidden"/);
  assert.match(html, /name="websiteUrl"[^>]*inputmode="url"/);
  assert.match(html, /raw=\['service','package','websiteUrl','problem'/);
  assert.match(html, /line\('website',d\.websiteUrl\)/);

  for (const event of [
    'quote_submit_attempt',
    'quote_validation_failed',
    'quote_lead_accepted',
    'quote_lead_failed'
  ]) assert.match(html, new RegExp(`track\\('${event}'(?:\\)|,)`));

  const visibleRequired = html.match(/<(?:input|textarea|select)[^>]*\srequired(?:\s|>)/g) || [];
  assert.equal(visibleRequired.length, 2);
  assert.match(html, /What are you trying to fix or build\?<\/span> <i>\(required\)<\/i>/i);
  assert.match(html, /Name <i>\(optional\)<\/i>/i);
  assert.match(html, /Email <i>\(required\)<\/i>/i);
  assert.match(html, /<details>[\s\S]*<summary>Add project details <i>\(optional\)<\/i><\/summary>/i);
  assert.match(html, /<button[^>]*type="submit"[^>]*>[\s\S]*Send my project details/i);
  assert.doesNotMatch(html, /Need help describing it\?|data-assist-open/i);
  assert.match(html, /No payment or commitment\.[\s\S]*scope and price are agreed before work begins/i);
  assert.ok(html.indexOf('name="websiteUrl"') < html.indexOf('name="problem"'));
  assert.ok(html.indexOf('name="problem"') < html.indexOf('name="email"'));
  assert.ok(html.indexOf('name="email"') < html.indexOf('type="submit"'));
  assert.ok(html.indexOf('type="submit"') < html.indexOf('<details>'));
  const optionalDetails = html.match(/<details>[\s\S]*?<\/details>/i)?.[0] || '';
  assert.match(optionalDetails, /name="name"/i, 'optional name stays inside optional project details');
  for (const field of ['company', 'currentTools', 'desiredOutcome', 'timeline', 'budget', 'phone']) {
    assert.match(html, new RegExp(`name="${field}"`));
  }

  const ids = Array.from(html.matchAll(/\bid="([^"]+)"/g), match => match[1]);
  assert.equal(new Set(ids).size, ids.length, 'quote page has no duplicate static IDs');

  for (const script of inlineScripts(html)) assert.doesNotThrow(() => new vm.Script(script));
});

test('all booking pages expose a resilient, privacy-bounded calendar funnel', () => {
  const pages = ['call.html', 'pt/agendar.html', 'es/agendar.html', 'zh/yuyue.html'];
  for (const file of pages) {
    const html = read(file);
    assert.match(html, /id="leon-booker"[^>]*aria-busy="true"[^>]*min-height:680px/);
    assert.match(html, /https:\/\/cal\.com\/leonbuilds\/15min\?redirect=false/);
    assert.match(html, /action:'bookerReady'/);
    assert.match(html, /action:'linkFailed'/);
    assert.match(html, /action:'bookingSuccessfulV2'/);
    assert.match(html, /track\('calendar_ready'\)/);
    assert.match(html, /track\('calendar_failed'\)/);
    assert.match(html, /track\('calendar_booking_success'/);
    assert.match(html, /function booked\(payload\)/);
    assert.match(html, /data\.uid\|\|\(data\.booking&&data\.booking\.uid\)/);
    assert.match(html, /var extra=\{bookingUid:bookingUid\}/);
    assert.match(html, /\^\[A-Za-z0-9\._~-\]\{8,64\}\$/);
    assert.match(html, /track\('calendar_booking_uid_missing'\)/);
    assert.match(html, /extra\.service=service/);
    assert.match(html, /extra\.package=packageName/);
    assert.ok(html.indexOf("track('calendar_booking_uid_missing')") < html.indexOf('bookedTracked=true'), 'a missing UID cannot latch the conversion');
    assert.doesNotMatch(html, /track\('calendar_booking_success',payload\)/);
    assert.match(html, /query\.get\('s'\)/);
    assert.match(html, /out\.utm_source=source/);
    assert.match(html, /out\.utm_medium=medium/);
    assert.match(html, /out\.utm_campaign=campaign/);
    assert.match(html, /out\.utm_term=term/);
    assert.match(html, /out\.utm_content=content/);
    assert.match(html, /id="leon-cal-direct"/);
    assert.match(html, /class="btn calendar-direct"[^>]*id="leon-cal-direct"/);
    assert.ok(html.indexOf('id="leon-cal-direct"') < html.indexOf('id="leon-booker"'), 'direct booking fallback appears before the tall embed');
    assert.match(html, /<body\b[^>]*data-assistant-launcher="hidden"/i);
    assert.match(html, /hideEventTypeDetails:false/);
    assert.match(html, /\['utm_source','utm_medium','utm_campaign','utm_term','utm_content'\]/);
    assert.doesNotMatch(html, /out\.(?:gclid|gbraid|wbraid|fbclid|msclkid)/);
    assert.doesNotMatch(html, /forwardQueryParams/);
    assert.doesNotMatch(html, /query\.get\('(email|name|phone)'\)/);
    assert.doesNotMatch(html, /callform|CALL_JS/);
    for (const script of inlineScripts(html)) assert.doesNotThrow(() => new vm.Script(script));
  }
});

test('browser attribution captures only bounded campaign identifiers with first/last touch', () => {
  const source = read('assist.js');
  for (const queryField of [
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid'
  ]) assert.match(source, new RegExp(`'${queryField}'`));
  assert.match(source, /ATTR_TTL_MS = 90 \* 24 \* 60 \* 60 \* 1000/);
  assert.match(source, /referrerOrigin\(document\.referrer\)/);
  assert.match(source, /applyAttribution\(payload\)/);
  assert.match(source, /applyAttribution\(leadBody\)/);
  assert.doesNotMatch(source, /current\.forEach\(function \(value, key\)/);
});

test('generator remains the source for each localized booking variant', () => {
  const source = read('tools/build_pages.py');
  assert.match(source, /def booker\(lang="en"\):/);
  assert.match(source, /booker_html = booker\("en"\)/);
  assert.match(source, /render_call\(_lang, booker\(_lang\), LANG_CTX\)/);
  assert.doesNotMatch(source, /CALL_JS|id="callform"/);
});

test('contractor lead recovery is a focused website plus follow-up product', () => {
  const html = read('missed-lead-recovery.html');
  const visible = html
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim();
  const main = html.match(/<main\b[^>]*>[\s\S]*?<\/main>/i)?.[0] || '';
  const mainWords = main
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  assert.match(html, /<link rel="canonical" href="https:\/\/leonbuilds\.org\/missed-lead-recovery">/);
  assert.match(html, /"@type": "Service"/);
  assert.match(html, /"name": "Contractor Lead Recovery System"/);
  assert.match(html, /"name": "United States"/);
  assert.match(html, /"price": "1500"/);
  assert.match(html, /Contractor website \+ missed-lead follow-up/i);
  assert.ok(html.indexOf('class="sec page-hero"') < html.indexOf('id="scope"'));
  assert.match(visible, /A contractor website that captures estimate requests and follows up automatically\./i);
  assert.match(visible, /Leon builds the site, estimate form, prompt automatic acknowledgment, owner handoff, and up to two follow-ups/i);
  assert.match(visible, /Fixed scope starts at \$1,500; timing follows the written scope and access check/i);
  assert.doesNotMatch(visible, /10[- ]business|10-day/i);
  assert.match(html, /structured (?:estimate )?intake/i);
  assert.match(visible, /Based in California\. Working remotely with contractors and home-service businesses across the U\.S\./i);
  assert.doesNotMatch(html, /id="fit"|id="workflow"|id="automotive"|id="restaurants"|related-services/i, 'removed repetitive sections stay removed');
  assert.match(html, /id="scope"/);
  assert.match(html, /id="proof" aria-labelledby="contractor-proof-title"/);
  assert.match(html, /id="faq"/);
  assert.match(html, /class="rail landing-jump"/);
  for (const href of ['#scope', '#proof', '#faq']) assert.match(html, new RegExp(`href="${href}"`));
  assert.ok(html.indexOf('class="landing-jump-wrap"') < html.indexOf('id="scope"'), 'find-it-fast links appear before the detailed scope');
  assert.ok(html.indexOf('id="scope"') < html.indexOf('id="proof"'), 'scope appears before proof');
  const faqBlock = html.match(/<div class="faq">[\s\S]*?<\/div>/)?.[0] || '';
  assert.equal((faqBlock.match(/<details\b/g) || []).length, 3, 'contractor landing keeps three FAQs');
  assert.match(visible, /Client website project · demo checkout/i);
  assert.match(visible, /beastypages\.com/i);
  assert.match(visible, /Illustrative workflow · not a live client result/i);
  assert.match(visible, /See the estimate-to-follow-up path/i);
  assert.match(html, /<ol class="contractor-example business-copy" aria-label="Example estimate follow-up workflow">/);
  for (const step of ['Estimate request', 'Clear acknowledgment', 'Owner handoff', 'Follow-up with limits']) assert.match(visible, new RegExp(step));
  assert.match(visible, /A reply or opt-out stops the sequence/i);
  assert.match(visible, /evidence of website delivery, not a contractor lead or revenue result/i);
  assert.match(visible, /Payment and kitchen progression are simulations/i);
  assert.match(html, /href="\/work\/beastypages-website"/i);
  assert.match(html, /href="\/guides\/contractor-inquiry-workflow"/i);
  assert.match(html, /id="proof"[^>]*data-view-event="proof_view"/i);
  assert.match(html, /id="faq"[^>]*data-view-event="start_section_view"/i);
  assert.match(html, /30 days of fixes (?:for defects )?against the (?:agreed )?written scope/);
  assert.match(visible, /Provider fees remain with the provider/i);
  assert.match(html, /data-evt="cta_call_click"/);
  assert.match(html, /href="\/call\?service=contractor-lead-recovery" data-evt="cta_call_click"/);
  assert.match(html, /href="\/quote\?service=contractor-lead-recovery" data-evt="contractor_review_click"/);
  assert.match(html, /Get a free 3-point website review/i);
  assert.match(html, /href="\/quote" data-evt="contractor_fixed_quote_click"/);
  assert.match(visible, /No call or paid planning session required/);
  assert.match(html, /Prefer to talk\? Book 15 minutes/i);
  assert.match(visible, /three specific observations by email/i);
  assert.equal((html.match(/href="\/call\?service=contractor-lead-recovery"/g) || []).length, 2, 'booking remains prominent in hero and final CTA');
  assert.equal((html.match(/href="\/quote\?service=contractor-lead-recovery"/g) || []).length, 2, 'the lower-friction written review remains prominent');
  assert.ok((html.match(/<section\b/g) || []).length <= 5, 'landing page stays to the approved focused structure');
  assert.ok(mainWords.length <= 650, `contractor landing has ${mainWords.length} main words; maximum is 650`);
  assert.doesNotMatch(html, /\$2,500/);
  assert.doesNotMatch(html, /guarantee(?:d|s)? (?:leads|bookings|revenue)/);
  const hasRelevantFeedback = approvedTestimonials().some(item => ['testimonial-03', 'testimonial-04', 'testimonial-05'].includes(item.id));
  if (hasRelevantFeedback) {
    assert.match(html, /id="client-feedback"/);
    assert.match(html, /href="#client-feedback">Client feedback<\/a>/);
    assert.ok(html.indexOf('id="scope"') < html.indexOf('id="client-feedback"'));
    assert.ok(html.indexOf('id="client-feedback"') < html.indexOf('id="proof"'));
  } else {
    assert.doesNotMatch(html, /id="client-feedback"|data-testimonial-id|testimonial-stars|5 out of 5 stars/);
    assert.doesNotMatch(html, /href="#client-feedback"/);
  }
  assert.match(read('sitemap.xml'), /<loc>https:\/\/leonbuilds\.org\/missed-lead-recovery<\/loc>/);

  const call = read('call.html');
  assert.match(call, /service==='contractor-lead-recovery'/);
  assert.match(call, /Book a free <em>15-minute website review<\/em>/);
  assert.match(read('app.js'), /closest\('\.contractor-landing,\.contractor-call-context,\.technical-partner-page,\.technical-partner-call-context'\)/);

  assert.match(mainOnly(read('industries/contractors.html')), /href="\/missed-lead-recovery"/);
  assert.doesNotMatch(mainOnly(read('industries/automotive.html')), /href="\/missed-lead-recovery/);
  assert.doesNotMatch(mainOnly(read('industries/restaurants.html')), /href="\/missed-lead-recovery/);

  const copyGate = read('tools/check_copy.py');
  assert.match(copyGate, /TARGETED_PLACE_OK = \{\}/);
});

test('technical build partner is a concrete, attributable offer with honest timing', () => {
  const html = read('technical-build-partner.html');
  const visible = html
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim();

  assert.match(html, /<title>Websites, Apps &amp; Automation for Small Businesses \| Leon Builds<\/title>/);
  assert.match(html, /<meta name="description" content="Work directly with Leon to build a website, automate repeat tasks, or create a custom tool or app\. Clear scope, upfront pricing, and a free project quote\.">/);
  assert.match(html, /<link rel="canonical" href="https:\/\/leonbuilds\.org\/technical-build-partner">/);
  assert.match(html, /<body class="technical-partner-page" data-assistant-launcher="hidden">/);
  assert.match(visible, /Your website, tools, and apps\. Handled by Leon\./i);
  assert.match(visible, /recommend a practical solution, build it, and make sure it works/i);
  assert.match(visible, /first reviewable milestone can be targeted within 1–3 business days/i);
  assert.match(visible, /Free project quote.*I reply by email/i);
  assert.match(visible, /(?:Systems Plan \$199|\$199 Systems Plan)/i);
  assert.match(visible, /One-time project[^$]*From \$1,500/i);
  assert.match(visible, /Ongoing partner[^$]*From \$2,000\/month/i);
  assert.match(visible, /one primary milestone plus agreed maintenance or fixes/i);
  assert.match(visible, /capacity, exclusions, and how unfinished work carries over before the month starts/i);
  assert.match(visible, /45-minute working session/i);
  assert.match(visible, /Requesting a quote is free/);
  assert.match(visible, /optional.*Systems Plan/);
  assert.match(visible, /weekly progress note/i);
  assert.match(visible, /This is not the full build/i);
  assert.match(visible, /Read 3 client reviews/i);
  assert.match(html, /class="fixrow partner-proof-grid"/);
  assert.match(html, /class="service-proof-media proof-phone-pair"><img src="\/assets\/proof\/home-screen-catalog\.png" alt="beastypages\.com catalog of local-business destinations"/);
  assert.match(html, /<img src="\/assets\/proof\/home-screen-menu\.png" alt="beastypages\.com business-specific menu and demonstration cart"/);
  assert.match(html, /package=systems-plan" data-evt="technical_partner_systems_plan_click"/);
  assert.match(html, /package=focused-build-sprint" data-evt="technical_partner_sprint_click"/);
  assert.match(html, /package=ongoing-technical-partner" data-evt="technical_partner_ongoing_click"/);
  assert.match(html, /href="\/call\?service=technical-build-partner"/);
  assert.match(html, /href="\/quote\?service=technical-build-partner"/);
  assert.equal((html.match(/href="\/call\?service=technical-build-partner"/g) || []).length, 2);
  assert.equal((html.match(/href="\/quote\?service=technical-build-partner"/g) || []).length, 2);
  assert.match(html, /class="btn btn-solid magnet" href="\/quote\?service=technical-build-partner"[^>]*data-evt="technical_partner_quote_click"/);
  assert.match(html, /technical_partner_quote_click[\s\S]*technical_partner_call_click/);
  assert.doesNotMatch(html, /data-testimonial-id=/, 'approved testimonial placement is not expanded without permission');
  assert.match(html, /"@type": "WebPage"/);
  assert.match(html, /"@type": "Service"/);
  assert.match(html, /"@type": "BusinessAudience"/);
  assert.match(html, /"price": "199"/);
  assert.match(html, /"minPrice": "1500"/);
  assert.match(html, /"minPrice": "2000"/);
  assert.doesNotMatch(html, /"price": "(?:1500|2000)"/);
  assert.match(html, /"unitText": "MONTH"/);
  const faqBlock = html.match(/<div class="faq">[\s\S]*?<\/div>/)?.[0] || '';
  assert.equal((faqBlock.match(/<details\b/g) || []).length, 4);

  for (const file of [
    'services/index.html', 'about.html', 'work.html',
    'services/websites.html', 'services/business-automation.html',
    'services/business-dashboards.html', 'services/custom-software.html',
    'services/mobile-apps.html'
  ]) assert.match(read(file), /href="\/technical-build-partner"/, `${file} links to the offer`);

  const homepage = read('homepage/index.html');
  assert.equal((homepage.match(/class="build-card /g) || []).length, 6, 'membership exposes six bounded examples');
  assert.match(homepage, /href="#start"[^>]*data-evt="subscription_hero_cta"/);
  assert.match(homepage, /24 hours over 12 months/);
  assert.match(read('sitemap.xml'), /<loc>https:\/\/leonbuilds\.org\/technical-build-partner<\/loc>/);

  const call = read('call.html');
  assert.match(call, /service==='technical-build-partner'/);
  assert.match(call, /Your website, app, or automation project/);
  assert.match(call, /Book a free <em>15-minute project call<\/em>/);
  assert.match(call, /call_context_technical_partner/);
  assert.match(call, /trackContext\('call_context_technical_partner',context\)/);
  assert.match(call, /packageName==='systems-plan'/);

  const quote = read('quote.html');
  assert.match(quote, /technicalPartner=service==='technical-build-partner'/);
  assert.match(quote, /Website, app, or automation project/);
  assert.match(quote, /Send my project details/);
  assert.match(quote, /technical build partner inquiry/);
  assert.match(quote, /One-time project · from \$1,500/);
  assert.match(quote, /What is the first part of the project you want built\?/);
  assert.match(quote, /Describe the part of your project you want built first/);
  assert.match(quote, /Ongoing partner · from \$2,000\/month/);
  assert.match(quote, /What would you like help with each month, and what should come first\?/);
  assert.match(quote, /I will propose an agreed monthly scope; this is not unlimited development/);
  assert.match(quote, /packageName=.*get\('package'\)/);
  assert.match(quote, /bookCall\.href='\/call\?service='/);
  assert.match(quote, /details\.service=service/);
  assert.match(quote, /details\.package=packageName/);

  assert.match(read('assist.js'), /\['receipt', 'bookingUid', 'status', 'service', 'package'\]/);
  assert.match(read('server/events.js'), /\['receipt', 'bookingUid', 'status', 'service', 'package'\]/);
  assert.match(read('llms.txt'), /Technical Build Partner[\s\S]*Systems Plan: \$199/);
  assert.match(read('server/prompt.js'), /\$2,499\/year billed annually/);
});

test('metadata, handoff copy, and generated footer stay honest and synchronized', () => {
  const source = read('tools/build_pages.py');
  const ownershipOutputs = [
    'about.html', 'services/index.html',
    ...fs.readdirSync(path.join(ROOT, 'services')).filter(f => f.endsWith('.html')).map(f => `services/${f}`),
    ...fs.readdirSync(path.join(ROOT, 'industries')).filter(f => f.endsWith('.html')).map(f => `industries/${f}`)
  ];
  const ownershipCorpus = [source, ...ownershipOutputs.map(read)].join('\n');
  for (const stale of [
    'you own everything',
    'a fast site you own completely',
    'you own the developer accounts and the code from day one',
    'you own the code and hosting',
    'completely — repo, accounts and infrastructure from day one'
  ]) assert.doesNotMatch(ownershipCorpus, new RegExp(stale));
  assert.match(source, /included source code/);
  assert.match(source, /third-party (?:hosts|infrastructure|services)/);

  const localizedCorpus = [
    'es/pagina-web.html', 'es/pedidos-en-linea.html', 'es/automatizacion.html',
    'pt/criar-site.html', 'pt/pedidos-online.html', 'pt/automacao.html',
    'zh/zuo-wangzhan.html', 'zh/zaixian-diandan.html', 'zh/zidonghua.html'
  ].map(read).join('\n');
  for (const stale of [
    'todo queda a tu nombre',
    'el sistema es tuyo, completo',
    'tudo fica no seu nome',
    'tudo é seu, completo',
    '域名、服务器、代码、账号和数据都在你名下'
  ]) assert.doesNotMatch(localizedCorpus, new RegExp(stale));
  assert.match(localizedCorpus, /(?:servicios de terceros|serviços de terceiros|第三方服务)/);

  const descriptions = ['zh/yuyue.html', 'services/booking-systems.html', 'services/business-dashboards.html'];
  for (const file of descriptions) {
    const match = read(file).match(/<meta name="description" content="([^"]+)">/);
    assert.ok(match, `${file} has a meta description`);
    assert.ok(Array.from(match[1]).length >= 50, `${file} description is at least 50 characters`);
    assert.ok(Array.from(match[1]).length <= 160, `${file} description is at most 160 characters`);
  }

  const generated = [
    'about.html', 'call.html', 'quote.html', 'missed-lead-recovery.html', 'technical-build-partner.html', 'services/index.html', 'industries/index.html',
    ...fs.readdirSync(path.join(ROOT, 'services')).filter(f => f.endsWith('.html')).map(f => `services/${f}`),
    ...fs.readdirSync(path.join(ROOT, 'industries')).filter(f => f.endsWith('.html')).map(f => `industries/${f}`)
  ];
  for (const file of new Set(generated)) {
    const html = read(file);
    assert.match(html, /href="\/privacy"/);
    assert.match(html, /data-evt="footer_email_click"/);
    assert.match(html, /data-evt="footer_phone_click"/);
  }
  assert.match(read('about.html'), /data-evt="about_quote_click"/);
  assert.match(read('sitemap.xml'), /<loc>https:\/\/leonbuilds\.org\/privacy<\/loc>/);
});
