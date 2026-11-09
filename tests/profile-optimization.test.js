'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const read = file => fs.readFileSync(path.join(__dirname, '..', file), 'utf8');

test('about respects public biography limits and labels commerce demo', () => {
  const page = read('about.html');
  assert.doesNotMatch(page, /California State|Green River|alumniOf|CollegeOrUniversity|computer engineering student/i);
  assert.match(page, /payment and kitchen progression are simulations/i);
  assert.match(page, /existing real-estate seller portal/i);
});

test('seller portal proof is attributed and keeps private data out', () => {
  const page = read('work/loqol-seller-portal.html');
  assert.match(page, /existing product and design/i);
  assert.match(page, /not a production screenshot/i);
  assert.match(page, /does not prove the server kept the answer/i);
  assert.match(page, /href="\/work#work-loqol"/);
  assert.doesNotMatch(page, /loqol-(?:questionnaire|filled-pdf)\.png|sellerToken|sellerLink=/i);
  assert.match(read('work.html'), /href="\/work\/loqol-seller-portal"/);
});

test('starter website offer is separate from systems plan and larger websites', () => {
  const page = read('services/websites.html');
  assert.match(page, /One-page starter website · \$199/);
  assert.match(page, /one revision/);
  assert.match(page, /larger business-website scope above starts at \$300/);
  const home = read('homepage/index.html');
  assert.match(home, /href="#scope"/);
  assert.doesNotMatch(home, /\$199 systems plan/i);
  assert.match(read('technical-build-partner.html'), /\$199 Systems Plan/);
});
