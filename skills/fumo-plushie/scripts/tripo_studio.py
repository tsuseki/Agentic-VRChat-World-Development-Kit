"""Drive the Tripo Studio web UI (headless Chrome via Playwright) for the plush pipeline: generate 4 takes, look at them, texture one, export it.
Studio-only: the API cannot select Smart Mesh P2.0 Quad with these options, and Studio credits are separate from API credits.

Usage:  python tripo_studio.py <step> <run_dir> [args]
  generate <run_dir> [faces=2000]   upload <run_dir>/tripo_slots/{front,left,right,back}.png, Smart Mesh P2.0, Quad, polycount `faces`
                                    (2000 -> about 2,700 faces / 4.4k tris), same count on, 4 generations (100 credits). Screenshots in <run_dir>/studio/.
  takes <run_dir>                   screenshot the four newest takes (front view + face/vertex counts): studio/take{1..4}.png and studio/takes.png (contact row)
  views <run_dir>                   rotate each take and screenshot it (grid studio/views_grid.png) to check the back and sides before choosing
  texture <run_dir> <take 1-4>      sidebar Texture panel: Remove Lighting ON, 2K (10 credits)
  export <run_dir> <take 1-4>       Export -> FBX (Blender preset) zip into <run_dir>/gen/, extracted to <run_dir>/gen/export/

Environment (required, nothing is hard-coded):
  TRIPO_STUDIO_PROFILE  persistent Chrome profile directory that already holds the logged-in Studio session / Cloudflare clearance
If Studio Chrome is stale, kill only the chrome.exe processes whose command line contains the profile directory name.
The click coordinates assume a 1440x900 viewport; the four newest takes are the top tiles of the right-hand asset list."""
import os, sys, glob, zipfile
from playwright.sync_api import sync_playwright
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
TAKE_POS = [(1362, 210), (1245, 328), (1362, 328), (1245, 445)]       # newest first: take 1 = top right tile
URL = "https://studio.tripo3d.ai/workspace/generate"
step, run = sys.argv[1], os.path.abspath(sys.argv[2]); extra = sys.argv[3:]
SD = os.path.join(run, "studio"); os.makedirs(SD, exist_ok=True)
profile = os.environ.get("TRIPO_STUDIO_PROFILE") or sys.exit("set TRIPO_STUDIO_PROFILE to the Studio Chrome profile directory")
def shot(pg, name): pg.screenshot(path=os.path.join(SD, name)); print("shot", name, flush=True)
def open_ctx(p):
    return p.chromium.launch_persistent_context(profile, channel="chrome", headless=True, args=["--disable-blink-features=AutomationControlled", "--headless=new"],
                                                user_agent=UA, viewport={"width": 1440, "height": 900})
def goto(pg, wait=15000): pg.goto(URL, wait_until="domcontentloaded"); pg.wait_for_timeout(wait)
with sync_playwright() as p:
    ctx = open_ctx(p); pg = ctx.new_page()
    if step == "generate":
        faces = extra[0] if extra else "2000"; slots = os.path.join(run, "tripo_slots")
        goto(pg, 12000)
        pg.get_by_text("Smart", exact=False).filter(has_text="Mesh").first.click(); pg.wait_for_timeout(2500)
        pg.mouse.click(167, 189); pg.wait_for_timeout(2500)                      # multiview tab
        for f in ("front", "left", "right", "back"):
            pg.query_selector_all("input[type=file]")[0].set_input_files(os.path.join(slots, f + ".png")); pg.wait_for_timeout(5000)
        pg.get_by_text("Topology", exact=True).first.click(); pg.wait_for_timeout(1500)       # Quad is the default; the panel holds the polycount
        pg.mouse.click(555, 690, click_count=3); pg.keyboard.type(faces); pg.keyboard.press("Enter"); pg.wait_for_timeout(1000)
        shot(pg, "before_generate.png")
        pg.get_by_text("Generate", exact=False).filter(has_text="100").last.click()
        pg.wait_for_timeout(5000)
        for k in range(1, 12):
            pg.wait_for_timeout(15000); shot(pg, "progress_%02d.png" % k)
    elif step == "takes":
        goto(pg)
        from PIL import Image
        row = Image.new("RGB", (4 * 560, 560))
        for k, (x, y) in enumerate(TAKE_POS, 1):
            pg.mouse.click(x, y); pg.wait_for_timeout(6000); shot(pg, "take%d.png" % k)
            row.paste(Image.open(os.path.join(SD, "take%d.png" % k)).convert("RGB").crop((330, 60, 1130, 860)).resize((560, 560)), ((k - 1) * 560, 0))
        row.save(os.path.join(SD, "takes.png"))
    elif step == "views":
        goto(pg)
        from PIL import Image
        grid = Image.new("RGB", (4 * 400, 4 * 400))
        for k, (x, y) in enumerate(TAKE_POS, 1):
            pg.mouse.click(x, y); pg.wait_for_timeout(6000)
            pg.mouse.click(1105, 108); pg.wait_for_timeout(2500)                  # clay/solid shading
            for j in range(4):
                shot(pg, "view_t%d_%d.png" % (k, j))
                grid.paste(Image.open(os.path.join(SD, "view_t%d_%d.png" % (k, j))).convert("RGB").crop((380, 60, 1120, 800)).resize((400, 400)), (j * 400, (k - 1) * 400))
                pg.mouse.move(600, 560); pg.mouse.down(); pg.mouse.move(730, 560, steps=10); pg.mouse.up(); pg.wait_for_timeout(1500)
        grid.save(os.path.join(SD, "views_grid.png"))
    elif step == "texture":
        x, y = TAKE_POS[int(extra[0]) - 1]
        goto(pg); pg.mouse.click(x, y); pg.wait_for_timeout(6000)
        pg.mouse.click(39, 470); pg.wait_for_timeout(3000)                        # sidebar Texture panel
        pg.mouse.click(285, 407); pg.wait_for_timeout(800)                        # Remove Lighting toggle (off by default)
        pg.mouse.click(114, 472); pg.wait_for_timeout(1200); shot(pg, "before_texture.png")   # 2K
        pg.mouse.click(190, 856); pg.wait_for_timeout(5000)                       # Generate Texture (10 credits)
        for k in range(1, 9):
            pg.wait_for_timeout(15000); shot(pg, "texture_%02d.png" % k)
            if k >= 4:
                body = pg.inner_text("body")
                if "Generating" not in body and "%" not in body: break
        shot(pg, "textured.png")
    elif step == "export":
        x, y = TAKE_POS[int(extra[0]) - 1]; out = os.path.join(run, "gen"); os.makedirs(out, exist_ok=True)
        goto(pg); pg.mouse.click(x, y); pg.wait_for_timeout(9000)
        pg.get_by_text("Export", exact=True).last.click(); pg.wait_for_timeout(3500)
        with pg.expect_download(timeout=120000) as d: pg.mouse.click(1033, 796)   # dialog Export button (FBX, Blender preset, 2K)
        dl = d.value; path = os.path.join(out, "studio_export_" + dl.suggested_filename); dl.save_as(path)
        ex = os.path.join(out, "export"); os.makedirs(ex, exist_ok=True)
        with zipfile.ZipFile(path) as z: z.extractall(ex); print("extracted", z.namelist())
        shot(pg, "after_export.png")
    ctx.close()
