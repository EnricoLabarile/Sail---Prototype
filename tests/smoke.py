"""Smoke test for Vento e Vele: two days of orders, no JS errors.
Day 1: bring home 3 fish before dinner (the guests' mood goes up). Day 2: a new
order at first light (fish of one kind and a village dish): buy the dish at its
village with foreign fish, bring it all home, and it's delivered.
Run from the project folder:  python tests/smoke.py
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

GAME = pathlib.Path(__file__).resolve().parent.parent / 'index.html'

# expose a few internals to the test (the game keeps its state in a closure)
HOOK = ('requestAnimationFrame(loop);\n})();',
        'globalThis.__d={boat,counts,VILLAGES,PIER,dishHold,'
        'get order(){return order},get sat(){return satisfaction},get moor(){return moor},'
        'get dayT(){return dayT},set dayT(v){dayT=v},'
        'dinnerT:(DINNER_HOUR-DAWN_HOUR)/24,'
        'unmoor(){moor=null;moorLock=null;}};'
        'tutSet("done");'                  # skip the tutorial: the test drives the controls directly
        'requestAnimationFrame(loop);\n})();')

def dock_at(pg, pier_expr):
    pg.evaluate(f"""()=>{{const d=__d; d.unmoor(); const pr={pier_expr}; const a=pr.total-20;
        d.boat.x=pr.x0+pr.dx*a - pr.dy*18; d.boat.y=pr.y0+pr.dy*a + pr.dx*18; d.boat.speed=5;}}""")
    pg.wait_for_timeout(2600)

def leave(pg):
    pg.keyboard.press('Space'); pg.wait_for_timeout(1300)          # weigh anchor

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
        o = pg.evaluate('__d.order')
        assert o['day'] == 1 and o['items'][0]['kind'] == 'fish' and o['items'][0]['n'] == 3, f'odd first order: {o}'
        leave(pg)
        assert not pg.evaluate('!!__d.moor'), 'did not leave the home pier'

        # day 1: three fish home before dinner
        pg.evaluate("()=>{__d.counts.sarde += 3}")
        dock_at(pg, 'd.PIER')
        assert pg.evaluate('__d.order.items.every(it=>it.got>=it.n)'), 'day 1 order not delivered'
        sat0 = pg.evaluate('__d.sat')
        pg.evaluate('()=>{__d.dayT = __d.dinnerT - 0.002}'); pg.wait_for_timeout(1500)   # dinner time
        assert pg.evaluate('__d.order.closed') and pg.evaluate('__d.sat') > sat0, 'dinner not served, or the mood did not rise'

        # day 2: first light brings a new order
        pg.evaluate('()=>{__d.dayT = 0.9995}'); pg.wait_for_timeout(1500)
        o = pg.evaluate('__d.order')
        assert o['day'] == 2 and any(it['kind'] == 'dish' for it in o['items']), f'odd second order: {o}'
        leave(pg)
        for it in o['items']:
            if it['kind'] == 'fish':
                pg.evaluate(f"()=>{{__d.counts['{it['key']}'] += {it['n']}}}")
            else:
                k = pg.evaluate(f"__d.VILLAGES.findIndex(v=>v.dishes.some(d=>d.icon==={it['icon']!r}))")
                # four foreign fish to pay with (3 coins each, a dish costs 6)
                pg.evaluate(f"""()=>{{const v=__d.VILLAGES[{k}]; const other=['sarde','sgombri','triglie','orate'].find(x=>x!==v.own); __d.counts[other]+=4; window.__pay=other;}}""")
                dock_at(pg, f'd.VILLAGES[{k}].pier')
                for _ in range(2):
                    pg.click('#mk-you-items .mk-unit[data-origin=you]'); pg.wait_for_timeout(50)
                pg.click(f'#mk-them-items .mk-unit[data-kind=food][aria-label^="{it["name"]},"]'); pg.wait_for_timeout(50)
                pg.click('#mk-deal'); pg.wait_for_timeout(200)
                assert pg.evaluate(f"__d.dishHold[{it['icon']!r}]") >= 1, f"{it['name']} not in the hold"
                leave(pg)
        dock_at(pg, 'd.PIER')
        assert pg.evaluate('__d.order.items.every(it=>it.got>=it.n)'), 'day 2 order not delivered: ' + str(pg.evaluate('__d.order'))
        b.close()
    if errors:
        print('JS errors:', *errors, sep='\n  '); sys.exit(1)
    print('OK: two days of orders delivered, dinner served, no JS errors')

if __name__ == '__main__':
    main()
