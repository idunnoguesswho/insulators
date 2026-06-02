# Insulator Field Notebook

Mobile-first static reference site generated from the files in `F:\Insulator Book`.

## Local Preview

```powershell
python -m http.server 4173 --bind 127.0.0.1
```

Open <http://127.0.0.1:4173/index.html>.

## Rebuild After Additions

```powershell
& 'C:\Users\katie\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'tools\import_insulator_book.py' --source 'F:\Insulator Book' --out 'C:\Users\katie\OneDrive\Documents\Insulators'
```

The importer extracts text from Word, Excel, and searchable PDFs, copies small reference assets, and flags oversized or scanned files in `data/catalog.json`.

## Free Hosting

This site is plain HTML, CSS, JavaScript, and static assets. It can be hosted with GitHub Pages, Cloudflare Pages, Netlify, or another free static host.
