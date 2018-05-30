import os
from tkFileDialog import askopenfile
import Tkinter as tk
from Tkinter import *
from Tkinter import Label
from PIL import ImageTk
from PIL import Image
from utils import Service, encode_image
from pdf2image import convert_from_path, convert_from_bytes
import cv2
def drawWindow():
    window = tk.Tk()
    window.title("OCR Form") # sets the window title to the

    window.geometry("%dx%d+0+0" % (850, 700))
    window.resizable(0, 0)
    return window

def Closing():
    window.destroy()
# Global variables for window and canvas
window = drawWindow()
class Point:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
def get_rectangle(res):
    Pos=[]
    for i in range(4):
        x=res[i]['x']
        y = res[i]['y']
        P=Point(x,y)
        Pos.append(P)
    return Pos
def reset_points(points):
    P=[]
    P1=points[0];P2=points[1];P3=points[2];P4=points[3]
    cx=(P1.x+P2.x+P3.x+P4.x)/4;cy=(P1.y+P2.y+P3.y+P4.y)/4
    for i in range(4):
        if(points[i].x<cx and points[i].y<cy):
            Q1=Point(points[i].x,points[i].y)
        elif(points[i].x<cx and points[i].y>cy):
            Q2 = Point(points[i].x, points[i].y)
        elif (points[i].x > cx and points[i].y > cy):
            Q3 = Point(points[i].x, points[i].y)
        else:
            Q4 = Point(points[i].x, points[i].y)
    P.append(Q1);P.append(Q2);P.append(Q3);P.append(Q4)
    return P
def inline_H(points1, points2):
    points1=reset_points(points1)
    points2=reset_points(points2)
    w11=abs(points1[0].y-points1[1].y)
    w21 = abs(points1[2].y - points1[3].y)
    w12 = abs(points2[0].y - points2[1].y)
    w22 = abs(points2[2].y - points2[3].y)
    w1=float(w11+w21)/2.0
    w2 = float(w12 + w22) / 2.0
    if abs(w1-w2)<13 and abs(points1[3].y-points2[0].y)<15 and points1[0].x<points2[0].x+20:
        return True
    return False
def inline_W(points1, points2):
    points1 = reset_points(points1)
    points2 = reset_points(points2)
    w1=float(points1[1].y+points1[2].y) / 2.0
    w2 = float(points2[0].y+points2[3].y) / 2.0
    if abs(w1-w2)<80 and abs(points1[0].x-points2[0].x)<120:
        return True
    return False
def is_letter(s):
    s=s.lower()
    for c in s:
        if( c.islower()):
            return False
    return True

def is_number(s):
    for i in range (len(s)):
        try:
            float(s[i])
            return True
        except ValueError:
            pass

        try:
            import unicodedata
            unicodedata.numeric(s[i])
            return True
        except (TypeError, ValueError):
            pass


    return False
def find_invoice_number(res):
    n=len(res)
    m=min(n-1,120)
    flag=0
    for i in range(1,m):
        S=res[i]['description'].lower()
        if('invoice' in S or ('invoice' in S and 'number' in S)):
            points1=get_rectangle(res[i]['boundingPoly']['vertices'])
            t = max(i - 10, 0)
            index=t
            S1 = res[index]['description']
            points2 = get_rectangle(res[index]['boundingPoly']['vertices'])
            while ((len(S1) < 3 or is_number(S1) == False or (inline_H(points1, points2)==False and inline_W(points1, points2)==False)) and index<m):
                index += 1
                S1 = res[index]['description']
                points2 = get_rectangle(res[index]['boundingPoly']['vertices'])
            if ((len(S1) > 3 and is_number(S1) == True  and (
                inline_H(points1, points2) or inline_W(points1, points2)))):
                flag = 1
                break
    if(flag==1):
        if(inline_H(points1,points2) or inline_W(points1,points2)):
            S1=S1.strip('#')
            return S1
    return ''
def invoice_date(res):
    n = len(res)
    m = min(n - 1, 70)
    flag = 0
    for i in range(1, m):
        S = res[i]['description'].lower()
        if ('date' in S):
            if(i>0):
                T = res[i-1]['description'].lower()
                if(T=='order' or T=='price'):
                    continue
            points1 = get_rectangle(res[i]['boundingPoly']['vertices'])
            S1 = res[i + 1]['description']
            index = i + 1
            points2 = get_rectangle(res[index]['boundingPoly']['vertices'])
            while ((len(S1) < 3 or is_number(S1) == False or is_letter(S1)==False or (inline_H(points1, points2)==False and inline_W(points1, points2)==False)) and index<m):
                index += 1
                S1 = res[index]['description']
                points2 = get_rectangle(res[index]['boundingPoly']['vertices'])
            if((len(S1) > 3 and is_number(S1) == True and is_letter(S1) and (inline_H(points1, points2) or inline_W(points1, points2)))):
                flag = 1
                break
    if (flag == 1):
        S1 = S1.strip()
        return S1
    return ''
def total_amountname_check(S,T):
    if ('total' in S and ('totals' in S) == False and S != 'sub-total' and S != 'subtotal' and T!='tax'):
        return True
    if(S=='amount' and T=='due'):
        return True
    return False
def Totla_amount(res):
    n = len(res)
    flag = 0
    for i in range(1, n-1):
        S = res[i]['description'].lower()
        T= res[i+1]['description'].lower()
        if total_amountname_check(S,T):
            points1 = get_rectangle(res[i]['boundingPoly']['vertices'])
            t=max(i-10,0)
            S1 = res[t]['description']
            index = t
            points2 = get_rectangle(res[index]['boundingPoly']['vertices'])
            while ((len(S1) < 3 or is_number(S1) == False or (
                    inline_H(points1, points2) == False and inline_W(points1, points2) == False)) and index < n-1):
                index += 1
                S1 = res[index]['description']
                points2 = get_rectangle(res[index]['boundingPoly']['vertices'])
            if ((len(S1) > 3 and is_number(S1) == True and (inline_H(points1, points2) or inline_W(points1, points2)))):
                flag = 1
                break
    if (flag == 1):
        S1 = S1.strip()
        return S1
    return ''
def name_check(S1):
    if ('number' in S1 or 'invoice' in S1 or 'date' in S1):
        return True
    if ('client' in S1 or 'name' in S1 or 'due' in S1):
        return True
    if ('duplicate' in S1 or 'total' in S1 or 'appreciate' in S1):
        return True
    if ('budget' in S1 or 'section' in S1 or 'llc' in S1):
        return True
    flag,S=number_check(S1)
    if(flag):
        return True
    return False
def vendorname(res):
    S=res[0]['description'].split('\n')
    n=len(S)
    m=min(n,10)
    for i in range(m):
        S1=S[i].lower()
        if(name_check(S1)):
            continue
        return S1,i
    return ''
def vaddress_check(S1):
    if('usa' in S1 or 'chicago' in S1 or 'united state' in S1 or 'new york' in S1 or 'india' in S1):
        return True
    if('monterey park' in S1 or 'des plaines' in S1 or 'boulder' in S1):
        return True
    return False
def non_address(S1):
    if('.com' in S1 or '@' in S1 or 'address' in S1 or 'charge' in S1 or 'amount' in S1):
        return True
    return False
def vendor_address(res,vname, index):
    if(vname!=''):
        vname=vname.lower()
        S = res[0]['description'].split('\n')
        n = len(S)
        m = min(index+20, n)
        address=''
        for i in range(index+1,m):
            S1=S[i].lower().strip()
            v1=''.join(vname.split())
            S11 = ''.join(S1.split())
            if(v1 in S11):
                continue
            if (name_check(S1)):
                continue
            if(is_letter(S1)):
                continue
            if (non_address(S1)):
                continue
            address+=S[i].strip()+' '
            if(vaddress_check(S1)):
                address=address.strip()
                return address
    return ''
def number_check(S):
    S=S.strip('$')
    S = ''.join(S.split(','))
    if(len(S)>0 and S[0]=='s'):
        S = ''.join(S.split('s'))
    try:
        float(S)
        return True,S
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(S)
        return True,S
    except (TypeError, ValueError):
        pass
    return False,S
def order_points(indexes,res):
    for i in range(len(indexes)):
        P1 = get_rectangle(res[indexes[i]]['boundingPoly']['vertices'])
        P1 = reset_points(P1)
        for j in range(i,len(indexes)):
            P2 = get_rectangle(res[indexes[j]]['boundingPoly']['vertices'])
            P2 = reset_points(P2)
            if(P1[0].x>P2[0].x):
                T=P1
                P1=P2
                P2=T
                s=indexes[i]
                indexes[i]=indexes[j]
                indexes[j]=s
    return indexes

def find_item(res,index):
    result=''
    indexes=[]
    n = len(res)
    MP = get_rectangle(res[index]['boundingPoly']['vertices'])
    MP=reset_points(MP)
    for i in range(1, n-10):
        if(i==index):
            continue
        NP = get_rectangle(res[i]['boundingPoly']['vertices'])
        NP = reset_points(NP)
        if(MP[3].x<=NP[0].x):
            return ''
    for i in range(1, n-10):
        if (i == index):
            continue
        NP = get_rectangle(res[i]['boundingPoly']['vertices'])
        NP = reset_points(NP)
        if(abs(NP[3].y-MP[3].y)<10):
            indexes.append(i)
    if(len(indexes)>0):
        indexes=order_points(indexes,res)
        for i in range(len(indexes)):
            S = res[indexes[i]]['description']
            s=S.lower()
            s=''.join(s.split())
            if(s=='date' or s=='invoice' or s=='knife' or s=='total' or  s=='amountdue' or 'when' in s):
                return ''
            if ('city' in s  or 'page' in s  or 'amount' in s or 'job' in s or 'custom' in s):
                return ''
            if ('account' in s or 'umber' in s or 'street' in s or 'job' in s or 'custom' in s):
                return ''
            result+=S+' '
    return result.strip()
def item_find(res):
    n = len(res)
    items=[]
    for i in range(1, n):
        S = res[i]['description'].lower()
        flag,S=number_check(S)
        if(flag and float(S)!=0):
           item= find_item(res,i)
           if(item!=''):
            items.append(item+' '+S+'$')
    return items
def main1():
    directory = askopenfile()
    filename = directory.name
    W = 500
    H = 600
    tex.delete(1.0, END)
    tex.insert(tk.END, filename)
    if (".png" in filename  or ".jpg" in filename or ".pdf" in filename):
        if(".pdf" in filename):
            images =  convert_from_path(filename)
            im1=images[0]
            im1.save('jpg1.jpg')
            img = cv2.imread('jpg1.jpg')
            filename='jpg1.jpg'
        else:
            img = cv2.imread(filename)
        im1 = cv2.resize(img, (W, H))
        im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)
        im1 =Image.fromarray(im1)
        im1 = ImageTk.PhotoImage(im1)
        panelA = Label(image=im1)
        panelA.image = im1
        panelA.place(x=10, y=50)
        canvas = tk.Canvas(window, width=W, height=H)
        canvas.create_image(0, 0, image=im1, anchor=NW)
        canvas.place(x=10, y=50)

        """Run a text detection request on a single image"""
        # os.environ['VISION_API'] = 'F:/Mycompleted task/OCR/vendornam/key.json'
        access_token = 'AIzaSyDMTvUK6Mlr_BWwwjJ3eFVxhGDKixlFgjQ'

        service = Service('vision', 'v1', access_token=access_token)

        with open(filename, 'rb') as image:

            base64_image = encode_image(image)
            body = {
                'requests': [{
                    'image': {
                        'content': base64_image,
                    },
                    'features': [{
                        'type': 'TEXT_DETECTION',
                        'maxResults': 1,
                    }]

                }]
            }
            response = service.execute(body=body)
            res = response['responses'][0]['textAnnotations']
            invoice_num=find_invoice_number(res)
            invoice_dat=invoice_date(res)
            invoice_total=Totla_amount(res)
            invoice_name,index = vendorname(res)
            invoice_address=vendor_address(res,invoice_name, index)
            items=item_find(res)
            outtext.delete(1.0, END)
            result="Vendor name: " + invoice_name+'\n'
            result += "Vendor address: " + invoice_address + '\n'
            result += "Invoice number: " + invoice_num + '\n'
            result += "Invoice Date: " + invoice_dat + '\n'
            if(len(items)!=0):
                for t in range(len(items)):
                    result += "item"+str(t+1)+": " + items[t] + '\n'
            result += "Total Amount: " + invoice_total + '\n'
            outtext.insert(tk.END, result)
            print("invoice_num: "+invoice_num)
            print("invoice_date: " + invoice_dat)
            print("invoice_total: " + invoice_total)
            print("invoice_name: " + invoice_name)
            print("invoice_address: " + invoice_address)
    if os.path.exists('jpg1.jpg'):
        os.remove("jpg1.jpg")
def main():
    global tex,outtext
    global openflag
    tex = tk.Text(window, height=1, width=60, font=('comicsans', 9))
    tex.place(x=15, y=15)
    # here are the buttons
    OpenBtn = tk.Button(window, width=5, text='Open', fg='white', bg='purple', font=('comicsans', 10), command=main1)
    OpenBtn.place(x=460, y=10)
    outtext = tk.Text(window, height=39, width=45, font=('comicsans', 9))
    outtext.place(x=515, y=52)
    window.protocol('WM_DELETE_WINDOW', Closing)  # root is your root window

    window.mainloop()
if __name__ == '__main__':
    main()