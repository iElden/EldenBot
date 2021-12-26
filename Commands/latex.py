import requests
import nextcord
from PIL import Image

def get_formula(formula):
    r = requests.get( 'http://latex.codecogs.com/png.latex?\dpi{300} \huge %s' % formula )
    with open("formula.png", 'wb') as f:
        f.write(r.content)
    img = Image.open("formula.png")
    img = img.convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        if item[3] < 128:
            newData.append((255, 255, 255, 255))
        else:
            newData.append(item)
    img.putdata(newData)
    img.save("formula.png", "PNG")

class CmdLatex:
    async def cmd_latex(self, *args, channel, **_):
        args = "".join(args)
        get_formula(args)
        await channel.send(".", file=nextcord.File("formula.png", filename="formula.png"))
