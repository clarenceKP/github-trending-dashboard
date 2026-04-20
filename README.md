# GitHub Trending(Python)


## Intro
Tracking the most popular Github repos, updated daily(Python version)

## Run

You need install `pyquery` & `requests`

```bash
  $ git clone https://github.com/bonfy/github-trending.git
  $ cd github-trending
  $ pip install -r requirements.txt
  $ python scraper.py
```

## Dashboard

Build a shareable static dashboard from the collected markdown files:

```bash
  $ python build_dashboard.py
```

Open `dashboard.html` in a browser to browse the daily, weekly, and monthly trending rankings. New snapshots include total stars, forks, and stars gained today, so the dashboard can mark high-star repositories as `高星口碑` and fast-growing repositories as `飙升项目`. The main view deduplicates repositories across languages and ranks them by a weighted score that prioritizes stars and star growth while still considering rank and repeat appearances. It also tags AI and finance projects and provides dedicated tabs for those two focus areas. By default the dashboard includes the latest 370 days to keep the HTML easy to share. Use `python build_dashboard.py --all` if you need the full historical dataset.

GitHub Pages entrypoint:

```bash
  $ python build_dashboard.py --output docs/index.html
```

Recommended share URL:

```text
https://clarenceKP.github.io/github-trending-dashboard/
```

## Advance

A better place to use the script is in VPS

* You should have a VPS first, and then you should Add SSH Keys of your VPS to Github

* Then you can run the code in VPS

Thus the code will run never stop

## Special Day

- [2017-03-29](https://github.com/bonfy/github-trending/blob/master/2017/2017-03-29.md) - my repo [qiandao](https://github.com/bonfy/qiandao) record by github-trending(Python)
- [2018-09-27](https://github.com/bonfy/github-trending/blob/master/2018/2018-09-27.md)/[2018-10-09](https://github.com/bonfy/github-trending/blob/master/2018/2018-10-09.md) - my repo [go-mega](https://github.com/bonfy/go-mega) record by github-trending(Go)

## Sponsor

![support](https://raw.githubusercontent.com/bonfy/image/master/global/sponsor.jpg)

## License

MIT
