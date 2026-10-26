#!/usr/bin/env python3
"""Generates the SEO page fleet: /services/*, /industries/*, both index pages,
/work, /work/* case studies, /guides/*, conditional /reviews, /missed-lead-recovery,
/quote, sitemap.xml and robots.txt — all in the site's own visual language
(same styles.css, nav, footer, lowercase-by-CSS, one accent).

Run after editing PAGE DATA below:   python3 tools/build_pages.py
Anything inside services/ and industries/ is overwritten on every run.
Render static sites serve pretty URLs, so /services/websites -> websites.html.
"""
import html, json, os, datetime, subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from testimonial_gate import load_testimonial_release
from seo_system import assert_publication_paths, related_html, read_json as seo_json, validate_topics
from visual_explainers import service_visual, industry_visual, choice_scene, flow_scene

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://leonbuilds.org"
TODAY = datetime.date.today().isoformat()
TESTIMONIAL_DRAFTS, RELEASED_TESTIMONIALS = load_testimonial_release(
    Path(ROOT)
)
TESTIMONIAL_DRAFTS_BY_ID = {item["id"]: item for item in TESTIMONIAL_DRAFTS}
TESTIMONIAL_DISPLAY_ORDER = [
    "testimonial-04",  # contractor website
    "testimonial-03",  # business homepage
    "testimonial-05",  # dealership phone workflow
    "testimonial-01",  # custom product design
    "testimonial-02",  # location-planning platform
    "testimonial-07",  # renovation proposal
    "testimonial-06",  # evidence-aware assistant
]
HOMEPAGE_TESTIMONIAL_LIMIT = 2
TESTIMONIAL_PROJECT_LINKS = {
    "testimonial-02": "/work/allcpr-site-intelligence",
    "testimonial-03": "/work/beastypages-website",
}
TESTIMONIAL_PROJECT_LABELS = {
    "testimonial-03": "beastypages.com",
}
TESTIMONIAL_PROJECT_NOTES = {
    "testimonial-03": "Current name: beastypages.com.",
}
REVIEWS_ROUTE_ENABLED = len(RELEASED_TESTIMONIALS) >= 3
REVIEWS_PUBLISHED = bool(RELEASED_TESTIMONIALS)
IDENTITY_URLS = [
    "https://trycurio.app/team.html#leon",
    "https://www.worldcubeassociation.org/persons/2016LILE01",
    "https://www.f6s.com/leonkelvinli",
    "https://www.linkedin.com/in/leon-kelvin-li",
    "https://apps.apple.com/us/developer/leon-kelvin-li/id6781121129",
    "https://www.instagram.com/lkelvn_/",
]

# ══════════════════════════════════════════════════════════════════
# PAGE DATA
# ══════════════════════════════════════════════════════════════════

SERVICES = [
 dict(slug="websites", name="small-business web design", h1=("Small-business web design with", "one clear next step."),
  price="$300", title="Small Business Web Design | Fixed-Price Websites | Leon Builds",
  desc="Phone-first small-business web design from a California-based, founder-led studio. Clear calls to action, fixed scope, direct communication and clean handover.",
  intro=["your website has seconds to answer four questions: what you do, who it is for, why the visitor should trust you, and what they should do next.",
   "we design fast, phone-first business websites around that decision. you work directly with the founder who builds the project, see a working link during the build, and get a written scope and handover."],
  pains=["you have no website, or you're embarrassed to send people to it","it looks broken on phones","nobody on your team can change the text or the hours","it doesn't take bookings, orders or payments","you paid an agency and can't even log into your own site"],
  build=["a fast, responsive website with clear calls, quote requests, bookings or orders","search-ready titles, page structure, internal links, sitemap and structured data","editable content where the scope calls for it","the included source code and setup notes handed over; domains, hosting, fonts, plugins and other vendors keep their own terms","multilingual website layouts and content, with translated copy reviewed and approved by you before launch"],
  proof=("beastypages.com client website","inspect the phone-first catalog, which contained 37 businesses in the September 4, 2026 review snapshot, plus search, menus, and a clearly labelled demo cart. payment and kitchen progression are simulations."),
  faqs=[("how much does a website cost?","the focused one-page starter is $199 with supplied content, one contact or booking link and one revision. larger frontend business sites start at $300. a small, defined backend integration starts around $625, not a complete custom application. you get a written fixed quote before work starts; any change to that scope needs your agreement first."),
   ("i already have a website. do i have to start over?","usually not. most sites have one real problem — slow, broken on phones, or nobody can update it. a redesign is priced like a new build, from $300, and we'll tell you which parts are worth keeping."),
   ("how long does it take?","most focused business sites take one to two weeks after the scope, content and required access are ready. you get a working link to review during the build."),
   ("do you only design websites in california?","no. we're based in california and work remotely with businesses across the united states."),
   ("is seo included?","every build includes clean technical foundations: descriptive titles, crawlable links, a sitemap, mobile performance and structured content. ongoing search work is a separate scope when needed."),
   ("will i be able to update the site?","yes when editing is part of the scope. the proposal states what you can change, which accounts are yours and what is included in handover.")],
  review_ids=["testimonial-04", "testimonial-03"],
  web_guide=True,
  related=["booking-systems","seo","business-automation"]),

 dict(slug="mobile-apps", name="mobile apps", h1=("Turn your app idea into", "a working iPhone and Android product."),
  price="$3,500", title="iOS & Android App Development — from $3,500 | Leon Builds",
  desc="Custom iOS and Android app development for founders and small businesses—from first usable release through backend, testing and store submission. From $3,500.",
  intro=["We design and build focused mobile apps for founders and businesses—from the first usable version through backend, testing, and store submission.",
   "You work directly with Leon, who shipped a live App Store product end to end, including subscriptions and review."],
  pains=["You have an app idea and no technical team","Customers keep asking whether your business has an app","You need a first usable product before investing in a larger build","Your existing prototype still cannot be shipped","You need the backend, accounts, notifications, or payments—not just screens"],
  build=["iPhone and Android from one codebase when that is the right technical choice","the backend, accounts, notifications, and payments behind the app","App Store and Google Play submission support, including review responses","subscriptions and in-app purchases wired to the agreed scope","agreed project accounts are set up in your name and included source code is handed over; app stores, libraries, and vendors keep their own terms"],
  proof=("Curio — live App Store product","A consumer iOS app designed and shipped end to end, with a backend, subscriptions, App Store review, and content in four languages."),
  faqs=[("What happens before you build, and what does an app cost?","We first define the smallest useful release, its users, required screens, accounts, integrations, and store plan. Focused app builds start at $3,500, and you receive a fixed written quote before work begins."),
   ("Do I need an app or would a mobile website be enough?","A mobile website is usually the smaller first step when people only need to find, contact, book, or buy from you occasionally. An app becomes useful when customers return often or need accounts, notifications, offline access, or phone features. We'll recommend the smaller option when it fits."),
   ("Can you take over an existing prototype or codebase?","Often, but we inspect the code, accounts, backend, and store setup before quoting. If repairing it would cost more than rebuilding the focused first version, we'll explain that before work starts."),
   ("Should we start with iPhone, Android, or both?","That depends on your users and the fastest useful first release. When one shared codebase is a sound choice, we can build for both; otherwise we'll explain why starting with one platform reduces risk."),
   ("How long does launch take, and can you guarantee store approval?","The build timeline is written into the scope after the first version is defined. Store review happens on Apple or Google's schedule and approval cannot be guaranteed, but submission support and reasonable review responses are included when specified."),
   ("Who owns the app, and what happens after launch?","The agreed project accounts and store listing are set up in your name, and the included source code and backend setup notes are handed over. Any maintenance or post-launch support is written separately; app stores, hosting providers, libraries, and other vendors keep their own terms.")],
  related=["custom-software","websites","booking-systems"]),

 dict(slug="ai-chatbots", name="ai chatbots", h1=("help customers get answers", "from your business information"),
  price="$750", title="AI Chatbot for Your Business — from $750 | Leon Builds",
  desc="A website chatbot built around your approved business information, with answer testing, lead capture, and clear rules for human handoff. From $750.",
  intro=["customers often ask the same questions: hours, prices, availability, 'do you do X'. a chatbot can help answer them after hours and in multiple languages, using the information you approve.",
   "we ground the assistant in your approved information, test its answers, and give it a clear route to a person when it is unsure. ai can still make mistakes, so sensitive decisions stay with your staff. the assistant on this site is one Leon built."],
  pains=["staff answer the same questions all day","after-hours visitors leave without answers","your website gets traffic but no messages","spanish or chinese-speaking customers get no help","you tried a chatbot builder and it made things up"],
  build=["a chatbot grounded in your approved business information","written handoff rules and a way for visitors to reach a person","lead capture so visitors can request a reply","multilingual: english, spanish, portuguese, chinese","rules and tests for prices, policies, and questions it should not answer"],
  proof=("two different assistant projects","Leon built a chinese-language health-education prototype with source citations and safety rules. the project assistant on this website is a separate build: try it at the bottom right to discuss a project or request a reply."),
 faqs=[("what does a chatbot cost?","from $750 for a site chatbot trained on your business. connecting it to booking or your other systems adds scope — fixed quote before anything starts."),
   ("will it say something wrong to a customer?","it can. we reduce that risk with approved source material, answer testing, clear limits, and human handoff. prices, policies, and sensitive decisions need explicit rules; an ai assistant should never be treated as infallible."),
   ("can it capture leads?","yes — we can add a short handoff that collects the visitor's project details and contact information for your reply. the assistant on this site shows that flow.")],
  review_ids=["testimonial-06"],
  related=["ai-phone-agents","business-automation","websites"]),

 dict(slug="ai-phone-agents", name="ai phone agents", h1=("your phone, answered", "at 2am and during the rush"),
  price="$1,000", title="AI Phone Agent — from $1,000 | Leon Builds",
  desc="An AI that answers your business phone, handles the repetitive calls, books appointments and hands anything unusual to a person. Built with written handoff rules.",
  intro=["when your team is busy, a missed call can mean a missed booking. an ai phone agent can help with routine questions while staff focus on customers.",
   "we define which calls it can handle — hours, booking, status checks — and when it should transfer or take a message. those rules are agreed with you and tested before launch. ai can make mistakes, so important decisions stay with a person."],
  pains=["calls ring out during the rush or after close","one person spends half their day on 'are you open' and 'is it ready'","voicemail is where your leads go to die","the front desk can't book and answer phones at once"],
  build=["an agent for routine calls, with a fallback when the service is unavailable","booking wired into your real calendar or scheduling system","status lookups from your own systems where they expose data","staff transfer or message-taking under agreed rules","call summaries so you see what customers actually ask"],
  proof=("built with the same discipline as the review desk","every ai system we ship keeps a human in the loop by design — the review desk drafts replies but a person presses send. phone agents get the same treatment."),
 faqs=[("what happens when the ai can't handle a call?","we agree on transfer and message-taking rules before launch, including what happens when no staff member is available. the goal is reducing repetitive calls while keeping a route to a person."),
   ("what does it cost?","from $1,000 depending on what the agent needs to do — answering and booking is simpler than pulling live order status from your systems."),
   ("does it work with my scheduling software?","often, if your system exposes the data. we verify the specific integration before quoting rather than promising first.")],
  review_ids=["testimonial-05"],
  related=["ai-chatbots","booking-systems","business-automation"]),

 dict(slug="business-automation", name="business automation", h1=("the follow-ups happen", "whether anyone remembers or not"),
  price="$500", title="Workflow & Business Automation — from $500 | Leon Builds",
  desc="Form-to-sheet-to-email workflows, Google Workspace and n8n automation, and integrations that stop your team copying data between systems by hand.",
  intro=["most 'we need software' problems are actually 'two systems don't talk' problems. the fix is rarely a new platform — it's a pipe between the tools you already pay for.",
   "we build those pipes where your team can see them: google workspace automations in apps script, n8n workflows your staff can read and edit, and integrations with quickbooks, stripe, slack, twilio, your pos, or your ats."],
  pains=["data gets copied between systems by hand","new leads and form submissions sit unanswered","reports take hours of exporting and pasting","approvals and handoffs live in someone's memory","five tools, none of them talking to each other"],
  build=["form → sheet → document → email chains, end to end","n8n pipelines your team can edit without calling us","integrations: quickbooks, stripe, google, slack, twilio, your pos","automatic reports that build themselves on schedule","document workflows: created, filed, approved, versioned"],
  proof=("document control","a request names a template; seconds later the google doc exists, filed and shared correctly. approval locks it, publishing versions it. built in apps script, then again as six n8n workflows the team edits themselves."),
  faqs=[("what should i automate first?","the thing a person does most often with the least judgment — retyping, forwarding, filing. we find it in the free call; it's usually obvious within ten minutes."),
   ("is this ai?","mostly not, and that's a feature. deterministic automations are cheaper and more reliable. ai enters only where reading or drafting is involved."),
   ("what does it cost?","workflow automation starts at $500. a single pipe between two systems is the low end; multi-step pipelines touching several systems scale from there. after launch, the event log and time spent on the old process give you a concrete way to judge whether the automation is worth keeping or expanding.")],
  review_ids=["testimonial-05"],
  related=["business-dashboards","ai-chatbots","custom-software"]),

 dict(slug="custom-software", name="custom software", h1=("built around how your", "business actually runs"),
  price="$1,500", title="Custom Software Development | Leon Builds",
  desc="Custom business software built end to end by one developer: portals, platforms, operations systems. Fixed written quotes. U.S.-wide, remote.",
  intro=["off-the-shelf software fits the average business. yours isn't average — that's why there's still a spreadsheet holding part of it together.",
   "custom software is for when nothing on the menu is the shape of your problem. the client-funded beastypages.com website, for example, pairs public business pages with server-side pricing and vendor-separated demo order logic while clearly keeping payments and kitchen operations mocked."],
  pains=["you've outgrown the spreadsheet that runs part of the business","off-the-shelf tools each do 70% of what you need","your industry has a workflow no product understands","you're paying for five subscriptions to approximate one system"],
  build=["operations systems designed around your real workflow","web apps your team logs into every day","the database, accounts, permissions and reports underneath","migrations off the spreadsheet without losing history","one system replacing several almost-right subscriptions"],
  proof=("ALLCPR Site Intelligence","an operational location-planning platform built from 33,772 U.S. ZIP-code records in the reviewed project dataset while keeping uncertainty and field validation visible."),
 faqs=[("how do i know custom is worth it vs off-the-shelf?","if an existing product does 90% of what you need, buy it — we'll tell you so in the free call. custom wins when the missing part is what your business actually runs on."),
   ("what does custom software cost?","full builds start at $1,500 and scale with scope. quotes are written and fixed, with staged payments tied to milestones you can see working."),
   ("can another developer take over later?","yes. the agreed repo and project accounts, included source code and setup documentation are handed over. third-party hosts and licensed services keep their terms, and another competent developer can use the handoff — nothing is set up to make us irreplaceable.")],
  review_ids=["testimonial-02", "testimonial-07"],
  related=["mobile-apps","business-automation","business-dashboards"]),

 dict(slug="booking-systems", name="booking & online ordering", h1=("customers book and order themselves —", "the reminder does the rest"),
  price="$600", title="Booking & Online Ordering — from $600 | Leon Builds",
  desc="Booking and ordering on your website: appointments, deposits, reminders and a direct-order cart. We add no booking fee; provider terms still apply.",
  intro=["every booking handled by phone uses staff time, and every no-show leaves a slot unused. online booking removes the retyping; reminders, deposits and easy rescheduling give you measurable ways to address missed appointments.",
   "we build booking around your site, calendar and rules instead of defaulting to a generic branded widget. any payment, messaging, hosting or calendar-provider fees stay visible in the written scope.",
   "ordering works the same way. a direct cart gives returning customers a channel you control. marketplace, card, delivery and hosting costs vary by provider and contract, so the comparison uses your real statements."],
  pains=["booking happens by phone and eats front-desk time","no-shows are killing your calendar","after-hours visitors can't book and don't call back","a delivery app takes a cut of every order and owns your customer","your current booking tool takes a cut or looks like an ad for itself"],
  build=["booking pages that match your site, not a widget's brand","staff calendars, service durations, buffer rules","deposits and card-on-file through stripe","automatic sms/email reminders and easy rescheduling","sync with the calendar your team already lives in","direct ordering with no per-order commission added by us: cart, payment, and a ticket that reaches the kitchen"],
  proof=("built like the ordering system","the same server-side discipline as the multi-brand ordering platform: rules enforced where customers can't edit them."),
  faqs=[("what does a booking system cost?","from $600 built into your site, and direct online ordering from $600. we charge no monthly per-booking or per-order cut; payment, messaging, hosting and other provider terms still apply."),
   ("can customers pay a deposit when they book?","yes — deposits, full prepayment or card-on-file, through stripe, with receipts handled."),
   ("we already use a scheduling tool. keep it?","if it works, keep it — sometimes the right build is your website talking to it. we'll tell you which in the free call.")],
  related=["websites","ai-phone-agents","business-automation"]),

 dict(slug="business-dashboards", name="dashboards & internal tools", h1=("the four numbers that decide", "your week, on one screen"),
  price="$750", title="Dashboards & Internal Tools — from $750 | Leon Builds",
  desc="Live dashboards and focused internal tools that replace manual exports, surface the numbers that matter and remove repetitive copy-paste from daily work.",
  intro=["somebody on your team spends part of every week exporting, pasting and reformatting the same report. and by the time it's read, it's old.",
   "a dashboard pulls those numbers live from the systems that already have them — sales, bookings, stock, ad spend — onto one screen you check in ten seconds.",
   "the same goes for a job somebody repeats forty times a day in six clicks. a focused internal tool can shorten that path, and the scope can define exactly which clicks or minutes to measure before and after."],
  pains=["reports are assembled by hand every week","the numbers live in five different logins","you find out about a bad week after it's over","a repetitive task eats hours across the team","the answer to 'how do we know this number' is 'ask the one person who knows'"],
  build=["live dashboards fed straight from your real systems","the handful of numbers that matter, not eighty charts","alerts when a number crosses a line you set","scheduled email summaries for people who won't open a dashboard","clean history so trends are visible, not remembered","chrome extensions and small tools built for the exact job, nothing else"],
  proof=("ALLCPR Site Intelligence","decision support built from 33,772 U.S. ZIP-code records in the reviewed project dataset, with Maps context, public data, company history, uncertainty ranges, screening verdicts and team exports."),
 faqs=[("what does a dashboard cost?","both a small internal tool and a dashboard start at $750, and scale with how many systems have to feed them. fixed quote before work starts."),
   ("our data is a mess. does that matter?","that's normal — cleaning and joining it is part of the build, not a surcharge surprise."),
   ("can it pull from our pos / quickbooks / sheets?","usually yes. we verify your specific systems before quoting.")],
  review_ids=["testimonial-02"],
  related=["business-automation","ai-chatbots","custom-software"]),

 dict(slug="seo", name="technical seo & ai search", h1=("technical seo for google —", "structured for ai search"),
  price="$450", title="Technical SEO & AI Search (GEO) Optimization | Leon Builds",
  price_note='AI search (GEO) pass from <b>$1,350</b> · ongoing search or AI-visibility work from <b>$450/mo</b> · every scope agreed in writing',
  desc="Technical SEO, Search Console cleanup and GEO-ready structure for Google and AI answers. Measurable changes, no fake locations, ranking promises or mass content.",
  intro=["google search and ai answer systems both need a crawlable site, clear language, useful pages and claims they can verify. there is no separate shortcut that replaces those fundamentals.",
   "we fix the technical and content structure: titles, internal links, indexing, schema, sitemaps, page speed and direct answers to real buyer questions — without fake city pages or mass-produced articles."],
  pains=["google has discovered pages but does not index the ones that matter","the site never says the service in the words customers search","important pages are buried or linked with vague anchor text","nobody measures impressions, clicks, calls or inquiries after a change"],
  build=["search console and index-coverage diagnosis","titles, descriptions, headings, canonicals, sitemaps and crawlable internal links","useful service and industry pages with distinct buyer answers","structured data that matches visible content","clear entity, proof and citation paths for answer systems","a before-and-after check of how chatgpt, perplexity and google's ai answers describe the business","measurement tied to calls, quote requests and bookings"],
  proof=("this site's public search foundation","inspect the clean sitemap, canonical pages, reciprocal language clusters, public proof links and structured data. none of those is presented as a ranking guarantee."),
  faqs=[("how is ai search different from seo?","there is no special markup that guarantees ai visibility. clear, crawlable, useful pages and verifiable claims support both traditional search and answer systems."),
   ("what does it cost?","from $450 for a technical seo pass on an existing site. the ai search (geo) pass starts at $1,350 and includes the answer-engine check described above. ongoing search or ai-visibility work is scoped in writing from $450 a month — no vague retainer. the fixed price is written down before anything starts."),
   ("what does the ai search (geo) pass include?","generative engine optimization means making your business easy for chatgpt, perplexity and google's ai answers to find, understand and cite. the pass records how those systems currently answer real buyer questions about your business and category, fixes the entity, proof and citation paths and the structured data they rely on, adds an llms.txt index, rewrites the key service pages to answer first, and re-runs the same questions after the changes. no citation or ranking guarantee — the work is documented and measured."),
   ("can you guarantee rankings?","no. we can document the changes, validate the technical implementation and measure impressions, clicks and inquiries, but search engines decide rankings."),
   ("do i need an llms.txt file?","it can provide a concise factual index for some systems, but it is not a google ranking control. the main work still belongs in visible pages, normal links and accurate structured data.")],
  related=["websites","ai-chatbots","business-dashboards"]),
]

INDUSTRIES = [
 dict(slug="restaurants", name="restaurants & food", h1=("restaurant web design,", "online ordering & automation"),
  title="Restaurant Website Design & Online Ordering | Leon Builds",
  desc="Phone-first restaurant website design, direct online ordering, menu updates and call automation from one California-based developer serving U.S. businesses.",
  intro=["restaurants run on thin margins while marketplace terms vary and the phone pulls staff away during a rush. a direct website can add a channel you control alongside the platforms that bring discovery.",
   "beastypages.com, a client website, shows the underlying interaction: business-specific menus, server-side pricing and vendor-scoped demo tickets. payments and kitchen operations remain mocked."],
  pains=["delivery apps take a commission on orders that were already yours","the phone rings out during every rush","your menu is a pdf nobody can read on a phone","'are you open' and 'do you have parking' — forty times a day","multiple locations or brands, zero shared systems"],
  fixes=[("online ordering you own","direct ordering with no per-order commission added by us — cart, payment, kitchen ticket. from $600","booking-systems"),
   ("ai phone agent","answers during the rush, takes the routine calls, hands the rest to staff. from $1,000","ai-phone-agents"),
   ("a menu-first website","fast, phone-first, editable by you when prices change. from $300","websites"),
   ("review desk","every review read and a reply drafted for you — a human presses send. from $750",None)],
  proof=("the beastypages.com client website","open the public website to inspect business-specific menus, server-side pricing and vendor-scoped demo tickets. payments and kitchen operations are not live."),
  faqs=[("can i stop paying delivery-app commissions?","you can give regular customers a direct pickup or own-delivery option without us adding a per-order cut. marketplaces can still be useful for discovery, while payment, hosting, messaging and delivery providers keep their own terms."),
   ("what does online ordering cost?","from $600 one-time for ordering on your own site; we charge no per-order cut. payment, hosting and other provider fees still apply. compare that to a month of commissions."),
   ("i have two locations with different menus.","that can be handled with a shared site and separate location menus, hours and order routing. the exact payment and kitchen integrations are verified before quoting.")],
  related_services=["booking-systems","ai-phone-agents","websites"]),

 dict(slug="contractors", name="contractors & home services", h1=("contractor web design &", "lead follow-up"),
  title="Contractor Web Design & Lead Follow-Up | Leon Builds",
  desc="Contractor website design, quote-request capture, lead follow-up and job workflows for U.S. home-service businesses, built by a founder-led studio.",
  intro=["contracting work is won and lost in the follow-up: the lead that came in while you were on a roof, the estimate that never went out, the customer who called someone else because you answered second.",
   "software fixes the boring half of that — instant lead responses, scheduling, job status a customer can check without calling you."],
  pains=["leads arrive while you're on site and go cold","estimates and invoices happen at 9pm from the truck","customers call constantly for status updates","jobs live on a whiteboard or in one person's head","reviews never get asked for, so the profile looks dead"],
  fixes=[("lead follow-up automation","every web lead gets an instant text/email and lands in one list. from $600","business-automation"),
   ("scheduling & job tracking","jobs, crews and dates in one system the whole team sees. from $1,500","custom-software"),
   ("customer portal","clients see their own job status, photos and invoices. from $1,500","custom-software"),
   ("a website that sells","before/after work, service areas, instant quote requests. from $300","websites")],
  proof=("document control","approvals, versioned documents and automatic filing — the same machinery that keeps a contracting back office from living in someone's memory."),
  faqs=[("i'm not technical at all. is that a problem?","no. you describe the week, we build around it, and everything is handed over working with training included."),
   ("where is a practical place to start?","lead follow-up is often a focused first workflow because response timing and handoffs can be measured. compatible standard scopes start at $600; timing depends on the tools and access involved."),
   ("do you work outside california?","yes — remote across the u.s. this kind of build never needs us on site.")],
  related_services=["business-automation","custom-software","websites"]),

 dict(slug="automotive", name="auto repair & automotive", h1=("auto repair web design,", "booking & call automation"),
  title="Auto Repair Website Design & Booking | Leon Builds",
  desc="Auto repair website design, online booking, status updates and call automation for U.S. shops, built directly by one California-based developer.",
  intro=["every shop knows the two calls: 'can i bring it in?' and 'is it ready yet?'. both interrupt the person doing the actual work.",
   "booking can go straight into your calendar. status can text the customer automatically the moment a job changes state — and an ai phone agent can answer the rest."],
  pains=["'is my car ready' calls interrupt the bay all day","booking happens by phone and gets double-entered","customers wait on hold, then show up at the wrong time","your shop software has the data but customers can't see it"],
  fixes=[("automatic status updates","'your car is ready' sends itself when the job closes. from $600","business-automation"),
   ("online booking","customers pick a slot; your calendar stays sane. from $600","booking-systems"),
   ("ai phone agent","handles hours, booking and routine status; transfers the rest. from $1,000","ai-phone-agents"),
   ("shop website","services, trust proof, booking and a clear call path on any phone. from $300","websites")],
  proof=("public implementation evidence","inspect shipped product screens, a public workflow demo and a clearly labelled client website with demo ordering; none is presented as an automotive outcome claim."),
  faqs=[("does this work with my shop management system?","often — many expose the data needed for status and booking. we verify yours specifically before quoting anything."),
   ("what is a focused first step?","status notifications can reduce manual update calls when the shop system exposes reliable status data. we verify that data and define what will be measured before quoting."),
   ("multiple locations?","yes — shared platform, per-location calendars and numbers is a normal build.")],
  related_services=["ai-phone-agents","booking-systems","business-automation"]),

 dict(slug="healthcare", name="medical & dental", h1=("software for", "medical & dental practices"),
  title="Software for Medical & Dental Offices | Leon Builds",
  desc="Online booking, appointment reminders and after-hours question handling for clinics and dental practices. Careful, human-in-the-loop builds.",
  intro=["a practice front desk answers the same questions all day — insurance, hours, directions, 'can i move my appointment' — while missed appointments leave unused time. reminders and self-service rescheduling address one part of that workflow and can be measured against the current baseline.",
   "we focus on administrative work: reminders, booking, and approved logistical information. clinical advice is outside the scope. if an assistant is included, its answers need testing and a clear path to staff; ai can still make mistakes."],
  pains=["no-shows burn schedule and revenue","the phone queue is insurance and reschedule questions","after-hours callers reach voicemail and book elsewhere","forms are still paper or pdf-by-email"],
  fixes=[("appointment reminders","sms/email sequences with timing and opt-out rules; track confirmations, reschedules and missed appointments. from $600","booking-systems"),
   ("online booking & rescheduling","patients handle the routine moves themselves. from $600","booking-systems"),
   ("after-hours question handling","routine questions answered; anything clinical goes to staff. from $1,000","ai-phone-agents"),
   ("digital intake forms","filled on a phone before the visit, filed automatically. from $600","business-automation")],
  proof=("health-education prototype","Leon built a chinese-language health-education prototype with source citations and safety checks that run before the model. it is an example of bounded assistant design, not clinical validation or a guarantee of compliance."),
  faqs=[("is this hipaa compliant?","builds are designed so sensitive data stays in your existing systems wherever possible, and we're direct about what we will and won't touch. compliance requirements get scoped in writing before anything starts — never assumed."),
   ("will ai talk to my patients about medical questions?","the assistant is scoped for routine logistics, not medical advice. we agree on limits and staff handoff, then test them before launch. those controls reduce risk but do not make model answers infallible."),
   ("what does this cost?","reminders and intake from about $600; booking from $600. fixed written quotes.")],
  related_services=["booking-systems","ai-chatbots","business-automation"]),

 dict(slug="real-estate", name="real estate & property", h1=("software for", "real estate & property management"),
  title="Software for Real Estate & Property | Leon Builds",
  desc="Tenant portals, maintenance-request tracking, listing sites and follow-up automation for property managers and real-estate businesses.",
  intro=["property work is coordination: tenants, owners, vendors, showings, maintenance — most of it still happening over scattered calls and texts nobody can find later.",
   "a portal gives tenants somewhere to submit and track requests. automation gives owners their statements without you assembling them. your phone gets quieter."],
  pains=["maintenance requests arrive by call and text, then get lost","tenants call for updates because there's nowhere to look","owner statements are assembled by hand every month","showings and applications live in three inboxes"],
  fixes=[("tenant portal","submit a request, attach a photo, watch the status change. from $1,500","custom-software"),
   ("maintenance tracking","requests routed to vendors, updates sent automatically. from $1,000",None),
   ("owner reporting","statements that build themselves from your real data. from $1,000","business-dashboards"),
   ("listing website","fast property pages with inquiry capture that reaches you instantly. from $300","websites")],
  proof=("Loqol disclosure workflow","a public demo showing per-user saved answers, an agent review workspace, consistency checks and generated documents. signing and email delivery are incomplete."),
  faqs=[("can tenants see each other's information?","no — per-account visibility is enforced on the server, which is the core of the build."),
   ("we use appfolio / buildium / yardi.","keep it if it works — often the right build is a portal or automation talking to your existing system. we verify the integration before quoting."),
   ("what does a tenant portal cost?","from $1,500 depending on what tenants and owners need to see and do.")],
  related_services=["custom-software","business-automation","websites"]),

 dict(slug="logistics", name="logistics & warehousing", h1=("software for", "logistics & warehousing"),
  title="Software for Logistics & Trucking | Leon Builds",
  desc="Dispatch boards, driver apps, document automation and customer tracking for logistics and warehouse operations.",
  intro=["logistics runs on information handoffs — and every handoff that happens by phone, email-forward or retyping is a delay and an error waiting to happen.",
   "dispatchers copying between emails and spreadsheets, drivers texting photos of paperwork, customers calling for eta: each of those is a solved software problem."],
  pains=["dispatch copies the same info between email, sheets and texts","drivers hand in paperwork that gets retyped","customers call for status because they can't see it","inventory counts drift from reality"],
  fixes=[("dispatch board","loads, drivers and statuses on one live screen. from $1,500","custom-software"),
   ("driver app","photos, signatures and status from the cab — no retyping. from $3,500","mobile-apps"),
   ("document automation","pods, bols and invoices extracted and filed automatically. from $500","business-automation"),
   ("customer tracking portal","they look it up instead of calling you. from $1,500","custom-software")],
  proof=("ALLCPR Site Intelligence","a nationwide location-planning platform that turns Maps context, public data and operating history into reviewable market screens instead of a black-box answer."),
  faqs=[("our process is unusual. can software fit it?","unusual processes are the reason custom exists — the build is shaped around your real workflow, not a template's guess."),
   ("what's the first thing to fix?","usually the dispatch copy-paste loop — highest error rate, easiest automation."),
   ("do drivers need new hardware?","no — driver tools run on the phones they already carry.")],
  related_services=["custom-software","business-dashboards","websites"]),

 dict(slug="gyms", name="gyms & fitness", h1=("software for", "gyms & fitness businesses"),
  title="Software for Gyms & Fitness | Leon Builds",
  desc="Class booking, membership management, reminder automation and websites for gyms, studios and trainers.",
  intro=["a gym's software problem is churn wearing a disguise: missed classes, lapsed cards, members who drift because nobody noticed they stopped coming.",
   "booking, reminders and a membership view fix the mechanics — you see who's fading while there's still time to wave them back."],
  pains=["class booking happens by dm and spreadsheet","no-shows leave paid slots empty","failed card payments quietly become lost members","you can't see who's about to churn until they're gone"],
  fixes=[("class booking","members book, waitlist and cancel themselves. from $600","booking-systems"),
   ("membership dashboard","attendance, payments and fade-outs on one screen. from $1,000","business-dashboards"),
   ("reminder automation","class reminders and win-back nudges that send themselves. from $600","business-automation"),
   ("a site that converts","schedule, pricing and signup without a phone call. from $300","websites")],
  proof=("curio","a consumer subscription app on the app store — retention mechanics, streaks and subscriptions are literally what it runs on."),
  faqs=[("we use mindbody / glofox. switch?","only if it's failing you. often the right move is automation around what you have — we'll say which in the free call."),
   ("can members pay online?","yes — stripe subscriptions, class packs and drop-ins, with receipts and failed-payment recovery."),
   ("what does this cost?","booking from $600; most gym builds land between $600 and $3,500.")],
  related_services=["booking-systems","websites","business-dashboards"]),

 dict(slug="retail", name="retail & e-commerce", h1=("software for", "retail & e-commerce"),
  title="Software for Retail & E-commerce | Leon Builds",
  desc="Inventory that survives a busy Saturday, order automation, dashboards and storefronts for retailers and e-commerce operators.",
  intro=["retail dies by a thousand small syncs: the count that drifted, the online order nobody saw, the bestseller that sold out because reordering lived in someone's head.",
   "the fix is rarely a new platform — it's the connective tissue: inventory that matches reality, orders flowing into one queue, numbers you see daily without exporting anything."],
  pains=["stock counts drift from reality","online and in-store systems don't talk","reordering depends on someone noticing","you learn about a bad week from the bank balance"],
  fixes=[("inventory system","stock, suppliers and low-stock alerts that survive a rush. from $1,500","custom-software"),
   ("order automation","every channel's orders into one queue with alerts. from $600","business-automation"),
   ("sales dashboard","today's numbers without opening five systems. from $1,000","business-dashboards"),
   ("storefront","fast product pages, clean checkout, no template bloat. from $300","websites")],
  proof=("the beastypages.com client website","a public client website showing business-specific catalogs, menus, server-side pricing and vendor-scoped demo tickets. payments and fulfillment are not live."),
  faqs=[("we're on shopify / square. is that a problem?","no — keep them. most retail builds connect and automate around the platform you're on."),
   ("can inventory sync between online and the register?","usually yes, depending on your pos. we verify the specific integration before quoting."),
   ("what should we fix first?","whatever loses money silently — usually inventory drift or unwatched online orders.")],
  related_services=["business-automation","business-dashboards","websites"]),

 dict(slug="professional-services", name="professional services", h1=("software for", "professional services"),
  title="Software for Professional Firms | Leon Builds",
  desc="Client portals, intake automation, document workflows and dashboards for law, accounting, consulting and agency work.",
  intro=["service firms sell hours, then spend a shocking share of them on intake, status emails, document wrangling and 'just checking in' calls.",
   "a client portal, automated intake and document workflows give those hours back — and make the firm feel bigger and calmer than the inbox it replaced."],
  pains=["intake is a pdf emailed back and forth","clients email for status because there's nowhere to look","documents have four versions in three inboxes","billable time leaks into administration"],
  fixes=[("client portal","cases, files, invoices and status in one login. from $1,500","custom-software"),
   ("intake automation","forms that fill in on a phone, file and notify automatically. from $600","business-automation"),
   ("document workflows","created, versioned, approved and filed — automatically. from $500","business-automation"),
   ("firm dashboard","matters, pipeline and billing on one screen. from $1,000","business-dashboards")],
  proof=("Loqol guided document workflow","a public demo showing a long questionnaire, saved answers, consistency checks, an agent review view and generated PDF output."),
  faqs=[("is client data safe?","per-client visibility is enforced server-side. the agreed project accounts, included source code and setup notes are handed over, while hosting providers, licensed software and other vendors keep their own terms. your reviewer can audit the included code."),
   ("we bill hourly. does this change that?","it removes the hours you can't bill — admin — and keeps the ones you can."),
   ("what does a portal cost?","from $1,500; intake automation from $600. written fixed quotes.")],
  related_services=["custom-software","business-automation","business-dashboards"]),

 dict(slug="startups", name="startups", h1=("software for", "startups & founders"),
  title="MVP & Product Development for Startups | Leon Builds",
  desc="MVPs that actually ship: app, backend and payments from a founder-led studio with a live product through App Store review.",
  intro=["a founder with an idea needs the version of the product that can meet users — not a six-month engagement, not a no-code demo that collapses at the first real feature.",
   "Leon shipped a consumer app end to end: design, code, backend, subscriptions, app store review, and the appeal when review got it wrong. that full path is what an mvp needs; the agreed repo, included source and setup notes are part of the written handoff, while third-party and licensed terms remain."],
  pains=["you have the idea and the users, not the technical team","agency quotes start at six figures","the no-code prototype hit its ceiling","your technical co-founder search is month six"],
  fixes=[("mvp build","the smallest version that real users can use — app or web. from $3,500","custom-software"),
   ("app + backend + payments","the whole stack, not just screens. from $3,500","mobile-apps"),
   ("ai features","assistants, retrieval and pipelines with tested limits and human handoff. from $1,000","ai-chatbots"),
   ("ongoing development","a standing block of hours as you see fit. from $400/mo",None)],
  proof=("curio","consumer ios app on the app store: react/typescript, capacitor, express, postgres, storekit subscriptions, ai content in four languages — built alone."),
  faqs=[("how fast can an mvp ship?","weeks, not quarters — scope decides. we cut to the version that tests the idea, in writing, before building."),
   ("do i own the code?","the agreed repo and project accounts, plus the source code and setup notes included in scope, are handed over. third-party infrastructure, app stores, libraries and other licensed services keep their own terms. investors can review the written handoff."),
   ("can you keep building after launch?","yes — ongoing from $400/mo, or fixed quotes per milestone as you raise.")],
  related_services=["mobile-apps","custom-software","ai-chatbots"]),
]

# ══════════════════════════════════════════════════════════════════
# TEMPLATE
# ══════════════════════════════════════════════════════════════════

FONTS = ''  # The shared design layer reuses the homepage's self-hosted fonts.

def e(s): return html.escape(str(s), quote=True)


def testimonial_card(testimonial_id, classes="testimonial-card", link_project=True):
    """Render one exact, individually released testimonial or nothing."""
    item = RELEASED_TESTIMONIALS.get(testimonial_id)
    if not item:
        return ''
    stars = ''
    if item["show_rating"]:
        stars = '<p class="testimonial-stars" aria-label="5 out of 5 stars">★★★★★</p>'
    project = e(TESTIMONIAL_PROJECT_LABELS.get(testimonial_id, item["project"]))
    project_href = TESTIMONIAL_PROJECT_LINKS.get(testimonial_id) if link_project else None
    if project_href:
        project = (
            f'<a href="{e(project_href)}" data-evt="testimonial_project_click">'
            f'{project}</a>'
        )
    project_note = TESTIMONIAL_PROJECT_NOTES.get(testimonial_id)
    note = f'<p class="testimonial-project-note">{e(project_note)}</p>' if project_note else ''
    return (
        f'<article class="{e(classes)}" data-testimonial-id="{e(testimonial_id)}">'
        f'{stars}<p class="testimonial-project">{project}</p>'
        f'{note}'
        f'<blockquote>“{e(item["quote"])}”</blockquote>'
        f'<p class="testimonial-person"><strong>{e(item["attribution"])}</strong>'
        f'<span>{e(item["attribution_context"])}</span></p></article>'
    )


def testimonial_cards(testimonial_ids, classes="testimonial-card"):
    return ''.join(testimonial_card(testimonial_id, classes) for testimonial_id in testimonial_ids)


def released_testimonial_ids():
    """Return released records in buyer-relevant order, never private drafts."""
    ordered = [
        testimonial_id for testimonial_id in TESTIMONIAL_DISPLAY_ORDER
        if testimonial_id in RELEASED_TESTIMONIALS
    ]
    return ordered + [
        testimonial_id for testimonial_id in RELEASED_TESTIMONIALS
        if testimonial_id not in ordered
    ]


def homepage_testimonial_section():
    """Generate the homepage section only from the explicit release manifest."""
    released_ids = released_testimonial_ids()
    if not released_ids:
        return ''
    first = testimonial_cards(released_ids[:HOMEPAGE_TESTIMONIAL_LIMIT])
    more = ('<a class="cx-mini" href="/reviews">All reviews →</a>'
            if REVIEWS_ROUTE_ENABLED else '')
    count = len(released_ids)
    noun = "review" if count == 1 else "reviews"
    return f'''<section class="sec reviews-early" id="testimonials">
  <div class="rail">
    <header class="sec-head reviews-head">
      <div><p class="label">{count} direct client {noun}</p>
        <h2 class="dsp">Feedback on real <em>business projects.</em></h2></div>
      <p class="sub business-copy">Client-approved project feedback.</p>
    </header>
    <div class="testimonial-grid">{first}</div>
{more}
  </div>
</section>'''

def nav():
    return f'''<a class="skip" href="#main">Skip to content</a>
<div class="progress" id="progress" aria-hidden="true"></div>
<header class="nav" id="nav">
  <a class="mark" href="/">
    <span class="mark-dot" aria-hidden="true">lb</span>
    <span class="mark-name">Leon Builds</span>
    <span class="mark-handle">by Leon Kelvin Li</span>
  </a>
  <nav class="nav-mid" id="navMid" aria-label="site">
    <a href="/#services"><i>[</i><span>Services</span><i>]</i></a>
    <a href="/work"><i>[</i><span>Work</span><i>]</i></a>
    <a href="/about"><i>[</i><span>About</span><i>]</i></a>
    <a class="nav-book" href="/#start"><i>[</i><span>Start</span><i>]</i></a>
  </nav>
  <div class="nav-end">
    <a class="btn btn-solid magnet" href="/quote" data-evt="nav_quote_click"><span>Get a fixed quote</span></a>
    <button class="burger" id="burger" aria-expanded="false" aria-controls="navMid" aria-label="Open menu"><span></span><span></span></button>
  </div>
</header>'''

def footer():
    reviews_href = '/reviews' if REVIEWS_ROUTE_ENABLED else '/#testimonials'
    reviews_link = (f'<a href="{reviews_href}">approved client feedback</a>'
                    if REVIEWS_PUBLISHED else '')
    return f'''<footer class="foot">
  <div class="rail footer-topline">
    <a class="mark" href="/"><span class="mark-name">Leon Builds</span></a>
    <a href="mailto:leondragon3798@gmail.com" data-evt="footer_email_click">leondragon3798@gmail.com ↗</a>
    <a href="tel:+15108267735" data-evt="footer_phone_click">(510) 826-7735</a>
  </div>
  <details class="rail footer-directory">
    <summary>Explore services, guides &amp; work</summary>
  <div class="foot-in">
    <div class="foot-brand">
      <a class="mark" href="/"><span class="mark-dot" aria-hidden="true">lb</span><span class="mark-name">Leon Builds</span><span class="mark-handle">by Leon Kelvin Li</span></a>
      <p>small-business websites, lead follow-up and workflow automation, built directly by one california-based developer.</p>
      <p class="avail"><i></i>available for new projects</p>
    </div>
    <nav><h4>services</h4><a href="/missed-lead-recovery">website + lead follow-up</a><a href="/services/websites">business websites</a><a href="/services/business-automation">workflow automation</a><a href="/services/">all services and prices</a></nav>
    <nav><h4>explore</h4><a href="/work">work and case studies</a>{reviews_link}<a href="/guides/contractor-inquiry-workflow">contractor inquiry guide</a><a href="/about">about leon</a><a href="/industries/">browse industries</a></nav>
    <nav><h4>contact &amp; language</h4><a href="/quote">get a fixed quote</a><a href="/call">book a 15-minute call</a><a href="/es">español</a><a href="/pt">português</a><a href="/zh">中文</a><a href="/privacy">privacy</a></nav>
  </div>
  </details>
  <div class="rail foot-bar">
    <p>© <span id="yr">2026</span> <span class="keepcase">Leon Kelvin Li</span> · california · working with businesses across the u.s.</p>
    <p><a href="/es">Español</a> · <a href="/pt">Português</a> · <a href="/zh">中文</a> · <a href="/privacy">Privacy</a></p>
  </div>
</footer>
<script src="/app.js" defer></script>
<script src="/assist.js" defer></script>'''

def head(title, desc, path, schema, alts='', head_extra='', social_image='/assets/og.png', social_alt='Leon Builds — websites, apps and business systems'):
    """alts carries the hreflang cluster. Hreflang only works when it is
    RECIPROCAL — a Portuguese page pointing at its English twin while the twin
    stays silent is a cluster Google discards, so the English service pages that
    have translations must name them back. head_extra is reserved for page-only
    identity metadata so it does not leak into the generated page fleet."""
    head_links = "\n".join(link for link in (alts, head_extra) if link)
    social_url = social_image if social_image.startswith('http') else BASE + social_image
    social_dimensions = ('''<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">''' if social_image == '/assets/og-mobile-apps.png' else '')
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#f6f5f1">
<meta name="color-scheme" content="light">
<link rel="canonical" href="{BASE}{path}">
{head_links}
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:site_name" content="Leon Builds">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{social_url}">
<meta property="og:image:alt" content="{e(social_alt)}">
{social_dimensions}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{social_url}">
<meta name="twitter:image:alt" content="{e(social_alt)}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{FONTS}
<link rel="stylesheet" href="/styles.css">
<link rel="stylesheet" href="/assist.css">
<link rel="stylesheet" href="/site-design.css">
<script src="/site-motion.js" defer></script>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body>'''

def crumbs(items):
    parts = ' <i>/</i> '.join(f'<a href="{h}">{e(t)}</a>' if h else f'<span>{e(t)}</span>' for t, h in items)
    return f'<p class="crumbs">{parts}</p>'

def breadcrumb_schema(items, path):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i+1,"name":t,"item":BASE+(h or path)} for i,(t,h) in enumerate(items)]}

def faq_schema(faqs):
    return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]}

def faq_html(faqs):
    out = '<div class="faq">'
    for q,a in faqs:
        out += f'<details><summary>{e(q)}<i></i></summary><p>{e(a)}</p></details>'
    return out + '</div>'

def cta_block(starter, quote_first=False):
    primary = (f'<a class="btn btn-solid magnet" href="/quote" data-evt="pricing_cta_click"><span>get a fixed quote</span><svg class="ic"><use href="#ic-arrow"/></svg></a>'
               if quote_first else
               f'<a class="btn btn-solid magnet" href="/call" data-evt="cta_call_click"><span>book a free 15-minute call</span><svg class="ic"><use href="#ic-arrow"/></svg></a>')
    secondary = (f'<a class="btn magnet" href="/call" data-evt="cta_call_click"><span>book a free 15-minute call</span></a>'
                 if quote_first else
                 f'<a class="btn magnet" href="/quote" data-evt="pricing_cta_click"><span>get a fixed quote</span></a>')
    if quote_first:
        return f'''<div class="ctarow">
      {primary}
      {secondary}
    </div>'''
    return f'''<div class="ctarow">
      {primary}
      {secondary}
      <a class="cx-mini" href="mailto:leondragon3798@gmail.com" data-evt="email_click">or email us directly →</a>
    </div>
    <p class="assist-fallback">Not ready to talk? <button class="linklike" type="button" data-assist-open data-assist-starter="{e(starter)}">Describe the problem to the site assistant.</button></p>'''

ICONS = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="ic-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 6l6 6-6 6"/></symbol><symbol id="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 12.5l5 5 10-11"/></symbol></svg>'


# Proof links must land on visible, current public evidence. Unreleased client
# feedback is never a proof destination.
WORK_ROUTES = [
    ('allcpr site intelligence', '/work/allcpr-site-intelligence'),
    ('site intelligence', '/work/allcpr-site-intelligence'),
    ('location', '/work/allcpr-site-intelligence'),
    ('beastypages.com', '/work/beastypages-website'),
    ('home screen', '/work/beastypages-website'),
    ('ordering', '/work/beastypages-website'),
    ('operator prototype', '/work/beastypages-website'),
    ('curio', '/work/curio-app'),
    ('loqol', '/work#work-loqol'),
]

def work_link(proof_title):
    t = (proof_title or '').lower()
    for needle, route in WORK_ROUTES:
        if needle in t:
            return route
    return '/work'

def service_page(s):
    path = f'/services/{s["slug"]}'
    bc = [("home","/"),("services","/services/"),(s["name"], None)]
    offer_price = s["price"].replace('$', '').replace(',', '')
    service_name = "iOS and Android app development" if s["slug"] == "mobile-apps" else s["name"]
    page_id = BASE + path + "#webpage"
    service_schema = {
         "@context":"https://schema.org","@type":"Service","@id":BASE+path+"#service",
         "name":service_name, "url":BASE+path, "serviceType":service_name,
         "mainEntityOfPage":{"@id":page_id},
         "provider":{"@id":BASE+"/#leon"},
         "areaServed":{"@type":"Country","name":"United States"},
         "description":s["desc"],
         "offers":{"@type":"Offer","url":BASE+path,"price":offer_price,"priceCurrency":"USD",
                   "description":"Published starting price; final fixed quote depends on the written scope."}}
    if s["slug"] == "mobile-apps":
        service_schema["audience"] = {"@type":"BusinessAudience", "audienceType":"Founders and small businesses"}
    schema = [
        {"@context":"https://schema.org","@type":"WebPage","@id":page_id,
         "url":BASE+path,"name":s["title"],"description":s["desc"],
         "isPartOf":{"@id":BASE+"/#website"},"mainEntity":{"@id":BASE+path+"#service"}},
        service_schema,
        faq_schema(s["faqs"]), breadcrumb_schema(bc, path)]
    pains = ''.join(f'<li>{e(p)}</li>' for p in s["pains"])
    build = ''.join(f'<li><svg class="ic"><use href="#ic-check"/></svg>{e(b)}</li>' for b in s["build"])
    intro = ''.join(f'<p class="sub">{e(p)}</p>' for p in s["intro"])
    starter_website = ''
    starter_note = ''
    price_note = f'<p class="sub pricetag-note">{s["price_note"]}</p>\n    ' if s.get("price_note") else ''
    if s["slug"] == "websites":
        starter_note = '<p class="sub">Only need one page? The <a href="#starter">$199 starter</a> includes supplied content, up to four sections, one contact or booking link and one revision. Larger website scopes start at $300.</p>\n    '
        starter_website = '''<section class="sec" id="starter"><div class="rail">
  <p class="label">A smaller starting point</p><h2 class="page-section-title">One-page starter website · $199</h2>
  <p class="sub">One responsive page with up to four sections, your supplied copy and images, one contact or booking link, and one revision. Target delivery is five days after the scope, content, access and start date are agreed.</p>
  <p class="sub">Extra pages, new writing, backend forms, checkout, accounts and integrations are separate. Hosting and domains are not included. The larger business-website scope above starts at $300; this is the same focused $199 starter offered on Upwork.</p>
  <a class="btn btn-solid" href="/quote?service=websites" data-evt="starter_website_quote_click"><span>Ask about the one-page starter</span></a>
</div></section>\n'''
    partner_related = (
        '<a class="rel" href="/technical-build-partner">website, app &amp; automation help →</a>'
        if s["slug"] in {"websites", "business-automation", "business-dashboards", "custom-software", "mobile-apps"}
        else ''
    )
    related = partner_related + ''.join(f'<a class="rel" href="/services/{r}">{e(next(x["name"] for x in SERVICES if x["slug"]==r))} →</a>' for r in s["related"])
    decision_guide = related_html(path)
    decision_guide = '\n    ' + decision_guide if decision_guide else ''
    starter = f'i\'m looking at {s["name"]} — here\'s my situation: '
    quote_first = s["slug"] == "mobile-apps"
    service_label = "Custom iOS and Android app development" if quote_first else f'leon builds --services {s["slug"]}'
    pains_heading = "Is this the app problem you have?" if quote_first else "Does this sound familiar?"
    build_heading = "What the first release can include" if quote_first else "What we build for this"
    proof_label = "Public product proof" if quote_first else "proof, not promises"
    proof_heading = "A live app you can verify" if quote_first else "Evidence related to this service"
    faq_label = "Before scoping an app" if quote_first else "questions people ask first"
    faq_heading = "App development questions" if quote_first else "Questions before starting"
    proof_visual = ('''<figure class="service-proof-media">
        <img src="/assets/proof/curio-appstore-current.png" alt="Current screens from Leon's live App Store product" loading="lazy" width="1559" height="510">
      </figure>''' if quote_first else '')
    reviews = ''
    cards = testimonial_cards(s.get("review_ids", []), "service-review")
    if cards:
        reviews_href = "/reviews" if REVIEWS_ROUTE_ENABLED else "/#testimonials"
        review_heading = ("What website clients said after the build"
                          if s["slug"] == "websites"
                          else "What clients said about related work")
        reviews = f'''<section class="sec service-reviews">
  <div class="rail">
    <p class="label">direct client feedback</p>
    <h2 class="page-section-title">{e(review_heading)}</h2>
    <div class="service-review-grid">{cards}</div>
    <a class="cx-mini" href="{reviews_href}">read approved client feedback →</a>
  </div>
</section>
'''
    web_guide = ''
    if s.get("web_guide"):
        web_guide = '''<section class="sec web-guide">
  <div class="rail">
    <p class="label">small-business website decision guide</p>
    <h2 class="page-section-title">What your website must answer in five seconds</h2>
    <p class="sub">A visitor should not have to hunt for the basics. The first screen needs to make these decisions easy.</p>
    <div class="answer-grid">
      <article><span>01</span><h3>What do you do?</h3><p>Name the service in the words customers search and use.</p></article>
      <article><span>02</span><h3>Who is it for?</h3><p>Make the customer, service area, or situation unmistakable.</p></article>
      <article><span>03</span><h3>Why trust you?</h3><p>Show real work, direct feedback, credentials, or a verifiable result.</p></article>
      <article><span>04</span><h3>What happens next?</h3><p>Give one obvious action: call, book, order, or request a quote.</p></article>
    </div>
  </div>
</section>
<section class="sec web-scope-guide">
  <div class="rail">
    <p class="label">choose the smallest useful scope</p>
    <h2 class="page-section-title">Website cost depends on what the site must do</h2>
    <div class="scope-grid">
      <article><span>01</span><h3>Frontend presence site</h3><p>A fast, responsive site with your offer, proof, contact path and handover. Starts at $300.</p></article>
      <article><span>02</span><h3>One backend integration</h3><p>A small, defined form, data or API integration starts at $625. Accounts, admin areas and complete custom applications need a separate scope and quote.</p></article>
      <article><span>03</span><h3>One booking or ordering flow</h3><p>A focused setup using an agreed existing platform starts at $600. Custom calendars, marketplaces and multiple payment flows are quoted separately.</p></article>
    </div>
    <p class="sub web-scope-note">If an existing website only needs one repair, we'll say so. If a standard platform is the better fit, we'll recommend that instead of custom code.</p>
    <p class="label web-industry-label">web design by business type</p>
    <div class="relrow"><a class="rel" href="/industries/contractors">contractor web design →</a><a class="rel" href="/industries/automotive">auto repair web design →</a><a class="rel" href="/industries/restaurants">restaurant web design →</a><a class="rel" href="/industries/gyms">gym web design →</a><a class="rel" href="/industries/professional-services">professional-firm websites →</a></div>
  </div>
</section>
'''
    social_image = '/assets/og-mobile-apps.png' if quote_first else '/assets/og.png'
    social_alt = ('Custom iOS and Android app development for businesses, with live product screens'
                  if quote_first else 'Leon Builds — websites, apps and business systems')
    page_head = head(s["title"], s["desc"], path, schema, EN_ALTS.get(s["slug"], ""),
                     social_image=social_image, social_alt=social_alt)
    if quote_first:
        page_head = page_head.replace('<body>', '<body class="app-service" data-assistant-launcher="hidden">', 1)
    return page_head + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">{e(service_label)}</p>
    <h1 class="dsp" >{e(s["h1"][0])} <em>{e(s["h1"][1])}</em></h1>
    {service_visual(s['slug'])}
    <p class="pricetag">From <b>{s["price"]}</b> · final scope and price agreed in writing</p>
    {price_note}{starter_note}{cta_block(starter, quote_first=quote_first or s["slug"] in {"websites", "business-automation"})}
  </div>
</section>
<details class="rail visual-details"><summary>Scope, examples &amp; what is included</summary><div class="visual-details-content">
{intro}{web_guide}<section class="sec">
  <div class="rail two-col">
    <div>
      <h2 class="page-section-title">{e(pains_heading)}</h2>
      <ul class="plist">{pains}</ul>
    </div>
    <div>
      <h2 class="page-section-title">{e(build_heading)}</h2>
      <ul class="blist">{build}</ul>
    </div>
  </div>
</section>
</div></details>
{reviews}{starter_website}<section class="sec">
  <div class="rail">
    <p class="label">{e(proof_label)}</p>
    <h2 class="page-section-title">{e(proof_heading)}</h2>
    <div class="proofcard">{proof_visual}
      <h3>{e(s["proof"][0])}</h3>
      <p class="sub">{e(s["proof"][1])}</p>
      <a class="cx-mini" href="{work_link(s["proof"][0])}">open the related proof →</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">{e(faq_label)}</p>
    <h2 class="page-section-title">{e(faq_heading)}</h2>
    {faq_html(s["faqs"])}{decision_guide}
    <p class="label" style="margin-top:3rem">related</p>
    <div class="relrow">{related}</div>
    {cta_block(starter, quote_first=quote_first or s["slug"] in {"websites", "business-automation"})}
  </div>
</section>
</main>''' + footer() + '</body></html>'


INDUSTRY_WEB_DESIGN = {
    "restaurants": {
        "heading": "What a restaurant website needs to turn searches into orders",
        "intro": "A restaurant visitor is usually deciding on a phone, quickly. The site should remove friction between the search result and the order or reservation.",
        "bullets": [
            "a readable menu with current prices, hours and location details",
            "one obvious action for ordering, reserving or calling",
            "fast pages that do not make the customer pinch and zoom",
            "separate menus and hours when locations differ",
        ],
    },
    "contractors": {
        "heading": "What a contractor website needs to turn visits into estimate requests",
        "intro": "The buyer wants to know what work you do, whether you serve their area and whether you look trustworthy before they give you a phone number.",
        "bullets": [
            "service and service-area pages written in the customer's language",
            "real project proof, licenses or credentials where applicable",
            "a short estimate request that works from the job site or driveway",
            "an immediate response and a human follow-up path",
        ],
        "review_id": "testimonial-03",
    },
    "automotive": {
        "heading": "What an auto repair website needs to turn visits into appointments",
        "intro": "A shop website should make services, trust, hours and the next available action clear before the customer calls the next result.",
        "bullets": [
            "services and vehicle types explained without shop-software jargon",
            "one-tap calling and a booking or service-request path",
            "review and project proof near the decision point",
            "clear expectations for estimates, drop-off and status updates",
        ],
        "review_id": "testimonial-04",
    },
}


def industry_page(i):
    path = f'/industries/{i["slug"]}'
    bc = [("home","/"),("industries","/industries/"),(i["name"], None)]
    schema = [
        {"@context":"https://schema.org","@type":"Service","@id":BASE+path+"#service",
         "name":f'software for {i["name"]}', "url":BASE+path,
         "mainEntityOfPage":BASE+path,
         "provider":{"@id":BASE+"/#leon"},
         "areaServed":{"@type":"Country","name":"United States"},
         "description":i["desc"]},
        faq_schema(i["faqs"]), breadcrumb_schema(bc, path)]
    pains = ''.join(f'<li>{e(p)}</li>' for p in i["pains"])
    # THE 40 DEAD ENDS (fixed 2026-08-21). These cards are the highest-intent
    # element on an industry page — a restaurant owner reads "online ordering you
    # own — from $600" and decides right there — and every one of them was an
    # <article> with nowhere to click. Three of the four cards on a page now carry
    # the reader to the priced service page; the rest stay inert on purpose,
    # because a card promising less than the page it opens is worse than a card
    # that opens nothing. check_prices.py enforces that direction.
    fixes = ''.join(
        (f'<a class="fixcard link" href="/services/{sl}" data-evt="fixcard_{sl}">'
         f'<h3>{e(t)}</h3><p>{e(d)}</p><span class="go">see how →</span></a>'
         if sl else
         f'<article class="fixcard"><h3>{e(t)}</h3><p>{e(d)}</p></article>')
        for t, d, sl in i["fixes"])
    intro = ''.join(f'<p class="sub">{e(p)}</p>' for p in i["intro"])
    related = ''.join(f'<a class="rel" href="/services/{r}">{e(next(x["name"] for x in SERVICES if x["slug"]==r))} →</a>' for r in i["related_services"])
    starter = f'i run a business in {i["name"]} — here\'s what i\'m dealing with: '
    web_focus = ''
    if i["slug"] in INDUSTRY_WEB_DESIGN:
        focus = INDUSTRY_WEB_DESIGN[i["slug"]]
        bullets = ''.join(f'<li><svg class="ic"><use href="#ic-check"/></svg>{e(item)}</li>' for item in focus["bullets"])
        review = testimonial_card(focus.get("review_id", ""), "service-review industry-review")
        web_focus = f'''<section class="sec industry-web-focus">
  <div class="rail industry-web-grid">
    <div><p class="label">web design for {e(i["name"])}</p><h2 class="page-section-title">{e(focus["heading"])}</h2>
      <p class="sub">{e(focus["intro"])}</p><ul class="blist">{bullets}</ul>
      <a class="cx-mini" href="/services/websites">see small-business website scope and pricing →</a></div>
{review}
  </div>
</section>
'''
    sprint_copy = {
        "contractors": ("estimate requests that arrive while the owner is on a job",
                        "see the contractor website + follow-up scope"),
    }.get(i["slug"])
    sprint_bridge = ''
    if sprint_copy:
        sprint_bridge = f'''<section class="sec">
  <div class="rail">
    <p class="label">one focused starting point</p>
    <div class="proofcard">
      <h2>contractor lead recovery system</h2>
      <p class="sub">a fixed-scope product for {e(sprint_copy[0])}: a focused contractor website, estimate intake, prompt acknowledgment, short follow-up sequence and documented human handoff. Timing is confirmed after scope and access are checked.</p>
      <a class="cx-mini" href="/missed-lead-recovery" data-evt="lead_sprint_detail_click">{e(sprint_copy[1])} →</a>
      <a class="cx-mini" href="/guides/contractor-inquiry-workflow" data-evt="contractor_guide_click">audit your current inquiry path →</a>
    </div>
  </div>
</section>
'''
    return head(i["title"], i["desc"], path, schema) + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">For {e(i["name"])}</p>
    <h1 class="dsp">{e(i["h1"][0])} <em>{e(i["h1"][1])}</em></h1>
    {industry_visual(i['slug'])}
    {cta_block(starter)}
  </div>
</section>
<details class="rail visual-details"><summary>Scope &amp; examples for {e(i["name"])}</summary><div class="visual-details-content">
{intro}{web_focus}{sprint_bridge}<section class="sec">
  <div class="rail">
    <p class="label">the usual pain</p>
    <h2 class="page-section-title">Problems we hear from {e(i["name"])} owners</h2>
    <ul class="plist wide">{pains}</ul>
  </div>
</section>
</div></details>
<section class="sec">
  <div class="rail">
    <p class="label">what actually fixes it</p>
    <h2 class="page-section-title">Practical starting points</h2>
    <div class="fixrow">{fixes}</div>
    <p class="sub" style="margin-top:1.4rem">every price is a published starting point, not a quote — the real number is agreed in writing before anything starts.</p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">proof, not promises</p>
    <h2 class="page-section-title">Evidence related to this work</h2>
    <div class="proofcard">
      <h2>{e(i["proof"][0])}</h2>
      <p class="sub">{e(i["proof"][1])}</p>
      <a class="cx-mini" href="{work_link(i["proof"][0])}">open the related proof →</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <p class="label">questions people ask first</p>
    <h2 class="page-section-title">Questions from {e(i["name"])} owners</h2>
    {faq_html(i["faqs"])}
    <p class="label" style="margin-top:3rem">related services</p>
    <div class="relrow">{related}</div>
    {cta_block(starter)}
  </div>
</section>
</main>''' + footer() + '</body></html>'


CASE_STUDIES = [
    dict(
        slug="allcpr-site-intelligence",
        name="ALLCPR Site Intelligence",
        status="Operational client system · ALLCPR",
        title="ALLCPR Site Intelligence Case Study | Leon Builds",
        desc=("How Leon built an operational location-planning system from 33,772 reviewed U.S. ZIP-code "
              "records while keeping uncertainty and field checks visible."),
        lede=("ALLCPR needed a consistent way to compare expansion markets without reducing a real location "
              "decision to one unexplained score. Leon built the internal system the team uses to screen and "
              "review those markets."),
        image="/assets/proof/site-intelligence-map.png",
        image_alt="ALLCPR Site Intelligence nationwide opportunity map",
        image_width=1200,
        image_height=480,
        role="Data product and full-stack developer",
        project_type="Client project",
        decision_heading="Compare expansion markets without hiding uncertainty.",
        problem=("Opening a training location depends on more than population. ALLCPR needed one reviewable "
                 "place to compare local demand signals, its own operating history, nearby businesses and "
                 "facilities, and the practical reasons to investigate or reject an area."),
        built=[
            ("Reviewed nationwide dataset", "The reviewed project dataset contained 33,772 U.S. ZIP-code records, with selected public business and facility data, local map context, and ALLCPR's own history brought into one workflow."),
            ("Reasons, ranges, and maps", "Each area exposes the reasons for and against it, uncertainty ranges, map context, and an Excel export the team can review outside the product."),
            ("A reliability correction", "Leon found and removed a misleading validation loop. The current system keeps uncertainty visible instead of presenting false confidence as a fact."),
        ],
        evidence=[
            "The screenshot on this page shows the system's nationwide map interface.",
            "ALLCPR approved the exact client statement published below for this project.",
            "The system is operational for the client; it is an internal tool, so there is no public login offered as proof.",
        ],
        boundary=("The system prioritizes markets for investigation. Rent, parking, classroom fit, instructor "
                  "coverage, and current local conditions still require human field validation. This case does "
                  "not claim that every recommendation became a branch or produced leads or revenue."),
        testimonial_id="testimonial-02",
        proof_links=[],
        service_href="/services/custom-software",
        service_label="See custom software scope and pricing",
    ),
    dict(
        slug="curio-app",
        name="Curio",
        status="Live product · App Store",
        title="Curio iPhone App Case Study | Leon Builds",
        desc=("A public case study of Curio: the iPhone client, backend, subscriptions, content pipeline, "
              "and four-language in-app content experience Leon built end to end."),
        lede=("Curio turns short-form scrolling into source-backed learning. Leon took the product from "
              "interface and system decisions through a release that anyone can inspect on the U.S. App Store."),
        image="/assets/proof/curio-appstore-current.png",
        image_alt="Curio live listing on the U.S. App Store",
        image_width=1200,
        image_height=630,
        role="Solo product developer",
        project_type="Founder-built product",
        decision_heading="Release one connected app, backend, subscription, and content system.",
        problem=("The product needed to deliver short learning experiences without treating the mobile feed as "
                 "an isolated set of screens. Accounts, content delivery, subscriptions, localization, and the "
                 "App Store release all had to work as one product."),
        built=[
            ("Mobile product", "A React and TypeScript client with a native iOS shell and the product states needed for discovery and learning."),
            ("Backend and subscriptions", "An Express and Postgres backend plus the subscription flow behind the public iPhone release."),
            ("Content and localization", "The content pipeline and a four-language in-app content experience carried through the released app."),
        ],
        evidence=[
            "The U.S. App Store listing is public and downloadable.",
            "The page image records the public App Store listing rather than a design mockup.",
            "Curio's public team profile identifies Leon and his role in the product.",
        ],
        boundary=("This case establishes that the product was built and released with the listed technical "
                  "scope. It does not make claims about revenue, user growth, retention, or a client outcome."),
        testimonial_id="",
        proof_links=[
            ("Open Curio on the App Store", "https://apps.apple.com/app/apple-store/id6781121127?pt=129044256&ct=leonbuilds-case-study&mt=8", "case_curio_app_store_click", True),
            ("View Leon's public Curio profile", "https://trycurio.app/team.html#leon", "case_curio_profile_click", True),
        ],
        service_href="/services/mobile-apps",
        service_label="See mobile app development scope and pricing",
    ),
    dict(
        slug="beastypages-website",
        name="beastypages.com",
        status="Client website project · demo checkout",
        title="beastypages.com Website Case Study | Leon Builds",
        desc=("How Leon built a phone-first catalog with 37 businesses in a September 4, 2026 review snapshot, "
              "plus search, menus, and clearly labeled demo ordering."),
        lede=("A client needed one phone-first website for browsing local-business pages and menus in a "
              "consistent interface. Leon built the public site and the supporting demonstration flow while "
              "keeping the unfinished commerce boundary explicit."),
        image="/assets/proof/home-screen-catalog.png",
        image_alt="beastypages.com catalog of local-business destinations",
        image_width=380,
        image_height=844,
        secondary_image="/assets/proof/home-screen-menu.png",
        secondary_image_alt="beastypages.com business-specific menu and demonstration cart",
        role="Website and full-stack developer",
        project_type="Client website project",
        decision_heading="Make many business pages feel like one phone-first website.",
        problem=("The website had to organize many distinct businesses without making a phone visitor relearn "
                 "the interface on every page. Search, business details, menus, and the cart demonstration had "
                 "to remain understandable in one compact experience."),
        built=[
            ("Catalog snapshot: 37 businesses", "The September 4, 2026 review snapshot contained 37 businesses. Search and consistent business-specific pages give phone visitors one place to browse the catalog."),
            ("Business menus", "Each business can present its own menu or offering inside the shared site structure."),
            ("Demonstration order logic", "A prototype cart uses server-side repricing and vendor-separated demo tickets instead of trusting totals from the browser."),
        ],
        evidence=[
            "A public business page can be opened from this case study.",
            "The two published screenshots show the catalog and menu interfaces on a phone-sized layout.",
            "The website client approved the exact project statement published below.",
        ],
        boundary=("Payment and kitchen progression are simulations. The public evidence supports the website "
                  "build and the labelled demonstration flow; it does not establish a production ordering "
                  "rollout, completed transactions, sales, or lead performance."),
        testimonial_id="testimonial-03",
        proof_links=[
            ("Open a live business page", "https://beastypages.com/?b=b_bulapies", "case_beastypages_live_click", True),
        ],
        service_href="/services/websites",
        service_label="See small-business website scope and pricing",
    ),
]

CASE_STUDIES.append(seo_json("loqol-seller-portal.json"))
CASE_STUDY_BY_SLUG = {case["slug"]: case for case in CASE_STUDIES}


def case_study_page(case):
    path = f'/work/{case["slug"]}'
    bc = [("home", "/"), ("work and case studies", "/work"), (case["name"], None)]
    article_id = f'{BASE}{path}#case-study'
    person_ref = {"@type": "Person", "@id": f"{BASE}/#leon", "name": "Leon Kelvin Li", "url": f"{BASE}/about"}
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{BASE}{path}#page",
            "url": f"{BASE}{path}",
            "name": case["title"].split(" | ", 1)[0],
            "description": case["desc"],
            "isPartOf": {"@id": f"{BASE}/#website"},
            "mainEntity": {"@id": article_id},
            "dateModified": case.get("reviewed_date", "2026-09-04"),
        },
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "@id": article_id,
            "headline": case["title"].split(" | ", 1)[0],
            "description": case["desc"],
            "image": f'{BASE}{case["image"]}',
            "author": person_ref,
            "publisher": {"@id": f"{BASE}/#business"},
            "mainEntityOfPage": {"@id": f"{BASE}{path}#page"},
            "dateModified": case.get("reviewed_date", "2026-09-04"),
        },
        breadcrumb_schema(bc, path),
    ]
    build_cards = ''.join(
        f'<article><span>{number:02d}</span><h3>{e(title)}</h3><p>{e(copy)}</p></article>'
        for number, (title, copy) in enumerate(case["built"], 1)
    )
    evidence_items = ''.join(
        f'<li><svg class="ic"><use href="#ic-check"/></svg>{e(item)}</li>'
        for item in case["evidence"]
    )
    proof_links = ''.join(
        f'<a class="case-link" href="{e(href)}" data-evt="{e(event)}"'
        f'{" target=\"_blank\" rel=\"noopener\"" if external else ""}>{e(label)} →</a>'
        for label, href, event, external in case["proof_links"]
    )
    testimonial = testimonial_card(
        case["testimonial_id"], "service-review case-study-review", link_project=False
    )
    secondary_image = ''
    cover_class = ''
    if case.get("secondary_image"):
        cover_class = ' case-study-cover--phones'
        secondary_image = (
            f'<img src="{e(case["secondary_image"])}" alt="{e(case["secondary_image_alt"])}" '
            f'width="380" height="844">'
        )
    feedback = ''
    if testimonial:
        feedback = f'''<section class="sec case-study-feedback" aria-labelledby="case-feedback-title">
  <div class="rail">
    <p class="label">Approved client feedback</p>
    <h2 class="page-section-title" id="case-feedback-title">The client's exact, approved words.</h2>
    {testimonial}
  </div>
</section>'''
    page_head = head(
        case["title"], case["desc"], path, schema,
        social_image=case["image"], social_alt=case["image_alt"],
    ).replace('<body>', '<body class="evidence-page" data-assistant-launcher="hidden">', 1)
    return page_head + ICONS + nav() + f'''
<main id="main">
<article>
<section class="sec page-hero case-study-hero">
  <div class="rail case-study-hero-grid">
    <div>
      {crumbs(bc)}
      <p class="label">{e(case["status"])}</p>
      <h1 class="dsp business-copy">{e(case["name"])} <em>case study.</em></h1>
      <p class="sub business-copy">{e(case["lede"])}</p>
      <p class="case-study-meta business-copy">Role: {e(case["role"])} · {e(case["project_type"])} · reviewed {e(case.get("reviewed_label", "September 4, 2026"))}</p>
    </div>
    <figure class="case-study-cover{cover_class}"><img src="{e(case["image"])}" alt="{e(case["image_alt"])}" width="{case["image_width"]}" height="{case["image_height"]}">{secondary_image}</figure>
  </div>
</section>

<section class="sec case-study-answer" aria-labelledby="case-answer-title">
  <div class="rail">
    <p class="label">The decision this solved</p>
    <h2 class="page-section-title" id="case-answer-title">{e(case["decision_heading"])}</h2>
    <p class="sub business-copy">{e(case["problem"])}</p>
  </div>
</section>

<section class="sec" aria-labelledby="case-built-title">
  <div class="rail">
    <p class="label">What Leon built</p>
    <h2 class="page-section-title" id="case-built-title">{e(case.get("scope_heading", "Delivered scope."))}</h2>
    <div class="scope-grid case-study-build">{build_cards}</div>
  </div>
</section>

<section class="sec case-study-evidence" aria-labelledby="case-evidence-title" data-view-event="proof_view">
  <div class="rail two-col">
    <div>
      <p class="label">Evidence on this page</p>
      <h2 class="page-section-title" id="case-evidence-title">What supports the case.</h2>
      <ul class="blist">{evidence_items}</ul>
      <div class="case-links">{proof_links}</div>
    </div>
    <aside class="proofcard case-study-boundary">
      <p class="label">Claim boundary</p>
      <h3>What this case does not claim</h3>
      <p class="sub business-copy">{e(case["boundary"])}</p>
    </aside>
  </div>
</section>

{feedback}

<section class="sec case-study-start" data-view-event="start_section_view">
  <div class="rail">
    <p class="label">Have a related problem?</p>
    <h2 class="page-section-title">Bring the decision or workflow, even if the right build is still unclear.</h2>
    <div class="ctarow"><a class="btn btn-solid magnet" href="/quote" data-evt="case_study_quote_click"><span>Get a fixed quote</span><svg class="ic"><use href="#ic-arrow"/></svg></a><a class="btn magnet" href="/call" data-evt="case_study_call_click"><span>Book a free 15-minute call</span></a><a class="cx-mini" href="{e(case["service_href"])}">{e(case["service_label"])} →</a></div>
  </div>
</section>
</article>
</main>''' + footer() + '</body></html>'


def contractor_inquiry_guide_page():
    path = '/guides/contractor-inquiry-workflow'
    title = 'What Happens After a Contractor Quote Request? | Leon Builds'
    desc = ('A five-step contractor inquiry workflow and self-audit for estimate forms, acknowledgments, '
            'owner handoff, limited follow-up, and useful measurement.')
    bc = [("home", "/"), ("contractor inquiry guide", None)]
    article_id = f'{BASE}{path}#article'
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{BASE}{path}#page",
            "url": f"{BASE}{path}",
            "name": "What happens after a contractor quote request?",
            "description": desc,
            "isPartOf": {"@id": f"{BASE}/#website"},
            "mainEntity": {"@id": article_id},
            "dateModified": "2026-09-04",
        },
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "@id": article_id,
            "headline": "What happens after a contractor quote request?",
            "description": desc,
            "author": {"@type": "Person", "@id": f"{BASE}/#leon", "name": "Leon Kelvin Li", "url": f"{BASE}/about"},
            "publisher": {"@id": f"{BASE}/#business"},
            "mainEntityOfPage": {"@id": f"{BASE}{path}#page"},
            "dateModified": "2026-09-04",
        },
        breadcrumb_schema(bc, path),
    ]
    page_head = head(title, desc, path, schema).replace(
        '<body>', '<body class="evidence-page guide-page" data-assistant-launcher="hidden">', 1
    )
    return page_head + ICONS + nav() + f'''
<main id="main">
<article>
<section class="sec page-hero guide-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">Contractor inquiry self-audit · reviewed September 4, 2026</p>
    <h1 class="dsp business-copy">What happens after a contractor <em>quote request?</em></h1>
    <p class="sub business-copy">A useful inquiry path does five things: captures enough information to route the job, confirms receipt, assigns a person, follows up with clear stop rules, and records what happened. Use this page to inspect your current path from a customer's phone.</p>
    <div class="ctarow"><a class="btn btn-solid magnet" href="#audit"><span>Run the self-audit</span><svg class="ic"><use href="#ic-arrow"/></svg></a><a class="btn magnet" href="/missed-lead-recovery"><span>See the built service</span></a></div>
  </div>
</section>

<section class="sec guide-workflow" id="workflow" aria-labelledby="guide-workflow-title" data-view-event="proof_view">
  <div class="rail">
    <p class="label">A five-step handoff</p>
    <h2 class="page-section-title" id="guide-workflow-title">The form is the start of the workflow.</h2>
    <ol class="contractor-example business-copy" aria-label="Five-step contractor inquiry workflow">
      <li><span>01</span><h3>Capture</h3><p>Ask for the job type, service area, contact route, and only the details needed to decide who should respond.</p></li>
      <li><span>02</span><h3>Acknowledge</h3><p>Confirm that the request arrived. State the response expectation the business can actually meet; an automatic receipt is not a human reply.</p></li>
      <li><span>03</span><h3>Route</h3><p>Send the inquiry to one monitored inbox, CRM, or shared sheet. Avoid a hidden mailbox that nobody owns.</p></li>
      <li><span>04</span><h3>Assign and follow up</h3><p>Name the person responsible. If reminders are appropriate, limit them and stop when the person replies or opts out.</p></li>
      <li><span>05</span><h3>Record the result</h3><p>Keep distinct statuses for received, acknowledged, assigned, replied, booked, and closed. Do not count a form receipt as a booked estimate.</p></li>
    </ol>
  </div>
</section>

<section class="sec" id="audit" aria-labelledby="guide-audit-title">
  <div class="rail">
    <p class="label">Eight checks from a customer's phone</p>
    <h2 class="page-section-title" id="guide-audit-title">Can your current site answer yes?</h2>
    <div class="guide-audit">
      <article><span>01</span><h3>Service fit</h3><p>Can a visitor tell what work you do and whether their job is in your service area?</p></article>
      <article><span>02</span><h3>One estimate action</h3><p>Is the primary quote or estimate action obvious without opening a menu or zooming?</p></article>
      <article><span>03</span><h3>Reasonable intake</h3><p>Does the form collect enough to route the job without turning the first contact into a long application?</p></article>
      <article><span>04</span><h3>Visible receipt</h3><p>After submission, does the visitor see a clear accepted or failed state rather than an endless spinner?</p></article>
      <article><span>05</span><h3>Monitored delivery</h3><p>Can the team name the exact inbox, CRM, or sheet where every accepted request appears?</p></article>
      <article><span>06</span><h3>Named owner</h3><p>Does each new request have a person responsible for the next human action?</p></article>
      <article><span>07</span><h3>Stop rules</h3><p>Do automated reminders stop on reply or opt-out, with consent and provider requirements documented?</p></article>
      <article><span>08</span><h3>Honest measurement</h3><p>Can you separate received requests from replies, booked estimates, held appointments, and won work?</p></article>
    </div>
  </div>
</section>

<section class="sec" aria-labelledby="guide-boundary-title">
  <div class="rail two-col">
    <div>
      <p class="label">What the workflow can improve</p>
      <h2 class="page-section-title" id="guide-boundary-title">A clearer path and a reviewable handoff.</h2>
      <ul class="blist">
        <li><svg class="ic"><use href="#ic-check"/></svg>fewer unanswered questions at the first contact</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>a consistent place for accepted requests to arrive</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>clear responsibility for the next human action</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>event states that can be checked instead of guessed</li>
      </ul>
    </div>
    <aside class="proofcard case-study-boundary">
      <p class="label">Claim boundary</p>
      <h3>What the workflow cannot guarantee</h3>
      <p class="sub business-copy">It does not create demand, repair weak pricing, qualify every visitor, or guarantee leads, bookings, revenue, or won jobs. Traffic, service fit, availability, and the team's sales process still matter.</p>
    </aside>
  </div>
</section>

<section class="sec guide-start" data-view-event="start_section_view">
  <div class="rail">
    <p class="label">Free 3-point review</p>
    <h2 class="page-section-title">Send your current website and ask Leon to inspect the inquiry path.</h2>
    <p class="sub business-copy">Include the website address in the first field. The review is a focused look at the public path, not a traffic, ranking, or revenue promise.</p>
    <div class="ctarow"><a class="btn btn-solid magnet" href="/quote?service=contractor-lead-recovery" data-evt="contractor_guide_review_click"><span>Request the 3-point review</span><svg class="ic"><use href="#ic-arrow"/></svg></a><a class="btn magnet" href="/missed-lead-recovery" data-evt="contractor_guide_service_click"><span>See website + follow-up scope</span></a></div>
  </div>
</section>
</article>
</main>''' + footer() + '</body></html>'


def buyer_decision_guide_page():
    guide = seo_json('buyer-guide.json')
    path = guide['path']
    assert_publication_paths([path])
    bc = [('home', '/'), ('services', '/services/'), ('choosing the right build', None)]
    schema = [
        {'@context': 'https://schema.org', '@type': 'WebPage', '@id': BASE + path + '#page',
         'url': BASE + path, 'name': guide['title'], 'description': guide['description'],
         'mainEntity': {'@id': BASE + path + '#article'}},
        {'@context': 'https://schema.org', '@type': 'Article', '@id': BASE + path + '#article',
         'headline': guide['title'], 'description': guide['description'], 'abstract': guide['answer'],
         'author': {'@type': 'Person', '@id': BASE + '/#leon', 'name': guide['author'], 'url': BASE + '/about'},
         'publisher': {'@id': BASE + '/#business'}, 'mainEntityOfPage': {'@id': BASE + path + '#page'},
         'datePublished': guide['published_at'], 'dateModified': guide['updated_at'],
         'citation': [BASE + row['path'] for row in guide['evidence']]},
        breadcrumb_schema(bc, path),
    ]
    choices = ''.join(f'<article><h3>{e(row["name"])}</h3><p>{e(row["fits"])}</p><p><strong>Try this:</strong> {e(row["test"])}</p><p>{e(row["watch"])}</p></article>' for row in guide['choices'])
    sections = ''.join(f'<section class="sec" id="{e(row["id"])}"><div class="rail"><h2 class="page-section-title">{e(row["heading"])}</h2>' + ''.join(f'<p class="sub business-copy">{e(paragraph)}</p>' for paragraph in row['paragraphs']) + '</div></section>' for row in guide['sections'])
    checklist = ''.join(f'<li><svg class="ic" aria-hidden="true"><use href="#ic-check"/></svg>{e(item)}</li>' for item in guide['checklist'])
    evidence = ''.join(f'<article><h3><a href="{e(row["path"])}" data-evt="seo_related_click">{e(row["label"])}</a></h3><p>{e(row["note"])}</p></article>' for row in guide['evidence'])
    page_head = head(guide['title'] + ' | Leon Builds', guide['description'], path, schema).replace('<body>', '<body class="evidence-page guide-page visual-guide" data-assistant-launcher="hidden">', 1)
    return page_head + ICONS + nav() + f'''
<main id="main"><article>
<section class="sec page-hero guide-hero"><div class="rail">
<p class="label">Website · automation · custom software</p>
<h1 class="dsp business-copy">What do you <em>actually need?</em></h1>
{choice_scene()}
<p class="choice-verdict">Choose the smallest option that fixes the broken step. <strong>You do not need all three at once.</strong></p>
<div class="ctarow"><a class="btn btn-solid" href="{e(guide['cta']['path'])}" data-evt="seo_guide_review_click"><span>Help me choose ↗</span></a><span class="visual-caution">Send your website and one task that is not working.</span></div>
<p class="visual-byline">By <a href="/about">Leon Kelvin Li</a> · September 5, 2026 · Leon Builds sells implementation services.</p>
</div></section>
<details class="rail visual-details" id="full-guide"><summary>Read the full guide &amp; quote checklist</summary><div class="visual-details-content">
<p class="sub business-copy">{e(guide['answer'])}</p><p class="sub business-copy">{e(guide['intro'])}</p>
<section class="sec" id="compare-options" data-view-event="proof_view"><div class="rail">
<h2 class="page-section-title">Match the build to the job.</h2><div class="scope-grid business-copy">{choices}</div>
</div></section>
{sections}
<section class="sec" id="scope-checklist"><div class="rail">
<h2 class="page-section-title">Your quote-preparation checklist</h2>
<ul class="blist business-copy">{checklist}</ul>
<p class="sub business-copy">{e(guide['boundary'])}</p>
</div></section>
</div></details>
<section class="sec" id="examples"><div class="rail">
<h2 class="page-section-title">See it in real work.</h2><div class="scope-grid business-copy">{evidence}</div>
</div></section>
<section class="sec guide-start" data-view-event="start_section_view"><div class="rail">
<h2 class="page-section-title">Show the problem. <em>Start small.</em></h2>
<div class="ctarow"><a class="btn btn-solid magnet" href="{e(guide['cta']['path'])}" data-evt="seo_guide_review_click"><span>{e(guide['cta']['label'])}</span></a><a class="btn magnet" href="/services/"><span>See services and published starting prices</span></a></div>
</div></section>
</article></main>''' + footer() + '</body></html>'


def work_page():
    """Long-form proof and project archive kept off the conversion homepage."""
    path = '/work'
    title = 'Work & Case Studies | Leon Builds'
    desc = ('Inspect client websites, business systems, public demos and a live App Store product built by '
            'Leon Builds. Every project is labelled with its current, honest status.')
    bc = [("home", "/"), ("work and case studies", None)]
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "@id": f"{BASE}{path}#page",
            "url": f"{BASE}{path}",
            "name": "Leon Builds work and case studies",
            "description": desc,
            "isPartOf": {"@id": f"{BASE}/#website"},
            "about": {"@id": f"{BASE}/#leon"},
        },
        breadcrumb_schema(bc, path),
    ]
    page_head = head(title, desc, path, schema).replace(
        '<body>', '<body data-assistant-launcher="hidden">', 1
    )
    return page_head + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">Work and case studies</p>
    <h1 class="dsp">Real systems. <em>Honest status.</em></h1>
    <p class="sub business-copy">The archive includes client builds, operational systems, public demos, and a live App Store product. Each case says what is live, what is simulated, what problem it addresses, and what Leon built.</p>
    <div class="ctarow"><a class="btn btn-solid magnet" href="/quote" data-evt="work_quote_click"><span>Get a fixed quote</span><svg class="ic"><use href="#ic-arrow"/></svg></a></div>
  </div>
</section>

<section class="sec" aria-labelledby="selected-work-title" data-view-event="proof_view">
  <div class="rail">
    <header class="sec-head">
      <p class="label">Selected work</p>
      <h2 class="page-section-title" id="selected-work-title">Business problems, working interfaces, and inspectable evidence.</h2>
    </header>
    <div class="case-grid">
      <article class="case-card case-featured" id="work-site-intelligence">
        <span id="work-zips" aria-hidden="true"></span>
        <figure class="case-media"><img src="/assets/proof/site-intelligence-map.png" alt="ALLCPR Site Intelligence nationwide opportunity map" loading="lazy" width="1200" height="480"></figure>
        <div class="case-copy">
          <p class="label">Operational client system · ALLCPR</p>
          <h3>ALLCPR Site Intelligence</h3>
          <p class="business-copy"><b>Problem:</b> ALLCPR needed a consistent way to compare where to open, staff, and grow instead of manually searching maps or trusting one headline score.</p>
          <p class="business-copy"><b>Built:</b> Leon built a location-planning system from a reviewed project dataset containing 33,772 U.S. ZIP-code records. It brings together targeted local-business map data, public business and facility data, ALLCPR's history, uncertainty ranges, reasons for and against each area, maps, and Excel exports for the team.</p>
          <p class="business-copy"><b>Reliability check:</b> Leon found and removed a misleading validation loop, so the platform shows uncertainty instead of presenting false confidence as fact.</p>
          <p class="business-copy"><b>Decision boundary:</b> The platform prioritizes markets to investigate. Rent, parking, classroom fit, instructor coverage, and current local conditions still require human field validation before opening.</p>
          <p class="case-role">Role: data product and full-stack developer · ALLCPR client project</p>
          {testimonial_card("testimonial-02", "service-review case-review")}
          <a class="case-link" href="/work/allcpr-site-intelligence" data-evt="work_allcpr_case_click">Read the full case study →</a>
        </div>
      </article>

      <article class="case-card" id="work-beastypages">
        <span id="work-homescreen" aria-hidden="true"></span>
        <span id="work-ordering" aria-hidden="true"></span>
        <figure class="case-media proof-phone-pair">
          <img src="/assets/proof/home-screen-catalog.png" alt="beastypages.com catalog of local-business destinations" loading="lazy" width="380" height="844">
          <img src="/assets/proof/home-screen-menu.png" alt="A business-specific menu and cart inside beastypages.com" loading="lazy" width="380" height="844">
        </figure>
        <div class="case-copy">
          <p class="label">Client website project · demo checkout</p>
          <h3>beastypages.com</h3>
          <p class="business-copy"><b>Problem:</b> A client needed a phone-first website for browsing local-business pages and menus in one consistent interface.</p>
          <p class="business-copy"><b>Built:</b> The September 4, 2026 review snapshot contained 37 businesses, with search, business-specific menus, a prototype cart, server-side repricing, and vendor-separated demo tickets.</p>
          <p class="business-copy"><b>Honest boundary:</b> Payment and kitchen progression are simulations. The client claim is for the website build, not a production ordering rollout.</p>
          <p class="case-role">Role: website and full-stack developer · client identity withheld</p>
          <div class="case-links"><a class="case-link" href="/work/beastypages-website" data-evt="work_beastypages_case_click">Read the full case study →</a><a class="case-link" href="https://beastypages.com/?b=b_bulapies" target="_blank" rel="noopener" data-evt="case_homescreen_click">Open a live business page →</a></div>
        </div>
      </article>

      <article class="case-card" id="work-curio-public">
        <span id="work-curio" aria-hidden="true"></span>
        <figure class="case-media">
          <video controls muted playsinline preload="metadata" poster="/assets/proof/curio-appstore-current.png" aria-label="Curio product screen recording">
            <source src="/assets/proof/curio-feed-demo.mp4" type="video/mp4">
          </video>
        </figure>
        <div class="case-copy">
          <p class="label">Live product · App Store</p>
          <h3>Curio</h3>
          <p class="business-copy"><b>Problem:</b> Turn passive scrolling into short, source-backed learning.</p>
          <p class="business-copy"><b>Built:</b> The React and TypeScript client, native iOS shell, Express and Postgres backend, subscriptions, content pipeline, and four-language in-app content experience.</p>
          <p class="business-copy"><b>Public proof:</b> The product is downloadable on the U.S. App Store and its public founder profile identifies Leon's role.</p>
          <p class="case-role">Role: solo product developer</p>
          <div class="case-links">
            <a class="case-link" href="/work/curio-app" data-evt="work_curio_case_click">Read the full case study →</a>
            <a class="case-link" href="https://apps.apple.com/app/apple-store/id6781121127?pt=129044256&amp;ct=leonbuilds-work&amp;mt=8" target="_blank" rel="noopener" data-evt="case_curio_click">Open on the App Store →</a>
            <a class="case-link" href="https://trycurio.app/team.html#leon" target="_blank" rel="me noopener">View the founder profile →</a>
            <a class="case-link" href="/services/mobile-apps" data-evt="case_app_service_click">See mobile app development →</a>
          </div>
        </div>
      </article>

      <article class="case-card" id="work-loqol-portal">
        <figure class="case-media"><img src="/assets/proof/loqol-seller-portal-contribution.svg" alt="Labelled implementation diagram of Leon's seller-portal contribution, not a production screenshot" loading="lazy" width="1600" height="1200"></figure>
        <div class="case-copy">
          <p class="label">Client product contribution · existing product and design</p>
          <h3>LOQOL seller portal</h3>
          <p class="business-copy"><b>Problem:</b> Sellers need to complete long disclosure forms without losing the answer they are still writing.</p>
          <p class="business-copy"><b>Contribution:</b> Built parts of the existing portal to connect answers to seller records, request automatic saves, and protect unfinished text during background updates.</p>
          <p class="case-role">Role: frontend implementation within the team's existing product and design</p>
          <div class="case-links"><a class="case-link" href="/work/loqol-seller-portal" data-evt="work_loqol_portal_case_click">Read the contribution case →</a></div>
        </div>
      </article>

      <article class="case-card" id="work-loqol">
        <figure class="case-media loqol-proof-grid">
          <img src="/assets/proof/loqol-questionnaire.png" alt="Loqol seller questionnaire with conflicting public-sewer and septic-tank answers saved" loading="lazy" width="1800" height="900">
          <img src="/assets/proof/loqol-filled-pdf.png" alt="Three-page California disclosure PDF generated from saved Loqol answers" loading="lazy" width="1800" height="900">
          <img class="loqol-flag" src="/assets/proof/loqol-contradiction.png" alt="Loqol flags the sewer and septic contradiction for review" loading="lazy" width="350" height="360">
        </figure>
        <div class="case-copy">
          <p class="label">Public demo · incomplete signing and email steps</p>
          <h3>Loqol disclosures</h3>
          <p class="business-copy"><b>Problem:</b> Translate a dense California disclosure form into a guided seller workflow.</p>
          <p class="business-copy"><b>Built:</b> An 82-question seller flow, 16 consistency rules, an agent review workspace, saved answers, and a three-page PDF output.</p>
          <p class="business-copy"><b>Honest boundary:</b> Buyer and agent signing plus seller email delivery are not complete.</p>
          <p class="case-role">Role: full-stack product developer</p>
          <div class="case-links">
            <a class="case-link" href="https://loqol-tds.onrender.com/agent" target="_blank" rel="noopener" data-evt="case_loqol_click">Open the public demo →</a>
          </div>
        </div>
      </article>
    </div>
  </div>
</section>

<section class="sec" id="work-archive" aria-labelledby="archive-title">
  <div class="rail">
    <header class="sec-head">
      <p class="label">Additional project archive</p>
      <h2 class="page-section-title" id="archive-title">Operational patterns behind the interfaces.</h2>
      <p class="sub business-copy">These anonymized project notes preserve useful implementation detail. They are not presented as public client demos or outcome guarantees.</p>
    </header>
    <div class="case-grid">
      <article class="case-card" id="work-reviews">
        <div class="case-copy">
          <p class="label">Internal workflow · client anonymized</p>
          <h3>Review desk</h3>
          <p class="business-copy"><b>Problem:</b> Review notifications arrived faster than a small team could classify and answer them consistently.</p>
          <p class="business-copy"><b>Built:</b> An inbox workflow that classifies the issue, drafts from verified business facts, and routes a Gmail draft, Slack card, and sheet row to a person.</p>
          <p class="business-copy"><b>Control:</b> The workflow never posts a reply. A human reviews and sends it.</p>
        </div>
      </article>

      <article class="case-card" id="work-docs">
        <div class="case-copy">
          <p class="label">Internal workflow · client anonymized</p>
          <h3>Document control</h3>
          <p class="business-copy"><b>Problem:</b> Company documents and approvals lived across folders, inboxes, and memory.</p>
          <p class="business-copy"><b>Built:</b> A template request creates and files the document; approval locks it; publishing increments the version, writes the change log, and exports the external PDF.</p>
          <p class="business-copy"><b>Handoff:</b> The workflow was implemented in Apps Script and as six editable n8n workflows.</p>
        </div>
      </article>

      <article class="case-card" id="work-assistant">
        <div class="case-copy">
          <p class="label">Regulated-market prototype · Chinese language</p>
          <h3>Compliance-aware assistant</h3>
          <p class="business-copy"><b>Problem:</b> Health-education answers needed source citations and deterministic safety limits in a market with strict advertising rules.</p>
          <p class="business-copy"><b>Built:</b> Safety screening before the model, hybrid retrieval, evidence tiers, numbered citations, and a final legal-claim validator.</p>
          <p class="business-copy"><b>Control:</b> If a revised answer still fails validation, the assistant declines rather than guessing.</p>
        </div>
      </article>
    </div>
    <p class="more">This is Leon's current public work archive. Each entry states what is live, incomplete, or anonymized.</p>
    <div class="ctarow"><a class="btn btn-solid magnet" href="/quote" data-evt="work_final_quote_click"><span>Get a fixed quote</span><svg class="ic"><use href="#ic-arrow"/></svg></a><a class="cx-mini" href="/technical-build-partner">Need help choosing what to build? Start here →</a><a class="cx-mini" href="/about">More about Leon →</a></div>
  </div>
</section>
</main>''' + footer() + '</body></html>'


def reviews_page():
    """Render all and only released feedback when three records make a real route."""
    if not REVIEWS_ROUTE_ENABLED:
        raise RuntimeError('reviews page requested without three released testimonials')
    path = '/reviews'
    title = 'Approved Client Feedback | Leon Builds'
    desc = ('Project-specific client feedback published only after approval of the exact quote, '
            'attribution and placement.')
    bc = [("home", "/"), ("approved client feedback", None)]
    ids = released_testimonial_ids()
    cards = testimonial_cards(ids)
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{BASE}{path}#page",
            "url": f"{BASE}{path}",
            "name": "Approved client feedback for Leon Builds",
            "description": desc,
            "isPartOf": {"@id": f"{BASE}/#website"},
        },
        breadcrumb_schema(bc, path),
    ]
    page_head = head(title, desc, path, schema).replace(
        '<body>', '<body data-assistant-launcher="hidden">', 1
    )
    return page_head + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">Approved client feedback</p>
    <h1 class="dsp">What clients said <em>after the work.</em></h1>
    <p class="sub business-copy">These are complete, project-specific quotes. Each one is published only after the client approved the exact wording, attribution, and placement.</p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <div class="testimonial-grid">{cards}</div>
    <div class="ctarow"><a class="btn btn-solid magnet" href="/quote" data-evt="reviews_quote_click"><span>Get a fixed quote</span><svg class="ic"><use href="#ic-arrow"/></svg></a><a class="cx-mini" href="/work">See real work →</a></div>
  </div>
</section>
</main>''' + footer() + '</body></html>'


def missed_lead_recovery_page():
    """Focused Search landing page for the contractor acquisition offer."""
    path = '/missed-lead-recovery'
    title = 'Contractor Lead Recovery System | Website + Follow-Up | Leon Builds'
    desc = ('A fixed-scope contractor website and missed-lead follow-up system: estimate intake, '
            'prompt acknowledgment, owner handoff and tracking. Starting at $1,500.')
    faqs = [
        ("Can you improve my current website instead?",
         "Yes. If the current site is sound, we can repair its estimate path and connect the follow-up workflow instead of replacing pages that already work."),
        ("Is this lead generation, ad management, or a guarantee?",
         "No. This product improves how an existing visitor becomes an estimate request and how that request reaches your team. Traffic, lead quality, pricing, availability, and your sales process still determine results."),
        ("How is timing set, and what is handed over?",
         "The schedule is confirmed after the written scope, compatible access, and customer-facing copy are approved. Handoff includes the agreed project accounts, included source or configuration, setup notes, one handoff session, and 30 days of fixes against the written scope."),
    ]
    bc = [("home", "/"), ("contractor lead recovery system", None)]
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "Service",
            "@id": f"{BASE}{path}#service",
            "name": "Contractor Lead Recovery System",
            "url": f"{BASE}{path}",
            "provider": {"@id": f"{BASE}/#leon"},
            "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "BusinessAudience", "audienceType": "Owner-run contractors and home-service businesses"},
            "description": desc,
            "offers": {
                "@type": "Offer",
                "price": "1500",
                "priceCurrency": "USD",
                "description": "Starting scope; a written compatibility check and fixed quote come before work begins.",
            },
        },
        faq_schema(faqs),
        breadcrumb_schema(bc, path),
    ]
    review_cta = '''<a class="btn btn-solid magnet" href="/quote?service=contractor-lead-recovery" data-evt="contractor_review_click"><span class="business-copy">Get a free 3-point website review</span><svg class="ic"><use href="#ic-arrow"/></svg></a>'''
    call_cta = '''<a class="btn magnet" href="/call?service=contractor-lead-recovery" data-evt="cta_call_click"><span class="business-copy">Prefer to talk? Book 15 minutes</span></a>'''
    check = '<svg class="ic"><use href="#ic-check"/></svg>'
    review_cards = testimonial_cards(
        ["testimonial-03", "testimonial-04", "testimonial-05"], "service-review"
    )
    reviews_section = ''
    if review_cards:
        reviews_href = '/reviews' if REVIEWS_ROUTE_ENABLED else '/#testimonials'
        reviews_section = f'''<section class="sec service-reviews" id="client-feedback">
  <div class="rail">
    <p class="label">Approved client feedback</p>
    <h2 class="page-section-title">Website client feedback</h2>
    <div class="service-review-grid">{review_cards}</div>
    <a class="cx-mini" href="{reviews_href}">Read approved client feedback →</a>
  </div>
</section>'''
    feedback_jump = ('    <a href="#client-feedback">Client feedback</a>\n'
                     if review_cards else '')
    page_head = head(title, desc, path, schema).replace(
        '<body>', '<body class="contractor-landing" data-assistant-launcher="hidden">', 1
    )
    return page_head + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">Contractor website + missed-lead follow-up</p>
    <h1 class="dsp business-copy">A contractor website that captures estimate requests <em>and follows up automatically.</em></h1>
    <p class="sub business-copy">Leon builds the site, estimate form, prompt automatic acknowledgment, owner handoff, and up to two follow-ups. Fixed scope starts at $1,500; timing follows the written scope and access check.</p>
    <p class="hero-local business-copy">The free review sends three specific observations by email. Prefer a conversation? Choose the 15-minute call.</p>
    <div class="ctarow">{review_cta}{call_cta}</div>
    <p class="hero-local business-copy">Already know what needs building? <a href="/quote" data-evt="contractor_fixed_quote_click">Request a fixed quote by email</a>. No call or paid planning session required.</p>
    <p class="hero-local business-copy">Based in California. Working remotely with contractors and home-service businesses across the U.S.</p>
  </div>
</section>

<div class="landing-jump-wrap" aria-label="Find it fast">
  <nav class="rail landing-jump">
    <span>Find it fast</span>
    <a href="#scope">Scope &amp; pricing</a>
{feedback_jump}    <a href="#proof">How it works</a>
    <a href="#faq">Questions</a>
  </nav>
</div>

<section class="sec" id="scope">
  <div class="rail">
    <p class="label">The $1,500 starting scope</p>
    <h2 class="page-section-title business-copy">A complete estimate path, not just a nicer homepage.</h2>
    <div class="two-col">
      <div>
        <ul class="blist">
          <li>{check}one focused, phone-first contractor website or lead page</li>
          <li>{check}services, service area, trust proof, and one primary estimate action</li>
          <li>{check}structured intake for the agreed project details and optional photos</li>
          <li>{check}one automatic email or SMS acknowledgment using approved copy</li>
        </ul>
      </div>
      <div>
        <ul class="blist">
          <li>{check}delivery to one agreed CRM, shared sheet, or monitored inbox</li>
          <li>{check}up to two follow-ups with reply, stop, and opt-out rules</li>
          <li>{check}one owner or staff handoff rule and one booking or contact link</li>
          <li>{check}a basic received, sent, replied, and handed-off event log</li>
          <li>{check}handoff session, setup notes, and included source or configuration</li>
        </ul>
      </div>
    </div>
    <div class="scope-boundary business-copy"><p><b>Boundaries:</b> Buying leads, ad management, a new CRM, live call answering, historical-data cleanup, and large multi-location sites are separate. Provider fees remain with the provider. Compatibility and consent requirements are checked before the fixed quote.</p></div>
    <p class="pricetag business-copy"><b>From $1,500.</b> You receive the fixed price, schedule, inclusions, and handoff terms in writing before work begins.</p>
  </div>
</section>

{reviews_section}

<section class="sec" id="proof" aria-labelledby="contractor-proof-title" data-view-event="proof_view">
  <div class="rail">
    <p class="label">Illustrative workflow · not a live client result</p>
    <h2 class="page-section-title business-copy" id="contractor-proof-title">See the estimate-to-follow-up path.</h2>
    <ol class="contractor-example business-copy" aria-label="Example estimate follow-up workflow">
      <li><span>01</span><h3>Estimate request</h3><p>A visitor sends the job type, service area, and best way to reach them.</p></li>
      <li><span>02</span><h3>Clear acknowledgment</h3><p>They get your approved confirmation and a clear next step.</p></li>
      <li><span>03</span><h3>Owner handoff</h3><p>Your chosen inbox, sheet, or CRM receives the request and its status.</p></li>
      <li><span>04</span><h3>Follow-up with limits</h3><p>Up to two reminders. A reply or opt-out stops the sequence.</p></li>
    </ol>
    <div class="proofcard">
      <p class="label">Client website project · demo checkout</p>
      <h3>beastypages.com</h3>
      <p class="sub business-copy">Related website work: Leon built phone-first business pages, search, menus, and server-side cart logic. Payment and kitchen progression are simulations. This is evidence of website delivery, not a contractor lead or revenue result.</p>
      <a class="cx-mini" href="/work/beastypages-website" data-evt="contractor_proof_demo_click">Read the website case study →</a>
    </div>
    <a class="cx-mini" href="/guides/contractor-inquiry-workflow" data-evt="contractor_guide_click">Use the 5-step contractor inquiry audit →</a>
  </div>
</section>

<section class="sec" id="faq" data-view-event="start_section_view">
  <div class="rail">
    <p class="label">Three questions before booking</p>
    {faq_html(faqs)}
    <div class="ctarow">{review_cta}{call_cta}</div>
    <p class="sub business-copy">Bring your current website. We'll show you the smallest sensible improvement and say plainly if this product is not the right fit.</p>
  </div>
</section>
</main>''' + footer() + '</body></html>'


def technical_partner_page():
    """One-on-one technical planning and build support for owner-led businesses."""
    path = '/technical-build-partner'
    title = 'Websites, Apps & Automation for Small Businesses | Leon Builds'
    desc = ('Work directly with Leon to build a website, automate repeat tasks, or create a custom tool or app. '
            'Clear scope, upfront pricing, and a free project quote.')
    faqs = [
        ("Do I need a technical brief?", "No. Describe the problem in your own words. Requesting a quote is free, and a call or paid plan is optional."),
        ("How quickly can I see progress?", "For a ready, well-scoped project, a first reviewable milestone can be targeted within 1–3 business days. This is not the full build. The full schedule is agreed after checking scope and access."),
        ("What is included in my quote?", "The agreed work, testing, source code, account access, setup notes, and support period. Hosting, paid tools, advertising, data cleanup, ongoing content, and extra work are separate. Third-party licenses keep their own terms."),
        ("How does monthly work stay on track?", "We agree on capacity, exclusions, and how unfinished work carries over before the month starts. You get a weekly progress note and a monthly review. This is not unlimited development."),
    ]
    bc = [("home", "/"), ("technical build partner", None)]
    service_id = f'{BASE}{path}#service'
    offers = [
        {
            "@type": "Offer", "name": "Systems Plan", "url": f"{BASE}{path}#offers",
            "price": "199", "priceCurrency": "USD",
            "description": "Written problem map, smallest recommended solution, and proposed scope, budget, and timeline. Credited toward the agreed build if the client continues with us.",
        },
        {
            "@type": "Offer", "name": "One-time project", "url": f"{BASE}{path}#offers",
            "priceSpecification": {
                "@type": "UnitPriceSpecification", "minPrice": "1500",
                "priceCurrency": "USD",
            },
            "description": "Starting price for one priority website, automation, internal-tool, or app milestone with written scope, review checkpoints, testing, and agreed handoff.",
        },
        {
            "@type": "Offer", "name": "Ongoing partner", "url": f"{BASE}{path}#offers",
            "priceSpecification": {
                "@type": "UnitPriceSpecification", "minPrice": "2000",
                "priceCurrency": "USD", "unitText": "MONTH",
            },
            "description": "Starting monthly price for reserved build capacity, a written priority backlog, and an agreed monthly scope.",
        },
    ]
    schema = [
        {
            "@context": "https://schema.org", "@type": "WebPage",
            "@id": f"{BASE}{path}#webpage", "url": f"{BASE}{path}",
            "name": title, "description": desc,
            "isPartOf": {"@id": f"{BASE}/#website"},
            "mainEntity": {"@id": service_id},
        },
        {
            "@context": "https://schema.org", "@type": "Service", "@id": service_id,
            "name": "Website, App and Automation Development for Small Businesses", "url": f"{BASE}{path}",
            "provider": {"@id": f"{BASE}/#leon"},
            "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "BusinessAudience", "audienceType": "Owner-led small businesses"},
            "description": desc,
            "hasOfferCatalog": {
                "@type": "OfferCatalog", "name": "Technical build partner offers",
                "itemListElement": offers,
            },
        },
        faq_schema(faqs),
        breadcrumb_schema(bc, path),
    ]
    quote_cta = '''<a class="btn btn-solid magnet" href="/quote?service=technical-build-partner" data-evt="technical_partner_quote_click"><span class="business-copy">Tell me what you need fixed</span><svg class="ic"><use href="#ic-arrow"/></svg></a>'''
    call_cta = '''<a class="btn magnet" href="/call?service=technical-build-partner" data-evt="technical_partner_call_click"><span class="business-copy">Book 15 minutes</span></a>'''
    systems_plan_cta = '''<a class="cx-mini" href="/quote?service=technical-build-partner&amp;package=systems-plan" data-evt="technical_partner_systems_plan_click">Ask about planning →</a>'''
    sprint_cta = '''<a class="cx-mini" href="/quote?service=technical-build-partner&amp;package=focused-build-sprint" data-evt="technical_partner_sprint_click">Talk to Leon →</a>'''
    ongoing_cta = '''<a class="cx-mini" href="/quote?service=technical-build-partner&amp;package=ongoing-technical-partner" data-evt="technical_partner_ongoing_click">Talk to Leon →</a>'''
    page_head = head(title, desc, path, schema).replace(
        '<body>', '<body class="technical-partner-page" data-assistant-launcher="hidden">', 1
    )
    return page_head + ICONS + nav().replace('Get a fixed quote', 'Talk to Leon') + f'''
<main id="main" class="partner-simple">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">For small businesses · Work directly with Leon</p>
    <h1 class="dsp business-copy">Your website, tools, and apps. Handled by Leon.</h1>
    <p class="sub business-copy">Tell me what's slowing your business down. I'll recommend a practical solution, build it, and make sure it works.</p>
    <p class="partner-capabilities">Websites · Automation · Internal tools · Apps</p>
    <div class="ctarow">{quote_cta}{call_cta}</div>
    <p class="partner-cta-note">Free project quote. I reply by email.</p>
  </div>
</section>

<section class="sec partner-problems" id="fit">
  <div class="rail">
    <h2 class="page-section-title">Sound familiar?</h2>
    <ul class="partner-problem-list">
      <li>Leads are slipping through.</li>
      <li>Your team keeps doing the same admin work.</li>
      <li>You've outgrown a spreadsheet or existing tool.</li>
      <li>Your website makes it hard to take the next step.</li>
      <li>Customers keep calling with the same questions.</li>
      <li>You have an app idea and need someone to build it.</li>
    </ul>
  </div>
</section>

<section class="sec" id="build">
  <div class="rail">
    <h2 class="page-section-title">Here's what I can handle.</h2>
    <div class="partner-build-grid">
      <article><h3>Websites</h3><p>A clear way for customers to call, book, or request a quote.</p></article>
      <article><h3>Automation</h3><p>Automatic replies and reminders, with less repetitive work.</p></article>
      <article><h3>Internal tools</h3><p>One place to manage the work your team does every day.</p></article>
      <article><h3>Apps</h3><p>A working product for your customers or staff.</p></article>
    </div>
  </div>
</section>

<section class="sec partner-proof-section" id="proof" aria-labelledby="partner-proof-title">
  <div class="rail">
    <h2 class="page-section-title" id="partner-proof-title">See what I've built.</h2>
    <div class="fixrow partner-proof-grid">
      <a class="fixcard link" href="/work/allcpr-site-intelligence"><figure class="service-proof-media service-proof-media--map"><img src="/assets/proof/site-intelligence-map.png" alt="ALLCPR Site Intelligence nationwide opportunity map" loading="lazy" width="1200" height="480"></figure><h3>ALLCPR</h3><p>ALLCPR needed a way to compare potential locations. I built a planning tool from a reviewed dataset of 33,772 U.S. ZIP-code records. Explore the maps and decision process.</p><span class="go">View case study →</span></a>
      <a class="fixcard link" href="/work/curio-app"><figure class="service-proof-media"><img src="/assets/proof/curio-appstore-current.png" alt="Curio live App Store listing" loading="lazy" width="1200" height="630"></figure><h3>Curio</h3><p>An app idea taken through design, development, and release. I built the iPhone app, backend, subscriptions, and content experience in four languages. See the live App Store product.</p><span class="go">View case study →</span></a>
      <a class="fixcard link" href="/work/beastypages-website"><figure class="service-proof-media proof-phone-pair"><img src="/assets/proof/home-screen-catalog.png" alt="beastypages.com catalog of local-business destinations" loading="lazy" width="380" height="844"><img src="/assets/proof/home-screen-menu.png" alt="beastypages.com business-specific menu and demonstration cart" loading="lazy" width="380" height="844"></figure><h3>Beasty Pages</h3><p>A client website that brings business pages, menus, and search together. I built the mobile experience and a demo cart. See exactly which parts are live and which are demonstrations.</p><span class="go">View case study →</span></a>
    </div>
    <a class="section-link" href="/reviews" data-evt="technical_partner_reviews_click">Read 3 client reviews →</a>
  </div>
</section>

<section class="sec" id="process">
  <div class="rail">
    <h2 class="page-section-title">From problem to finished work.</h2>
    <ol class="partner-steps">
      <li><span>01</span>Tell me what's stuck.</li>
      <li><span>02</span>Agree on the solution, scope, and price.</li>
      <li><span>03</span>Review it as I build.</li>
      <li><span>04</span>Get the finished work and handoff.</li>
    </ol>
  </div>
</section>

<section class="sec" id="offers">
  <div class="rail">
    <h2 class="page-section-title">A project or an ongoing partner.</h2>
    <div class="scope-grid partner-offers">
      <article id="offer-sprint"><h3>One-time project</h3><p class="pricetag"><b>From $1,500</b></p><p>One agreed milestone: a quote flow, automation, or feature of a larger tool or app.</p><p>Includes a working preview, testing, and agreed handoff.</p>{sprint_cta}</article>
      <article id="offer-ongoing"><h3>Ongoing partner</h3><p class="pricetag"><b>From $2,000/month</b></p><p>Reserved development time for one primary milestone plus agreed maintenance or fixes.</p><p>Monthly scope and capacity are agreed first, with weekly updates and a monthly review.</p>{ongoing_cta}</article>
    </div>
    <p class="partner-plan" id="offer-plan"><b>Need help deciding?</b> The optional <b>$199 Systems Plan</b> includes a 45-minute working session and written recommendation, budget range, and timeline. Keep the plan either way; the fee is credited toward the agreed build. {systems_plan_cta}</p>
    <p class="partner-price-note">Smaller, defined jobs: <a href="/services/websites">websites from $300</a> · <a href="/services/business-automation">automation from $500</a>. <a href="/services/mobile-apps">Full app projects start at $3,500</a>.</p>
  </div>
</section>

<section class="sec" id="faq">
  <div class="rail">
    <h2 class="page-section-title">Before we start.</h2>
    {faq_html(faqs)}
    <div class="partner-final" id="start">
      <h2 class="page-section-title">What do you need fixed?</h2>
      <div class="ctarow">{quote_cta}{call_cta}</div>
    </div>
  </div>
</section>
</main>''' + footer() + '</body></html>'

def listing_page(kind, items, title, desc, blurb):
    path = f'/{kind}/'
    bc = [("home","/"),(kind, None)]
    schema = [breadcrumb_schema(bc, path)]
    def card_summary(value, limit=132):
        if len(value) <= limit:
            return value
        return value[:limit].rsplit(' ', 1)[0].rstrip(' ,;:—-') + '…'

    cards = ''.join(
        f'<a class="fixcard link" href="/{kind}/{x["slug"]}"><h3>{e(x["name"])}</h3><p>{e(card_summary(x["desc"]))}</p><span class="go">'
        f'{e("from " + x["price"] + " · details →") if kind == "services" else "open →"}</span></a>'
        for x in items)
    featured = ('''<div class="proofcard">
      <p class="label">Not sure which service fits?</p>
      <h2>Start with the bottleneck, then choose the smallest useful build.</h2>
      <p class="sub">Work with us on a website, automation, internal tool, app, or a written Systems Plan before committing to a larger build.</p>
      <a class="cx-mini" href="/technical-build-partner">Explore website, app &amp; automation help →</a>
      <p class="sub business-copy"><a href="/guides/website-builder-or-custom-software" data-evt="seo_related_click">Website builder, automation or custom software? Use the decision guide before choosing a service.</a></p>
    </div>''' if kind == 'services' else '<!-- featured offer is service-specific -->')
    return head(title, desc, path, schema) + ICONS + nav() + f'''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    {crumbs(bc)}
    <p class="label">leon builds --{kind}</p>
    <h1 class="dsp">{e(kind)} <em>{'we build' if kind=='services' else 'we build for'}</em></h1>
    <p class="sub">{e(blurb)}</p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    {featured}
    <div class="fixrow">{cards}</div>
    {cta_block("i'm not sure which of these i need — here's my situation: ")}
  </div>
</section>
</main>''' + footer() + '</body></html>'

def about_page():
    """The page that answers "who is Leon Kelvin Li". Nothing on the internet
       did before this existed, which is why the name query had nothing to
       resolve to. Every fact here is checkable and every claim is one he
       would be happy to be asked about on a call."""
    path = '/about'
    bc = [("home","/"),("about", None)]
    person = {
        "@type": "Person",
        "@id": f"{BASE}/#leon",
        "name": "Leon Kelvin Li",
        "alternateName": ["Leon Li"],
        "url": f"{BASE}/about",
        "mainEntityOfPage": {"@id": f"{BASE}/about#webpage"},
        "jobTitle": "Software Developer",
        "description": ("Independent software developer building client portals, websites, mobile apps "
                        "and connected business workflows. Works directly with clients from scope through handoff."),
        "knowsLanguage": ["en", "zh", "pt-BR", "es"],
        "knowsAbout": ["web development", "iOS development", "Android development",
                       "online ordering systems", "booking systems", "AI chatbots",
                       "business automation", "custom software"],
        "email": "leondragon3798@gmail.com",
        "telephone": "+1-510-826-7735",
        "address": {"@type": "PostalAddress", "addressRegion": "CA", "addressCountry": "US"},
        "worksFor": {"@id": f"{BASE}/#business"},
        "sameAs": IDENTITY_URLS,
    }
    profile = {
        "@type": "ProfilePage",
        "@id": f"{BASE}/about#webpage",
        "url": f"{BASE}/about",
        "name": "About Leon Kelvin Li — Software Developer",
        "description": "Leon Kelvin Li's project work, responsibilities and public professional profiles.",
        "isPartOf": {"@id": f"{BASE}/#website"},
        "mainEntity": {"@id": f"{BASE}/#leon"},
    }
    schema = [{"@context": "https://schema.org", "@graph": [profile, person]}, breadcrumb_schema(bc, path)]
    rel_me = "\n".join(f'<link rel="me" href="{e(url)}">' for url in IDENTITY_URLS)
    return head("About Leon Kelvin Li — Software Developer | Leon Builds",
        "Meet Leon Kelvin Li, a California-based independent developer who builds websites, apps and automation directly for U.S. businesses in four languages.",
        path, schema, head_extra=rel_me) + ICONS + nav() + '''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    ''' + crumbs(bc) + '''
    <p class="label">Your developer</p>
    <h1 class="dsp">Meet <span class="keepcase">Leon <em>Kelvin Li.</em></span></h1>
    <p class="sub">I build websites, apps, and automation for small businesses. You work directly with me, from the first conversation to launch.</p>
    <p class="sub">Tell me what you need in English, Chinese, Portuguese, or Spanish.</p>
  </div>
</section>

<section class="sec">
  <div class="rail two-col">
    <div>
      <p class="label">What I've built</p>
      <ul class="blist">
        <li><svg class="ic"><use href="#ic-check"/></svg><span><span class="keepcase">Curio:</span> an iOS and Android app I built, including subscriptions and release on both stores.</span></li>
        <li><svg class="ic"><use href="#ic-check"/></svg><span><span class="keepcase">ALLCPR:</span> a tool for comparing expansion areas, built from 33,772 U.S. ZIP-code records in the reviewed project dataset.</span></li>
        <li><svg class="ic"><use href="#ic-check"/></svg><span><span class="keepcase">Beasty Pages:</span> a business catalog and demo cart. Payment and kitchen progression are simulations.</span></li>
        <li><svg class="ic"><use href="#ic-check"/></svg><span>A review-reply tool that drafts responses from a business's verified facts. A person reviews and sends them.</span></li>
        <li><svg class="ic"><use href="#ic-check"/></svg><span>A Chinese-language health-education prototype with source citations and checks before answering.</span></li>
      </ul>
    </div>
    <div>
      <p class="label">How we'll work together</p>
      <ul class="blist">
        <li><svg class="ic"><use href="#ic-check"/></svg>You work directly with me.</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>We agree on a written scope and fixed price before I start. Additions are priced and approved first.</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>You review working previews along the way.</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>You receive the agreed code, accounts, data, and setup notes. Third-party services keep their own terms.</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>I recommend existing tools when they can do the job.</li>
      </ul>
    </div>
  </div>
</section>

<section class="sec">
  <div class="rail">
    <p class="label">More of my work</p>
    <p class="sub">I'm Lead Software Engineer at <span class="keepcase">LOQOL</span>, working on its existing real-estate seller portal, Charlie AI and document integrations. <a class="tlink" href="/work/loqol-seller-portal">Read about my contribution</a>, separate from the older public disclosure demo.</p>
    <p class="sub">Previously, I worked as a Software Engineer at <span class="keepcase">GOSVEA</span> on <span class="keepcase">USJOPU</span>, a learning and project platform. My GOSVEA work concluded in early October 2026.</p>
    <p class="sub">Other work includes <span class="keepcase">Curio</span>'s content automation and an interactive 3D renovation proposal for <span class="keepcase">ONPECY AI Lab</span>.</p>
    <p class="sub">I also built the <span class="keepcase">FLORES Boxing Gloves</span> website and <span class="keepcase">ONPECY</span>'s bilingual site. <a class="tlink" href="/work">Explore the projects</a>.</p>
    <p class="sub">My own app, <a class="tlink" href="https://trycurio.app/" target="_blank" rel="noopener"><span class="keepcase">Curio</span></a>, shows what I can deliver through my <a class="tlink" href="/services/mobile-apps">app development service</a>. You can also read my <a class="tlink" href="https://trycurio.app/team.html#leon" target="_blank" rel="me noopener">founder profile</a>.</p>
    <p class="sub">Need ongoing help with your website, tools, or app? <a class="tlink" href="/technical-build-partner">See how we can work together</a>.</p>
    <p class="sub" aria-label="Leon Kelvin Li public profiles">Find me on <a class="tlink" href="https://www.worldcubeassociation.org/persons/2016LILE01" target="_blank" rel="me noopener">WCA</a> · <a class="tlink" href="https://www.f6s.com/leonkelvinli" target="_blank" rel="me noopener">F6S</a> · <a class="tlink" href="https://www.linkedin.com/in/leon-kelvin-li" target="_blank" rel="me noopener">LinkedIn</a> · <a class="tlink" href="https://apps.apple.com/us/developer/leon-kelvin-li/id6781121129" target="_blank" rel="me noopener">Apple Developer</a> · <a class="tlink" href="https://www.instagram.com/lkelvn_/" target="_blank" rel="me noopener">Instagram</a>.</p>
    <div class="ctarow">
      <a class="btn btn-solid magnet" href="/quote" data-evt="about_quote_click"><span>Tell me what you need fixed</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
      <a class="btn magnet" href="https://wa.me/15108267735?text=Hi%20Leon%20-%20saw%20your%20site.%20My%20business%20is%3A%20" target="_blank" rel="noopener" data-evt="wa_click_about"><span>whatsapp</span></a>
      <a class="cx-mini" href="mailto:leondragon3798@gmail.com" data-evt="email_click">or email leon directly →</a>
    </div>
  </div>
</section>
</main>
''' + footer()

CAL_SLUG = "leonbuilds/15min"

ZH_CALL_DESCRIPTION = "免费 15 分钟，中文沟通。你说说生意里哪一块还在靠人工、哪里最费时间，Leon 会告诉你适合怎么做、大概从多少钱起，也会直说暂时不需要做系统。"

CAL_COPY = {
    "en": {
        "loading": "loading live availability…",
        "failed": "the inline calendar did not load. use the direct booking link above.",
        "booked_label": "you are booked",
        "booked": "cal.com will send the video link and calendar invitation to the email used for the booking.",
        "fallback": "calendar not showing?",
        "direct": "open the booking page directly",
        "email": "email leon",
        "call": "call (510) 826-7735",
        "unavailable": "online booking is temporarily unavailable. email leon or call (510) 826-7735.",
    },
    "pt": {
        "loading": "carregando os horários disponíveis…",
        "failed": "o calendário não carregou aqui. use o link direto acima.",
        "booked_label": "horário marcado",
        "booked": "o cal.com vai mandar o link da chamada e o convite para o e-mail usado no agendamento.",
        "fallback": "o calendário não apareceu?",
        "direct": "abrir a página de agendamento",
        "email": "mandar e-mail",
        "call": "ligar para (510) 826-7735",
        "unavailable": "o agendamento online está indisponível por enquanto. mande um e-mail ou ligue para (510) 826-7735.",
    },
    "es": {
        "loading": "cargando los horarios disponibles…",
        "failed": "el calendario no cargó aquí. usa el enlace directo de arriba.",
        "booked_label": "llamada agendada",
        "booked": "cal.com enviará el enlace de video y la invitación al correo usado para agendar.",
        "fallback": "¿no aparece el calendario?",
        "direct": "abrir la página de reservas",
        "email": "enviar un correo",
        "call": "llamar al (510) 826-7735",
        "unavailable": "las reservas en línea no están disponibles por ahora. envía un correo o llama al (510) 826-7735.",
    },
    "zh": {
        "loading": "正在加载可预约时间…",
        "failed": "日历没有成功加载，请使用上面的直接预约链接。",
        "booked_label": "预约成功",
        "booked": "cal.com 会把视频链接和日历邀请发到预约时填写的邮箱。",
        "fallback": "没有看到日历？",
        "direct": "直接打开预约页面",
        "email": "发邮件给 Leon",
        "call": "拨打 (510) 826-7735",
        "unavailable": "在线预约暂时不可用，请发邮件或拨打 (510) 826-7735。",
    },
}

# Cal.com's OFFICIAL inline embed, not a raw iframe. A raw iframe of the
# public booking URL inherits the visitor's cal.com session, so a logged-in
# user — i.e. Leon himself — sees his own bookings dashboard instead of the
# booker. The embed script renders in an isolated context and cannot.
def booker(lang="en"):
    """One instrumented Cal.com embed, shared by every booking page.

    Only the five standard UTM fields already captured by the site are forwarded.
    Arbitrary page query parameters are deliberately not forwarded: names,
    emails, or other accidental URL data must never cross into the calendar.
    """
    copy = CAL_COPY.get(lang, CAL_COPY["en"])
    if not CAL_SLUG:
        return (
            '<div class="calwrap" style="min-height:14rem;padding:2rem">'
            f'<p class="sub">{copy["unavailable"]}</p>'
            '<p class="qnote"><a href="mailto:leondragon3798@gmail.com" data-evt="calendar_email_fallback">'
            f'{copy["email"]}</a> · <a href="tel:+15108267735" data-evt="calendar_phone_fallback">'
            f'{copy["call"]}</a></p></div>'
        )

    calendar_url = f"https://cal.com/{CAL_SLUG}?redirect=false"
    template = r'''<div class="calendar-direct-row">
  <span>__FALLBACK__</span>
  <a class="btn calendar-direct" id="leon-cal-direct" href="__CAL_URL__" target="_blank" rel="noopener" data-evt="calendar_direct_fallback">__DIRECT__</a>
</div>
<div class="calwrap" id="leon-booker" aria-busy="true" style="min-height:680px;position:relative">
  <div id="leon-cal-status" role="status" style="position:absolute;inset:0;z-index:2;min-height:680px;padding:2rem;background:#f6f5f1;pointer-events:none">
    <p class="label" id="leon-cal-status-text">__LOADING__</p>
    <div aria-hidden="true" style="margin-top:2rem;display:grid;gap:1rem">
      <i style="display:block;height:3.25rem;border:1px solid #262626;border-radius:9px;background:linear-gradient(90deg,#090909,#151515,#090909)"></i>
      <i style="display:block;height:18rem;border:1px solid #202020;border-radius:9px;background:linear-gradient(135deg,#080808,#111,#080808)"></i>
      <i style="display:block;height:3.25rem;border:1px solid #262626;border-radius:9px;background:linear-gradient(90deg,#090909,#151515,#090909)"></i>
    </div>
  </div>
  <div id="leon-cal" style="min-height:680px"></div>
</div>
<div class="qok" id="bookingok" hidden tabindex="-1" aria-live="polite">
  <p class="label">__BOOKED_LABEL__</p>
  <p class="sub">__BOOKED__</p>
</div>
<p class="qnote"><a href="mailto:leondragon3798@gmail.com" data-evt="calendar_email_fallback">__EMAIL__</a> · <a href="tel:+15108267735" data-evt="calendar_phone_fallback">__CALL__</a></p>
<script>
(function(){
  var scriptNode=document.currentScript;
  var wrap=document.getElementById('leon-booker');
  var status=document.getElementById('leon-cal-status');
  var statusText=document.getElementById('leon-cal-status-text');
  var confirmation=document.getElementById('bookingok');
  var readyTracked=false,failedTracked=false,bookedTracked=false;
  var timeout;

  // Put the calendar first visually immediately, then first in the DOM once the
  // parser is done. This keeps translated pages generated by their shared
  // layout accessible without duplicating that layout here.
  var column=scriptNode&&scriptNode.closest('.callgrid > div');
  if(column){
    column.style.order='-1';
    var moveFirst=function(){
      var grid=column.parentElement;
      if(grid&&grid.classList.contains('callgrid')&&grid.firstElementChild!==column){
        grid.insertBefore(column,grid.firstElementChild);
      }
    };
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',moveFirst,{once:true});
    else moveFirst();
  }

  function track(name,extra){
    if(window.leonEvt){ window.leonEvt(name,extra); return; }
    document.addEventListener('DOMContentLoaded',function(){ if(window.leonEvt) window.leonEvt(name,extra); },{once:true});
  }
  function safeParam(value,max){
    return String(value||'').trim().replace(/[^A-Za-z0-9._~-]/g,'-').slice(0,max);
  }
  function safeSlug(value){
    var text=String(value||'').trim();
    return /^[a-z0-9][a-z0-9-]{0,63}$/.test(text)?text:'';
  }
  function sourceConfig(){
    var attr={};
    try{ attr=JSON.parse(localStorage.getItem('leon_attr')||'{}')||{}; }catch(e){}
    var query=new URLSearchParams(location.search);
    var out={layout:'month_view',theme:'light'};
    var source=safeParam(query.get('utm_source')||query.get('s')||attr.utmSource,120);
    var medium=safeParam(query.get('utm_medium')||attr.utmMedium,120);
    var campaign=safeParam(query.get('utm_campaign')||attr.utmCampaign,120);
    var term=safeParam(query.get('utm_term')||attr.utmTerm,120);
    var content=safeParam(query.get('utm_content')||attr.utmContent,120);
    if(source) out.utm_source=source;
    if(medium) out.utm_medium=medium;
    if(campaign) out.utm_campaign=campaign;
    if(term) out.utm_term=term;
    if(content) out.utm_content=content;
    return out;
  }
  function ready(){
    clearTimeout(timeout);
    wrap.setAttribute('aria-busy','false');
    status.hidden=true;
    if(!readyTracked){ readyTracked=true; track('calendar_ready'); }
  }
  function failed(){
    clearTimeout(timeout);
    wrap.setAttribute('aria-busy','false');
    statusText.textContent='__FAILED__';
    if(!failedTracked){ failedTracked=true; track('calendar_failed'); }
  }
  function booked(payload){
    ready();
    confirmation.hidden=false;
    var data=payload&&payload.detail&&payload.detail.data;
    var rawUid=data&&(data.uid||(data.booking&&data.booking.uid));
    var bookingUid=String(rawUid||'').trim();
    if(!/^[A-Za-z0-9._~-]{8,64}$/.test(bookingUid)){
      track('calendar_booking_uid_missing');
    }else if(!bookedTracked){
      var extra={bookingUid:bookingUid};
      var query=new URLSearchParams(location.search);
      var service=safeSlug(query.get('service'));
      var packageName=safeSlug(query.get('package'));
      if(service) extra.service=service;
      if(packageName) extra.package=packageName;
      bookedTracked=true;
      track('calendar_booking_success',extra);
    }
    try{ confirmation.focus({preventScroll:true}); }catch(e){ confirmation.focus(); }
    confirmation.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
  }

  (function(C,A,L){var p=function(a,ar){a.q.push(ar)};var d=C.document;
    C.Cal=C.Cal||function(){var cal=C.Cal;var ar=arguments;if(!cal.loaded){cal.ns={};cal.q=cal.q||[];
    d.head.appendChild(d.createElement('script')).src=A;cal.loaded=true}
    if(ar[0]===L){var api=function(){p(api,arguments)};var ns=ar[1];api.q=api.q||[];
    if(typeof ns==='string'){cal.ns[ns]=cal.ns[ns]||api;p(cal.ns[ns],ar);p(cal,['initNamespace',ns])}
    else p(cal,ar);return}p(cal,ar)}})(window,'https://app.cal.com/embed/embed.js','init');

  var calConfig=sourceConfig();
  var direct=document.getElementById('leon-cal-direct');
  if(direct){
    try{
      var directUrl=new URL(direct.href);
      ['utm_source','utm_medium','utm_campaign','utm_term','utm_content'].forEach(function(key){
        if(calConfig[key]) directUrl.searchParams.set(key,calConfig[key]);
      });
      direct.href=directUrl.toString();
    }catch(e){}
  }
  Cal('init','leon15',{origin:'https://app.cal.com'});
  Cal.ns.leon15('on',{action:'linkReady',callback:ready});
  Cal.ns.leon15('on',{action:'bookerReady',callback:ready});
  Cal.ns.leon15('on',{action:'linkFailed',callback:failed});
  Cal.ns.leon15('on',{action:'bookingSuccessfulV2',callback:booked});
  Cal.ns.leon15('inline',{elementOrSelector:'#leon-cal',config:calConfig,calLink:'__CAL_SLUG__'});
  Cal.ns.leon15('ui',{theme:'light',hideEventTypeDetails:false,layout:'month_view'});
  var embedScript=document.querySelector('script[src="https://app.cal.com/embed/embed.js"]');
  if(embedScript) embedScript.addEventListener('error',failed,{once:true});
  timeout=setTimeout(failed,15000);
})();
</script>'''
    replacements = {
        "__LOADING__": copy["loading"],
        "__FAILED__": copy["failed"],
        "__BOOKED_LABEL__": copy["booked_label"],
        "__BOOKED__": copy["booked"],
        "__FALLBACK__": copy["fallback"],
        "__DIRECT__": copy["direct"],
        "__EMAIL__": copy["email"],
        "__CALL__": copy["call"],
        "__CAL_URL__": calendar_url,
        "__CAL_SLUG__": CAL_SLUG,
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template



def call_page():
    """Book a 15-minute call with a visible, instrumented calendar and fallbacks."""
    path = '/call'
    bc = [("home","/"),("book a call", None)]
    schema = [breadcrumb_schema(bc, path), {
        "@context": "https://schema.org", "@type": "Service",
        "name": "Free 15-minute call with Leon",
        "provider": {"@id": f"{BASE}/#leon"},
        "areaServed": {"@type": "Country", "name": "United States"},
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "A free 15-minute call with Leon to discuss your project, a practical next step, and a starting budget.",
    }]
    booker_html = booker("en")
    call_alts = ''.join(
        f'<link rel="alternate" hreflang="{hl}" href="{BASE}{href}">'
        for hl, href in lang_pages.call_alternates())
    return head("Book a Free 15-Minute Call | Leon Builds",
        "Talk directly with Leon about your website, app, or a task you want to automate. A free 15-minute call to discuss the next step and a starting budget.",
        path, schema, call_alts).replace('<body>', '<body class="call-page" data-assistant-launcher="hidden">', 1) + ICONS + nav() + '''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    ''' + crumbs(bc) + '''
    <p class="label" id="call-context-label">Free call with Leon</p>
    <h1 class="dsp" id="call-context-title">Book a free <em>15-minute call</em></h1>
    <p class="sub" id="call-context-intro">Tell me about your website, app, or a task you want to automate. I'll help you work out the next step and a starting budget.</p>
    <p class="pricetag" id="call-context-price">Free · 15 minutes · weekday availability, Pacific time · directly with Leon</p>
  </div>
</section>

<section class="sec">
  <div class="rail">
    <div class="callgrid">
    <div>
      ''' + booker_html + '''
    </div>
    <div>
      <p class="label" id="call-context-agenda">what happens on the call</p>
      <ul class="blist">
        <li><svg class="ic"><use href="#ic-check"/></svg>Tell me what you want to build or improve.</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>I'll ask about the tools you use and what needs to change.</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>We'll discuss a practical next step and starting budget.</li>
        <li><svg class="ic"><use href="#ic-check"/></svg>I'll tell you if an existing tool would solve it.</li>
      </ul>
      <p class="sub">We can speak English, Spanish, Portuguese, or Chinese.</p>
    </div>
    </div>
  </div>
</section>
</main>
<script>
(function(){
  var params=new URLSearchParams(location.search);
  var service=params.get('service')||'';
  var packageName=params.get('package')||'';
  var label=document.getElementById('call-context-label');
  var title=document.getElementById('call-context-title');
  var intro=document.getElementById('call-context-intro');
  var price=document.getElementById('call-context-price');
  var agenda=document.getElementById('call-context-agenda');
  function trackContext(name,extra){
    if(window.leonEvt){ window.leonEvt(name,extra); return; }
    document.addEventListener('DOMContentLoaded',function(){
      if(window.leonEvt) window.leonEvt(name,extra);
    },{once:true});
  }
  if(service==='contractor-lead-recovery'){
    document.body.classList.add('contractor-call-context');
    document.title='Book a Contractor Website Review | Leon Builds';
    if(label) label.textContent='Contractor website + follow-up review';
    if(title) title.innerHTML='Book a free <em>15-minute website review</em>';
    if(intro) intro.textContent='Show me your current contractor website and how customers request an estimate. I will help you decide whether the $1,500 website and follow-up package fits.';
    if(price) price.textContent='Free · 15 minutes · weekday availability, Pacific time · directly with Leon';
    if(agenda) agenda.textContent='What happens in the contractor review';
    trackContext('call_context_contractor',{service:'contractor-lead-recovery'});
  }else if(service==='technical-build-partner'){
    document.body.classList.add('technical-partner-call-context');
    document.title='Discuss Your Website, App or Automation | Leon Builds';
    if(label) label.textContent='Your website, app, or automation project';
    if(title) title.innerHTML='Book a free <em>15-minute project call</em>';
    if(intro) intro.textContent='Tell me what you want to build or improve. We can discuss your website, app, or repeat tasks and decide on a practical next step.';
    if(price) price.textContent='Free · 15 minutes · weekday availability, Pacific time · directly with Leon';
    if(agenda) agenda.textContent='What happens on the call';
    if(packageName==='systems-plan'){
      if(label) label.textContent='Discuss the $199 Systems Plan';
      if(intro) intro.textContent='Tell me what you want to improve. I will confirm whether a 45-minute working session and written Systems Plan would help before you pay for it.';
    }
    var context={service:'technical-build-partner'};
    if(/^(systems-plan|focused-build-sprint|ongoing-technical-partner)$/.test(packageName)) context.package=packageName;
    trackContext('call_context_technical_partner',context);
  }
})();
</script>
''' + footer()

def quote_page():
    path = '/quote'
    bc = [("home","/"),("get a quote", None)]
    schema = [breadcrumb_schema(bc, path)]
    page_head = head("Get a Fixed Quote | Leon Builds",
        "Tell Leon what you need fixed. Share your idea or business problem and get a practical next step by email.",
        path, schema).replace('<body>', '<body class="quote-page" data-assistant-launcher="hidden">', 1)
    return page_head + ICONS + nav() + '''
<main id="main">
<section class="sec page-hero">
  <div class="rail">
    ''' + crumbs(bc) + '''
    <p class="label" id="quote-context-label">Tell me about your project</p>
    <h1 class="dsp" id="quote-context-title">Tell me what you <em>need fixed.</em></h1>
    <p class="sub business-copy" id="quote-context-intro">Describe what you want to build or improve. I'll reply by email with a practical next step. No technical brief needed.</p>
  </div>
</section>
<section class="sec">
  <div class="rail">
    <form class="qform" id="qform" method="post" action="/quote" novalidate aria-describedby="qnote">
      <label>Business website <i>(optional if it is not live)</i><input name="websiteUrl" type="text" inputmode="url" autocomplete="url" maxlength="300" placeholder="yourbusiness.com"></label>
      <label><span id="quote-problem-label">What are you trying to fix or build?</span> <i>(required)</i><textarea name="problem" rows="4" required placeholder="The task that is still manual, the thing that is broken, or what you wish existed…"></textarea></label>
      <label>Email <i>(required)</i><input name="email" type="email" required autocomplete="email" inputmode="email" placeholder="Where I should reply"></label>
      <button class="btn btn-solid magnet qsend" type="submit"><span>Send my project details</span><svg class="ic"><use href="#ic-arrow"/></svg></button>
      <noscript><p class="qnote">This form needs JavaScript to submit safely. <a href="mailto:leondragon3798@gmail.com">Email Leon</a> or <a href="tel:+15108267735">call (510) 826-7735</a>.</p></noscript>
      <p class="qnote" id="qnote">No payment or commitment. Your message comes directly to me. Scope and price are agreed before work begins. Prefer another route? <a href="https://wa.me/15108267735?text=Hi%20Leon%20-%20saw%20your%20site.%20My%20business%20is%3A%20" target="_blank" rel="noopener" data-evt="wa_click_quote">WhatsApp</a> · <a href="mailto:leondragon3798@gmail.com" data-evt="quote_manual_email">Email Leon</a> · <a href="tel:+15108267735" data-evt="phone_click">Call Leon</a></p>
      <details>
        <summary>Add project details <i>(optional)</i></summary>
        <div style="display:grid;gap:1.1rem;margin-top:1.1rem">
          <label>Name <i>(optional)</i><input name="name" type="text" autocomplete="name"></label>
          <label>what does your business do?<input name="company" type="text" placeholder="two taquerias in dallas / a plumbing company / a dental office…"></label>
          <label>what do you currently use for it?<input name="currentTools" type="text" placeholder="paper + phone / spreadsheets / quickbooks / square / nothing…"></label>
          <label>what result would make this worth paying for?<input name="desiredOutcome" type="text" placeholder="phone stops ringing about status / orders without commission / one less hire…"></label>
          <div class="qrow">
            <label>when do you want to start?
              <select name="timeline"><option value="">choose…</option><option>as soon as possible</option><option>within a month</option><option>next few months</option><option>just exploring</option></select>
            </label>
            <label>rough budget <i>(optional)</i>
              <select name="budget"><option value="">need guidance</option><option>under $1,000 — focused site or fix</option><option>$1,000–$3,500</option><option>$3,500–$7,500</option><option>$7,500–$15,000</option><option>$15,000+</option></select>
            </label>
          </div>
          <label>phone <i>(optional)</i><input name="phone" type="tel" autocomplete="tel"></label>
        </div>
      </details>
      <input name="service" type="hidden" value="">
      <input name="package" type="hidden" value="">
      <input name="website" type="text" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">
      <p class="qerr" id="qerr" role="alert" aria-live="polite"></p>
      <div id="qfail" hidden role="alert">
        <p class="sub">the site did not accept that request. your answers are still here. <a id="qmail" href="mailto:leondragon3798@gmail.com" data-evt="quote_manual_email">open a prepared email</a>, then hit send in your email app; or use whatsapp or phone below.</p>
      </div>
    </form>
    <div class="qok" id="qok" hidden tabindex="-1" role="region" aria-labelledby="qok-title">
      <span class="qok-mark" aria-hidden="true">✓</span>
      <p class="label" role="status" aria-live="assertive" aria-atomic="true">project sent</p>
      <h2 class="dsp" id="qok-title">Your project was <em>sent to Leon Builds.</em></h2>
      <p class="sub">Your request was saved. I'll reply to the email you provided.</p>
      <p class="qreceipt">Submission receipt: <code id="qreceipt"></code></p>
      <div class="ctarow">
        <a class="btn btn-solid magnet" id="quote-book-call" href="/call" data-evt="quote_to_calendar"><span>Book the free 15-minute call</span><svg class="ic"><use href="#ic-arrow"/></svg></a>
        <a class="btn magnet" href="/work"><span>See my work</span></a>
      </div>
    </div>
  </div>
</section>
</main>
<script>
(function(){
  var f=document.getElementById('qform'),err=document.getElementById('qerr'),fail=document.getElementById('qfail'),ok=document.getElementById('qok');
  if(!f)return;
  var API=(window.LEON_ASSIST&&window.LEON_ASSIST.api)||(/^(localhost|127\\.0\\.0\\.1)$/.test(location.hostname)?'http://localhost:8787':'https://leon-assist.onrender.com');
  var button=f.querySelector('button[type="submit"]'),buttonText=button.querySelector('span');
  var manual=document.getElementById('qmail'),receipt=document.getElementById('qreceipt'),bookCall=document.getElementById('quote-book-call');
  var started=false,submitting=false,submissionKey='',attemptStorage='leon_quote_attempt_v1';
  var service=(new URLSearchParams(location.search)).get('service')||'';
  var packageName=(new URLSearchParams(location.search)).get('package')||'';
  var contractorReview=service==='contractor-lead-recovery';
  var technicalPartner=service==='technical-build-partner';
  if(!technicalPartner||!/^(systems-plan|focused-build-sprint|ongoing-technical-partner)$/.test(packageName)) packageName='';
  var idleButtonText=contractorReview?'Request the 3-point review':'Send my project details';
  if(contractorReview){
    f.elements.service.value=service;
    document.getElementById('quote-context-label').textContent='Free contractor website review';
    document.getElementById('quote-context-title').innerHTML='Send your current website for a <em>3-point review.</em>';
    document.getElementById('quote-context-intro').textContent='Share the URL and the biggest issue you see. I will reply with three specific observations and a practical next step. No payment or commitment.';
    document.getElementById('quote-problem-label').textContent='What is the biggest lead problem?';
    f.elements.problem.placeholder='Estimate requests get lost, the mobile form is hard to use, or another specific issue…';
    buttonText.textContent=idleButtonText;
  }else if(technicalPartner){
    f.elements.service.value=service;
    f.elements.package.value=packageName;
    document.getElementById('quote-context-label').textContent='Website, app, or automation project';
    document.getElementById('quote-context-title').innerHTML='What would you like to <em>build or improve?</em>';
    document.getElementById('quote-context-intro').textContent='Tell me about your business and what you need. I will reply by email with a recommended next step. Requesting a quote is free, and you do not need a technical brief.';
    document.getElementById('quote-problem-label').textContent='What would you like to build or improve?';
    f.elements.problem.placeholder='A new website, automatic replies to inquiries, a dashboard for the team, an app idea, or something else…';
    if(packageName==='systems-plan'){
      document.getElementById('quote-context-label').textContent='$199 Systems Plan';
      document.getElementById('quote-context-title').innerHTML='Start with a <em>written technical plan.</em>';
      document.getElementById('quote-context-intro').textContent='Describe what you want to improve and any tools you use today. I will confirm whether the 45-minute working session and written plan would help before you pay.';
      document.getElementById('quote-problem-label').textContent='What would you like help planning?';
      f.elements.problem.placeholder='A task takes too much time, your tools do not connect, or you need help deciding how to build an idea…';
      buttonText.textContent='Ask to start the Systems Plan';
      idleButtonText='Ask to start the Systems Plan';
    }else if(packageName==='focused-build-sprint'){
      document.getElementById('quote-context-label').textContent='One-time project · from $1,500';
      document.getElementById('quote-context-title').innerHTML='What should I <em>build first?</em>';
      document.getElementById('quote-context-intro').textContent='Describe the part of your project you want built first. I will reply with what is included, how I will check it works, the price, and the timeline.';
      document.getElementById('quote-problem-label').textContent='What is the first part of the project you want built?';
      f.elements.problem.placeholder='A lead form that reaches the right person, an internal dashboard, one app workflow, or another testable result…';
      idleButtonText='Discuss this project';
    }else if(packageName==='ongoing-technical-partner'){
      document.getElementById('quote-context-label').textContent='Ongoing partner · from $2,000/month';
      document.getElementById('quote-context-title').innerHTML='Pick your first <em>monthly priority.</em>';
      document.getElementById('quote-context-intro').textContent='Share what you want to build or improve each month, along with any maintenance or fixes you need. I will propose an agreed monthly scope; this is not unlimited development.';
      document.getElementById('quote-problem-label').textContent='What would you like help with each month, and what should come first?';
      f.elements.problem.placeholder='Ship one milestone while keeping the current site, automations, or app stable…';
      idleButtonText='Discuss ongoing support';
    }
    buttonText.textContent=idleButtonText;
  }
  if(bookCall&&service){
    bookCall.href='/call?service='+encodeURIComponent(service)+(packageName?'&package='+encodeURIComponent(packageName):'');
  }
  function track(name,extra){
    var details=extra||{};
    if(service) details.service=service;
    if(packageName) details.package=packageName;
    if(window.leonEvt) window.leonEvt(name,details);
  }
  function fingerprint(d){
    var raw=['service','package','websiteUrl','problem','email','name','company','currentTools','desiredOutcome','timeline','budget','phone']
      .map(function(k){return String(d[k]||'');}).join('\\u001f');
    var hash=2166136261;
    for(var i=0;i<raw.length;i++){hash^=raw.charCodeAt(i);hash=Math.imul(hash,16777619);}
    return 'v1_'+(hash>>>0).toString(16);
  }
  function submissionKeyFor(d){
    var fp=fingerprint(d),saved={};
    try{saved=JSON.parse(sessionStorage.getItem(attemptStorage)||'{}')||{};}catch(e){}
    if(saved.fingerprint===fp&&/^leadreq_[A-Za-z0-9-]{16,80}$/.test(saved.key||'')) return saved.key;
    var key='leadreq_'+((window.crypto&&crypto.randomUUID)?crypto.randomUUID():String(Date.now())+'-'+Math.random().toString(16).slice(2));
    try{sessionStorage.setItem(attemptStorage,JSON.stringify({key:key,fingerprint:fp}));}catch(e){}
    return key;
  }
  f.addEventListener('input',function(ev){
    if(!started){ started=true; track('quote_form_start'); }
    if(ev.target&&ev.target.removeAttribute) ev.target.removeAttribute('aria-invalid');
  },{once:false});
  f.addEventListener('submit',async function(ev){
    ev.preventDefault();
    if(submitting)return;
    track('quote_submit_attempt');
    err.textContent=''; fail.hidden=true;
    var d=Object.fromEntries(new FormData(f).entries());
    Object.keys(d).forEach(function(k){ if(typeof d[k]==='string') d[k]=d[k].trim(); });
    var invalid=null;
    if(!d.problem){ err.textContent='Please describe what you need.'; invalid=f.elements.problem; }
    else if(!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(d.email||'')){ err.textContent='that email does not look right.'; invalid=f.elements.email; }
    if(invalid){
      invalid.setAttribute('aria-invalid','true');
      invalid.focus();
      track('quote_validation_failed');
      return;
    }
    submissionKey=submissionKeyFor(d);
    d.idempotencyKey=submissionKey;
    var attr={}; try{attr=JSON.parse(localStorage.getItem('leon_attr')||'{}')}catch(e){}
    d.via='quote-form'; d.sourcePage=location.pathname; d.referrer=attr.referrer||'';
    d.utmSource=attr.utmSource||''; d.utmMedium=attr.utmMedium||''; d.utmCampaign=attr.utmCampaign||''; d.utmTerm=attr.utmTerm||''; d.utmContent=attr.utmContent||'';
    d.gclid=attr.gclid||''; d.gbraid=attr.gbraid||''; d.wbraid=attr.wbraid||''; d.fbclid=attr.fbclid||''; d.msclkid=attr.msclkid||'';
    d.firstPage=(attr.first&&attr.first.page)||attr.firstPage||'/';
    d.firstReferrer=(attr.first&&attr.first.referrer)||'';
    d.firstUtmSource=(attr.first&&attr.first.utmSource)||'';
    d.firstUtmMedium=(attr.first&&attr.first.utmMedium)||'';
    d.firstUtmCampaign=(attr.first&&attr.first.utmCampaign)||'';
    d.firstUtmTerm=(attr.first&&attr.first.utmTerm)||'';
    d.firstUtmContent=(attr.first&&attr.first.utmContent)||'';
    d.firstGclid=(attr.first&&attr.first.gclid)||'';
    d.firstGbraid=(attr.first&&attr.first.gbraid)||'';
    d.firstWbraid=(attr.first&&attr.first.wbraid)||'';
    d.firstFbclid=(attr.first&&attr.first.fbclid)||'';
    d.firstMsclkid=(attr.first&&attr.first.msclkid)||'';
    d.lastPage=(attr.last&&attr.last.page)||location.pathname;
    d.lastReferrer=(attr.last&&attr.last.referrer)||attr.referrer||'';
    d.lastUtmSource=(attr.last&&attr.last.utmSource)||attr.utmSource||'';
    d.lastUtmMedium=(attr.last&&attr.last.utmMedium)||attr.utmMedium||'';
    d.lastUtmCampaign=(attr.last&&attr.last.utmCampaign)||attr.utmCampaign||'';
    d.lastUtmTerm=(attr.last&&attr.last.utmTerm)||attr.utmTerm||'';
    d.lastUtmContent=(attr.last&&attr.last.utmContent)||attr.utmContent||'';
    d.lastGclid=(attr.last&&attr.last.gclid)||attr.gclid||'';
    d.lastGbraid=(attr.last&&attr.last.gbraid)||attr.gbraid||'';
    d.lastWbraid=(attr.last&&attr.last.wbraid)||attr.wbraid||'';
    d.lastFbclid=(attr.last&&attr.last.fbclid)||attr.fbclid||'';
    d.lastMsclkid=(attr.last&&attr.last.msclkid)||attr.msclkid||'';
    try{ d.analyticsSessionId=sessionStorage.getItem('leon_analytics_session')||''; }catch(e){ d.analyticsSessionId=''; }
    submitting=true; button.disabled=true; button.setAttribute('aria-busy','true'); buttonText.textContent='sending…';
    var controller=window.AbortController?new AbortController():null;
    var timer=controller?setTimeout(function(){controller.abort();},35000):null;
    try{
      var options={method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)};
      if(controller) options.signal=controller.signal;
      var response=await fetch(API+'/api/lead',options);
      var result={}; try{result=await response.json();}catch(e){}
      if(!response.ok||result.ok!==true) throw new Error('lead rejected');
      var receiptId=String(result.receiptId||'');
      if(!/^lead_[A-Za-z0-9-]{16,}$/.test(receiptId)) throw new Error('missing receipt');
      receipt.textContent=receiptId;
      f.hidden=true; ok.hidden=false;
      track('quote_lead_accepted',{receipt:receiptId});
      try{ ok.focus({preventScroll:true}); }catch(e){ ok.focus(); }
      ok.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
    }catch(e){
      manual.href=mailtoFor(d);
      fail.hidden=false;
      err.textContent='that did not send through the site.';
      track('quote_lead_failed');
      try{ fail.scrollIntoView({behavior:'smooth',block:'center'}); }catch(ignore){}
    }finally{
      if(timer)clearTimeout(timer);
      submitting=false; button.disabled=false; button.removeAttribute('aria-busy'); buttonText.textContent=idleButtonText;
    }
  });
  function line(label,val){ return val&&String(val).trim() ? label+': '+String(val).trim()+'\\n' : ''; }
  function mailtoFor(d){
    var body=''
      + line('name',d.name)
      + line('email',d.email)
      + line('phone',d.phone)
      + line('business',d.company)
      + line('website',d.websiteUrl)
      + line('package',d.package)
      + line('currently using',d.currentTools)
      + line('timeline',d.timeline)
      + line('budget',d.budget)
      + '\\nwhat i need:\\n' + String(d.problem||'').trim() + '\\n'
      + (d.desiredOutcome ? '\\nwhat would make it worth paying for:\\n'+String(d.desiredOutcome).trim()+'\\n' : '')
      + '\\n— sent from leonbuilds.org'+(d.sourcePage&&d.sourcePage!=='/quote'?' ('+d.sourcePage+')':'');
    if(body.length>1600) body=body.slice(0,1600)+'\\n…';
    var subject=(d.service==='contractor-lead-recovery'?'contractor website review':(d.package==='systems-plan'?'Systems Plan inquiry':(d.service==='technical-build-partner'?'technical build partner inquiry':'project inquiry')))+(d.company?' — '+String(d.company).trim():(d.name?' — '+String(d.name).trim():''));
    return 'mailto:leondragon3798@gmail.com?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
  }
})();
</script>''' + footer() + '</body></html>'

# ══════════════════════════════════════════════════════════════════
# EMIT
# ══════════════════════════════════════════════════════════════════

def w(rel, content):
    """Write generated content only when its bytes actually changed."""
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    old = None
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            old = f.read()
    if old == content:
        return
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    print('wrote', rel)

# ── language service pages ────────────────────────────────────────
# The one thing an agency cannot copy: the developer speaks the language the
# owner explains the problem in. Copy is native, never translated, and lives
# in data/lang_pages.json.
import lang_pages

# Keep the localized call metadata in the same generator path as its page.
# The long-form translation table remains owned by tools/lang_pages.py.
lang_pages.CALL_COPY["zh"]["desc"] = ZH_CALL_DESCRIPTION

LANG_COPY = {}
_copy_path = os.path.join(ROOT, 'content', 'lang_pages.json')
if os.path.exists(_copy_path):
    with open(_copy_path, encoding='utf-8') as f:
        for row in json.load(f)['pages']:
            LANG_COPY[(row['lang'], row['service'])] = row['page']

def _siblings(lang, key):
    return [(k, LANG_COPY[(lang, k)]) for (l, k) in LANG_COPY
            if l == lang and k != key]

LANG_CTX = dict(e=e, BASE=BASE, FONTS=FONTS, ICONS=ICONS, siblings=_siblings)

# Reciprocal hreflang for the English pages that now have translations. Built
# from the same SLUGS table the language pages use, so the two sides cannot
# drift into a one-way cluster Google throws away.
EN_ALTS = {}
for _key, _en in lang_pages.EN_COUNTERPART.items():
    if not any(l for (l, k) in LANG_COPY if k == _key):
        continue
    _tags = [f'<link rel="alternate" hreflang="en" href="{BASE}{_en}">']
    for _code in ['pt', 'es', 'zh']:
        if (_code, _key) in LANG_COPY:
            _hl = lang_pages.LANGS[_code]['hreflang']
            _tags.append(f'<link rel="alternate" hreflang="{_hl}" '
                         f'href="{BASE}/{_code}/{lang_pages.SLUGS[(_code, _key)]}">')
    _tags.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}{_en}">')
    EN_ALTS[_en.rsplit("/", 1)[-1]] = ''.join(_tags)


for s in SERVICES: w(f'services/{s["slug"]}.html', service_page(s))
for i in INDUSTRIES: w(f'industries/{i["slug"]}.html', industry_page(i))

w('services/index.html', listing_page('services', SERVICES,
  "Services — Websites, Apps, AI & Automation | Leon Builds",
  "Every service we build, with honest starting prices: websites, mobile apps, AI chatbots and phone agents, automation, portals, dashboards and more.",
  "every price is a published floor, not a quote. most jobs turn out to be two or three of these stitched together — describe the problem and we'll quote the shape of it."))

w('industries/index.html', listing_page('industries', INDUSTRIES,
  "Industries We Build Software For | Leon Builds",
  "Software, AI and automation shaped for restaurants, contractors, auto shops, clinics, real estate, logistics, gyms, retail, firms and startups.",
  "the problems repeat inside an industry — the fixes below come from systems already running, not a template's guess. don't see yours? that's what custom means."))

LANG_URLS = []
for (lang, key), page in sorted(LANG_COPY.items()):
    slug = lang_pages.SLUGS[(lang, key)]
    w(f'{lang}/{slug}.html', lang_pages.render(lang, key, page, LANG_CTX))
    LANG_URLS.append(f'/{lang}/{slug}')

# The booking page in each language. The English /call is where a translated
# funnel used to end: three paragraphs in Portuguese, then a wall of English at
# the moment of deciding. Same Cal.com embed, translated page around it.
for _lang in sorted(lang_pages.CALL_COPY):
    _c = lang_pages.CALL_COPY[_lang]
    w(f"{_lang}/{_c['slug']}.html", lang_pages.render_call(_lang, booker(_lang), LANG_CTX))
    LANG_URLS.append(f"/{_lang}/{_c['slug']}")

# Refill the link block on each language home so the service pages are not
# orphans. Sentinels live in the hand-written homes; everything between them
# is generated, everything around them is Leon's own copy.
for _lang in sorted({l for (l, _k) in LANG_COPY}):
    _p = os.path.join(ROOT, _lang, 'index.html')
    if not os.path.exists(_p):
        continue
    with open(_p, encoding='utf-8') as f:
        _s = f.read()
    _links = ''.join(
        f'<a href="/{_lang}/{lang_pages.SLUGS[(_lang, k)]}">'
        f'{e(LANG_COPY[(_lang, k)]["h1_plain"])} {e(LANG_COPY[(_lang, k)]["h1_em"])}</a>'
        for k in ['websites', 'ordering', 'automation'] if (_lang, k) in LANG_COPY)
    _a, _b = '<!-- LANGSERVICES:START -->', '<!-- LANGSERVICES:END -->'
    if _a in _s and _b in _s:
        _pre, _rest = _s.split(_a, 1)
        _mid, _post = _rest.split(_b, 1)
        _new = _pre + _a + _links + _b + _post
        # The localized homes are hand-written, but their generated link block
        # is also the safe point where global brand chrome is synchronized.
        # Keep the culturally written CTA copy; only normalize the shared brand
        # and remove the obsolete custom-cursor element.
        _new = _new.replace(
            '<span class="mark-name">Leon Kelvin Li</span>\n'
            '    <span class="mark-handle">/ Leon Builds</span>',
            '<span class="mark-name">Leon Builds</span>\n'
            '    <span class="mark-handle">by Leon Kelvin Li</span>',
        )
        _new = _new.replace(
            '<div class="cursor" id="cursor" aria-hidden="true"><span></span></div>\n',
            '',
        )
        _new = _new.replace('aria-label="menu"', 'aria-label="Open menu"')
        if _new != _s:
            with open(_p, 'w', encoding='utf-8') as f:
                f.write(_new)
            print('relinked', _lang + '/index.html')

# The hand-written homepage keeps one generated testimonial slot. The slot is
# empty by default and can contain only records released by testimonial_gate.py.
_home_path = os.path.join(ROOT, 'index.html')
with open(_home_path, encoding='utf-8') as _home_file:
    _home_source = _home_file.read()
_home_start = '<!-- TESTIMONIALS:START -->'
_home_end = '<!-- TESTIMONIALS:END -->'
if _home_start not in _home_source or _home_end not in _home_source:
    raise RuntimeError('homepage testimonial release sentinels are missing')
_home_pre, _home_rest = _home_source.split(_home_start, 1)
_home_old, _home_post = _home_rest.split(_home_end, 1)
_home_block = homepage_testimonial_section()
_home_new = _home_pre + _home_start + '\n' + _home_block + '\n' + _home_end + _home_post

def _replace_home_slot(source, start, end, block, label, indent=''):
    if start not in source or end not in source:
        raise RuntimeError(f'homepage {label} release sentinels are missing')
    before, rest = source.split(start, 1)
    _old, after = rest.split(end, 1)
    rendered_block = indent + block if block else ''
    return before + start + '\n' + rendered_block + '\n' + indent + end + after


_home_reviews_href = '/reviews' if REVIEWS_ROUTE_ENABLED else '#testimonials'
_home_nav_block = (
    f'<a href="{_home_reviews_href}"><i>[</i><span>Reviews</span><i>]</i></a>'
    if REVIEWS_PUBLISHED else ''
)
_home_footer_block = (
    f'<a href="{_home_reviews_href}">Client reviews</a>'
    if REVIEWS_PUBLISHED else ''
)
_home_new = _replace_home_slot(
    _home_new,
    '<!-- TESTIMONIAL-NAV:START -->',
    '<!-- TESTIMONIAL-NAV:END -->',
    _home_nav_block,
    'testimonial navigation',
    '    ',
)
_home_new = _replace_home_slot(
    _home_new,
    '<!-- TESTIMONIAL-FOOTER:START -->',
    '<!-- TESTIMONIAL-FOOTER:END -->',
    _home_footer_block,
    'testimonial footer',
)
w('index.html', _home_new)

w('quote.html', quote_page())
w('about.html', about_page())
w('call.html', call_page())
w('work.html', work_page())
for case in CASE_STUDIES:
    w(f'work/{case["slug"]}.html', case_study_page(case))
if REVIEWS_ROUTE_ENABLED:
    w('reviews.html', reviews_page())
w('missed-lead-recovery.html', missed_lead_recovery_page())
w('technical-build-partner.html', technical_partner_page())
w('guides/contractor-inquiry-workflow.html', contractor_inquiry_guide_page())
w('guides/website-builder-or-custom-software.html', buyer_decision_guide_page())

# sitemap + robots
urls = ['/', '/about', '/call', '/work'] + [f'/work/{case["slug"]}' for case in CASE_STUDIES] \
     + ['/guides/contractor-inquiry-workflow', '/guides/website-builder-or-custom-software', '/missed-lead-recovery', '/technical-build-partner', '/quote', '/privacy', '/es', '/pt', '/zh', '/services/'] + [f'/services/{s["slug"]}' for s in SERVICES] \
     + ['/industries/'] + [f'/industries/{i["slug"]}' for i in INDUSTRIES]\
     + LANG_URLS
if REVIEWS_ROUTE_ENABLED:
    urls.append('/reviews')
assert_publication_paths(urls)
validate_topics(paths=urls)

# A sitemap date means "this URL's content changed", not "the sitemap builder ran".
# The old builder stamped TODAY on all forty URLs whenever one page changed, making
# the freshness signal useless to a crawler. A working-tree change is from today;
# otherwise Git supplies the last commit date for that page. This also avoids a file
# copy or no-op generator run making an old page look new.
def url_output(url):
    if url == '/':
        return 'homepage/index.html'
    # Language homes intentionally use /es, /pt and /zh without trailing slashes.
    # Resolve any route backed by a directory before asking Git for its lastmod;
    # otherwise every generator run falsely stamps those unchanged homes as today.
    if not url.endswith('/') and os.path.isfile(os.path.join(ROOT, url.strip('/') + '.html')):
        return url.strip('/') + '.html'
    if url.endswith('/') or os.path.isdir(os.path.join(ROOT, url.strip('/'))):
        return url.strip('/') + '/index.html'
    return url.strip('/') + '.html'

def committed_sitemap_dates():
    """Keep an unchanged page's published date across merges and rebuilds."""
    result = subprocess.run(['git', 'show', 'HEAD:sitemap.xml'], cwd=ROOT,
                            capture_output=True, text=True)
    if result.returncode:
        return {}
    try:
        root = ET.fromstring(result.stdout)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        return {row.findtext('sm:loc', namespaces=ns): row.findtext('sm:lastmod', namespaces=ns)
                for row in root.findall('sm:url', ns)}
    except ET.ParseError:
        return {}


SITEMAP_DATES = committed_sitemap_dates()


def url_lastmod(url):
    rel = url_output(url)
    page = os.path.join(ROOT, rel)
    if not os.path.exists(page):
        return TODAY
    dirty = subprocess.run(
        ['git', 'status', '--porcelain', '--', rel], cwd=ROOT,
        check=True, capture_output=True, text=True).stdout.strip()
    if dirty:
        return TODAY
    prior = SITEMAP_DATES.get(BASE + url)
    if prior:
        return prior
    committed = subprocess.run(
        ['git', 'log', '-1', '--format=%cs', '--', rel], cwd=ROOT,
        check=True, capture_output=True, text=True).stdout.strip()
    return committed or TODAY

sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    sm += f'  <url><loc>{BASE}{u}</loc><lastmod>{url_lastmod(u)}</lastmod></url>\n'
sm += '</urlset>\n'
w('sitemap.xml', sm)
w('robots.txt', f'User-agent: *\n'
    '# Keep personal founder portraits out of search results, including older versions.\n'
    'Disallow: /images/leon-kelvin-li\nAllow: /\n\n'
    f'Sitemap: {BASE}/sitemap.xml\n')

print(f'\n{len(SERVICES)} service pages, {len(INDUSTRIES)} industry pages, 2 indexes, work, '
      f'{len(CASE_STUDIES)} case studies, contractor inquiry guide, '
      f'{"reviews, " if REVIEWS_ROUTE_ENABLED else ""}contractor product, quote, '
      f'sitemap ({len(urls)} urls), robots.')
