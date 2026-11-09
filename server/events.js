/* Traffic events: where visitors come from and what they do.
   Same storage philosophy as leads.js — stdout is the sink that always works
   (grep "EVT " in Render logs). JSONL is replaceable by default and becomes
   durable when LEON_DATA_DIR points inside a mounted disk. */

'use strict';

const fs = require('fs');
const path = require('path');
const { normalizeAttribution } = require('./attribution');
const { dataFile } = require('./storage');

// EVENTS_FILE keeps tests isolated. LEON_DATA_DIR is the production switch for
// putting this file on a mounted disk rather than Render's replaceable app FS.
const EVENTS_FILE = dataFile('events.jsonl', 'EVENTS_FILE');
const DATA_DIR = path.dirname(EVENTS_FILE);

// Event names become dashboard labels and log keys. Keep the vocabulary small
// and machine-readable; values such as `fixcard_ai-chatbots` are intentionally
// allowed, while markup, whitespace and control characters are not.
const EVENT_NAME_RE = /^[a-z][a-z0-9_-]{0,47}$/;
const RECEIPT_ID_RE = /^lead_[A-Za-z0-9-]{16,59}$/;
const BOOKING_UID_RE = /^[A-Za-z0-9._~-]{8,64}$/;
const SLUG_RE = /^[a-z0-9][a-z0-9-]{0,63}$/;
const EVENT_STATUSES = new Set(['accepted', 'failed']);
const DEVICE_CLASSES = new Set(['mobile', 'tablet', 'desktop', 'unknown']);

function validEventName(value) {
  return typeof value === 'string' && EVENT_NAME_RE.test(value);
}

function eventText(value, max) {
  if (value == null) return '';
  return String(value)
    .replace(/[\u0000-\u001f\u007f]/g, ' ')
    .trim()
    .slice(0, max);
}

function eventExtraValue(field, value) {
  if (typeof value !== 'string') return '';
  const text = value.trim();
  if (!text || text.length > 64 || /[\u0000-\u001f\u007f]/.test(text)) return '';
  if (field === 'receipt') return RECEIPT_ID_RE.test(text) ? text : '';
  if (field === 'bookingUid') return BOOKING_UID_RE.test(text) ? text : '';
  if (field === 'status') return EVENT_STATUSES.has(text) ? text : '';
  if (field === 'device') return DEVICE_CLASSES.has(text) ? text : '';
  if (field === 'service' || field === 'package') return SLUG_RE.test(text) ? text : '';
  return '';
}

function firstPresent(raw, names, max) {
  for (const name of names) {
    const value = eventText(raw[name], max);
    if (value) return value;
  }
  return '';
}

function anonymousSession(raw) {
  const value = firstPresent(raw, ['sessionId', 'session'], 96);
  return /^[A-Za-z0-9_-]{8,96}$/.test(value) ? value : '';
}

function referrerOrigin(value) {
  const raw = eventText(value, 500);
  if (!raw) return '';
  try {
    const url = new URL(raw);
    // The source report needs a domain, not a referrer's path/query, which can
    // contain search terms or identifiers the visitor never meant to submit.
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.origin : '';
  } catch (e) {
    return '';
  }
}

function firstReferrer(raw, names) {
  for (const name of names) {
    const value = referrerOrigin(raw[name]);
    if (value) return value;
  }
  return '';
}

/* Normalize the public beacon into a bounded analytics record with no contact
   fields. The legacy ref/utm fields remain so old log tooling keeps working;
   explicit first and last fields stop campaign re-entry from overwriting
   acquisition. */
function normalizeEvent(raw, now) {
  if (!raw || typeof raw !== 'object' || !validEventName(raw.name)) return null;

  const currentAttribution = normalizeAttribution(raw);
  const firstAttribution = normalizeAttribution(raw, 'first');
  const lastAttribution = normalizeAttribution(raw, 'last');
  const pathNow = eventText(raw.path, 200);
  const legacyRef = referrerOrigin(raw.ref);
  const legacyUtm = eventText(raw.utm, 120);
  const legacyMedium = eventText(raw.medium, 120);
  const legacyCampaign = eventText(raw.campaign, 120);
  const firstRecorded = firstPresent(raw, ['firstPage', 'firstRef', 'firstReferrer', 'firstUtm', 'firstUtmSource', 'firstMedium', 'firstUtmMedium', 'firstCampaign', 'firstUtmCampaign'], 300) || Object.keys(firstAttribution).length > 0;
  const firstFallback = firstRecorded ? {} : currentAttribution;
  const out = {
    ts: now || new Date().toISOString(),
    name: raw.name,
    path: pathNow,
    sessionId: anonymousSession(raw),
    firstPage: firstPresent(raw, ['firstPage'], 200),
    lastPage: firstPresent(raw, ['lastPage'], 200) || pathNow,
    firstRef: firstReferrer(raw, ['firstRef', 'firstReferrer']) || (firstRecorded ? '' : legacyRef),
    lastRef: firstReferrer(raw, ['lastRef', 'lastReferrer']) || legacyRef,
    firstUtm: firstPresent(raw, ['firstUtm', 'firstUtmSource'], 120) || (firstRecorded ? '' : legacyUtm),
    lastUtm: firstPresent(raw, ['lastUtm', 'lastUtmSource'], 120) || legacyUtm,
    firstMedium: firstPresent(raw, ['firstMedium', 'firstUtmMedium'], 120) || (firstRecorded ? '' : legacyMedium),
    lastMedium: firstPresent(raw, ['lastMedium', 'lastUtmMedium'], 120) || legacyMedium,
    firstCampaign: firstPresent(raw, ['firstCampaign', 'firstUtmCampaign'], 120) || (firstRecorded ? '' : legacyCampaign),
    lastCampaign: firstPresent(raw, ['lastCampaign', 'lastUtmCampaign'], 120) || legacyCampaign,
    firstUtmTerm: firstAttribution.utmTerm || firstFallback.utmTerm || '',
    lastUtmTerm: lastAttribution.utmTerm || currentAttribution.utmTerm || '',
    firstUtmContent: firstAttribution.utmContent || firstFallback.utmContent || '',
    lastUtmContent: lastAttribution.utmContent || currentAttribution.utmContent || '',
    // Backward-compatible fields used by existing Render-log searches.
    ref: legacyRef,
    utm: legacyUtm,
    medium: legacyMedium,
    campaign: legacyCampaign,
    term: currentAttribution.utmTerm || '',
    content: currentAttribution.utmContent || ''
  };

  const device = eventExtraValue('device', raw.device);
  if (device) out.device = device;
  if (raw.name === 'web_vital') {
    if (!['LCP', 'INP', 'CLS'].includes(raw.metricName)
        || typeof raw.metricValue !== 'number' || !Number.isFinite(raw.metricValue)
        || raw.metricValue < 0 || raw.metricValue > (raw.metricName === 'CLS' ? 100 : 3600000)
        || !/^[A-Za-z0-9_-]{1,96}$/.test(raw.metricId || '')) return null;
    out.metricName = raw.metricName;
    out.metricValue = raw.metricValue;
    out.metricId = raw.metricId;
    if (['good', 'needs-improvement', 'poor'].includes(raw.metricRating)) out.metricRating = raw.metricRating;
  }

  for (const field of ['gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid']) {
    const title = field.charAt(0).toUpperCase() + field.slice(1);
    out[field] = currentAttribution[field] || '';
    out['first' + title] = firstAttribution[field] || firstFallback[field] || '';
    out['last' + title] = lastAttribution[field] || currentAttribution[field] || '';
  }

  // These are opaque correlation values, never contact details.
  for (const field of ['receipt', 'bookingUid', 'status', 'service', 'package']) {
    const value = eventExtraValue(field, raw[field]);
    if (value) out[field] = value;
  }
  return out;
}

function persistEvent(ev) {
  console.log('EVT ' + JSON.stringify(ev));
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.appendFileSync(EVENTS_FILE, JSON.stringify(ev) + '\n');
  } catch (e) { /* file is best-effort; stdout already has it */ }
}

function readEvents(limit, { strict = false } = {}) {
  let raw = '';
  try { raw = fs.readFileSync(EVENTS_FILE, 'utf8'); }
  catch (error) {
    if (strict && (!error || error.code !== 'ENOENT')) throw error;
    return [];
  }
  const out = [];
  const lines = raw.split('\n');
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim()) continue;
    try { out.push(JSON.parse(line)); }
    catch (error) {
      if (strict) throw new Error(`corrupt events ledger at line ${index + 1}`);
      /* Best-effort ingestion paths skip a torn line; admin reporting is strict. */
    }
  }
  return out.slice(-(limit || 5000));
}

/* One event -> which bucket it counts toward on the dashboard.
   Priority: explicit tag (?s= or utm_source) > referrer domain > direct.
   Acquisition is the default; pass "last" for the latest campaign touch. */
const KNOWN_AI_REFERRERS = new Map([
  ['chatgpt.com', 'ChatGPT'],
  ['chat.openai.com', 'ChatGPT'],
  ['perplexity.ai', 'Perplexity'],
  ['claude.ai', 'Claude'],
  ['gemini.google.com', 'Gemini'],
  ['bard.google.com', 'Gemini'],
  ['copilot.microsoft.com', 'Microsoft Copilot']
]);

function knownAiReferrer(hostname) {
  const host = String(hostname || '').toLowerCase().replace(/^www\./, '');
  const product = KNOWN_AI_REFERRERS.get(host);
  return product ? `AI referral — ${product}` : '';
}

function sourceOf(ev, touch) {
  const last = touch === 'last';
  const utm = last ? (ev.lastUtm || ev.utm) : (ev.firstUtm || ev.utm);
  const ref = last ? (ev.lastRef || ev.ref) : (ev.firstRef || ev.ref);
  if (utm) return String(utm);
  if (ref) {
    try {
      const h = new URL(ref).hostname.replace(/^www\./, '');
      const aiReferral = knownAiReferrer(h);
      if (aiReferral) return aiReferral;
      if (h && !h.includes('leonbuilds') && !h.includes('leonkelvinli')) return h;
      return 'internal';
    } catch (e) { return 'unknown-ref'; }
  }
  return 'direct';
}

const HIGH_INTENT_NAMES = new Set([
  'nav_quote_click', 'hero_quote_click', 'hero_call_click', 'pricing_cta_click',
  'nav_call_click', 'cta_call_click', 'contact_call_click', 'contact_quote_click',
  'about_quote_click', 'work_quote_click', 'work_final_quote_click',
  'reviews_quote_click', 'footer_email_click', 'footer_phone_click',
  'subscription_nav_cta', 'subscription_hero_cta', 'subscription_pricing_cta',
  'quote_form_start', 'quote_form_submit', 'quote_submit_attempt',
  'contractor_review_click', 'hero_review_cta_click',
  'mobile_review_cta_click', 'work_review_cta_click',
  'about_review_cta_click', 'service_quote_start', 'calendar_direct_click',
  'chat_first_message', 'chat_handoff_offer_click', 'lead_submit', 'lead_submit_attempt',
  'quote_to_calendar', 'lead_booking_click',
  'calendar_direct_fallback', 'calendar_email_fallback', 'calendar_phone_fallback',
  'quote_manual_email', 'lead_email_fallback', 'email_click', 'phone_click',
  'technical_partner_call_click', 'technical_partner_quote_click',
  'technical_partner_systems_plan_click', 'technical_partner_sprint_click',
  'technical_partner_ongoing_click'
]);

function isHighIntent(name) {
  return HIGH_INTENT_NAMES.has(name)
    || /^(wa_click_|wechat_copy_|contact_click_|call_click_|handoff_)/.test(name);
}

/* Counts keep every matching record, including the legacy records written
   before session IDs existed. Unique-session rates are intentionally stricter:
   a rate numerator includes only IDs also seen in every preceding stage. */
function funnelStats(events) {
  const definitions = [
    { id: 'page', label: 'page view', match: name => name === 'page_view' },
    { id: 'intent', label: 'high-intent action', match: isHighIntent },
    {
      id: 'lead',
      label: 'lead accepted by API',
      match: name => name === 'lead_submit_success'
        || name === 'quote_lead_accepted'
        || name === 'call_request_sent'
    },
    {
      id: 'booking',
      label: 'embedded calendar success signal',
      match: name => name === 'calendar_booking_success'
    }
  ];

  let priorQualified = null;
  const stages = definitions.map(definition => {
    const matching = events.filter(ev => definition.match(String(ev.name || '')));
    const sessions = new Set(
      matching.map(ev => String(ev.sessionId || '')).filter(Boolean)
    );
    const qualified = priorQualified === null
      ? new Set(sessions)
      : new Set([...sessions].filter(session => priorQualified.has(session)));
    const stage = {
      id: definition.id,
      label: definition.label,
      eventCount: matching.length,
      sessionCount: sessions.size,
      sessionlessEventCount: matching.filter(ev => !ev.sessionId).length,
      qualifiedCount: qualified.size,
      priorQualifiedCount: priorQualified === null ? null : priorQualified.size
    };
    priorQualified = qualified;
    return stage;
  });

  return {
    stages,
    sessionlessEventCount: stages.reduce((sum, stage) => sum + stage.sessionlessEventCount, 0),
    funnelEventCount: stages.reduce((sum, stage) => sum + stage.eventCount, 0)
  };
}

/* A compact device view for deciding whether the next campaign or layout pass
   should favor phones, tablets or larger screens. These are event counts, not
   people: the table deliberately avoids pretending an anonymous viewport
   bucket is a durable user identity. Historical records without a bucket stay
   visible as unknown. */
function deviceJourneyStats(events) {
  const definitions = [
    ['pageViews', name => name === 'page_view'],
    ['proofViews', name => name === 'proof_view'],
    ['startViews', name => name === 'start_section_view'],
    ['formStarts', name => name === 'quote_form_start'],
    ['leadsAccepted', name => name === 'lead_submit_success'
      || name === 'quote_lead_accepted'
      || name === 'call_request_sent'],
    ['bookings', name => name === 'calendar_booking_success']
  ];
  const order = ['mobile', 'desktop', 'tablet', 'unknown'];
  const rows = new Map(order.map(device => [device, {
    device,
    pageViews: 0,
    proofViews: 0,
    startViews: 0,
    formStarts: 0,
    leadsAccepted: 0,
    bookings: 0
  }]));
  for (const event of events || []) {
    const device = DEVICE_CLASSES.has(String(event && event.device || ''))
      ? String(event.device)
      : 'unknown';
    const row = rows.get(device);
    const name = String(event && event.name || '');
    for (const [field, match] of definitions) {
      if (match(name)) row[field] += 1;
    }
  }
  return order.map(device => rows.get(device));
}

/* Report the new review path as independent milestones against the same
   page-view baseline. A hero visitor can jump straight to the form, so proof
   and Start views must not be treated as mandatory gates that erase a real
   form start from reporting. */
function reviewMilestoneStats(events) {
  const definitions = [
    { id: 'page', label: 'page viewed', names: new Set(['page_view']) },
    { id: 'proof', label: 'proof viewed', names: new Set(['proof_view']) },
    { id: 'start', label: 'Start section viewed', names: new Set(['start_section_view']) },
    { id: 'form', label: 'review form started', names: new Set(['quote_form_start']) },
    {
      id: 'lead',
      label: 'lead accepted by API',
      names: new Set(['lead_submit_success', 'quote_lead_accepted', 'call_request_sent'])
    },
    { id: 'booking', label: 'booking success signal', names: new Set(['calendar_booking_success']) }
  ];
  const pageSessions = new Set(
    (events || [])
      .filter(event => event && event.name === 'page_view')
      .map(event => String(event.sessionId || ''))
      .filter(Boolean)
  );
  const stages = definitions.map(definition => {
    const matching = (events || []).filter(event =>
      definition.names.has(String(event && event.name || '')));
    const sessions = new Set(
      matching.map(event => String(event.sessionId || '')).filter(Boolean));
    const attributableCount = [...sessions]
      .filter(session => pageSessions.has(session)).length;
    return {
      id: definition.id,
      label: definition.label,
      eventCount: matching.length,
      sessionCount: sessions.size,
      attributableCount,
      baselineSessionCount: pageSessions.size,
      sessionlessEventCount: matching.filter(event => !event.sessionId).length
    };
  });
  return { stages, baselineSessionCount: pageSessions.size };
}

module.exports = {
  persistEvent,
  readEvents,
  sourceOf,
  normalizeEvent,
  validEventName,
  funnelStats,
  deviceJourneyStats,
  reviewMilestoneStats
};
