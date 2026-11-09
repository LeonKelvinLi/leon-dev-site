'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const test = require('node:test');
const root = path.join(__dirname,'..');
const {validateLead} = require('../server/leads');
const {funnelStats} = require('../server/events');
test('subscription inquiry stores both answers without changing legacy lead contracts', () => {
 const {lead,error} = validateLead({problem:'A focused website for my business',desiredOutcome:'People can request appointments online',email:'qa@example.invalid',service:'personal-developer',via:'subscription-intake',idempotencyKey:'leadreq_00000000-0000-4000-8000-000000000000',budget:'$2,499/year'});
 assert.equal(error,undefined); assert.equal(lead.service,'personal-developer'); assert.match(lead.desiredOutcome,/appointments/); assert.match(lead.receiptId,/^lead_/);
});
test('subscription CTA events count toward intent while receipts remain separate from booking and payment', () => {
 for (const name of ['subscription_nav_cta','subscription_hero_cta','subscription_pricing_cta']) {
  const events=[{name:'page_view',sessionId:'qa'},{name,sessionId:'qa'},{name:'quote_lead_accepted',sessionId:'qa'}];
  const result=funnelStats(events); assert.equal(result.stages.find(s=>s.id==='intent').qualifiedCount,1); assert.equal(result.stages.find(s=>s.id==='lead').qualifiedCount,1); assert.equal(result.stages.find(s=>s.id==='booking').qualifiedCount,0);
 }
});
test('the actual public offer removes retired packages on all old inbound routes', () => {
 const result=spawnSync('python3',['tools/check_subscription_public.py'],{cwd:root,encoding:'utf8'});
 assert.equal(result.status,0,result.stdout+result.stderr);
 const sitemap=fs.readFileSync(path.join(root,'content/subscription-public/sitemap.xml'),'utf8');
 assert.doesNotMatch(sitemap,/\/services\/|\/industries\/|\/quote</);
 const bridge=fs.readFileSync(path.join(root,'content/subscription-public/quote.html'),'utf8');
 assert.match(bridge,/noindex,follow/); assert.match(bridge,/href="\/#start"/);
});
