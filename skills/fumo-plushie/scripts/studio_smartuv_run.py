"""Tripo Studio Smart UV, one model end to end, headless: upload -> Confirm (Use Original UV) -> Unwrap UV -> Save -> Export FBX.
Usage: python studio_smartuv_run.py <model.fbx|glb> <out_dir>      Env: TRIPO_STUDIO_PROFILE
Costs one Smart UV generation (20 Studio credits after the free trial). Screenshots in <out_dir>/shots/.
Coordinates assume a 1440x900 viewport (Save button 477,854; export dialog button 997,796)."""
import os, sys, time, zipfile
from playwright.sync_api import sync_playwright
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
src, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
shots = os.path.join(out, "shots"); os.makedirs(shots, exist_ok=True)
n = [0]
def shot(pg, tag):
    n[0] += 1; pg.screenshot(path=os.path.join(shots, f"{n[0]:02d}_{tag}.png"))
def credits(pg):
    import re
    m = re.search(r"\n(\d{2,6})\n", pg.inner_text("body")); return m.group(1) if m else "?"
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(os.environ["TRIPO_STUDIO_PROFILE"], channel="chrome", headless=True, accept_downloads=True,
        args=["--disable-blink-features=AutomationControlled", "--headless=new"], user_agent=UA, viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    try:
        pg.goto("https://studio.tripo3d.ai/workspace/smart-uv", wait_until="domcontentloaded"); pg.wait_for_timeout(15000)
        print("credits before", credits(pg), flush=True)
        pg.query_selector_all("input[type=file]")[0].set_input_files(src)
        pg.get_by_text("Confirm", exact=True).last.wait_for(timeout=120000); pg.wait_for_timeout(3000); shot(pg, "import")
        pg.get_by_text("Confirm", exact=True).last.click()
        pg.get_by_text("Unwrap UV", exact=False).last.wait_for(timeout=120000); pg.wait_for_timeout(8000); shot(pg, "loaded")
        pg.get_by_text("Unwrap UV", exact=False).last.click(); pg.wait_for_timeout(4000); shot(pg, "unwrap_clicked")
        t0 = time.time(); done = False
        while time.time() - t0 < 600:                       # done when the Save button appears (one unwrap took > 5 min)
            pg.wait_for_timeout(10000)
            if pg.get_by_text("Save", exact=True).count() and pg.get_by_text("Save", exact=True).last.is_visible(): done = True; break
        shot(pg, "unwrapped")
        if not done:
            raise SystemExit("UNWRAP_PENDING: the unwrap is paid and keeps running server-side; finish later with "
                             "studio_smartuv_finish.py <tile x> <tile y> <out_dir> (do not upload again)")
        body = pg.inner_text("body"); util = body.split("Utilization")[1].split("%")[0].strip() if "Utilization" in body else "?"
        pg.get_by_text("Save", exact=True).last.click(); pg.wait_for_timeout(15000); shot(pg, "saved")
        print("utilization", util, "credits after", credits(pg), flush=True)
        pg.mouse.click(945, 864); pg.wait_for_timeout(4000); shot(pg, "export_dialog")   # bottom-bar Export (a toast can cover the text locator)
        with pg.expect_download(timeout=180000) as d:
            pg.mouse.click(997, 796)
        dl = d.value; path = os.path.join(out, dl.suggested_filename); dl.save_as(path)
        if path.lower().endswith(".zip"):
            with zipfile.ZipFile(path) as z: z.extractall(os.path.join(out, "export"))
        print("EXPORTED", path, flush=True)
    finally:
        shot(pg, "final"); ctx.close()
