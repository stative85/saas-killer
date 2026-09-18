# 💸 SELL — From "value exists" to "value is sold"

You already built the engine. Positioning is sharp (`OFFER.md`). Three monetization paths are mapped (`MONETIZE.md`). The bottleneck is **the payment link**.

This is a 5-step checklist. Total time: under 2 hours. Output: a live way to take money today.

---

## Step 1 — Stand up the payment link (15 min)

Pick **one**. Don't shop, don't compare, don't read the FAQ. Just pick one and finish it.

- **Gumroad** — easiest for a `.zip` product. `SAAS_KILLER_V1_PRODUCT.zip` is already in this repo (6.5 MB).
- **LemonSqueezy** — better margins, slightly more setup, handles VAT.
- **Stripe Payment Link** — for the $1,000 Refinery service. No cart, no product page, just a link.

Drop the resulting URL into a file: `payment_links.txt` (gitignored). Three lines:
```
GUMROAD_PRODUCT_URL=https://...
STRIPE_REFINERY_URL=https://...
CONTACT_AGENCY_URL=mailto:stevesmith8504@gmail.com
```

## Step 2 — Wire `landing.html` (5 min)

Open `landing.html`. Search for `<!-- REPLACE -->` (4 markers). Paste your URLs. Save.

That's it. The page is self-contained — no backend, no build, no hosting prerequisites. Open it in a browser to confirm before you publish.

## Step 3 — Publish the page somewhere a stranger can hit it (10 min)

Pick one:
- **Netlify drop** — drag `landing.html` onto netlify.com/drop. Get a URL in 30 seconds.
- **Vercel** — `npx vercel --prod` from the repo root.
- **GitHub Pages** — won't work because this repo is private. Make a separate public repo just for the landing page if you want a custom domain.
- **Gumroad's own product page** — paste the OFFER.md copy directly into the description and skip hosting altogether.

## Step 4 — Pin the link in 3 places (10 min)

The link is worthless if nobody sees it. Pin it where you already have an audience:

- **GitHub bio** (`stative85`) — currently says "AI Prompt Engineer ⚡ Quantum-Bio Materials Researcher". Add the URL.
- **YouTube channel** (`CleverSiteGhost`) — channel description, top of the About page, and as a pinned community post.
- **Twitter / X bio** if you have one — link in bio is the highest-leverage real estate you own.

## Step 5 — Run the first 5 outbound shots (45 min)

Path 1 from `MONETIZE.md` (the $1,000 refinery service) is the fastest cash. Pick 5 podcasters / creators sitting on archives. DM them a 3-sentence offer:

> Hey [name] — I run a closed-loop content refinery. I take raw podcast transcripts and ship 30 high-retention short scripts (titles + thumbnails + pinned comments) in 48 hours. $1k flat. Want to see a sample on your last episode?

Track in a single Google Sheet:
- Name · Channel · DMed (date) · Replied (Y/N) · Sample sent · Booked

Don't optimize the message after fewer than 20 sends. The data isn't there yet.

---

## Anti-patterns to refuse this week

- ❌ Adding a new feature before the link exists.
- ❌ Polishing the README before the link exists.
- ❌ Switching frameworks for the landing page.
- ❌ Building a "real" backend for `/api/demo` instead of using the inline fallback.
- ❌ Renaming the product.

The constraint is the link. Everything else is procrastination wearing a productive costume.

---

## When you've made the first $1

Update `evidence_plane.log`:
```
2026-XX-XX  first_dollar  $X  source=gumroad|stripe|other  note=...
```

Then come back and pick the next path from `MONETIZE.md`. Not before.
