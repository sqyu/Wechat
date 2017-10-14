#coding=utf-8

import fundamental
import re
from merriam_webster.api import (LearnersDictionary, CollegiateDictionary,
                                 WordNotFoundException)

learnkey, collkey = ("0", "1") ## You need to get your own API key from Merriam-Webster

def lookup_single(query):
    query = query.encode("utf-8")
    try:
        collegiate = CollegiateDictionary(collkey)
        learners = LearnersDictionary(learnkey)
        try:
            defs = [(entry.word, entry.function, definition)
                for entry in collegiate.lookup(query)
                for definition, examples in entry.senses]
        except WordNotFoundException:
            defs = []
        if defs == []:
            return u"Merriam-Webster's Collegiate字典中找不到" + query.decode("utf-8") + u"這個詞"
        try:
            ipas = ["["+ipa+"]" for entry in learners.lookup(query) for ipa in entry.pronunciations]
            if ipas != []:
                ipas = u"發音：" + u"/".join(list(set(ipas))) + "\n"
            else:
                ipas = ""
        except WordNotFoundException:
            ipas = ""
        return query.decode("utf-8") + u"\n" + ipas + u"\n".join(map(lambda x:(u"{0}: {1}".format(x[1][0].upper()+x[1][1:].lower(),x[2])), defs))
    except:
        return u"查詢" + query.decode("utf-8") + u"中發生錯誤，請換詞重試"

def lookup(query):
    words = re.split(u"\s*[,，]\s*", query)
    words = fundamental.remove_dup(words)
    if len(words) > 5:
        return (u"請將搜索單詞數控制在五個以內。")
    return ("\n" + "*"*20 + "\n").join(map(lookup_single, words))
