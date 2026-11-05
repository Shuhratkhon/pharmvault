# PHARMVAULT PROJECT:

Database-driven pharmacy stock management website

**🌐 Live Website:** https://pharmvault-u5k0.onrender.com

## 🛠️ Technologies:

* PostgreSQL (database: medicines, pharma companies, ingredients, illnesses, stock, history)
* Python + Flask (backend and JSON API)
* HTML5 (Website structure)
* CSS3 (Interface and visual design)
* JavaScript (Application logic)
* Chart.js (Dashboard charts)
* FDA NDC Directory + Medicaid NADAC (real US medicine data and prices for Web Stock)
* Neon (online PostgreSQL database)
* Render (Website hosting)

## ✨ Innovative Features:

* Pharmacy Accounts (each pharmacy signs in with its own password and sees only its own stock)
* Two Stocks (Local Stock is the pharmacy's own editable inventory, Web Stock is a read-only national catalogue of 18,186 real medicines)
* Smart Search (searches names, ingredients, illnesses and pharma companies at once, with name matches first and the matched word highlighted)
* Category View (Show by illness, type, form, pharma, country, ingredients, stock status, expiry status or prescription, and click a group to filter)
* Inline Editing (price, quantity and expiry date are changed directly in the table and saved instantly)
* Smart Warnings (yellow and red colors for low stock and close expiry, with different limits for each medicine form)
* Watchlist (one popup listing every medicine that needs attention: red first, then yellow)
* Dashboard (charts for medicines and stock value per form, expiry timeline, top illnesses and medicine types)
* History (every import, download, edit, addition and delete is recorded with its time)
* Import & Download (upload Excel, CSV or text files, and download chosen tables as CSV or ZIP)

## 🔮 Future Improvements:

* Sell / dispense button (lowers quantity automatically and records the sale)
* Medicine detail window (all illnesses, dosages and ingredients of one medicine)
* Staff accounts (separate logins and roles inside one pharmacy)
* Local medicine list (Uzbekistan medicines with prices in sum)
* Automatic Web Stock price updates
* Language options (English, Uzbek, Korean)
* Better mobile layout

## 💻 Run It Yourself:

1. Install Python 3.12 and PostgreSQL 16
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your database settings
4. Create the tables with `schema.sql`, then load demo data with `python import_data.py`
5. Optional: load Web Stock with `python scripts/web_stock.py all`
6. Run `python app.py` and open http://localhost:5000
