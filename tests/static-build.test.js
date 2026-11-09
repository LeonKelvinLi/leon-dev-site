'use strict';

const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const SCRIPT = path.join(ROOT, 'tools', 'build_static.py');
const HOMEPAGE = path.join(ROOT, 'homepage');
const TEMP = fs.mkdtempSync(path.join(os.tmpdir(), 'leon-static-build-'));
const releasedTestimonials = JSON.parse(
  fs.readFileSync(path.join(ROOT, 'content', 'client-success', 'testimonial-publication.json'), 'utf8')
).approved_testimonials;

after(() => {
  fs.rmSync(TEMP, { recursive: true, force: true });
});

function run(args) {
  return spawnSync('python3', [SCRIPT, ...args], {
    cwd: ROOT,
    encoding: 'utf8',
    maxBuffer: 2 * 1024 * 1024
  });
}

function diagnostic(result) {
  return `status=${result.status}\nstdout=${result.stdout}\nstderr=${result.stderr}`;
}

function walkFiles(directory) {
  const out = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      for (const nested of walkFiles(absolute)) out.push(path.join(entry.name, nested));
    } else {
      out.push(entry.name);
    }
  }
  return out.sort();
}

test('--check validates the manifest without creating output', () => {
  const parent = path.join(TEMP, 'readonly');
  const output = path.join(parent, 'dist');
  fs.mkdirSync(parent);

  const result = run(['--check', '--output', output]);
  assert.equal(result.status, 0, diagnostic(result));
  assert.equal(fs.existsSync(output), false);
  assert.match(result.stdout, /manifest validated read-only/);
});

test('static build publishes only pages and required referenced assets', () => {
  const parent = path.join(TEMP, 'public');
  const output = path.join(parent, 'dist');
  fs.mkdirSync(parent);

  let result = run(['--output', output]);
  assert.equal(result.status, 0, diagnostic(result));

  for (const relative of [
    'index.html', 'about.html', 'privacy.html', 'quote.html', 'call.html', 'work.html',
    'work/allcpr-site-intelligence.html', 'work/curio-app.html', 'work/beastypages-website.html',
    'guides/contractor-inquiry-workflow.html', 'missed-lead-recovery.html', 'technical-build-partner.html',
    'services/index.html', 'services/websites.html', 'es/index.html',
    'styles.css', 'assist.css', 'app.js', 'assist.js',
    'assets/favicon.svg', 'assets/og.png', 'favicon.ico', 'apple-touch-icon.png',
    'sitemap.xml', 'robots.txt', 'llms.txt', 'site-version.txt',
    'google632f06756dffc4ba.html', 'b20f1e412f2cff8af636fe5676cfdbcd.txt'
  ]) {
    const published = path.join(output, relative);
    assert.equal(fs.existsSync(published) && fs.statSync(published).isFile(), true, relative);
  }

  const exportFiles = walkFiles(HOMEPAGE);
  assert.ok(exportFiles.some(file => /^_next\/.*\.js$/.test(file)), 'reviewed export includes browser chunks');
  assert.ok(exportFiles.some(file => /^_next\/.*\.woff2$/.test(file)), 'reviewed export includes nested fonts');
  assert.ok(exportFiles.some(file => /^images\/.*\.webp$/.test(file)), 'reviewed export includes project images');
  for (const relative of exportFiles) {
    assert.deepEqual(
      fs.readFileSync(path.join(output, relative)),
      fs.readFileSync(path.join(HOMEPAGE, relative)),
      `${relative} publishes the exact reviewed export bytes`
    );
  }
  for (const relative of [
    'work.html', 'work/allcpr-site-intelligence.html', 'work/curio-app.html',
    'work/beastypages-website.html', 'guides/contractor-inquiry-workflow.html',
    'privacy.html', 'quote.html', 'assist.js', 'styles.css',
    'services/websites.html', 'services/mobile-apps.html', 'industries/contractors.html',
    'es/index.html', 'pt/index.html', 'zh/index.html', 'assets/og.png',
    'sitemap.xml', 'robots.txt', 'llms.txt'
  ]) {
    assert.deepEqual(
      fs.readFileSync(path.join(output, relative)),
      fs.readFileSync(path.join(ROOT, fs.existsSync(path.join(ROOT, 'content/subscription-public', relative)) ? 'content/subscription-public' : '', relative)),
      `${relative} publishes the reviewed subscription page or unchanged infrastructure bytes`
    );
  }
  assert.notEqual(
    fs.readFileSync(path.join(output, 'index.html'), 'utf8'),
    fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8'),
    'the legacy root source cannot silently replace the new homepage'
  );

  const reviewsOutput = path.join(output, 'reviews.html');
  assert.equal(
    fs.existsSync(reviewsOutput),
    releasedTestimonials.length >= 3,
    '/reviews is published only when at least three testimonials pass the release gate'
  );

  for (const relative of [
    'content/publication-ledger.csv', 'content/posts.md',
    'tests/static-build.test.js', 'tools/build_static.py',
    'docs/seo/SEO_AUDIT.md', 'docs/seo/TOP_100_SEO_OPPORTUNITIES.csv', 'content/seo/publication.json',
    'server/index.js', 'data/events.jsonl', 'research',
    'package.json', 'package-lock.json', 'README.md', 'render.yaml', '.env',
    'assets/facebook.png', 'assets/listings/fb_en_1hook.png',
    'assets/social/ig_01_prices.png'
  ]) {
    assert.equal(fs.existsSync(path.join(output, relative)), false, relative);
  }

  const files = walkFiles(output);
  assert.equal(files.some(file => /^(content|data|homepage|research|server|tests|tools)(\/|$)/.test(file)), false);
  assert.equal(files.some(file => /\.(csv|json|md|py|ya?ml)$/i.test(file)), false);

  const versionPath = path.join(output, 'site-version.txt');
  const expectedVersion = fs.readFileSync(versionPath, 'utf8');
  assert.match(expectedVersion, /^[0-9a-f]{64}\n$/);

  // The generated marker is deterministic and --check never repairs it.
  fs.writeFileSync(versionPath, `${'0'.repeat(64)}\n`);
  result = run(['--check', '--output', output]);
  assert.notEqual(result.status, 0, diagnostic(result));
  assert.equal(fs.readFileSync(versionPath, 'utf8'), `${'0'.repeat(64)}\n`);
  result = run(['--output', output]);
  assert.equal(result.status, 0, diagnostic(result));
  assert.equal(fs.readFileSync(versionPath, 'utf8'), expectedVersion);

  const secondParent = path.join(TEMP, 'public-copy');
  const secondOutput = path.join(secondParent, 'dist');
  fs.mkdirSync(secondParent);
  result = run(['--output', secondOutput]);
  assert.equal(result.status, 0, diagnostic(result));
  assert.equal(fs.readFileSync(path.join(secondOutput, 'site-version.txt'), 'utf8'), expectedVersion);

  // A stale expected file is reported, never silently repaired by --check.
  const builtIndex = path.join(output, 'index.html');
  const expectedIndex = fs.readFileSync(builtIndex, 'utf8');
  fs.writeFileSync(builtIndex, 'stale but allowlisted output\n');
  result = run(['--check', '--output', output]);
  assert.notEqual(result.status, 0, diagnostic(result));
  assert.equal(fs.readFileSync(builtIndex, 'utf8'), 'stale but allowlisted output\n');

  // A repeat build may update expected generated files, after which the
  // read-only check verifies byte-for-byte currency.
  result = run(['--output', output]);
  assert.equal(result.status, 0, diagnostic(result));
  assert.equal(fs.readFileSync(builtIndex, 'utf8'), expectedIndex);
  result = run(['--check', '--output', output]);
  assert.equal(result.status, 0, diagnostic(result));
});

test('homepage overlay rejects private files and symlinks before publication', () => {
  const cases = [
    ['build-metadata', '_next/static/private.json', 'unsupported homepage asset'],
    ['private-copy', 'images/private.md', 'unsupported homepage asset'],
    ['server-output', 'server/index.js', 'unexpected homepage export path'],
    ['hidden-input', 'images/.private.png', 'hidden path is not a homepage asset'],
    ['symlink', 'images/linked.webp', 'homepage source may not be a symlink'],
  ];
  for (const [label, relative, expected] of cases) {
    const fixture = path.join(TEMP, label);
    fs.mkdirSync(fixture);
    fs.cpSync(HOMEPAGE, path.join(fixture, 'homepage'), { recursive: true });
    const injected = path.join(fixture, 'homepage', relative);
    fs.mkdirSync(path.dirname(injected), { recursive: true });
    if (label === 'symlink') {
      fs.symlinkSync(path.join(ROOT, 'package.json'), injected);
    } else {
      fs.writeFileSync(injected, 'must not be published\n');
    }
    const result = spawnSync('python3', ['-B', '-c',
      'import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import build_static; build_static.ROOT = Path(sys.argv[2]).resolve(); build_static.overlay_homepage({})',
      path.join(ROOT, 'tools'), fixture
    ], { encoding: 'utf8' });
    assert.notEqual(result.status, 0, label);
    assert.ok(result.stderr.includes(expected), `${label}: ${result.stderr}`);
    assert.equal(fs.existsSync(path.join(fixture, 'dist')), false, `${label} creates no output`);
  }
});

test('unexpected preexisting output aborts before any public file is written', () => {
  const parent = path.join(TEMP, 'poisoned');
  const output = path.join(parent, 'dist');
  const leaked = path.join(output, 'content', 'publication-ledger.csv');
  fs.mkdirSync(path.dirname(leaked), { recursive: true });
  fs.writeFileSync(leaked, 'must remain untouched\n');

  const result = run(['--output', output]);
  assert.notEqual(result.status, 0, diagnostic(result));
  assert.match(result.stderr, /outside the public manifest/);
  assert.equal(fs.readFileSync(leaked, 'utf8'), 'must remain untouched\n');
  assert.equal(fs.existsSync(path.join(output, 'index.html')), false);
});

test('unsafe output roots are refused', () => {
  for (const output of [
    ROOT,
    path.join(TEMP, 'not-the-dist-directory'),
    path.join(path.parse(ROOT).root, 'dist'),
    path.join(os.homedir(), 'dist')
  ]) {
    const result = run(['--output', output]);
    assert.notEqual(result.status, 0, diagnostic(result));
    assert.match(result.stderr, /output directory must be named 'dist'|refusing repository|refusing broad output/);
  }
});
