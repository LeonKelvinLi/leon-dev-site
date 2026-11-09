# Subscription publication — November 9, 2026

This branch is a local release candidate. Do not merge/push to a production-watched branch or deploy without Leon’s explicit approval.

The current homepage source is the sibling `leonbuilds-subscription` worktree of freelance2. Build it, then copy only `index.html`, `favicon.svg`, `_next/`, and `images/` from `dist/client` into `homepage/`. Generated assets are replaceable; never touch `data/` or runtime storage. Build into a new/empty output directory if old content-hashed chunks remain; the publisher intentionally refuses to delete unexpected output.

`tools/subscription_public.py` creates the new support pages in `content/subscription-public/`. Original service, localized, quote, and case-study source files remain recoverable as historical generator inputs. They are **not the final public offer**. `build_static.py` composes the new homepage, new membership transition pages, retained portfolio/privacy/guide content with a simplified shell, and unchanged working infrastructure. It validates original and final testimonial documents. The historical SEO ledger remains historical; the new public checker validates actual pages, internal destinations, scope, prices, canonical URLs, and the indexable sitemap. Old service/industry/localized/quote/call URLs become English transition pages marked `noindex,follow`, not advertised translations of the new landing page. The public sitemap contains 11 substantive pages.

Generate explicitly, then check/build:

```sh
python3 tools/subscription_public.py
npm run build:static
npm run check:subscription
node --test tests/*.test.js
python3 -m unittest tests/test_seo_system.py tests/test_search_console_sync.py tests/test_acquisition_report.py tests/test_indexnow.py tests/test_live_search.py
```

Generation is explicit. Manifest read-only checks reject stale generated pages and never regenerate them. Existing publication/proof gates run before composition, and the composed public documents are checked again. Existing legacy tests continue to protect historical inputs; changed assertions cover the new membership rather than old homepage tiers.

`npm run check` covers the current price, public-manifest, proof, content, SEO, API, security, analytics, and publication checks. `npm run check:legacy-creatives` retains the original exact-PNG comparisons for archived social/listing/Facebook campaigns. Those unchanged assets fail their old byte checks under Pillow 11.3 and 13.0. They are absent from the public manifest, and the active public checker rejects them if reintroduced. This explicitly retires that inactive campaign gate from the current release without hiding the failed archival comparison. Do not reuse or publish those campaigns until their asset check is resolved.

Local export QA: start the API on 8790 with an isolated LEON_DATA_DIR and no provider keys, then `node tools/preview_subscription.cjs` serves http://127.0.0.1:4600. Its API proxy is local-only. Never treat this as live email delivery, an external booking, payment, or production verification.

No customer data, persistent storage settings, production environment variables, Render configuration, domain bindings, consent settings, or provider billing have been modified. `server/prompt.js` quotes only the new offer. `server/events.js` recognizes the new CTA names while preserving historical funnel events.
