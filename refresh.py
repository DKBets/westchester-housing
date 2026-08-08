#!/usr/bin/env python3
"""Auto-refresh the Westchester Housing dashboard (index.html) in place."""
import html as htmllib
import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

INDEX = "index.html"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}

ROOMS_MIN = 8
VOUCHER_MIN = 10
ROOMS_MAX = 40


def get(url, timeout=30):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text


def esc(s):
    return htmllib.escape(s or "", quote=True)


def money(s):
    d = re.sub(r"[^\d]", "", s or "")
    return int(d) if d else None


def id_of(url):
    return url.rstrip("/").split("/")[-1].replace(".html", "")


def splice_table(html, header, body, search_from=0):
    h = html.index(header, search_from) + len(header)
    close = html.index("</table>", h)
    return html[:h] + "\n" + body + "\n        " + html[close:]


ROOMS_HEADER = ('<tr class="hrow"><th>#</th><th>Posted</th><th>Rent</th>'
                '<th>Room — opens the posting</th><th>Area</th><th>Contact</th></tr>')


def existing_room_contacts(html):
    start = html.index(ROOMS_HEADER)
    end = html.index("</table>", start)
    block = html[start:end]
    out = {}
    for row in re.findall(r'<tr class="link-row">.*?</tr>', block):
        m = re.search(r'href="([^"]+)"', row)
        tds = re.findall(r'<td class="(?:nophone|phone)[^"]*" data-label="Contact">.*?</td>', row)
        if m and tds:
            out[id_of(m.group(1))] = tds[-1]
    return out


def scrape_rooms():
    txt = get("https://newyork.craigslist.org/search/wch/roo?max_price=1200&sort=date")
    soup = BeautifulSoup(txt, "html.parser")
    rooms, seen = [], set()
    for li in soup.select("li.cl-static-search-result"):
        a = li.find("a", href=True)
        if not a:
            continue
        url = a["href"]
        pid = id_of(url)
        if pid in seen:
            continue
        title = (li.get("title") or "").strip()
        if not title:
            t = li.select_one(".title")
            title = t.get_text(strip=True) if t else "Room for rent"
        pe = li.select_one(".price")
        le = li.select_one(".location")
        price = money(pe.get_text()) if pe else None
        loc = le.get_text(strip=True) if le else ""
        if not price or price < 400 or price > 1200:
            continue
        seen.add(pid)
        rooms.append({"url": url, "id": pid, "title": title,
                      "price": price, "loc": loc.title() if loc else ""})
        if len(rooms) >= ROOMS_MAX:
            break
    for r in rooms:
        try:
            page = get(r["url"], timeout=20)
            m = re.search(r'datetime="(\d{4}-\d{2}-\d{2})', page)
            r["date"] = datetime.strptime(m.group(1), "%Y-%m-%d").date() if m else None
        except Exception:
            r["date"] = None
    return rooms


def rooms_body(rooms, contacts):
    today = date.today()
    dated = [r for r in rooms if r["date"]]
    undated = [r for r in rooms if not r["date"]]
    dated.sort(key=lambda r: r["date"], reverse=True)
    ordered = dated + undated
    lines = []
    for i, r in enumerate(ordered, 1):
        if r["date"]:
            label = r["date"].strftime("%b %-d")
            fresh = (today - r["date"]).days <= 4
            datecell = (f'<span style="color:var(--green);font-weight:700">{label} · new</span>'
                        if fresh else label)
        else:
            datecell = '<span style="color:var(--green);font-weight:700">new</span>'
        contact = contacts.get(r["id"], '<td class="nophone" data-label="Contact">—</td>')
        lines.append(
            f'          <tr class="link-row"><td class="numcell" data-label="">{i}</td>'
            f'<td class="srccell" data-label="Posted">{datecell}</td>'
            f'<td class="price" data-label="Rent">${r["price"]:,}</td>'
            f'<td class="titlecell"><a class="addr-link" href="{esc(r["url"])}">{esc(r["title"])}</a></td>'
            f'<td class="area" data-label="Area">{esc(r["loc"])}</td>{contact}</tr>')
    return "\n".join(lines)


VOUCHER_HEADER = ('<tr class="hrow"><th>Rent</th><th>Beds</th>'
                  '<th>Address — opens the listing</th><th>Town</th></tr>')
AH_TOWNS = ["westchester-county-ny", "yonkers-ny", "mount-vernon-ny",
            "new-rochelle-ny", "peekskill-ny", "ossining-ny",
            "yorktown-heights-ny", "white-plains-ny"]


def scrape_voucher():
    rows, seen = [], set()
    for town in AH_TOWNS:
        try:
            txt = get(f"https://www.affordablehousing.com/{town}/")
        except Exception:
            continue
        soup = BeautifulSoup(txt, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/" + town + "/" not in href and "affordablehousing.com/" not in href:
                continue
            if not re.search(r"-\d{4,}/?$", href):
                continue
            block = a.get_text(" ", strip=True)
            pm = re.search(r"\$([\d,]{3,6})", block)
            if not pm:
                continue
            price = money(pm.group(1))
            if not price or price >= 4000:
                continue
            url = href if href.startswith("http") else "https://www.affordablehousing.com" + href
            key = id_of(url)
            if key in seen:
                continue
            bm = re.search(r"(\d)\s*(?:bed|br)", block, re.I)
            beds = f"{bm.group(1)} BR" if bm else ("Studio" if "studio" in block.lower() else "—")
            addr = re.sub(r"\$[\d,]+.*", "", block).strip(" ,-") or "View listing"
            town_name = town.replace("-ny", "").replace("-", " ").title()
            if town == "westchester-county-ny":
                town_name = "Westchester"
            seen.add(key)
            rows.append({"price": price, "beds": beds,
                         "addr": addr[:60], "town": town_name, "url": url})
    rows.sort(key=lambda r: r["price"])
    return rows[:28]


def voucher_body(rows):
    lines = []
    for r in rows:
        lines.append(
            f'          <tr class="link-row"><td class="price" data-label="Rent">${r["price"]:,}</td>'
            f'<td data-label="Beds">{esc(r["beds"])}</td>'
            f'<td class="titlecell"><a class="addr-link" href="{esc(r["url"])}">{esc(r["addr"])}</a></td>'
            f'<td class="area" data-label="Town">{esc(r["town"])}</td></tr>')
    return "\n".join(lines)


def main():
    html = open(INDEX, encoding="utf-8").read()
    original = html
    notes = []

    try:
        contacts = existing_room_contacts(html)
        rooms = scrape_rooms()
        matched = sum(1 for r in rooms if r["id"] in contacts)
        if len(rooms) >= ROOMS_MIN and not (contacts and matched == 0):
            html = splice_table(html, ROOMS_HEADER, rooms_body(rooms, contacts))
            notes.append(f"rooms={len(rooms)} (contacts kept={matched})")
        else:
            notes.append(f"rooms kept (found {len(rooms)}, matched {matched})")
    except Exception as e:
        notes.append(f"rooms kept (error: {e})")

    try:
        vrows = scrape_voucher()
        if len(vrows) >= VOUCHER_MIN:
            body = voucher_body(vrows)
            vstart = html.index('id="voucherapts"')
            html = splice_table(html, VOUCHER_HEADER, body, vstart)
            html = splice_table(html, VOUCHER_HEADER, body, 0)
            stamp = date.today().strftime("%b %-d")
            html = re.sub(r"\(AffordableHousing\.com, [A-Za-z]+ \d+\)",
                          f"(AffordableHousing.com, {stamp})", html, count=1)
            notes.append(f"voucher+section8={len(vrows)}")
        else:
            notes.append(f"voucher kept (only {len(vrows)} found)")
    except Exception as e:
        notes.append(f"voucher kept (error: {e})")

    if html != original:
        stamp = date.today().strftime("%b %-d")
        html = re.sub(r"Rooms refreshed [A-Za-z]+ \d+",
                      f"Rooms refreshed {stamp}", html, count=1)
        open(INDEX, "w", encoding="utf-8").write(html)
        print("CHANGED:", "; ".join(notes))
    else:
        print("NO CHANGE:", "; ".join(notes))


if __name__ == "__main__":
    main()
