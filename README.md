# Godiva Facilities Management — website

Static, zero-dependency site. Build with `python3 build.py` → deploy the `dist/` folder to any static host (Cloudflare Pages, Cloudflare Pages, Vercel, GitHub Pages, S3). Clean URLs (`/services/`) come from `dist/<path>/index.html`.

## Structure
```
build.py                 site config (domain, phone, email, address) + build
src/layout.html          shared head / header / footer
src/pages/*.html         one file per page: front-matter + body
src/schema/*.json        page-level JSON-LD (FAQ, services, website)
src/templates/           location-page template for future SEO pages
assets/css/main.css      design tokens + components
assets/js/main.js        nav, FAQ, form validation, submission stub
dist/                    built output (deploy this)
```

Pages: `/`, `/commercial-cleaning/`, `/services/`, `/about/`, `/get-a-quote/`, `/contact/`, `/privacy/`, `/cookies/`, `/commercial-cleaning-coventry/`. Sitemap and robots.txt are generated on build.

## Before launch — do these
No phone number or email is published anywhere on the site — all contact goes through the quote and contact forms.
1. **Forms.** Both forms post to Web3Forms (hidden `access_key` in `src/pages/get-a-quote.html` and `contact.html`). To change the inbox, create a new key at web3forms.com with that address and replace the value in both files.
2. **Company details.** Once registered, add street/postcode/company number/VAT to `SITE`. The schema switches from `Organization` to `LocalBusiness` automatically. Add the address to `contact.html` and the privacy policy.
3. **Photography.** Images are hot-linked from Unsplash as placeholders. Replace with owned photography of real workplaces, save to `assets/img/`, and update the `<img>` `src`/`srcset` in each page. Keep the width/height attributes (prevents layout shift). Logo, OG image and icons are already in `assets/img/`.
4. **Fonts.** Archivo loads from Google Fonts. Self-host the woff2 files for better Core Web Vitals and no third-party request.
5. **Legal.** Have privacy/cookies reviewed. If you add analytics, a consent banner is required.

## Adding a location page
Copy `src/templates/location-page.html` → `src/pages/commercial-cleaning-<town>.html`, fill in the placeholders and write genuinely local content (300+ words that are actually about the town). Rebuild. It's added to the sitemap and gets breadcrumb schema automatically. Don't publish thin near-duplicates.

## Editing
- Copy: edit the page file under `src/pages/`, rebuild.
- Nav/footer: `src/layout.html`.
- Colours/type/spacing: tokens at the top of `assets/css/main.css`.
- Page title/description: front-matter at the top of each page file.

Local preview: `python3 build.py --serve` → http://localhost:8000
