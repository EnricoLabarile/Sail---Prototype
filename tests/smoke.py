"""Smoke test for Vento e Vele: full shopping trip (every dish: Banquet ending), no JS errors.
Run from the project folder:  python tests/smoke.py
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

GAME = pathlib.Path(__file__).resolve().parent.parent / 'index.html'

# expose a few internals to the test (the game keeps its state in a closure)
HOOK = ('requestAnimationFrame(loop);\n})();',
        'globalThis.__d={boat,counts,VILLAGES,PIER,get moor(){return moor},'
        'unmoor(){moor=null;moorLock=null;}};requestAnimationFrame(loop);\n})();')

def dock_at(pg, pier_expr):
    pg.evaluate(f"""()=>{{const d=__d; d.unmoor(); const pr={pier_expr}; const a=pr.total-20;
        d.boat.x=pr.x0+pr.dx*a - pr.dy*18; d.boat.y=pr.y0+pr.dy*a + pr.dx*18; d.boat.speed=5;}}""")
    pg.wait_for_timeout(2600)

def main():
    html = GAME.read_text(encoding='utf-8')
    assert HOOK[0] in html, 'loop hook not found: update HOOK in tests/smoke.py'
    html = html.replace(*HOOK)
    errors = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = b.new_page(viewport={'width': 360, 'height': 740})
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.set_content(html)
        pg.click('#start-btn', force=True)          # the button pulses, so force the click
        pg.wait_for_timeout(300)
        pg.keyboard.press('Space'); pg.wait_for_timeout(1500)   # weigh anchor, leave home
        assert not pg.evaluate('!!__d.moor'), 'did not leave the home pier'
        for k in range(4):
            pg.evaluate(f"""()=>{{const v=__d.VILLAGES[{k}]; const other=['sarde','sgombri','triglie','orate'].find(x=>x!==v.own); __d.counts[other]+=8;}}""")
            dock_at(pg, f'd.VILLAGES[{k}].pier')
            # barter table: tap the eight foreign fish across to the stall (2 coins
            # each), tap both dishes across to the hold (at most 14 coins), trade;
            # buying both brings the gift too
            for _ in range(8):
                pg.click('#mk-you-items .mk-unit[data-origin=you]'); pg.wait_for_timeout(50)
            for _ in range(2):
                pg.click('#mk-them-items .mk-unit[data-kind=food]'); pg.wait_for_timeout(50)
            pg.click('#mk-deal'); pg.wait_for_timeout(200)
            pg.keyboard.press('Space'); pg.wait_for_timeout(1300)   # weigh anchor
        bought = pg.evaluate('__d.VILLAGES.map(v=>v.dishes.every(d=>d.bought) && v.giftGot)')
        assert all(bought), f'not every dish and gift aboard: {bought}'
        dock_at(pg, 'd.PIER')
        pg.wait_for_timeout(11000)                    # banquet text, then the end screen
        title = pg.inner_text('#go-title')
        assert pg.is_visible('#gameover') and 'banquet' in title.lower(), f'no banquet ending ({title})'
        b.close()
    if errors:
        print('JS errors:', *errors, sep='\n  '); sys.exit(1)
    print('OK: full trip, banquet served, no JS errors')

if __name__ == '__main__':
    main()
