"""Finish a Smart UV whose run timed out: select the asset tile, Save if the unwrap is unsaved, Export FBX.
Usage: python studio_smartuv_finish.py <tile_x> <tile_y> <out_dir>      Env: TRIPO_STUDIO_PROFILE"""
import os, sys, zipfile
from playwright.sync_api import sync_playwright
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
x, y, out = int(sys.argv[1]), int(sys.argv[2]), os.path.abspath(sys.argv[3]); os.makedirs(out, exist_ok=True)
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(os.environ["TRIPO_STUDIO_PROFILE"], channel="chrome", headless=True, accept_downloads=True,
        args=["--disable-blink-features=AutomationControlled", "--headless=new"], user_agent=UA, viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    try:
        pg.goto("https://studio.tripo3d.ai/workspace/smart-uv", wait_until="domcontentloaded"); pg.wait_for_timeout(15000)
        pg.mouse.click(x, y); pg.wait_for_timeout(15000); pg.screenshot(path=f"{out}/finish_selected.png")
        save = pg.get_by_text("Save", exact=True)
        if save.count() and save.last.is_visible():
            save.last.click(); pg.wait_for_timeout(15000); print("saved", flush=True)
        pg.mouse.click(945, 864); pg.wait_for_timeout(4000); pg.screenshot(path=f"{out}/finish_dialog.png")
        with pg.expect_download(timeout=180000) as d:
            pg.mouse.click(997, 796)
        dl = d.value; path = os.path.join(out, dl.suggested_filename); dl.save_as(path)
        if path.lower().endswith(".zip"):
            with zipfile.ZipFile(path) as z: z.extractall(os.path.join(out, "export"))
        print("EXPORTED", path, flush=True)
    finally:
        pg.screenshot(path=f"{out}/finish_final.png"); ctx.close()
