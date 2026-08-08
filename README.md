# Westchester Housing Finder

A single-page dashboard of live Westchester + Lower Fairfield housing:
Section 8 / voucher waitlists, rooms under $1,200, apartments (800+ sq ft),
and voucher apartments under $4,000. Hosted free on GitHub Pages and
installable as an app on phone and PC.

---

## 1. Put it on GitHub (one time)

### Option A — the website (no command line)

1. Go to <https://github.com/new>.
2. **Repository name:** `westchester-housing`  ·  set it to **Public**  ·  click **Create repository**.
3. On the new repo page, click **uploading an existing file**.
4. Drag in ALL of these files (keep the names exactly):
   `index.html`, `manifest.webmanifest`, `icon-192.png`, `icon-512.png`, `.nojekyll`
5. Click **Commit changes**.

### Option B — command line (same flow as the scanner)

```bash
cd westchester-housing
git init
git add .
git commit -m "Westchester housing dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/westchester-housing.git
git push -u origin main
```

---

## 2. Turn on GitHub Pages

1. In the repo, go to **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Branch: **main**, folder: **/ (root)** → **Save**.
4. Wait ~1 minute. Your permanent link appears at the top of that page:

   **https://YOUR_USERNAME.github.io/westchester-housing/**

That link never changes. Send it to your wife once.

---

## 3. Install it as an app

**On her phone (iPhone/Android):**
open the link → Share button → **Add to Home Screen**. It gets its own
icon and opens fullscreen, no browser bars.

**On a PC (Chrome or Edge):**
open the link → click the **Install** icon in the address bar (or ⋮ menu →
**Install this site as an app**). It lands in the Start menu / dock and opens
in its own window.

---

## 4. Mon / Wed / Fri updates

The listings can't be scraped by a plain server (Craigslist and
AffordableHousing block datacenter IPs), so the refresh runs through Claude
on a schedule. Each Monday, Wednesday, and Friday morning it regenerates
`index.html` with the newest listings — keeping every phone number and reply
email already collected.

To publish an update you just replace `index.html`:

- **Website:** open the repo → click `index.html` → the pencil/​**Edit** →
  or use **Add file → Upload files** to drop in the new one → **Commit**.
- **Command line:**
  ```bash
  git add index.html
  git commit -m "refresh listings"
  git push
  ```

The live link updates within a minute. Nothing else changes.

---

## Files

| File | What it is |
|------|------------|
| `index.html` | the whole dashboard (all styles + data inline) |
| `manifest.webmanifest` | makes it installable as an app |
| `icon-192.png`, `icon-512.png` | app icons |
| `.nojekyll` | tells GitHub Pages to serve the files as-is |
