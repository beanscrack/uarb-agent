import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    for i in range(3):
        try:
            pg.goto(f"file:///C:/Users/fortn/task1/uarb_agent/demo_src/reply_{i}_M12205_Exhibits.html")
            pg.wait_for_timeout(400)
            pg.screenshot(path=f"demo_src/reply_{i}.png")
            print("shot reply", i)
        except Exception as e:
            print("skip", i, e)
    b.close()
