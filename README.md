# gasiin.co: Gasiin Enterprise website

A plain HTML and CSS site with no build step. **Everything inside the `docs/` folder is the live site.** The `tests/` folder holds automatic checks and is not published.

| File | Page |
|---|---|
| `docs/index.html` | Home |
| `docs/products.html` | Products & Services |
| `docs/about.html` | About |
| `docs/contact.html` | Contact form |
| `docs/thank-you.html` | Shown after a message is sent |
| `docs/assets/css/site.css` | All styles (brand colours at the top) |
| `docs/assets/img/` | Logos from Brand Kit v2, icons, share image |

## Editing text
Open a page on GitHub, click the pencil icon, change the words between the tags, then click **Commit changes**. The site updates within a minute or two.

The header and footer are repeated in every page. If you change one, change it in all five.

## Adding photos
1. Upload the photo to `docs/assets/img/photos/` (use a JPG under about 300 KB, around 1600 px wide).
2. In `docs/index.html`, find a block like this:
   `<div class="placeholder" role="img" aria-label="Photo coming soon: hay baling">…</div>`
3. Replace it with:
   `<img class="photo" src="assets/img/photos/hay-baling.jpg" alt="Hay baling at the Gasiin farm" loading="lazy">`

## The intro video
The one-minute intro on the home page is `docs/assets/video/gasiin-intro.mp4` (poster image: `gasiin-intro-poster.jpg` in the same folder). To replace it, upload a new MP4 with the same name.

## Adding a YouTube video
In `docs/index.html`, replace the "Video coming soon" block with:
`<div class="video"><button type="button" data-youtube="VIDEO_ID" aria-label="Play video: TITLE"><span>▶ Play video</span></button></div>`
`VIDEO_ID` is the part after `v=` in the YouTube link.

## Contact form
The form on `docs/contact.html` sends each message to **info@gasiin.co** through FormSubmit (formsubmit.co), which is free and needs no account.
- **One-time step:** the first time someone sends a message, FormSubmit emails info@gasiin.co asking to confirm. Click **Activate** in that email. After that, messages arrive directly.
- info@gasiin.co must be a working mailbox. If it isn't yet, set up free forwarding in Cloudflare: **Email → Email Routing**, then forward info@gasiin.co to a Gmail address.

## Publishing (GitHub Pages and Cloudflare)
1. On GitHub, open the repository's **Settings → Pages**. Set Source to **Deploy from a branch**, Branch to `main` and folder to **`/docs`**, then click **Save**. The `docs/CNAME` file already sets the domain to `gasiin.co`.
2. In Cloudflare, open **gasiin.co → DNS → Records** and add:

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | @ | 185.199.108.153 | DNS only (grey cloud) |
| A | @ | 185.199.109.153 | DNS only |
| A | @ | 185.199.110.153 | DNS only |
| A | @ | 185.199.111.153 | DNS only |
| CNAME | www | amousamf.github.io | DNS only |

   Delete any older A or CNAME records for `@` or `www` that point elsewhere.
3. Wait 10–30 minutes. Then, in GitHub **Settings → Pages**, tick **Enforce HTTPS** when the option appears.

## Checks
`python3 -m pytest -q` runs the automatic checks: no broken links, correct email, no investment or partners content, labels on form fields, and the files search engines and AI tools read.
