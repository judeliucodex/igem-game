# iGEM-game

**Microbe Wars : Void Edition** — a single-file pygame game that also runs in the browser via
[pygbag](https://pypi.org/project/pygbag/) (Python compiled to WebAssembly).

## Play on desktop

```bash
pip install pygame
python main.py
```

## Build for the web

```bash
pip install pygbag==0.9.3
python -m pygbag --build --title "Microbe Wars" .
```

The static site is written to `build/web/`. Upload that folder to any static host.
`vercel.json` already configures Vercel to run this build.

To test locally, serve `build/web/` and open it at `http://127.0.0.1:<port>/`. Do not use
`localhost`, because pygbag then looks for its own dev server on port 8000.

```bash
python -m http.server 8765 --directory build/web
```

On macOS with the python.org installer, the build may fail with `CERTIFICATE_VERIFY_FAILED`.
Run `Install Certificates.command` from the Python folder, or set
`SSL_CERT_FILE=$(python -m certifi)`.

## Files

- `main.py` — the game. pygbag requires this name.
- `font.ttf` — Noto Sans TC, subset to the characters the game uses, so Chinese text renders in
  the browser. Licensed under the SIL Open Font License (`OFL.txt`). If you add new Chinese text,
  regenerate it with `tools/make_font.py`, or the new characters will show as boxes.
- `pygbag.ini` — keeps non-game files out of the web bundle.
