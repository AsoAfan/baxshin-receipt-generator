# Receipt App - Complete Setup Guide

Your Receipt App is now fully configured with password protection, LAN sharing, and all your existing data!

---

## 🚀 Quick Start - One-Click Launch

**Double-click:** `RUN.vbs` 

This will:
1. ✅ Copy your database with all existing data
2. ✅ Start the app silently (no terminal windows)
3. ✅ Open your browser automatically
4. ✅ Show the login page

---

## 🔐 First Login

**Default Password:** `password`

After login, you'll see:
- All your existing receipts, customers, and items
- Settings button (⚙️) in the top right
- Full access to all features

---

## 📡 Share with Others on Your Network

### Inside the App (Easiest):
1. Click **⚙️ Settings** (top right of History page)
2. Copy the displayed URL under "Network Access"
3. Share with others on your WiFi

**Example:** `http://192.168.1.227:81`

---

## 🔧 Troubleshooting LAN Access

If other devices cannot open the app:

### 1. Windows Firewall (Most Common)
You must allow the app through the Windows Firewall:
1. Open **Windows Security** -> **Firewall & network protection**.
2. Click **Allow an app through firewall**.
3. Click **Change settings** (admin).
4. Look for `receipt_app.exe` or `python.exe` and ensure both **Private** and **Public** are checked.
5. If not there, click **Allow another app...** and select your app executable.

### 2. Network Type
Ensure your WiFi is set to **Private** network, not Public. Windows blocks incoming connections on Public networks.

### 3. Use Port 81
The app specifically uses port **81**. Ensure you include `:81` at the end of the IP address when typing it on other devices.

## 🔒 Security Features

- **Password protected** - Only authorized users can access
- **Change password anytime** - Go to Settings → Update Password
- **Toggle protection** - Can disable password if on private network
- **Session-based** - Stays logged in for 7 days

---

## 📊 Your Data

All existing data is preserved:
- ✅ All receipts
- ✅ All customers  
- ✅ All items
- ✅ Database structure intact

**Note:** After running `RUN.vbs` once, the database is synchronized. Any new data created in the app persists.

---

## 📁 What to Share with Others

To share the app with others, you can give them:

**Option 1 (Easiest):** Just the `RUN.vbs` file + `dist` folder
- They double-click `RUN.vbs` on their PC
- Enter your password
- Access via network URL

**Option 2:** The entire `marwa` folder
- Contains everything needed to run

---

## ⏸️ Stopping the App

- Close the browser, or
- Open Task Manager → Find "ReceiptApp.exe" → End Task

---

## 🔧 Troubleshooting

**"Database not loading?"**
- Make sure `receipts.db` is in the main marwa folder
- Run `RUN.vbs` again (it copies the database automatically)

**"Can't click Settings?"**
- Make sure you're logged in (you should see "Recent Receipts")
- Click the ⚙️ icon in the top right of History page

**"Forgot password?"**
- You can edit `app_config.json` in the main folder to reset it manually, or
- Ask IT to regenerate the executable configuration
