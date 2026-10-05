#!/usr/bin/env python3
"""Build reproducible static visuals with Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
NAVY, BLUE, TEAL, GOLD, RED, LIGHT, WHITE = "#14213D", "#2F67D8", "#159D8C", "#F4B942", "#D95D5D", "#F4F7FB", "white"

def font(size, bold=False):
    path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"
    return ImageFont.truetype(path, size)

def arrow(d, a, b, color=NAVY):
    d.line([a,b], fill=color, width=5)
    x,y=b; d.polygon([(x,y),(x-16,y-9),(x-16,y+9)], fill=color)

def matrix():
    im=Image.new("RGB",(1800,1100),WHITE); d=ImageDraw.Draw(im)
    d.text((90,55),"Kestrel opportunity portfolio favors bounded augmentation",fill=NAVY,font=font(48,True))
    x0,y0,x1,y1=220,170,1650,950; d.rounded_rectangle((x0,y0,x1,y1),25,fill=LIGHT)
    d.line((935,y0,935,y1),fill="#A7B0C0",width=4); d.line((x0,560,x1,560),fill="#A7B0C0",width=4)
    d.text((1320,870),"START",fill=TEAL,font=font(30,True)); d.text((270,205),"STRATEGIC / DEFER",fill=RED,font=font(28,True))
    pts=[("OPP-01\nReferral intake",1370,260,TEAL),("OPP-02\nDenial feedback",1450,420,BLUE),("OPP-03\nAppeal finder",960,550,GOLD),("OPP-04\nAuth chase",550,260,RED),("OPP-05\nCredentialing",550,410,"#8D72B8"),("OPP-06\nBalance agent",320,720,"#777777")]
    for label,x,y,c in pts:
        d.ellipse((x-35,y-35,x+35,y+35),fill=c,outline=WHITE,width=5)
        d.multiline_text((x+50,y-35),label,fill=NAVY,font=font(22,True),spacing=3)
    d.text((760,1000),"Feasibility →",fill=NAVY,font=font(28,True)); d.text((35,520),"Impact →",fill=NAVY,font=font(28,True))
    im.save(ROOT/"05-Opportunities"/"opportunity-matrix.png")

def swimlane():
    im=Image.new("RGB",(2200,1200),WHITE); d=ImageDraw.Draw(im)
    d.text((70,40),"Referral intake crosses four lanes before a clinic can act",fill=NAVY,font=font(52,True))
    lanes=[("RightFax",190),("Coordinator",420),("Reference data",650),("Caregate / clinic",880)]
    for name,y in lanes:
        d.rounded_rectangle((60,y,2140,y+165),20,fill=LIGHT,outline="#D5DCE7",width=3); d.text((90,y+55),name,fill=NAVY,font=font(27,True))
    steps=[("Fax arrives",390,230,BLUE),("Open + inspect",650,460,TEAL),("Lookup provider",950,690,GOLD),("Enter referral",1260,460,TEAL),("Missing data?",1550,460,RED),("Clinic review",1860,920,BLUE)]
    boxes=[]
    for label,x,y,c in steps:
        box=(x,y,x+215,y+75); boxes.append(box); d.rounded_rectangle(box,14,fill=c); d.text((x+18,y+23),label,fill=WHITE,font=font(20,True))
    for i in range(len(boxes)-1): arrow(d,(boxes[i][2],(boxes[i][1]+boxes[i][3])//2),(boxes[i+1][0],(boxes[i+1][1]+boxes[i+1][3])//2))
    d.text((1515,585),"Exception loop: seek missing information",fill=RED,font=font(22,True))
    d.text((330,1115),"Observed sample: 10 faxes  •  Projected handling: 6.3–8.1 min/fax  •  Human retains routing decision",fill=NAVY,font=font(25))
    im.save(ROOT/"04-Process-maps"/"WF-O02-referral-swimlane.png")

if __name__=="__main__": matrix(); swimlane(); print("Built opportunity matrix and referral swimlane")
