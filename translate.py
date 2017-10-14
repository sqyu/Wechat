#coding=utf-8
from fake_useragent import UserAgent
import re
import urllib
import urllib2


#def translate(text, fromlang="auto", tolang="en"):
#    text = urllib.quote(text.encode("utf-8"), safe='')
#    url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=%s&tl=%s&dt=t&q=%s" % (fromlang, tolang, text)).replace("\\n", "%0A")
#    opener = urllib2.build_opener()
#    opener.addheaders = [('User-Agent', UserAgent().random)]
#    response = opener.open(url).read()
#    translated = response.split("\",\"")[0][4:].decode("utf-8")
#    if fromlang == "auto":
#        fromlang = re.findall(",\[\".*\"\]\]\]", response)[-1].split("\"")[1]
#    return translated, fromlang


def translate(text, fromlang="auto", tolang="en"):
    text = urllib.quote(text.encode("utf-8"), safe='')
    url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=%s&tl=%s&dt=t&q=%s" % (fromlang, tolang, text)).replace("\\n", "%0A")
    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', UserAgent().random)]
    response = opener.open(url).read()
    response = response[1:-1].replace(",null","").split("]],")
    fromlang = response[1].split("\"")[1]
    t = (response[0] + "]]").replace("[", "").split("],")
    tt = [map(lambda x:(x!="")*x[1:-1].replace("\\n", "\n").replace("\\\\ n","\\n").replace("\\\"", "\""), ss.replace("]","").split(",")) for ss in t] # \\n compes from real new line, \\ n comes from user input of "\n"
    translated = u"".join([ss[0].decode("utf-8") for ss in tt])
    return translated, fromlang

def google_translate(msg):
    try:
        tt = translate(msg['Text'], "auto", "en")
        if tt[1] == "en":
            tt = translate(msg['Text'], "en", "zh-TW")
        return tt[0]
    except:
        return u"翻譯失敗，不要問我為什麼我也不知道！"
