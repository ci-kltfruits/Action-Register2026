#!/usr/bin/env python3
"""Usage: python patch_index.py [path/to/index.html]
Applies: (1) Christmas/Halloween mutual exclusion, (2) smaller/more/faster bats+leaves,
(3) sprite-based Halloween rendering (fixes lag). Writes a .bak backup first."""
import sys, shutil

path = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(path, encoding='utf-8').read()
shutil.copyfile(path, path + '.bak')

def swap(old, new):
    global s
    if s.count(old) != 1:
        sys.exit('Could not find a unique match for:\n' + old[:80] + '\n(already patched?)')
    s = s.replace(old, new)

# 1) one theme at a time
swap("function setXmas(on, quiet){\n  const root = document.documentElement;",
     "function setXmas(on, quiet){\n  if (on && isHweenOn()) setHween(false, true);\n  const root = document.documentElement;")
swap("function setHween(on, quiet){\n  const root = document.documentElement;",
     "function setHween(on, quiet){\n  if (on && isXmasOn()) setXmas(false, true);\n  const root = document.documentElement;")

# 2+3) replace startHweenFx() entirely
start_marker = "// Falling bats + drifting leaves, mirroring startSnow()'s canvas approach.\nfunction startHweenFx(){"
end_marker = "function stopHweenFx(){"
a = s.find(start_marker); b = s.find(end_marker)
if a == -1 or b == -1 or b < a:
    sys.exit('Could not locate startHweenFx() block.')

NEW_FX = r'''// Falling bats + drifting leaves. Emoji are pre-rendered once into sprites, then blitted with
// drawImage each frame (much cheaper than calling fillText on color emoji every frame).
function startHweenFx(){
  if (_hweenFx) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const canvas = document.createElement('canvas');
  canvas.id = 'hweenCanvas';
  canvas.style.cssText = 'position:fixed; inset:0; width:100%; height:100%; pointer-events:none; z-index:9999;';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  let W = 0, H = 0, dpr = 1, bits = [], raf = 0;

  function makeSprite(ch){
    const c = document.createElement('canvas');
    c.width = c.height = 64;
    const g = c.getContext('2d');
    g.font = '52px sans-serif';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText(ch, 32, 34);
    return c;
  }
  const batImg = makeSprite('\u{1F987}');
  const leafImg = makeSprite('\u{1F342}');

  function resize(){
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    const n = W < 720 ? 60 : 110;
    while (bits.length < n) bits.push(make(true));
    bits.length = n;
  }
  function make(initial){
    const isBat = Math.random() < 0.4;
    return {
      x: Math.random() * W,
      y: isBat ? (initial ? Math.random() * H : -20 - Math.random() * 40) : (-10 - (initial ? Math.random() * H : Math.random() * 40)),
      r: Math.random() * 8 + 13,
      s: Math.random() * 0.6 + (isBat ? 0.55 : 0.8),
      d: Math.random() * Math.PI * 2, w: Math.random() * 0.03 + 0.01,
      o: Math.random() * 0.3 + 0.65,
      bat: isBat, rot: 0, rotSpeed: isBat ? 0 : (Math.random() * 0.02 - 0.01)
    };
  }
  function frame(){
    raf = requestAnimationFrame(frame);
    if (document.hidden) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const b of bits){
      if (b.bat){
        b.x += Math.sin(b.d) * 1.1;
        b.y += b.s * 0.75;
        b.d += b.w * 2;
      } else {
        b.y += b.s;
        b.d += b.w;
        b.x += Math.sin(b.d) * 0.6;
        b.rot += b.rotSpeed;
      }
      if (b.y > H + 20){ Object.assign(b, make(false)); b.x = Math.random() * W; }
      if (b.x > W + 20) b.x = -20; else if (b.x < -20) b.x = W + 20;

      const size = b.r * 1.2;
      ctx.globalAlpha = b.o;
      if (b.bat){
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.drawImage(batImg, b.x - size / 2, b.y - size / 2, size, size);
      } else {
        const c = Math.cos(b.rot) * dpr, sn = Math.sin(b.rot) * dpr;
        ctx.setTransform(c, sn, -sn, c, b.x * dpr, b.y * dpr);
        ctx.drawImage(leafImg, -size / 2, -size / 2, size, size);
      }
    }
    ctx.globalAlpha = 1;
  }
  window.addEventListener('resize', resize);
  resize();
  frame();
  _hweenFx = { stop(){ cancelAnimationFrame(raf); window.removeEventListener('resize', resize); canvas.remove(); } };
}

'''
s = s[:a] + NEW_FX + s[b:]
open(path, 'w', encoding='utf-8').write(s)
print('Patched', path, '(backup at', path + '.bak)')
