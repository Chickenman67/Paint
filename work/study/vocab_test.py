from PIL import Image, ImageDraw, ImageFont
img=Image.new('RGB',(1280,540),'white'); d=ImageDraw.Draw(img)
labels=["HEADER (bold rounded caps)","PLANET LABEL (casual hand)"]
tests=[("comicbd.ttf","Comic Sans Bold"),("comic.ttf","Comic Sans"),("segoepr.ttf","Segoe Print")]
txt1="PSR B1257+12  KELT-9b  HD 80606 b"
txt2="HD 80606 b   PSR B1257+12   TrES-2b"
y=30
for fn,name in tests:
    f=ImageFont.truetype("C:/Windows/Fonts/"+fn,52)
    fs=ImageFont.truetype("C:/Windows/Fonts/"+fn,34)
    d.text((20,y),f"{name}  [header 52px]",fill=(150,150,150),font=ImageFont.truetype("C:/Windows/Fonts/consola.ttf",16))
    d.text((20,y+4),txt1,fill='black',font=f)
    d.text((20,y+70),f"{name}  [label 34px]",fill=(150,150,150),font=ImageFont.truetype("C:/Windows/Fonts/consola.ttf",16))
    d.text((20,y+74),txt2,fill='black',font=fs)
    y+=160
img.save('work/study/vocab.png'); print("ok")
