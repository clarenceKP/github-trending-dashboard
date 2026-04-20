# Publish Dashboard

Recommended repository:

```text
clarenceKP/github-trending-dashboard
```

After publishing with GitHub Pages, the shareable dashboard URL will be:

```text
https://clarenceKP.github.io/github-trending-dashboard/
```

## GitHub Pages Settings

In the GitHub repository, open `Settings` -> `Pages`, then set:

```text
Source: Deploy from a branch
Branch: main
Folder: /docs
```

## Update Data

Run these commands locally before pushing updates:

```powershell
cd D:\Trae\github-trending
.\.venv\Scripts\python.exe scraper.py
.\.venv\Scripts\python.exe build_dashboard.py --output docs\index.html
git add .
git commit -m "Update trending dashboard"
git push
```
