# Microbe Wars (iGEM game)

- Live: https://igem-game.vercel.app (Vercel project `igem-game`, team `judeliucodex`)
- Repo: git@github.com:judeliucodex/igem-game.git (`origin`). `upstream` is the original
  author's repo (s2025037-creator/iGEM-game); we have no push access there.
- Deploy: push to `main` and Vercel auto-deploys. Never deploy manually. Vercel builds with
  pygbag (see `vercel.json`); the web bundle is named `path0.tar.gz` on Vercel.
- Verify a deploy by comparing `font.ttf` / `main.py` inside the live `path0.tar.gz` with the
  repo. Vercel's pygbag rewrites the one `.bmp` mention in `main.py` to `.png`; that diff is expected.
- Local test: serve `build/web` and open `http://127.0.0.1:<port>`, not `localhost`.
- Do not `import PIL` directly in `main.py`: pygbag auto-installs Pillow, which breaks the display.
