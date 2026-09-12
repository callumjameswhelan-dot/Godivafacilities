#!/usr/bin/env python3
"""
Godiva Facilities Management — static site build.

    python3 build.py            # builds ./dist
    python3 build.py --serve    # builds, then serves dist on http://localhost:8000

No dependencies. Each file in src/pages/ has a small front-matter block
(key: value lines between --- fences) followed by the page's HTML body.
The body is dropped into src/layout.html. Clean URLs are produced by
writing /<path>/index.html.

SITE CONFIG — fill in real details before launch. Anything left blank is
omitted from the structured data rather than invented.
"""
import json, os, re, shutil, sys, datetime, hashlib, http.server, socketserver

SITE = {
    "url": "https://www.godivafacilities.com",
    "name": "Godiva Facilities Management",
    # LocalBusiness fields — leave blank until real. Rendered only if set.
    "street": "",
    "locality": "Coventry",
    "region": "West Midlands",
    "postcode": "",
    "company_number": "",
    "vat_number": "",
    "opening_hours": "",   # e.g. "Mo-Fr 08:00-18:00"
    "sameAs": [],          # e.g. ["https://www.linkedin.com/company/godiva-facilities"]
}

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, DIST = os.path.join(ROOT, "src"), os.path.join(ROOT, "dist")
YEAR = datetime.date.today().year


def org_schema():
    """Organization / LocalBusiness JSON-LD. LocalBusiness only when an address exists."""
    has_address = bool(SITE["street"] and SITE["postcode"])
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness" if has_address else "Organization",
        "@id": SITE["url"] + "/#organization",
        "name": SITE["name"],
        "url": SITE["url"] + "/",
        "logo": SITE["url"] + "/assets/img/logo.png",
        "description": "Reliable, professionally managed commercial cleaning for offices and workplaces across Coventry, Warwickshire and the West Midlands.",
        "areaServed": [{"@type": "Place", "name": n} for n in ["Coventry", "Warwickshire", "Birmingham", "West Midlands"]],
    }
    if has_address:
        data["address"] = {
            "@type": "PostalAddress", "streetAddress": SITE["street"],
            "addressLocality": SITE["locality"], "addressRegion": SITE["region"],
            "postalCode": SITE["postcode"], "addressCountry": "GB",
        }
        if SITE["opening_hours"]:
            data["openingHours"] = SITE["opening_hours"]
    if SITE["company_number"]:
        data["identifier"] = {"@type": "PropertyValue", "propertyID": "Companies House", "value": SITE["company_number"]}
    if SITE["vat_number"]:
        data["vatID"] = SITE["vat_number"]
    if SITE["sameAs"]:
        data["sameAs"] = SITE["sameAs"]
    return json.dumps(data, indent=2)


def parse_page(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError("Missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def breadcrumb_schema(path, name):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE["url"] + "/"}]
    if path != "/":
        items.append({"@type": "ListItem", "position": 2, "name": name, "item": SITE["url"] + path})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def build():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(DIST, "assets"))

    layout = open(os.path.join(SRC, "layout.html"), encoding="utf-8").read()
    # Cache-busting: append a content hash to CSS/JS URLs so browsers pick up every deploy.
    for asset in ["assets/css/main.css", "assets/js/main.js"]:
        h = hashlib.md5(open(os.path.join(ROOT, asset), "rb").read()).hexdigest()[:8]
        layout = layout.replace('"/%s"' % asset, '"/%s?v=%s"' % (asset, h))
    org = org_schema()
    urls = []

    for fname in sorted(os.listdir(os.path.join(SRC, "pages"))):
        if not fname.endswith(".html"):
            continue
        meta, body = parse_page(open(os.path.join(SRC, "pages", fname), encoding="utf-8").read())
        path = meta["path"]  # e.g. "/services/"
        canonical = SITE["url"] + ("/" if path == "/" else path)

        # Page-level schema: breadcrumbs plus anything the page declares (file in src/schema/)
        schemas = []
        if path != "/":
            schemas.append(breadcrumb_schema(path, meta.get("nav_name", meta["title"].split("|")[0].strip())))
        if meta.get("schema"):
            schemas.append(json.load(open(os.path.join(SRC, "schema", meta["schema"]), encoding="utf-8")))
        schema_page = "\n".join(
            '  <script type="application/ld+json">%s</script>' % json.dumps(s, indent=2).replace("{{site_url}}", SITE["url"])
            for s in schemas
        )

        html = layout
        repl = {
            "{{title}}": meta["title"],
            "{{og_title}}": meta.get("og_title", meta["title"]),
            "{{description}}": meta["description"],
            "{{canonical}}": canonical,
            "{{robots}}": meta.get("robots", "index, follow"),
            "{{site_url}}": SITE["url"],
            "{{schema_org}}": org,
            "{{schema_page}}": schema_page,
            "{{content}}": body,
            "{{year}}": str(YEAR),
        }
        for key in ["commercial", "services", "about", "contact"]:
            repl["{{cur_%s}}" % key] = ' aria-current="page"' if meta.get("nav") == key else ""
        for k, v in repl.items():
            html = html.replace(k, v)
        # second pass so placeholders inside page bodies (phone/email) resolve too
        for k in ["{{site_url}}", "{{year}}"]:
            html = html.replace(k, repl[k])

        out_dir = os.path.join(DIST, path.strip("/")) if path != "/" else DIST
        os.makedirs(out_dir, exist_ok=True)
        open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(html)
        if meta.get("robots", "index").startswith("index"):
            urls.append((canonical, meta.get("priority", "0.7"), meta.get("changefreq", "monthly")))
        print("built", path)

    # sitemap.xml
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, pri, freq in urls:
        sm.append("  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>" % (loc, today, freq, pri))
    sm.append("</urlset>")
    open(os.path.join(DIST, "sitemap.xml"), "w").write("\n".join(sm))

    shutil.copy(os.path.join(ROOT, "_headers"), os.path.join(DIST, "_headers"))

    # robots.txt
    open(os.path.join(DIST, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\nDisallow: /_templates/\n\nSitemap: %s/sitemap.xml\n" % SITE["url"]
    )
    print("sitemap + robots written →", DIST)


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        os.chdir(DIST)
        with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
            print("Serving on http://localhost:8000")
            httpd.serve_forever()
