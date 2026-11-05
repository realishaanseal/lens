"""Outlined wordmarks set in Montserrat (SIL OFL 1.1). The Λ is the V glyph flipped about the cap height."""
import os
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
FONTS={}
def font(w):
    if w not in FONTS:
        f=TTFont(os.path.join(os.path.dirname(__file__),'.fonts',f'Montserrat-{w}.ttf')); FONTS[w]=(f,f.getGlyphSet(),f.getBestCmap(),f['OS/2'].sCapHeight)
    return FONTS[w]
def glyph_path(ch,w):
    f,gs,cmap,cap=font(w); src='V' if ch=='A' else ch
    name=cmap[ord(src)]; p=pathops.Path(); gs[name].draw(p.getPen(glyphSet=gs)); p=pathops.simplify(p,fix_winding=True)
    bp=BoundsPen(None); p.draw(bp); return p,gs[name].width,bp.bounds,(ch=='A')
def wordmark(text,w,cap_units,tracking_em,x0=0.0,baseline=0.0):
    f,gs,cmap,cap=font(w); s=cap_units/cap; d=[]; x=x0; inkmin=None; inkmax=None; first=True
    for i,ch in enumerate(text):
        if ch==' ':
            sp=gs[cmap[32]].width; x+=(sp+tracking_em*1000)*s; continue
        p,adv,(bx0,by0,bx1,by1),flip=glyph_path(ch,w)
        sv=SVGPathPen(None)
        if flip: t=(s,0,0,s,x,baseline-s*cap)      # y' = baseline - s*(cap - y)
        else:    t=(s,0,0,-s,x,baseline)
        p.draw(TransformPen(sv,t)); d.append(sv.getCommands())
        lo=x+bx0*s; hi=x+bx1*s
        inkmin=lo if inkmin is None else min(inkmin,lo); inkmax=hi if inkmax is None else max(inkmax,hi)
        x+=(adv+tracking_em*1000)*s
    return d,(inkmin,inkmax)
