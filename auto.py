#coding=utf-8
#from hanziconv import HanziConv
import hashlib
import itchat
import json
import my_glob
import random
import re
import requests


def process_response(text):
    if not (re.search(u"爱|喜欢|爱你|喜欢你|想你|爱上你|想我|爱我|喜欢我|爱上我", text) is None):
        text = random.choice([u"好的吧", u"Okay", u"你说的都对", u"去死吧", u"吃屎", u"滚犊子", u"呵呵", u"天线宝宝说你好"])
    text = text.replace(u"喔",u"哦").replace(u"呢", "").replace(u"嘛","").replace(u"呀","").replace(u"哇","").replace(u"耶","").replace(u"啦",u"吧").replace(u"呐","").replace(u"哇","").replace(u"人家", u"我").replace("~", "").replace(u"～", "")
    return text

def auto(msg):
    url = "http://www.tuling123.com/openapi/api"
    hash = hashlib.md5()
    hash.update(my_glob._from_UN(msg['FromUserName']).encode("utf-8"))
    userid = hash.hexdigest()
    data = {
        "key":"5f07968e58fd47b096561e74125a4c44",
        "info":msg['Text'].encode("utf-8"),
        "loc":"美國",
        "userid":userid
    }
    apicon=requests.post(url,data).text
    s=json.loads(apicon,encoding="utf-8")
    #transformed_text = u"\u0489".join(HanziConv.toTraditional(s['text'])) + u"（自動回覆）"
    return u"\u0489" + process_response(s['text']) + u"\u0489"
