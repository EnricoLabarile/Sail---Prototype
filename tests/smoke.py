"""Smoke test for Vento e Vele, no JS errors.
With the daily orders on (ORDERS_ON): two days of orders. Day 1: bring home 3 fish
before dinner (the guests' mood goes up, when it's on). Day 2: a new order at first
light (fish of one kind and a village dish): buy the dish at its village with foreign
fish, bring it all home, and it's delivered.
With the orders off: a trip to a village to buy a dish with foreign fish, back home,
a new day, and the logbook (day and cargo) opens.
Run from the project folder:  python tests/smoke.py
"""
import math, pathlib, sys
from playwright.sync_api import sync_playwright

GAME = pathlib.Path(__file__).resolve().parent.parent / 'index.html'

# expose a few internals to the test (the game keeps its state in a closure)
HOOK = ('requestAnimationFrame(loop);\n})();',
        'globalThis.__d={boat,counts,VILLAGES,PIER,dishHold,'
        'get order(){return order},get sat(){return satisfaction},satOn:SATISFACTION_ON,get moor(){return moor},'
        'get dayT(){return dayT},set dayT(v){dayT=v},'
        'dinnerT:(DINNER_HOUR-DAWN_HOUR)/24,ordersOn:ORDERS_ON,get dayNo(){return dayNo},'
        'RUINS,get powerOwned(){return powerOwned},get rig(){return boat.rig},bottles,bottleHold,marks,homeStore,banks,get fishing(){return fishing},get reelOn(){return reelOn},setReel,REEL_ZONE,'
        'unmoor(){moor=null;moorLock=null;}};'
        'tutSet("done");'                  # skip the tutorial: the test drives the controls directly
        'requestAnimationFrame(loop);\n})();')

def dock_at(pg, pier_expr):
    pg.evaluate(f"""()=>{{const d=__d; d.unmoor(); const pr={pier_expr}; const a=pr.total-20;
        d.boat.x=pr.x0+pr.dx*a - pr.dy*18; d.boat.y=pr.y0+pr.dy*a + pr.dx*18; d.boat.speed=5;}}""")
    pg.wait_for_timeout(2600)

def press_dock(pg):
    # the badge over the quay (it follows the camera, which may still be on its way: press it from the page)
    pg.wait_for_function("!document.getElementById('dock-btn').classList.contains('hidden')", timeout=5000)
    pg.evaluate("document.getElementById('dock-btn').click()")

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
        if pg.evaluate('__d.ordersOn'): orders(pg)
        else: trip(pg)
        b.close()
    if errors:
        print('JS errors:', *errors, sep='\n  '); sys.exit(1)
    print('OK: the voyage plays (orders ' + ('on' if ORDERS else 'off') + '), no JS errors')

ORDERS = None

def buy_dish(pg, k, name, icon):
    # four foreign fish to pay with (3 coins each, a dish costs 6)
    pg.evaluate(f"""()=>{{const v=__d.VILLAGES[{k}]; const other=['sarde','sgombri','triglie','orate'].find(x=>x!==v.own); __d.counts[other]+=4;}}""")
    dock_at(pg, f'd.VILLAGES[{k}].pier')
    press_dock(pg); pg.wait_for_timeout(300)               # the coins badge over the quay opens the market
    for _ in range(2):
        pg.click('#mk-you-items .mk-unit[data-origin=you]'); pg.wait_for_timeout(50)
    pg.click(f'#mk-them-items .mk-unit[data-kind=food][aria-label^="{name},"]'); pg.wait_for_timeout(50)
    pg.click('#mk-deal'); pg.wait_for_timeout(200)
    assert pg.evaluate(f"__d.dishHold[{icon!r}]") >= 1, f"{name} not in the hold"
    leave(pg)

def eolus(pg):
    # the fair wind is locked until the Temple of Eolus gives it
    if not pg.evaluate('__d.RUINS.some(r=>r.eolus)'): return
    assert not pg.evaluate('__d.powerOwned'), 'the fair wind is not locked at the start'
    dock_at(pg, 'd.RUINS.find(r=>r.eolus).pier')
    pg.wait_for_selector('#talk:not(.hidden)', timeout=5000)      # the spirit speaks: three lines, a tap each
    for _ in range(12):
        if pg.evaluate("document.getElementById('talk').classList.contains('hidden')"): break
        pg.click('#talk .t-btn'); pg.wait_for_timeout(250)
    assert pg.evaluate("document.getElementById('talk').classList.contains('hidden')"), 'the talk box did not close'
    assert pg.evaluate('__d.powerOwned'), 'Eolus did not give the fair wind'
    pg.wait_for_timeout(1500)
    leave(pg)

def bottle(pg):
    # a message in a bottle: anchored on it, the net fishes it up; a tap in the Cargo reads it and marks the chart
    if not pg.evaluate('__d.bottles.length'): return
    pg.evaluate("()=>{const d=__d; d.unmoor(); const bo=d.bottles[0]; d.boat.x=bo.x-6; d.boat.y=bo.y; d.boat.speed=0;}")
    pg.keyboard.press('Space'); pg.wait_for_timeout(6000)                # anchor down, the net goes over and comes back
    assert pg.evaluate('__d.bottleHold.length') == 1, 'the bottle was not fished up'
    assert pg.evaluate('__d.bottles.length') == 0, 'the other copies of the message are still at sea'
    pg.click('#btn-list', force=True); pg.wait_for_timeout(900)
    pg.click('.slot.bottle'); pg.wait_for_timeout(300)
    assert pg.evaluate('__d.marks.length') == 1, 'reading the message put no cross on the chart'
    pg.click('#letter')
    # the bottle is picked by that tap: throw it overboard to make room
    pg.click('.throw'); pg.wait_for_timeout(200)
    assert pg.evaluate('__d.bottleHold.length') == 0, 'the bottle was not thrown overboard'
    pg.click('#btn-list', force=True); pg.wait_for_timeout(900)
    leave(pg)

def reel(pg):
    # anchored on a fish bank: a bite, the reel round the hub and the bar; turning the reel lifts the band;
    # kept on the fish the meter fills and it's caught; left alone it gets away
    pg.evaluate('__d.setReel(true)')                  # (off by default: the test switches it on)
    def anchor_on_bank():
        pg.evaluate("()=>{const d=__d; d.unmoor(); const b=d.banks.find(b=>b.state==='live'); d.boat.x=b.x; d.boat.y=b.y; d.boat.speed=0;}")
        pg.keyboard.press('Space')
        pg.wait_for_function("__d.fishing && __d.fishing.phase==='game'", timeout=9000)
        assert pg.evaluate("!document.getElementById('reel').classList.contains('hidden')"), 'the reel did not show'
    anchor_on_bank()
    fish0 = pg.evaluate('Object.values(__d.counts).reduce((a,n)=>a+n,0)')
    pg.evaluate("()=>{const t=setInterval(()=>{const f=__d.fishing; if(!f||f.phase!=='game'){clearInterval(t);return;} const g=f.game; window.__zmax=Math.max(window.__zmax||0, g.z); g.f=g.z+__d.REEL_ZONE/2; g.fv=0;},16);}")
    r = pg.evaluate("(()=>{const r=document.querySelector('#reel').getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2];})()")
    pg.mouse.move(r[0], r[1]-77); pg.mouse.down()
    for i in range(1, 50):
        a = -math.pi/2 + i*0.25
        pg.mouse.move(r[0] + 77*math.cos(a), r[1] + 77*math.sin(a)); pg.wait_for_timeout(16)
    pg.mouse.up()
    pg.wait_for_function("!__d.fishing || __d.fishing.phase!=='game'", timeout=8000)
    assert pg.evaluate('window.__zmax') > 0.15, 'turning the reel did not lift the band'
    assert pg.evaluate('Object.values(__d.counts).reduce((a,n)=>a+n,0)') > fish0, 'the fish kept in the band was not caught'
    leave(pg); pg.wait_for_timeout(1200)
    anchor_on_bank()
    pg.evaluate("()=>{const t=setInterval(()=>{const f=__d.fishing; if(!f||f.phase!=='game'){clearInterval(t);return;} const g=f.game; g.f=0.95; g.tgt=0.95; g.fv=0;},16);}")
    pg.wait_for_function("!__d.fishing || __d.fishing.phase!=='game'", timeout=8000)
    assert pg.evaluate("__d.fishing && __d.fishing.phase==='cancel'"), 'the fish left alone did not get away'
    assert pg.evaluate("document.getElementById('reel').classList.contains('hidden')"), 'the reel stayed up'
    leave(pg)
    pg.evaluate('__d.setReel(false)')

def trip(pg):
    global ORDERS; ORDERS = False
    leave(pg)
    assert not pg.evaluate('!!__d.moor'), 'did not leave the home pier'
    eolus(pg)
    reel(pg)
    bottle(pg)
    d = pg.evaluate('__d.VILLAGES[0].dishes[0]')
    buy_dish(pg, 0, d['name'], d['icon'])
    dock_at(pg, 'd.PIER')
    assert pg.evaluate('__d.moor && __d.moor.pier === __d.PIER'), 'did not tie up at home'
    # the crate badge opens the storehouse: a fish goes into it
    fish0 = pg.evaluate('Object.values(__d.counts).reduce((a,n)=>a+n,0)')
    press_dock(pg); pg.wait_for_timeout(300)
    pg.click('#mk-you-items .mk-unit[data-kind=fish]'); pg.wait_for_timeout(50)
    pg.click('#mk-deal'); pg.wait_for_timeout(200)
    assert pg.evaluate('Object.values(__d.counts).reduce((a,n)=>a+n,0)') == fish0 - 1, 'nothing went into the storehouse'
    assert pg.evaluate('Object.values(__d.homeStore.fish).reduce((a,n)=>a+n,0)') == 1, 'the storehouse is empty'
    pg.evaluate('()=>{__d.dayT = 0.9995}'); pg.wait_for_timeout(1500)
    assert pg.evaluate('__d.dayNo') == 2, 'no new day at first light'
    pg.click('#btn-list', force=True); pg.wait_for_timeout(900)
    assert 'Day 2' in pg.inner_text('#shoplist-body'), 'the logbook does not show the day'
    # the spare sail in the hold: a tap rigs it, the old one goes in its place
    if pg.query_selector('.spare-sail'):
        rig = pg.evaluate('__d.rig')
        pg.click('.spare-sail'); pg.wait_for_timeout(200)
        assert pg.evaluate('__d.rig') != rig, 'the spare sail was not rigged'

def orders(pg):
        global ORDERS; ORDERS = True
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
        assert pg.evaluate('__d.order.closed'), 'dinner not served'
        assert not pg.evaluate('__d.satOn') or pg.evaluate('__d.sat') > sat0, 'the mood did not rise'

        # day 2: first light brings a new order
        pg.evaluate('()=>{__d.dayT = 0.9995}'); pg.wait_for_timeout(1500)
        o = pg.evaluate('__d.order')
        assert o['day'] == 2 and any(it['kind'] == 'dish' for it in o['items']), f'odd second order: {o}'
        leave(pg)
        # the dishes first (paid with foreign fish), then the ordered fish, so the
        # fish tapped across at the stall are always the foreign ones
        for it in sorted(o['items'], key=lambda it: it['kind'] == 'fish'):
            if it['kind'] == 'fish':
                pg.evaluate(f"()=>{{__d.counts['{it['key']}'] += {it['n']}}}")
            else:
                k = pg.evaluate(f"__d.VILLAGES.findIndex(v=>v.dishes.some(d=>d.icon==={it['icon']!r}))")
                buy_dish(pg, k, it['name'], it['icon'])
        dock_at(pg, 'd.PIER')
        assert pg.evaluate('__d.order.items.every(it=>it.got>=it.n)'), 'day 2 order not delivered: ' + str(pg.evaluate('__d.order'))

if __name__ == '__main__':
    main()
