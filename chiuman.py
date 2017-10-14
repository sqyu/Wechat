#coding=utf-8
import my_glob
import itchat

def chiuman(msg):
    if my_glob.params.get("params", msg['FromUserName'], "chiuman") is None:
        my_glob.params.set("params", msg['FromUserName'], 0, "chiuman")
    funny = my_glob.funny_text[my_glob.params.get("params", msg['FromUserName'], "chiuman")]
    my_glob.params.set(task="params", UserName=msg['FromUserName'], value=(my_glob.params.get("params", msg['FromUserName'], "chiuman") + 1) % len(my_glob.funny_text), mode="chiuman")
    return funny
