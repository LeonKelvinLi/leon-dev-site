'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const ROOT = path.join(__dirname, '..');
const SOURCE = fs.readFileSync(path.join(ROOT, 'assist.js'), 'utf8');

const LABELS = {
  quote: 'AW-18407115426/ldkYCNKtreccEKKVmclE',
  booking: 'AW-18407115426/owGxCNWtreccEKKVmclE',
  phone: 'AW-18407115426/UrycCNitreccEKKVmclE',
  whatsapp: 'AW-18407115426/CGJTCNutreccEKKVmclE'
};

function storage(seed = {}) {
  const values = new Map(Object.entries(seed));
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { values.delete(key); }
  };
}

function harness(seed = {}, sharedSession, windowSeed = {}) {
  const listeners = new Map();
  const scripts = [];
  const firstPartyBeacons = [];
  const local = storage(seed);
  const session = sharedSession || storage();
  let banner = null;
  const bodyClasses = new Set();

  const document = {
    referrer: '',
    documentElement: { getAttribute(name) { return name === 'lang' ? 'en' : ''; } },
    head: { appendChild(node) { scripts.push(node); } },
    body: {
      appendChild(node) { if (node && node.hasAttribute && node.hasAttribute('data-ads-consent')) banner = node; },
      getAttribute() { return ''; },
      classList: {
        add(name) { bodyClasses.add(name); },
        remove(name) { bodyClasses.delete(name); }
      }
    },
    querySelector(selector) {
      if (selector === '[data-ads-consent]') return banner;
      return null;
    },
    querySelectorAll() { return []; },
    addEventListener(type, fn) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(fn);
    },
    createElement(tag) {
      const attrs = new Map();
      return {
        tagName: String(tag).toUpperCase(),
        hidden: false,
        async: false,
        src: '',
        innerHTML: '',
        className: '',
        style: {},
        classList: { add() {}, remove() {}, toggle() {} },
        setAttribute(name, value) { attrs.set(name, String(value)); },
        getAttribute(name) { return attrs.get(name) || ''; },
        hasAttribute(name) { return attrs.has(name); },
        appendChild() {},
        addEventListener() {},
        focus() { document.activeElement = this; }
      };
    }
  };
  document.activeElement = document.body;

  const location = {
    hostname: 'leonbuilds.org', pathname: '/quote', search: '?gclid=test-click',
    href: 'https://leonbuilds.org/quote?gclid=test-click'
  };
  const window = {
    LEON_ASSIST: { api: 'https://leon-assist.onrender.com' },
    dataLayer: [], document, location,
    crypto: { randomUUID: () => '00000000-0000-4000-8000-000000000001' },
    matchMedia: () => ({ matches: false, addEventListener() {} }),
    addEventListener() {},
    innerWidth: 1280,
    setTimeout,
    clearTimeout
  };
  Object.assign(window, windowSeed);
  window.window = window;

  const context = {
    window, document, location,
    navigator: {
      language: 'en-US',
      sendBeacon(url, payload) { firstPartyBeacons.push({ url, payload }); return true; }
    },
    localStorage: local,
    sessionStorage: session,
    crypto: window.crypto,
    URL,
    URLSearchParams,
    Blob,
    FormData,
    fetch: () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) }),
    setTimeout,
    clearTimeout,
    console
  };
  vm.runInNewContext(SOURCE, context, { filename: 'assist.js' });

  function click(closest) {
    const target = { closest };
    for (const fn of listeners.get('click') || []) fn({ target, preventDefault() {} });
  }

  function commands(name) {
    return window.dataLayer
      .map(entry => Array.from(entry))
      .filter(entry => !name || entry[0] === name);
  }

  return {
    window, document, scripts, bodyClasses, firstPartyBeacons, click, commands,
    get banner() { return banner; }
  };
}

function selectorTarget(match) {
  return selector => {
    const result = match(selector);
    if (!result) return null;
    return result === true ? {} : result;
  };
}

test('published membership CTA markup reaches the existing event bridge on click', async () => {
  const html = fs.readFileSync(path.join(ROOT, 'homepage/index.html'), 'utf8');
  const markedLinks = [...html.matchAll(/<a\b[^>]*\bdata-(?:evt|event)="[^"]+"[^>]*>/g)];
  assert.ok(markedLinks.length >= 5, 'hero, navigation, pricing and project links are marked');
  for (const [tag] of markedLinks) {
    const attrs = Object.fromEntries([...tag.matchAll(/([\w-]+)="([^"]*)"/g)].map(([, name, value]) => [name, value]));
    const name = attrs['data-evt'] || attrs['data-event'];
    const h = harness({}, undefined, { __leonMeasurementOwnsPageView: true });
    h.click(selectorTarget(selector => selector === '[data-evt]' && attrs['data-evt']
      ? { getAttribute: key => attrs[key] || null }
      : null));
    assert.equal(h.firstPartyBeacons.length, 1, name + ' produces a beacon');
    const beacon = h.firstPartyBeacons[0];
    assert.equal(beacon.url, 'https://leon-assist.onrender.com/api/event');
    assert.equal(JSON.parse(await beacon.payload.text()).name, name);
    assert.equal(h.scripts.length, 0, 'CTA tracking does not enable advertising without consent');
  }
});

test('homepage can own the single page view while legacy pages keep the automatic event', () => {
  const legacy = harness();
  assert.equal(legacy.firstPartyBeacons.length, 1);
  assert.equal(legacy.window.__leonMeasurementPageViewSent, true);

  const homepage = harness({}, undefined, {
    __leonMeasurementOwnsPageView: true
  });
  assert.equal(homepage.firstPartyBeacons.length, 0);
  homepage.window.leonEvt('page_view');
  assert.equal(homepage.firstPartyBeacons.length, 1);
});

test('real Google Ads labels use basic consent mode and explicit empty user-data overrides', () => {
  for (const label of Object.values(LABELS)) assert.ok(SOURCE.includes(label), label);
  assert.match(SOURCE, /gtag\(\)|adsGtag\(\)\('consent', 'default'/);
  assert.match(SOURCE, /ad_storage: 'denied'/);
  assert.match(SOURCE, /ad_user_data: 'denied'/);
  assert.match(SOURCE, /ad_personalization: 'denied'/);
  assert.match(SOURCE, /allow_ad_personalization_signals', false/);
  assert.match(SOURCE, /adsGtag\(\)\('set', 'user_data', \{\}\)/);
  assert.match(SOURCE, /fields = \{ send_to: sendTo, user_data: \{\} \}/);
  assert.match(SOURCE, /'config', ADS_ACCOUNT_ID, \{ send_page_view: false \}/);
  assert.doesNotMatch(SOURCE, /enhanced_conversion_data/);
  assert.doesNotMatch(SOURCE, /value:\s*1(?:\.0)?|currency:\s*['"]USD['"]/);
});

test('Google makes no request before consent, then flushes one receipt-deduplicated quote conversion', () => {
  const h = harness();
  assert.equal(h.scripts.length, 0);
  assert.equal(h.commands('event').length, 0);
  assert.equal(h.banner.hidden, false);
  assert.equal(h.banner.getAttribute('role'), 'dialog');
  assert.equal(h.banner.getAttribute('aria-modal'), 'false');
  assert.equal(h.banner.getAttribute('aria-describedby'), 'ads-consent-description');
  assert.equal(h.document.activeElement, h.banner, 'the newly shown consent dialog is announced through focus');

  h.window.leonEvt('quote_lead_accepted', { receipt: 'lead_1234567890abcdef' });
  h.window.leonEvt('quote_lead_accepted', { receipt: 'lead_1234567890abcdef' });
  assert.equal(h.scripts.length, 0);
  assert.equal(h.commands('event').length, 0);

  h.click(selectorTarget(selector => selector === '[data-ads-consent-allow]'));
  assert.equal(h.scripts.length, 1);
  assert.equal(h.scripts[0].src, 'https://www.googletagmanager.com/gtag/js?id=AW-18407115426');
  const events = h.commands('event');
  assert.equal(events.length, 1);
  assert.deepEqual(events[0].slice(0, 2), ['event', 'conversion']);
  assert.equal(events[0][2].send_to, LABELS.quote);
  assert.equal(events[0][2].transaction_id, 'lead_1234567890abcdef');
  assert.equal(Object.keys(events[0][2].user_data).length, 0);
  assert.equal(events[0][2].value, undefined);
  assert.equal(events[0][2].currency, undefined);

  const commands = h.commands();
  const consentUpdate = commands.find(command => command[0] === 'consent' && command[1] === 'update');
  assert.equal(consentUpdate[2].ad_storage, 'granted');
  assert.equal(consentUpdate[2].ad_user_data, 'granted');
  assert.equal(consentUpdate[2].ad_personalization, 'denied');
  const userDataSet = commands.findIndex(command => command[0] === 'set' && command[1] === 'user_data');
  const config = commands.findIndex(command => command[0] === 'config');
  assert.ok(userDataSet > -1 && userDataSet < config, 'empty tag-level user_data is queued before config');
  assert.equal(Object.keys(commands[userDataSet][2]).length, 0);
  assert.equal(commands[config][2].send_page_view, false);
  assert.deepEqual(Object.keys(commands[config][2]), ['send_page_view']);

  h.window.leonEvt('quote_lead_accepted', { receipt: 'lead_1234567890abcdef' });
  assert.equal(h.commands('event').length, 1, 'same receipt is not emitted twice');
});

test('assistant lead success uses the Quote action and dedupes against the same receipt', () => {
  const h = harness({ leon_ads_consent_v1: 'granted' });
  h.window.leonEvt('lead_submit_success', { receipt: 'lead_1234567890abcdef' });
  h.window.leonEvt('quote_lead_accepted', { receipt: 'lead_1234567890abcdef' });
  const events = h.commands('event');
  assert.equal(events.length, 1);
  assert.equal(events[0][2].send_to, LABELS.quote);
  assert.equal(events[0][2].transaction_id, 'lead_1234567890abcdef');
});

test('a consent-pending primary conversion survives a same-tab reload', () => {
  const sharedSession = storage();
  const first = harness({}, sharedSession);
  first.window.leonEvt('quote_lead_accepted', { receipt: 'lead_1234567890abcdef' });
  assert.equal(first.commands('event').length, 0);

  const reloaded = harness({}, sharedSession);
  reloaded.click(selectorTarget(selector => selector === '[data-ads-consent-allow]'));
  const events = reloaded.commands('event');
  assert.equal(events.length, 1);
  assert.equal(events[0][2].send_to, LABELS.quote);
  assert.equal(events[0][2].transaction_id, 'lead_1234567890abcdef');
});

test('booking, phone and WhatsApp actions use their own labels and dedupe repeated contact clicks per tab', () => {
  const h = harness({ leon_ads_consent_v1: 'granted' });
  assert.equal(h.scripts.length, 1);

  h.window.leonEvt('calendar_booking_success', { bookingUid: 'cal-booking-123' });
  h.window.leonEvt('calendar_booking_success', { bookingUid: 'cal-booking-123' });
  h.click(selectorTarget(selector => selector === 'a[href]' ? { getAttribute: () => 'tel:+15108267735' } : false));
  h.click(selectorTarget(selector => selector === 'a[href]' ? { getAttribute: () => 'tel:+15108267735' } : false));
  h.click(selectorTarget(selector => selector === 'a[href]' ? { getAttribute: () => 'https://wa.me/15108267735' } : false));
  h.click(selectorTarget(selector => selector === 'a[href]' ? { getAttribute: () => 'https://wa.me/15108267735' } : false));

  const events = h.commands('event').map(entry => entry[2]);
  assert.deepEqual(events.map(event => event.send_to), [LABELS.booking, LABELS.phone, LABELS.whatsapp]);
  assert.equal(events[0].transaction_id, 'cal-booking-123');
  assert.equal(events[1].transaction_id, undefined);
  assert.equal(events[2].transaction_id, undefined);
  for (const event of events) {
    assert.equal(Object.keys(event.user_data).length, 0);
    assert.equal(event.value, undefined);
    assert.equal(event.currency, undefined);
  }
});

test('quote and booking Ads conversions require valid opaque transaction identifiers', () => {
  const h = harness({ leon_ads_consent_v1: 'granted' });
  h.window.leonEvt('quote_lead_accepted', {});
  h.window.leonEvt('quote_lead_accepted', { receipt: 'visitor@example.com' });
  h.window.leonEvt('quote_lead_accepted', { receipt: 'lead_1234567890abcdef/poison' });
  h.window.leonEvt('quote_lead_accepted', { receipt: 'lead_' + 'a'.repeat(60) });
  h.window.leonEvt('calendar_booking_success', {});
  h.window.leonEvt('calendar_booking_success', { bookingUid: 'short' });
  h.window.leonEvt('calendar_booking_success', { bookingUid: 'booking@example.com' });
  h.window.leonEvt('calendar_booking_success', { bookingUid: 'b'.repeat(65) });
  assert.equal(h.commands('event').length, 0);

  h.window.leonEvt('quote_lead_accepted', { receipt: 'lead_valid-opaque-123456' });
  h.window.leonEvt('calendar_booking_success', { bookingUid: 'cal-valid-booking-123' });
  assert.deepEqual(
    h.commands('event').map(command => command[2].send_to),
    [LABELS.quote, LABELS.booking]
  );
});

test('declining conversion measurement keeps the Google tag and all conversion events blocked', () => {
  const h = harness();
  h.click(selectorTarget(selector => selector === '[data-ads-consent-deny]'));
  h.window.leonEvt('quote_lead_accepted', { receipt: 'lead_abcdef1234567890' });
  h.window.leonEvt('calendar_booking_success', { bookingUid: 'cal-denied-123' });
  h.click(selectorTarget(selector => selector === 'a[href]' ? { getAttribute: () => 'tel:+15108267735' } : false));
  assert.equal(h.scripts.length, 0);
  assert.equal(h.commands('event').length, 0);
});

test('consent preference dialog restores focus and presents equal-weight actions', () => {
  const h = harness({ leon_ads_consent_v1: 'denied' });
  const manage = { focus() { h.document.activeElement = manage; } };
  h.document.activeElement = manage;
  h.click(selectorTarget(selector => selector === '[data-ads-consent-manage]' ? manage : false));
  assert.equal(h.document.activeElement, h.banner);
  h.click(selectorTarget(selector => selector === '[data-ads-consent-deny]'));
  assert.equal(h.document.activeElement, manage);

  const css = fs.readFileSync(path.join(ROOT, 'assist.css'), 'utf8');
  assert.doesNotMatch(css, /\.ads-consent button\.allow/);
  assert.doesNotMatch(h.banner.innerHTML, /class="allow"/);
  assert.match(h.banner.innerHTML, /Allow ad measurement\?/);
  assert.match(h.banner.innerHTML, /Google Ads may use cookies/);
  assert.match(h.banner.innerHTML, /quote, booking, phone and WhatsApp actions/);
  assert.match(h.banner.innerHTML, /Form details stay out/);
  assert.match(h.banner.innerHTML, /personalization stays off/);
});

test('each explicit consent choice is recorded as a first-party event', () => {
  const allow = harness();
  allow.click(selectorTarget(selector => selector === '[data-ads-consent-allow]'));
  assert.equal(allow.firstPartyBeacons.length, 2, 'page view plus consent choice');

  const deny = harness();
  deny.click(selectorTarget(selector => selector === '[data-ads-consent-deny]'));
  assert.equal(deny.firstPartyBeacons.length, 2, 'page view plus consent choice');
});

test('privacy copy discloses the optional Google path and exposes a preference control', () => {
  const privacy = fs.readFileSync(path.join(ROOT, 'privacy.html'), 'utf8');
  assert.match(privacy, /Until you select “Allow measurement,” the Google tag is not requested and no data is sent to Google/);
  assert.match(privacy, /page URL—including campaign or advertising-click identifiers/);
  assert.match(privacy, /sets Google's user-provided-data field to an empty value/);
  assert.match(privacy, /automatic customer-data collection setting, which must remain disabled/);
  assert.match(privacy, /no monetary value is assigned/);
  assert.match(privacy, /data-ads-consent-manage/);
});
