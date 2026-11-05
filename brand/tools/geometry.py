"""Exact construction of the Varaxis, Scholar and ClinicOS marks.

All geometry is defined here; nothing is traced at build time.
See ../README.md for the construction rules these numbers encode."""
import math
import numpy as np

def fillet(poly, radii, seg=24):
    """poly: list of (x,y) vertices (closed, no repeat); radii: per-vertex radius (0 = sharp). returns polyline."""
    P=np.array(poly,float); n=len(P); out=[]
    for i in range(n):
        r=radii[i]; p=P[i]
        if r<=0: out.append(tuple(p)); continue
        a=P[i-1]; b=P[(i+1)%n]
        u=(a-p)/np.linalg.norm(a-p); v=(b-p)/np.linalg.norm(b-p)
        ang=math.acos(np.clip(u@v,-1,1))             # interior angle
        t=r/math.tan(ang/2)                           # tangent length
        p1=p+u*t; p2=p+v*t
        bis=(u+v)/np.linalg.norm(u+v); c=p+bis*(r/math.sin(ang/2))
        a1=math.atan2(*(p1-c)[::-1]); a2=math.atan2(*(p2-c)[::-1])
        d=(a2-a1+math.pi)%(2*math.pi)-math.pi
        for s in np.linspace(0,1,seg): out.append(tuple(c+r*np.array([math.cos(a1+d*s),math.sin(a1+d*s)])))
    return out

S2=math.sqrt(2)
def f(v): s=f"{v:.3f}".rstrip('0').rstrip('.'); return '0' if s in ('-0','') else s
# ---------- generic rounded-polygon -> SVG path with true arcs ----------
def rounded_path(poly, radii):
    P=[np.array(p,float) for p in poly]; n=len(P); segs=[]
    for i in range(n):
        p=P[i]; r=radii[i]
        if r<=0: segs.append(('pt',p)); continue
        a=P[i-1]; b=P[(i+1)%n]
        u=(a-p)/np.linalg.norm(a-p); v=(b-p)/np.linalg.norm(b-p)
        ang=math.acos(np.clip(u@v,-1,1)); t=r/math.tan(ang/2)
        p1=p+u*t; p2=p+v*t
        din=p-a; dout=b-p; cross=din[0]*dout[1]-din[1]*dout[0]
        segs.append(('arc',p1,p2,r,1 if cross>0 else 0))
    d=[]
    for i,s in enumerate(segs):
        if s[0]=='pt': d.append(('M' if i==0 else 'L')+f"{f(s[1][0])} {f(s[1][1])}")
        else:
            d.append(('M' if i==0 else 'L')+f"{f(s[1][0])} {f(s[1][1])}")
            d.append(f"A{f(s[3])} {f(s[3])} 0 0 {s[4]} {f(s[2][0])} {f(s[2][1])}")
    return ''.join(d)+'Z'
def poly_points(poly,radii,seg=48):
    return fillet(poly,radii,seg)

# ---------- V mark (H=600, slope 3:2) ----------
V=dict(t=1.5, H=600, W1=192, r=50, G=63, W2=176, Lv=233, XT=567, Wt=268)
def v_geom(c=V):
    t,H,W1,r,G,W2,Lv,XT,Wt=c['t'],c['H'],c['W1'],c['r'],c['G'],c['W2'],c['Lv'],c['XT'],c['Wt']
    k=1/t
    slab=[(0,0),(W1,0),(W1+k*H,H),(k*H,H)]
    xr=W1+G+k*H; XL=xr-W2; yll=H-W2*t; Ys=yll-Lv
    sliver=[(XL,Ys),(XL+W2,Ys+W2*t),(XL+W2,H),(XL,yll)]
    tri=[(XT,0),(XT+Wt,0),(XT+Wt/2,(Wt/2)*t)]
    return dict(slab=(slab,[0,r,0,r]),sliver=(sliver,[0,0,0,0]),apex=(tri,[0,0,0]))
