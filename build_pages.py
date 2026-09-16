from pathlib import Path
import shutil

from web_server import PAGES, WEB_ROOT, prepare_candidate_html

OUT = Path(__file__).resolve().parent / "docs"


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copytree(WEB_ROOT / "assets", OUT / "assets")
    shutil.copy2(WEB_ROOT / "overlay.js", OUT / "overlay.js")
    shutil.copy2(WEB_ROOT / "index.html", OUT / "index.html")
    for slug, page in PAGES.items():
        dest = OUT / slug
        dest.mkdir()
        (dest / "index.html").write_text(
            prepare_candidate_html(page, overlay_src="../overlay.js"),
            encoding="utf-8",
        )
    print(f"GitHub Pages: {OUT}")


if __name__ == "__main__":
    build()
