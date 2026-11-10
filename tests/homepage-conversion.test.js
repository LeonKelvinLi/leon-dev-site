'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root,'homepage/index.html'),'utf8');
const text = html.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ');
test('published export exposes one scoped membership and accurate billing', () => {
 assert.match(text,/A developer for websites and tools\./); assert.match(text,/\$2,499/);
 assert.match(text,/\$208\.25\/month, billed annually/); assert.match(text,/24 hours over 12 months/);
 assert.match(text,/one active request/); assert.match(text,/Manual renewal|renewal is manual/i);
 assert.equal((html.match(/class="pricing-card"/g)||[]).length,1);
 assert.doesNotMatch(text,/Systems Plan|From \$199|3-point review/);
});
test('the published export preserves discoverable intake, scope, developer proof and privacy', () => {
 for (const id of ['how-it-works','what-i-build','pricing','scope','meet-leon','start']) assert.ok(html.includes(`id="${id}"`),id);
 for (const href of ['#start','#scope','https://leonbuilds.org/privacy','https://leonbuilds.org/work/curio-app','https://leonbuilds.org/work/beastypages-website']) assert.ok(html.includes(`href="${href}"`),href);
 assert.match(html,/leon-kelvin-li-professional\.webp/); assert.match(html,/membership-og\.png/);
 assert.match(text,/before you pay/); assert.match(html,/<noscript>/);
});
test('all referenced export browser chunks, fonts and images exist', () => {
 for (const [,url] of html.matchAll(/(?:src|href)="(\/(?:_next|images)\/[^"?#]+)"/g)) assert.ok(fs.existsSync(path.join(root,'homepage',url)),url);
 const css = fs.readdirSync(path.join(root,'homepage/_next/static/css')).map(name=>fs.readFileSync(path.join(root,'homepage/_next/static/css',name),'utf8')).join('\n');
 assert.match(css,/prefers-reduced-motion/); assert.match(css,/focus-visible/);
 assert.match(fs.readFileSync(path.join(root,'robots.txt'),'utf8'),/Disallow: \/images\/leon-kelvin-li/);
});
