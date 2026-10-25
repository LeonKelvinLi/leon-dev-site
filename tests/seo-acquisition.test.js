const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
// The root source remains available for legacy page generation. Assertions must
// inspect the reviewed export that the publisher actually serves at /.
const read = (file) => fs.readFileSync(
  path.join(ROOT, file === 'index.html' ? 'homepage/index.html' : file), 'utf8'
);
const text = (html) => html
  .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
  .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
  .replace(/<[^>]+>/g, ' ')
  .replace(/&amp;/g, '&')
  .replace(/&#x27;|&#39;/g, "'")
  .replace(/\s+/g, ' ')
  .trim();

function publicHtmlFiles() {
  const out = [];
  const visit = (directory, prefix = '') => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      if (entry.name === 'dist' || entry.name.startsWith('.')) continue;
      const absolute = path.join(directory, entry.name);
      const relative = path.join(prefix, entry.name);
      if (entry.isDirectory()) {
        if (['assets', 'content', 'data', 'homepage', 'node_modules', 'private', 'research', 'server', 'tests', 'tools'].includes(entry.name)) continue;
        visit(absolute, relative);
      } else if (entry.name.endsWith('.html')) {
        out.push(relative);
      }
    }
  };
  visit(ROOT);
  return out.sort();
}

function metadataText(html, pattern) {
  const value = html.match(pattern)?.[1] || '';
  return text(`<span>${value}</span>`);
}

function schemaNodes(html) {
  return Array.from(
    html.matchAll(/<script\b[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi),
    match => JSON.parse(match[1])
  ).flatMap(root => {
    const roots = Array.isArray(root) ? root : [root];
    return roots.flatMap(node => Array.isArray(node['@graph']) ? node['@graph'] : [node]);
  });
}

test('published homepage metadata, services, and inquiry path state the current offer', () => {
  const html = read('index.html');
  const visible = text(html);
  assert.match(html, /<title>Small Business Websites &amp; Automation \| Leon Builds<\/title>/i);
  const description = metadataText(html, /<meta\b[^>]*name="description"[^>]*content="([^"]+)"/i);
  assert.match(description, /websites, automation, and custom tools/i);
  assert.match(description, /small business easier to run/i);
  assert.match(description, /directly with Leon/i);
  assert.match(html, /<link\b[^>]*rel="canonical"[^>]*href="https:\/\/leonbuilds\.org\/?"/i);
  assert.equal((html.match(/<h1\b/gi) || []).length, 1);
  assert.match(visible, /websites, apps & automation/i);
  assert.match(visible, /small businesses/i);
  assert.ok(html.indexOf('id="services"') < html.indexOf('id="work"'));
  assert.match(html, /href="#start"/i);
  assert.match(html, /href="#work"/i);
  assert.match(html, /id="start"/i);
  assert.match(html, /<form\b/i);
  assert.match(html, /id="quote-email"[^>]*type="email"|type="email"[^>]*id="quote-email"/i);
  assert.match(html, /id="quote-problem"/i);
  for (const price of ['$199', '$1,500', '$500']) {
    assert.match(visible, new RegExp('\\$\\s*' + price.slice(1)), `homepage includes the published ${price} starting floor`);
  }
  const nodes = schemaNodes(html);
  assert.equal(nodes.find(node => node['@id'] === 'https://leonbuilds.org/#business')?.['@type'], 'Organization');
  assert.equal(nodes.find(node => node['@id'] === 'https://leonbuilds.org/#leon')?.['@type'], 'Person');
  assert.doesNotMatch(html, /"@type"\s*:\s*"ProfessionalService"/i);
});

test('work archive is indexable, canonical, and honest about proof status', () => {
  const html = read('work.html');
  const visible = text(html);
  assert.match(html, /<title>[^<]*(?:Work|Websites|Software)[^<]*\| Leon Builds<\/title>/i);
  assert.match(html, /<link rel="canonical" href="https:\/\/leonbuilds\.org\/work">/i);
  assert.equal((html.match(/<h1\b/gi) || []).length, 1);
  assert.match(visible, /beastypages\.com/i);
  assert.match(visible, /ALLCPR Site Intelligence/i);
  assert.match(visible, /Operational client system.*ALLCPR/is);
  assert.match(visible, /33,772 U\.S\. ZIP-code records/i);
  assert.match(visible, /field validation before opening/i);
  assert.doesNotMatch(visible, /guaranteed best location|automatic opening decision/i);
  assert.match(visible, /client website project.*demo checkout/is);
  assert.match(html, /href="https:\/\/beastypages\.com\/\?b=b_bulapies"/i);
  assert.doesNotMatch(html, /the-home-screen\.onrender\.com/i);
  assert.match(visible, /payment and kitchen progression are simulations/is);
  assert.match(visible, /loqol disclosures/i);
  assert.match(visible, /public demo.*incomplete/is);
  assert.match(html, /href="https:\/\/loqol-tds\.onrender\.com\/agent"[^>]*data-evt="case_loqol_click"/i);
  assert.doesNotMatch(html, /case_loqol_source_click|Inspect the source/i);
  assert.match(visible, /curio/i);
  assert.match(visible, /live product.*app store/is);
  assert.doesNotMatch(html, /aggregateRating|reviewRating|ratingValue|"@type"\s*:\s*"Review"/i);
  assert.match(read('sitemap.xml'), /<loc>https:\/\/leonbuilds\.org\/work<\/loc>/i);
});

test('public pages route work and pricing links to the new real destinations', () => {
  for (const file of publicHtmlFiles()) {
    const html = read(file);
    assert.doesNotMatch(html, /href=["']\/#(?:fix|outcomes|pricing|work(?:-[^"']*)?)(?:["'])/i, `${file} has no stale English homepage anchor`);
    assert.doesNotMatch(
      html,
      /https:\/\/(?:github\.com\/Noctilucenty(?:\/|["'])|noctilucenty\.github\.io)/i,
      `${file} does not publish the retired external identity or portfolio destinations`
    );
    assert.doesNotMatch(
      html,
      /public source-backed document workflow|source-backed workflow demo|source repository showing/i,
      `${file} does not promise source access after the retired repository links were removed`
    );
    const title = html.match(/<title>([^<]+)<\/title>/i)?.[1] || '';
    if (title) {
      assert.match(title, /Leon Builds/i, `${file} uses the Leon Builds brand in its title`);
      assert.doesNotMatch(
        title,
        /Leon Builds by Leon Kelvin Li|\|\s*Leon Kelvin Li\s*$/i,
        `${file} does not publish a stale or overlong title suffix`
      );
    }
  }
});

test('service titles, social metadata, and WebPage schema use one current brand identity', () => {
  const files = fs.readdirSync(path.join(ROOT, 'services'))
    .filter(file => file.endsWith('.html') && file !== 'index.html')
    .map(file => path.join('services', file));

  for (const file of files) {
    const html = read(file);
    const title = metadataText(html, /<title>([^<]+)<\/title>/i);
    const socialTitle = metadataText(
      html,
      /<meta\s+property="og:title"\s+content="([^"]+)">/i
    );
    const page = schemaNodes(html).find(node => node['@type'] === 'WebPage');

    assert.match(title, /\| Leon Builds$/i, `${file} uses the concise current brand suffix`);
    assert.equal(socialTitle, title, `${file} Open Graph title matches its document title`);
    assert.ok(page, `${file} includes a WebPage schema node`);
    assert.equal(page.name, title, `${file} WebPage schema name matches its document title`);
  }
});

test('localized service and booking titles keep native intent with the concise brand suffix', () => {
  const files = publicHtmlFiles().filter(file => /^(?:es|pt|zh)\/(?!index\.html)[^/]+\.html$/.test(file));

  for (const file of files) {
    const html = read(file);
    const title = metadataText(html, /<title>([^<]+)<\/title>/i);
    const socialTitle = metadataText(
      html,
      /<meta\s+property="og:title"\s+content="([^"]+)">/i
    );
    const page = schemaNodes(html).find(node => node['@type'] === 'WebPage');
    const intentTitle = title.replace(/\s*\|\s*Leon Builds$/i, '');

    assert.match(title, /\| Leon Builds$/i, `${file} uses the concise current brand suffix`);
    assert.doesNotMatch(title, /Leon Builds by/i, `${file} leaves room for the native search intent`);
    assert.equal(socialTitle, title, `${file} Open Graph title matches its document title`);
    assert.ok(page, `${file} includes a WebPage schema node`);
    assert.equal(page.name, intentTitle, `${file} WebPage schema name matches the unbranded intent title`);
  }
});

test('localized schemas keep Leon Kelvin Li and Leon Builds as linked, distinct entities', () => {
  const files = publicHtmlFiles().filter(file => /^(?:es|pt|zh)\/[^/]+\.html$/.test(file));
  const personId = 'https://leonbuilds.org/#leon';
  const businessId = 'https://leonbuilds.org/#business';

  for (const file of files) {
    const nodes = schemaNodes(read(file));
    const person = nodes.find(node => node['@id'] === personId);
    const business = nodes.find(node => node['@id'] === businessId);
    assert.ok(person, `${file} defines the canonical Person node`);
    assert.equal(person['@type'], 'Person', `${file} keeps Leon as a Person`);
    assert.equal(person.name, 'Leon Kelvin Li', `${file} uses Leon's canonical name`);
    assert.equal(person.alternateName, 'Leon Li', `${file} keeps the business name off the Person`);
    assert.equal(person.worksFor?.['@id'], businessId, `${file} links Leon to Leon Builds`);
    assert.ok(business, `${file} defines the referenced business node`);
    assert.equal(business['@type'], 'Organization', `${file} keeps Leon Builds as an Organization`);
    assert.equal(business.name, 'Leon Builds', `${file} uses the canonical business name`);
    assert.equal(business.founder?.['@id'], personId, `${file} links the business to its founder`);
    assert.equal(business.employee?.['@id'], personId, `${file} links the business to Leon`);

    const ids = nodes.map(node => node['@id']).filter(Boolean);
    assert.equal(new Set(ids).size, ids.length, `${file} has no duplicate schema node IDs`);
  }
});

test('website pillar answers search, trust, scope, and next-action questions', () => {
  const html = read('services/websites.html');
  const visible = text(html);

  assert.match(html, /<title>Small Business Web Design \| Fixed-Price Websites \| Leon Builds<\/title>/i);
  assert.match(visible, /small-business web design with one clear next step/i);
  assert.doesNotMatch(visible, /Leon works in all four/i);
  assert.match(visible, /translated copy reviewed and approved by you/i);
  assert.match(visible, /not a complete custom application/i);
  assert.match(visible, /what your website must answer in five seconds/i);
  assert.match(visible, /website cost depends on what the site must do/i);
  assert.match(visible, /beastypages\.com client website/i);
  assert.match(visible, /37 businesses in the September 4, 2026 review snapshot/i);
  assert.match(html, /href="\/work\/beastypages-website"/i);
  assert.match(html, /data-testimonial-id="testimonial-03"/i);
  assert.match(visible, /I hired Leon to build The Home Screen website/i);
  assert.match(visible, /Current name: beastypages\.com/i);
  assert.doesNotMatch(html, /testimonial-stars|5 out of 5 stars|★★★★★/i);
  assert.match(html, /href="\/industries\/contractors"/i);
  assert.match(html, /href="\/industries\/automotive"/i);
  assert.match(html, /href="\/industries\/restaurants"/i);

  const hero = html.match(/<section class="sec page-hero">[\s\S]*?<\/section>/i)?.[0] || '';
  assert.ok(hero.indexOf('href="/quote"') < hero.indexOf('href="/call"'), 'quote-ready buyers do not have to book a call');
  assert.match(text(hero), /\$199 starter/);
  const detailsEnd = html.indexOf('</div></details>');
  assert.ok(html.indexOf('class="sec service-reviews"') > detailsEnd, 'client feedback is outside collapsed scope details');
});

test('app-development landing page is clear, credible, and quote-first', () => {
  const html = read('services/mobile-apps.html');
  const visible = text(html);
  const hero = html.match(/<section class="sec page-hero">[\s\S]*?<\/section>/i)?.[0] || '';
  const ctas = hero.match(/<div class="ctarow">[\s\S]*?<\/div>/i)?.[0] || '';

  assert.match(html, /<title>iOS &amp; Android App Development — from \$3,500 \| Leon Builds<\/title>/i);
  assert.match(visible, /turn your app idea into a working iPhone and Android product/i);
  assert.match(visible, /founders and businesses/i);
  assert.match(hero.replace(/<[^>]+>/g, ' '), /(?:starting at|from)\s+\$3,500/i);
  assert.match(visible, /fixed written quote|written fixed quote/i);
  assert.match(visible, /custom iOS and Android app development/i);
  assert.match(visible, /mobile website is usually the smaller first step/i);
  assert.match(visible, /existing prototype or codebase/i);
  assert.match(visible, /approval cannot be guaranteed/i);
  assert.match(visible, /smallest useful release/i);
  assert.match(html, /<body\b[^>]*class="app-service"[^>]*data-assistant-launcher="hidden"/i, 'paid app traffic gets its focused page treatment without a competing floating launcher');
  assert.match(hero, /turn your app idea into[\s\S]*working iPhone and Android product/i);
  assert.match(html, /<figure class="service-proof-media">[\s\S]*curio-appstore-current\.png[\s\S]*<\/figure>/i, 'app proof includes a real current product visual');
  assert.ok(hero.indexOf('href="/quote"') < hero.indexOf('href="/call"'), 'fixed quote is the first app-page action');
  assert.match(hero, /href="\/quote"[^>]*class="[^"]*btn-solid|class="[^"]*btn-solid[^"]*"[^>]*href="\/quote"/i, 'fixed quote is the filled app-page action');
  assert.equal((ctas.match(/<a\b/gi) || []).length, 2, 'app hero has only the quote and call actions');
  assert.doesNotMatch(hero, /mailto:|data-assist-open/i, 'app hero removes tertiary conversion choices');
  assert.doesNotMatch(visible, /most app projects die|agencies quote six figures|marketplaces hand you code|too many zeros/i);
  assert.match(html, /<meta property="og:image" content="https:\/\/leonbuilds\.org\/assets\/og-mobile-apps\.png">/i);
  assert.match(html, /<meta property="og:image:width" content="1200">/i);
  assert.match(html, /<meta property="og:image:height" content="630">/i);
  assert.match(html, /<meta name="twitter:image" content="https:\/\/leonbuilds\.org\/assets\/og-mobile-apps\.png">/i);

  const schema = Array.from(html.matchAll(/<script\b[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi), match => JSON.parse(match[1])).flat();
  const page = schema.find(node => node['@type'] === 'WebPage');
  const service = schema.find(node => node['@type'] === 'Service');
  assert.equal(service.name, 'iOS and Android app development');
  assert.equal(service.serviceType, 'iOS and Android app development');
  assert.equal(service.audience['@type'], 'BusinessAudience');
  assert.equal(page.mainEntity['@id'], service['@id']);
});

test('app service has natural authority links from relevant proof and identity pages', () => {
  assert.match(read('index.html'), /href="(?:https:\/\/leonbuilds\.org)?\/services\/mobile-apps"/i);
  assert.match(read('work.html'), /work-curio-public[\s\S]*href="\/services\/mobile-apps"/i);
  assert.match(read('about.html'), /My own app[\s\S]*href="\/services\/mobile-apps"/i);
});

test('services index exposes starting floors without making buyers open nine pages', () => {
  const visible = text(read('services/index.html'));
  for (const floor of ['$300', '$450', '$3,500', '$750', '$1,000', '$500', '$1,500', '$600']) {
    assert.ok(visible.includes(`from ${floor}`), `services index includes ${floor}`);
  }
});

test('high-intent industry pages form a focused web-design and lead-recovery cluster', () => {
  const pages = [
    ['industries/restaurants.html', /restaurant website design &amp; online ordering/i, /what a restaurant website needs/i],
    ['industries/contractors.html', /contractor web design &amp; lead follow-up/i, /what a contractor website needs/i],
    ['industries/automotive.html', /auto repair website design &amp; booking/i, /what an auto repair website needs/i],
  ];

  for (const [file, titlePattern, contentPattern] of pages) {
    const html = read(file);
    const main = html.match(/<main\b[^>]*>[\s\S]*?<\/main>/i)?.[0] || '';
    assert.match(html, titlePattern, `${file} has a specific search title`);
    assert.match(text(html), contentPattern, `${file} has distinct buyer guidance`);
    assert.match(html, /href="\/services\/websites"/i, `${file} links to the web-design pillar`);
    if (file === 'industries/contractors.html') {
      assert.match(main, /href="\/missed-lead-recovery"/i, `${file} links to the contractor product`);
      assert.match(main, /data-testimonial-id="testimonial-03"/i, `${file} puts an approved website-client review beside the web-design guidance`);
      assert.match(text(main), /I hired Leon to build The Home Screen website/i, `${file} uses the exact released website testimonial`);
      assert.match(text(main), /Current name: beastypages\.com/i, `${file} clarifies the current project name without rewriting the client's quote`);
    } else {
      assert.doesNotMatch(main, /href="\/missed-lead-recovery/i, `${file} main content does not point to a mismatched contractor product`);
    }
  }
});

test('only released client feedback appears on related service pages and ratings stay off', () => {
  const pages = [
    'services/ai-chatbots.html',
    'services/ai-phone-agents.html',
    'services/business-automation.html',
    'services/business-dashboards.html',
    'services/custom-software.html',
  ];
  const publication = JSON.parse(read('content/client-success/testimonial-publication.json'));
  const releasedIds = new Set(publication.approved_testimonials.map(record => record.id));

  for (const file of pages) {
    const html = read(file);
    const publishedOnPage = Array.from(
      html.matchAll(/data-testimonial-id=["']([^"']+)["']/gi),
      match => match[1]
    );
    for (const testimonialId of publishedOnPage) {
      assert.ok(releasedIds.has(testimonialId), `${file} only renders testimonials in the release manifest`);
    }
    assert.doesNotMatch(html, /testimonial-stars|5 out of 5 stars|★★★★★/i);
    const schemas = Array.from(html.matchAll(/<script\b[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi), match => match[1]);
    assert.doesNotMatch(schemas.join('\n'), /AggregateRating|Review|reviewRating|ratingValue/i);
  }
});

test('GEO index states current proof and avoids stale contradictions', () => {
  const llms = read('llms.txt');
  assert.match(llms, /business websites/i);
  assert.match(llms, /lead follow-up/i);
  assert.match(llms, /\$300/i);
  assert.match(llms, /\$1,500/i);
  assert.match(llms, /\$500/i);
  assert.match(llms, /inspectable public (?:work|proof)/i);
  assert.match(llms, /Curio.*App Store/is);
  assert.match(llms, /## Mobile app development/i);
  assert.match(llms, /founders and small businesses/i);
  assert.match(llms, /store.*approval.*does not guarantee|does not guarantee store approval/is);
  assert.match(llms, /beastypages\.com.*client website.*(?:demo|payments are mocked|payments are not live)/is);
  assert.match(llms, /https:\/\/beastypages\.com\/\?b=b_bulapies/i);
  assert.doesNotMatch(llms, /the-home-screen\.onrender\.com/i);
  assert.match(llms, /Loqol.*public demo.*incomplete/is);
  assert.doesNotMatch(llms, /there are no client names, testimonials, reviews or star ratings|seven direct client reviews|five-star|all 5 stars|#testimonials|22-business operation/i);
});
