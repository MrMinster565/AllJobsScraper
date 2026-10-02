# AllJobsScraper

Finds jobs on AllJobs (alljobs.co.il) that fit a free-text description (Hebrew), lets you send
your resume to the ones you pick (each batch confirmed by you), and sends employer phone numbers
to your Telegram.

## Status
- [x] Phone-number extraction (Israeli formats) - `alljobs/phones.py`
- [x] Matching: free local keyword matcher, or Claude Haiku 4.5 if `ANTHROPIC_API_KEY` is set - `alljobs/matcher.py`
- [x] Telegram sending - `alljobs/telegram_bot.py`, `setup_telegram.py`
- [ ] AllJobs scraper (waiting for sample pages in `samples/`)
- [ ] Local web page (criteria box, results table, confirm-and-send)
- [ ] Resume sending through your AllJobs login
- [ ] Excel export

## Setup (Windows)
```
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```
Then fill in `.env` (see the comments inside it). Run the tests with `python -m pytest`.
