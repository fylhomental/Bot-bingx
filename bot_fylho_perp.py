name: Run FYLHO PERP UNIVERSAL
on:
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: '0 */4 * * *'

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run bot
        env:
          BINGX_API_KEY: ${{ secrets.BINGX_API_KEY }}
          BINGX_SECRET_KEY: ${{ secrets.BINGX_SECRET_KEY }}
        run: python main.py
