# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib
import fundamental

ranges = [{"from": 0xF900, "to": 0xFB00},         # compatibility ideographs
          {"from": 0x2F800, "to": 0x2FA20}, # compatibility ideographs
          {"from": 0x2E80, "to": 0x2F00},         # cjk radicals supplement
          {"from": 0x4E00, "to": 0xA000},
          #{"from": 0x3400, "to": 0xd4DC0},
          {"from": 0x20000, "to": 0x2A6E0},
          {"from": 0x2A700, "to": 0x2B740},
          {"from": 0x2B740, "to": 0x2B820},
          {"from": 0x2B820, "to": 0x2CEB0},  # included as of Unicode 8.0,
          {"from": 0x9FA6, "to": 0x9FCC}]

def is_chin(char):
  return any([range["from"] <= ord(char) <= range["to"] for range in ranges])

def parse(text):
    return " ".join(text.split()).replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n").replace("\n", "  ")

def lookup(char):
    try:
        r = urllib.urlopen("http://ytenx.org/zim?dzih="+urllib.quote(char.encode("utf-8"), safe='')+"&dzyen=1&jtkb=1&jtdt=1").read()
        soup = BeautifulSoup(r)
        for a in soup.findAll('a'):
            del a['href']
        res = []
        kwang = soup.find_all("h1")[1]
        h1 = h2 = h3 = p = blockquote = ""
        while kwang:
            if kwang.name is None:
                kwang = kwang.next_sibling
                continue
            if kwang.name == "h1":
                if p or blockquote:
                    res.append("\n".join(filter(None,[h1,h2,h3,p,blockquote])))
                    h2=h3=p=blockquote=""
                h1 = parse(kwang.text)
            if kwang.name == "h2":
                if p or blockquote:
                    res.append("\n".join(filter(None,[h1,h2,h3,p,blockquote])))
                    h3=p=blockquote=""
                h2 = parse(kwang.text)
            if kwang.name == "h3":
                if p or blockquote:
                    res.append("\n".join(filter(None,[h1,h2,h3,p,blockquote])))
                    p=blockquote=""
                h3 = parse(kwang.text)
            if kwang.name == "p":
                p = parse(kwang.text)
            if kwang.name == "blockquote":
                blockquote = parse(kwang.text)
            kwang = kwang.next_sibling
        res.append("\n".join(filter(None,[h1,h2,h3,p,blockquote])))
        return res
    except:
        return [u"查詢「" + char + u"」的過程中遇到問題"]

def ytenx(string):
    string = fundamental.remove_dup(filter(is_chin,string))
    if len(string) > 5:
        return [u"請將字數控制在五個字以內"]
    return [("\n"+"*"*20+"\n").join(lookup(char)) for char in string]
