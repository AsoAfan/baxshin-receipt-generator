# Minimal Receipt Generator

Simple web app for non-technical staff to create printable receipts.

## Features

- Very simple form (SID, customer, items, tax)
- Auto-generated receipt IDs (`INV-00001`, `INV-00002`, ...)
- SQLite database to store:
  - receipt IDs
  - SIDs (with latest used receipt)
  - receipt items and totals
- Printable receipt page styled to match the provided clean medical-invoice look
- Receipt history page
- Easy branding customization using `branding.json`

## Tech Stack

- Flask (Python)
- SQLite (built-in)
- Plain HTML/CSS/JS

## Run

1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start app:

```bash
flask --app app run
```

5. Open browser:

- http://127.0.0.1:5000

## Database

The app creates `receipts.db` automatically on first run with these tables:

- `sids`
- `receipts`
- `receipt_items`

## Branding (easy to change later)

Edit `branding.json` to update:

- Clinic name and tagline
- Document labels (MEDICAL / INVOICE)
- Address lines
- Social/contact lines
- Terms text

To change the logo:

1. Put your logo image inside the `img` folder (example: `img/logo.png`).
2. Set `logo_url` in `branding.json` to:

```json
"logo_url": "/img/logo.png"
```

If `logo_url` is empty, the template shows a fallback icon.

## Non-tech usage flow

1. Fill SID and customer name.
2. Add one or more items.
3. Click **Generate Receipt**.
4. Click **Print** on the receipt page.
