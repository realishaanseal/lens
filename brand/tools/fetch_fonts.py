"""Download Montserrat (SIL OFL 1.1) from Google Fonts and pin the two weights the wordmarks use."""
import os, re, urllib.request
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, ".fonts")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"

def main():
    os.makedirs(OUT, exist_ok=True)
    req = urllib.request.Request("https://fonts.googleapis.com/css2?family=Montserrat:wght@100..900&display=swap", headers={"User-Agent": UA})
    css = urllib.request.urlopen(req).read().decode()
    url = re.search(r"url\((https://[^)]+)\)", css.split("/* latin */")[1]).group(1)
    vf = os.path.join(OUT, "Montserrat-VF-latin.woff2")
    urllib.request.urlretrieve(url, vf)
    for w in (500, 600):
        inst = instancer.instantiateVariableFont(TTFont(vf), {"wght": w})
        inst.flavor = None
        inst.save(os.path.join(OUT, f"Montserrat-{w}.ttf"))
    print("fonts ready in", OUT)

if __name__ == "__main__":
    main()
