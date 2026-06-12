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

### Option 1: Desktop App Mode (Recommended)
This runs the app as a standalone desktop window without needing a web browser.
1. Run `RUN-DESKTOP.bat`.

### Option 4: Standalone Executable (For Clients)
If you want to share the app without sharing the source code:
1. Run `BUILD-EXE.bat`.
2. Share the contents of the `dist` folder.

### Option 2: Browser Mode
1. Start app:
```bash
python app.py
```
2. Open browser: http://localhost:81 (or the port shown in terminal).

### Option 3: Waitress/Production Mode
```bash
python wsgi.py
```

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
