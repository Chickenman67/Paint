from PIL import Image, ImageDraw, ImageFont
cands=[("consolab.ttf","Consolas Bold (CURRENT)"),("comicbd.ttf","Comic Sans MS Bold"),
       ("comic.ttf","Comic Sans MS"),("segoeprb.ttf","Segoe Print Bold"),
       ("segoepr.ttf","Segoe Print"),("Inkfree.ttf","Ink Free"),
       ("Candarab.ttf","Candara Bold"),("corbelb.ttf","Corbel Bold"),
       ("segoeuib.ttf","Segoe UI Bold"),("ARIALNB.TTF","Arial Narrow Bold")]
ref=Image.open('work/study/ref_s1_5.png').crop((0,0,1280,90))
W,H=1280,90+len(cands)*76+20
img=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(img)
img.paste(ref,(0,0)); d.text((900,30),"<- REFERENCE",fill='red')
y=92
for fn,label in cands:
    try: f=ImageFont.truetype("C:/Windows/Fonts/"+fn,44)
    except Exception as e: print("skip",fn,e); continue
    d.text((20,y),label,fill=(120,120,120),font=ImageFont.truetype("C:/Windows/Fonts/consola.ttf",18))
    d.text((330,y-4),"HD 188753 AB",fill='black',font=f,stroke_width=0)
    y+=76
img.save('work/study/font_specimen.png')
print("ok",img.size)
