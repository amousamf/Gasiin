import json
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "docs"  # the published site folder (GitHub Pages: main /docs)
PAGES = ["index.html", "products.html", "about.html", "contact.html"]
FORBIDDEN = ["invest", "seed round", "funding", "ebitda", "projection", "partners", "gasiin.co.uk"]


def soup(name):
    return BeautifulSoup((ROOT / name).read_text(encoding="utf-8"), "html.parser")


def visible_and_source(name):
    return (ROOT / name).read_text(encoding="utf-8").lower()


def test_pages_exist():
    for p in PAGES:
        assert (ROOT / p).is_file(), p


@pytest.mark.parametrize("page", PAGES)
def test_no_forbidden_content(page):
    text = visible_and_source(page)
    for word in FORBIDDEN:
        assert word not in text, f"{page} contains forbidden '{word}'"


@pytest.mark.parametrize("page", PAGES)
def test_email_correct(page):
    s = soup(page)
    mails = [a["href"] for a in s.select('a[href^="mailto:"]')]
    assert mails, f"{page} has no email link"
    assert all(m == "mailto:info@gasiin.co" for m in mails), mails


@pytest.mark.parametrize("page", PAGES)
def test_internal_links_resolve(page):
    s = soup(page)
    refs = [a["href"] for a in s.select("a[href]")] + [i["src"] for i in s.select("img[src]")] + \
           [l["href"] for l in s.select("link[href]") if not l["href"].startswith("http")]
    for r in refs:
        if r.startswith(("http", "mailto:", "tel:", "#")):
            continue
        path, _, frag = r.partition("#")
        target = ROOT / path
        assert target.is_file(), f"{page}: broken link {r}"
        if frag and path.endswith(".html"):
            assert soup(path).find(id=frag) is not None, f"{page}: missing anchor {r}"


@pytest.mark.parametrize("page", PAGES)
def test_images_have_alt(page):
    s = soup(page)
    for img in s.find_all("img"):
        assert img.get("alt", "").strip(), f"{page}: img without alt {img}"
    for ph in s.select(".placeholder"):
        assert ph.get("aria-label") or ph.get("role") == "img", f"{page}: unlabeled placeholder"


def test_meta_unique():
    titles, descs = set(), set()
    for p in PAGES:
        s = soup(p)
        t = s.title.string.strip()
        d = s.find("meta", attrs={"name": "description"})["content"].strip()
        assert t and d
        titles.add(t)
        descs.add(d)
        assert s.find("html").get("lang") == "en"
        assert s.find("meta", attrs={"name": "viewport"})
    assert len(titles) == len(PAGES) and len(descs) == len(PAGES)


@pytest.mark.parametrize("page", PAGES)
def test_jsonld_valid(page):
    blocks = soup(page).select('script[type="application/ld+json"]')
    if not blocks:
        pytest.skip("no JSON-LD on this page yet")
    for b in blocks:
        json.loads(b.string)


def test_home_sections():
    s = soup("index.html")
    for sid in ["hero", "what", "why", "products", "services", "team", "gallery", "contact"]:
        assert s.find(id=sid) is not None, f"missing #{sid}"
    team = s.find(id="team").get_text(" ")
    for name in ["Ahmed Hersi Osman", "Kaisar Omer"]:
        assert name in team, name
    assert "20 years" in team
    assert "AU-IBAR" in s.find(id="why").get_text()
    contact = str(s.find(id="contact"))
    assert "mailto:info@gasiin.co" in contact and "wa.me/252634367575" in contact
    orgs = [json.loads(b.string) for b in s.select('script[type="application/ld+json"]')]
    org = next(o for o in orgs if o.get("@type") == "Organization")
    assert org["name"] == "Gasiin Enterprise" and org["email"] == "info@gasiin.co"


def test_subpages():
    prod = soup("products.html").get_text(" ")
    for w in ["Gasiin Hay", "Gasiin Silage", "Gasiin Feeds", "20 kg", "50 kg", "aflatoxin"]:
        assert w in prod, w
    about = soup("about.html").get_text(" ")
    for w in ["Vision", "Mission", "feed"]:
        assert w in about, w


def test_contact_form_emails_info():
    s = soup("contact.html")
    form = s.find("form")
    assert form is not None
    assert form["action"] == "https://api.web3forms.com/submit"
    assert form["method"].lower() == "post"
    names = {i.get("name") for i in form.find_all(["input", "textarea", "select"])}
    for n in ["access_key", "name", "email", "message", "subject", "redirect", "botcheck"]:
        assert n in names, n
    assert form.find("input", attrs={"name": "access_key"})["value"].strip()
    for field in form.find_all(["input", "textarea"]):
        if field.get("type") in ("hidden",) or field.get("name") == "botcheck":
            continue
        fid = field.get("id")
        assert fid and s.find("label", attrs={"for": fid}), f"field {field.get('name')} has no label"
    assert form.find("input", attrs={"name": "email"})["type"] == "email"
    assert form.find("input", attrs={"name": "redirect"})["value"] == "https://gasiin.co/thank-you.html"
    assert (ROOT / "thank-you.html").is_file()


def test_nav_contact_goes_to_contact_page():
    for p in PAGES:
        btn = soup(p).select_one(".nav a.btn")
        assert btn["href"] == "contact.html", p


def test_discovery_files():
    sm = (ROOT / "sitemap.xml").read_text()
    for p in ["https://gasiin.co/", "https://gasiin.co/products.html", "https://gasiin.co/about.html", "https://gasiin.co/contact.html"]:
        assert f"<loc>{p}</loc>" in sm, p
    assert "thank-you" not in sm
    assert "Sitemap: https://gasiin.co/sitemap.xml" in (ROOT / "robots.txt").read_text()
    llms = (ROOT / "llms.txt").read_text()
    assert "Gasiin Enterprise" in llms and "info@gasiin.co" in llms
    assert "gasiin.co.uk" not in llms and "invest" not in llms.lower()
    assert (ROOT / "assets/img/og-image.png").is_file()
    for p in PAGES:
        assert soup(p).find("meta", attrs={"property": "og:image"}), p


PUBLIC_EXT = {".html", ".css", ".js", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".xml", ".txt", ""}


def test_published_folder_holds_only_site_files():
    for f in ROOT.rglob("*"):
        if f.is_file():
            assert f.suffix in PUBLIC_EXT, f"non-site file published: {f.relative_to(REPO)}"
            assert "superpowers" not in str(f) and "test" not in f.name, f
    for f in ROOT.rglob("*"):
        if f.is_file() and f.suffix in {".html", ".css", ".js", ".xml", ".txt"}:
            text = f.read_text(encoding="utf-8").lower()
            for word in FORBIDDEN:
                assert word not in text, f"{f.name} contains '{word}'"


UNCONFIRMED = [
    "Every batch is moisture-checked", "Contract farms span", "We supply feed close",
    "stored in climate-protected depots", "supply agreements with dairy", "logistics along the port corridors",
    "Our own nucleus farm grows", "Feed delivered to quarantine stations",
]


def test_plans_not_stated_as_current_operations():
    for f in list(ROOT.glob("*.html")) + [ROOT / "llms.txt"]:
        text = f.read_text(encoding="utf-8")
        for phrase in UNCONFIRMED:
            assert phrase not in text, f"{f.name}: '{phrase}' states a plan as fact"


def _lum(hexc):
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contrast(a, b):
    la, lb = sorted([_lum(a), _lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _var(css, name):
    return re.search(rf"--{name}:\s*(#[0-9A-Fa-f]{{6}})", css).group(1)


def test_small_text_colours_meet_wcag_aa():
    css = (ROOT / "assets/css/site.css").read_text()
    gold_text = _var(css, "gold-text")
    assert _contrast(gold_text, "#FFFFFF") >= 4.5
    assert _contrast(gold_text, _var(css, "beige")) >= 4.5
    assert _contrast(_var(css, "gold-on-green"), _var(css, "forest")) >= 4.5
    assert re.search(r"\.eyebrow\s*{[^}]*color:\s*var\(--gold-text\)", css)
    assert re.search(r"\.role\s*{[^}]*color:\s*var\(--gold-text\)", css)
    assert re.search(r":focus-visible\s*{[^}]*outline:\s*3px solid var\(--deep-forest\)", css)


def test_anchor_targets_clear_sticky_header():
    css = (ROOT / "assets/css/site.css").read_text()
    assert re.search(r"html\s*{[^}]*scroll-padding-top:\s*88px", css)
    assert re.search(r"\.nav li a\.btn\s*{[^}]*padding:\s*12px 22px", css)


def test_mobile_menu_closes_on_link_and_escape():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 360, "height": 740})
        pg.goto((ROOT / "index.html").as_uri())
        pg.click(".menu-toggle")
        assert "open" in pg.get_attribute("#nav", "class")
        pg.click('#nav a[href="index.html#team"]')
        assert "open" not in (pg.get_attribute("#nav", "class") or "")
        assert pg.get_attribute(".menu-toggle", "aria-expanded") == "false"
        pg.click(".menu-toggle")
        pg.keyboard.press("Escape")
        assert "open" not in (pg.get_attribute("#nav", "class") or "")
        b.close()


def test_only_founders_shown_and_no_descriptor_line():
    for f in list(ROOT.glob("*.html")) + [ROOT / "llms.txt"]:
        text = f.read_text(encoding="utf-8")
        for name in ["Hood Mohamed", "Mawliid Osman", "Farhia Osman Moge", "Key staff"]:
            assert name not in text, f"{f.name} still shows '{name}'"
    assert soup("index.html").select_one(".descriptor") is None
