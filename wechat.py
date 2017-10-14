#coding=utf-8
import itchat
from itchat.content import *
import operator
import os
import re
import shutil
import signal
import sys
import threading
import time

import my_glob
import fundamental
import auto
import chiuman
import translate
import my_weather
import stock
import twitter
import mw
import ytenx
import wiki

class TimeoutError(Exception):
    pass

def handler(signum, frame):
    raise TimeoutError()

def safe_exec(command, msg):
    """\
    Executes a function (that returns a text to be sent to the user) or kill after 31 seconds
    """
    try:
        signal.signal(signal.SIGALRM, handler); signal.alarm(31) ##
        return_text = eval(command)
        signal.alarm(0); return return_text
    except TimeoutError:
        pass; return u"等候時間超過30秒，請求超時。"

def reverse(msg):
    return msg['Text'][::-1]


def match(keywords, friend=False, group=False):
    """\
    keywords: a list of keywords to match (A LIST! CANNOT BE A STRING)
    friend: search friends
    group: search groups
    """
    ress = []
    send_text = ""
    if keywords != [] and keywords[-1] == "FORCE":
        force = True
        keywords = keywords[:-1]
    else:
        force = False
    if friend:
        res_friends = [tu for kk in keywords for tu in my_glob.search_friend(kk)]
        if res_friends == []: send_text = send_text + u"\n検索条件に一致する友達が見つかりません。\n"
        elif len(res_friends) > 10 and not force: send_text = send_text + u"\n友達の検索結果が10件以上あります。続けるには、キーワードに「FORCE」を入れてもう一度検索してください。\n"
        else: send_text = send_text + u"\n友達の検索結果：\n" + u"\n".join([res[0] for res in res_friends]) + "\n"; ress = ress + [res[1] for res in res_friends]
    if group:
        res_chatrooms = [tu for kk in keywords for tu in my_glob.search_chatroom(kk)]
        if res_chatrooms == []: send_text = send_text + u"\n検索グループに一致するグループが見つかりません。\n"
        elif len(res_chatrooms) > 10 and not force: send_text = send_text + u"\nグループの検索結果が10件以上あります。続けるには、キーワードに「FORCE」を入れてもう一度検索してください。\n"
        else: send_text = send_text + u"\nグループの検索結果：\n" + u"\n".join([res[0] for res in res_chatrooms]) + "\n"; ress = ress + [res[1] for res in res_chatrooms]
    fundamental.send_to_me(send_text)
    return ress

def man():
    return u"モードリスト：$man mode, $manmode, $mode list, $modelist, $mode names, $modenames\n"  + \
        u"システムパラメータをローカルファイルに手動保存：$SAVE, $SAFE, $SAVE PARAMS, $SAVE PARAMETERS, $SA, $S, $保存 $保\n" + \
        u"パソコンのシステムファイルの手動更新後、システムとシンクロするには：$REFRESH, $UPDATE, $UP, $R, $更, $更新\n ** ローカルファイルを手動更新する前はまず既存の設定をローカルに保存してください。** \n" + \
	u"友達リストをアップデート:$UPDATE FRIENDS, $UP FRIENDS, $REFRESH FRIENDS, $RE FRIENDS, $UF, $RF\n" + \
        u"ユーザーをブロックリストに登録：$block User1/User2/...\n" + \
        u"ユーザーをブロックリストから解除：$unblock User1/User2/...\n" + \
        u"グループをホワイトリストに登録：$good User1/User2/...\n" + \
        u"グループをホワイトリストから解除：$ungood User1/User2/...\n" + \
        u"ユーザーやグループを検索：$search User1/User2/...\n" + \
        u"ユーザーやグループのモードを設定：$mode User modenameや$mode User 0（初期化）や$mode User None（削除）\n" + \
        u"以上いずれもキーワード検索可。ただし、十件以上の検索結果がある場合、$block User1/User2/.../FORCEが必要。\n" + \
        u"自分との会話をリダイレクト：$redirect User\n" + \
        u"リダイレクトを解除：$stop redirectまたは$stop re\n" + \
        u"グリーティングを睡眠モードに：$sleepまたは$sleeping\n" + \
        u"睡眠モードを解除：$wakeまたは$wakeup\n" + \
        u"あらゆるユーザのモードを検証：$USER_MODE, $USER_MODES, $USER MODE $USER MODES\n" + \
        u"あらゆるユーザのラストプレータイムを検証：$USER_TIME, $USER_TIMES, $USER TIME, $USER TIMES\n" + \
        u"プロンプトメッセージの変更：$MESSAGE、削除：$MESSAGE CLEAR, $MESSAGE REMOVE, $MESSAGE NONE\n" + \
        u"ユーザーアリアスの変更：$CHANGE NAME, $CHANGE REMARK (NAME), $CHANGE ALIAS, $SET ALIAS"

def command(text):
    if text.upper() in ["SAVE", "SAFE", "SAVE PARAMS", "SAVE PARAMETERS", "SAVE_PARAMS", "SAVE_PARAMETERS", "SAVE PARAMETRES", "SAVE_PARAMETRES", "SA", "S", u"保存", u"保"]:
        my_glob.params.write_all()
        fundamental.send_to_me(u"パラメータをセーブしました。")
    elif text.upper() in ["REFRESH","UPDATE","UP","R",u"更",u"更新"]:
        my_glob.params = my_glob.system_params()
        fundamental.send_to_me(u"パラメータをアップデートしました。")
    elif text.upper() in ["UPDATE FRIENDS", "UP FRIENDS", "REFRESH FRIENDS", "RE FRIENDS", "UF", "RF"]:
        my_glob.fl = my_glob.friend_lists()
	fundamental.send_to_me(u"Friend list updated.")
    elif text in ["blocklist", "block list", "block_list", "blacklist", "black list", "black_list", "block", "black"]:
        fundamental.send_to_me(u"只今ブロックされている友たちは次の通りです：" + u" | ".join(my_glob.params.blocking_list) + u"。\nユーザーを（アン）ブロックするには、「$(un)block User1/User2」で入力してください。")
    elif text in ["whitelist", "white list", "white_list", "white", "good", "good group", "good groups", "goodlist", "good list", "good_list", "good", "white"]:
        fundamental.send_to_me(u"只今ホワイトリストにあるグループは次の通りです：" + u" | ".join(my_glob.params.good_groups) + u"。\nユーザーを（アン）グッドするには、「$(un)good Group1/Group2」で入力してください。")
    elif text.startswith("block "):
        for res in match(fundamental.remove_dup(text.replace("block ", "").split("/")), friend=True, group=False):
            my_glob.params.set(task="blocking", UserName=res, value="add")
        my_glob.params.write("blocking_list")
        fundamental.send_to_me(u"新たにブロックされた友たちは以上です。")
    elif text.startswith("unblock "):
        for res in match(fundamental.remove_dup(text.replace("unblock ", "").split("/")), friend=True, group=False):
            my_glob.params.set(task="blocking", UserName=res, value="remove")
        my_glob.params.write("blocking_list")
        fundamental.send_to_me(u"ブラックリストから取り除かれた友たちは以上です。")
    elif text.startswith("good "):
        for res in match(fundamental.remove_dup(text.replace("good ", "").split("/")), friend=False, group=True):
            my_glob.params.set(task="good_group", UserName=res, value="add")
        my_glob.params.write("good_groups")
        fundamental.send_to_me(u"新たにホワイトリストに登録されたグループは以上です。")
    elif text.startswith("ungood "):
        for res in match(fundamental.remove_dup(text.replace("ungood ", "").split("/")), friend=False, group=True):
            my_glob.params.set(task="good_group", UserName=res, value="remove")
        my_glob.params.write("good_groups")
        fundamental.send_to_me(u"ホワイトリストから削除されたグループは以上です。")
    elif text.startswith("search "):
        match(fundamental.remove_dup(text.replace("search ", "").split("/")), friend=True, group=True)
    elif text.startswith("mode ") and len(text.split(" ")) >= 3:
        mode = text.split(" ")[-1]
        text = " ".join(text.split(" ")[1:-1])
        if mode == "0": mode = "CHANGE" # Shortcut
        elif mode == "None": mode = None
        elif not mode in my_glob.modes: fundamental.send_to_me(u"現在サポートされているモードは次の通りです（CHANGEは０でも可）：\n" + u"\n".join(my_glob.modes)); return False
        ress = match([text], friend=True, group=True)
        if len(ress) > 1: fundamental.send_to_me(u"検索結果が複数ありますので、実行できませんでした。"); return False
        elif len(ress) == 1: my_glob.params.set(task="mode", UserName=ress[0], value=mode); fundamental.send_to_me(u"以上のユーザーのモードを" + unicode(mode) + u"に変えました。\n");
        my_glob.params.write("friend_mode")
    elif text.startswith("redirect "):
        ress = match([text.replace("redirect ", "")], friend=True, group=True)
        if len(ress) > 1: fundamental.send_to_me(u"検索結果が複数ありますので、実行できませんでした。"); return False
        elif len(ress) == 1: my_glob.redirect_me_to = ress[0]; fundamental.send_to_me(u"会話をリダイレクトしました。Successfully redirected conversation.\n")
    elif text.upper() in ["STOP REDIRECT", "STOP RE"]:
        my_glob.redirect_me_to = my_glob.me; fundamental.send_to_me(u"会話のリダイレクトを解除しました。\n")
    elif text.upper() in ["SLEEP", "SLEEPING"]:
        my_glob.sleeping = True; fundamental.send_to_me(u"睡眠モードに切り替えました。\n")
    elif text.upper() in ["WAKE", "WAKEUP"]:
        my_glob.sleeping = False; fundamental.send_to_me(u"睡眠モードを解除しました。\n")
    elif text.upper() in ["MANMODE", "MAN_MODE", "MAN MODE", "MODE_LIST", "MODE LIST", "MODELIST", "MODENAMES", "MODE NAMES"]:
        fundamental.send_to_me(u"只今サポートされているモードは：" + u"、".join(my_glob.modes[:-1]) + u"と" + my_glob.modes[-1] + u"です。")
    elif text.startswith("time "):
        for res in match(fundamental.remove_dup(text.replace("time ", "").split("/")), friend=True, group=True):
            my_glob.params.set(task="time", UserName=res)
        my_glob.params.write("times")
        fundamental.send_to_me(u"上記の友達とグループのラストプレータイムを現在に設定しました。")
    elif text.upper() in ["USER_MODE", "USER_MODES", "USER MODE", "USER MODES"]:
        return_text = u"\n".join([user[0] + u": " + my_glob.modes[user[1]] for user in sorted(my_glob.params.friend_mode.items(), key=operator.itemgetter(1))]) ## Added "unicode()" to avoid None
        if return_text: fundamental.send_to_me(u"只今記録のあるユーザのモードは次のとおりです：\n" + return_text)
        else: fundamental.send_to_me(u"ユーザのモードログが見つかりませんでした。\n")
    elif text.upper() in ["USER_TIME", "USER_TIMES", "USER TIME", "USER TIMES"]:
        now = time.time()
        return_text = u"\n".join([user[0] + u": " + unicode(now - user[1]) + u"秒前" for user in sorted(my_glob.params.friend_times.items(), key=operator.itemgetter(1))]) ## Added "unicode()" to avoid None
        if return_text: fundamental.send_to_me(u"只今記録のあるユーザのラストプレータイムは次のとおりです：\n" + return_text)
        else: fundamental.send_to_me(u"ユーザのラストプレータイムログが見つかりませんでした。\n")
    elif text.upper().startswith("MESSAGE") or text.upper().startswith("MASSAGE") or text.upper().startswith("MESAGE") or text.upper().startswith("MASAGE"):
        if not " " in text:
            my_glob.prompt_message = ""
            fundamental.send_to_me(u"プロンプトメッセージを削除しました。\n")
        else:
            text = " ".join(text.split(" ")[1:])
            if text.upper() in ["NONE", "CLEAR", "REMOVE"]:
                my_glob.prompt_message = ""
                fundamental.send_to_me(u"プロンプトメッセージを削除しました。\n")
            else:
                my_glob.prompt_message = text
                fundamental.send_to_me(u"プロンプトメッセージを次の通りに設定しました：\n" + my_glob.prompt_message)
    elif text.upper().startswith("CHANGE NAME") or text.upper().startswith("CHANGE REMARK") or text.upper().startswith("CHANGE REMARK NAME") or text.upper().startswith("CHANGE ALIAS") or text.upper().startswith("SET ALIAS"):
        text = text.replace("CHANGE NAME", "").replace("CHANGE REMARK NAME", "").replace("CHANGE REMARK", "").replace("CHANGE ALIAS", "").replace("SET ALIAS", "").lstrip()
        if len(text.split("/")) != 2:
            fundamental.send_to_me(u"$CHANGE NAME BEFORE_NAME/AFTER_NAME\n")
        else:
            res = my_glob.search_friend(text.split("/")[0])
            if res == []:
                fundamental.send_to_me(text.split("/")[0] + u"の検索結果が見つかりませんでした。\n")
            elif len(res) > 1:
                fundamental.send_to_me(unicode(len(res)) + u"件の検索結果が見つかりました：\n" + u"\n".join([f[0] for f in res[0:5]]) + u"\n（下略）"*(len(res)>5))
            else:
                old_alias = res[0][0]
                usern = res[0][1]
                new_alias = text.split("/")[1]
                itchat.set_alias(userName=usern, alias=new_alias)
                my_glob.fl = my_glob.friend_lists()
                if old_alias in my_glob.params.friend_mode:
                    my_glob.params.friend_mode[new_alias] = my_glob.params.friend_mode.pop(old_alias)
                if old_alias in my_glob.params.friend_params:
                    my_glob.params.friend_params[new_alias] = my_glob.params.friend_params.pop(old_alias)
                if old_alias in my_glob.params.friend_times:
                    my_glob.params.friend_times[new_alias] = my_glob.params.friend_times.pop(old_alias)
                if old_alias in my_glob.params.blocking_list:
                    my_glob.params.blocking_list[new_alias] = my_glob.params.blocking_list.pop(old_alias)
                my_glob.params.write_all()
                fundamental.send_to_me(old_alias + u"のアリアスを" + new_alias + u"に変えました。")
    elif text.upper() in ["KILL", "QUIT", "EXIT"]:
        raise KeyboardInterrupt
    else:
        fundamental.send_to_me(man())


def process(msg, group = False):
    #if msg['FromUserName'] == my_glob.me:
    #    return
    #msg['RemarkName'] = my_glob.UserName_to_name(msg['FromUserName'])
    #if msg['RemarkName'] == None:
    #    print("No remark name for this person. Returned.")
    #    return
    if time.time() - my_glob.last_save_time > 300:
        my_glob.params.write_all()
        my_glob.last_save_time = time.time()
    msg['Text'] = msg['Text'].rstrip(".").rstrip(u"。") ##
    if msg['FromUserName'] == my_glob.me and msg['Text'].startswith("$"):
        command(msg['Text'][1:])
        return
    if my_glob.params.get("time", msg['FromUserName']) :
        if my_glob.params.get("mode", msg['FromUserName']) == "shutup" and (time.time() - my_glob.params.get("time", msg['FromUserName']) > 18000.0): ## If shutup, reset after 5 hrs instead of 20 mins
            fundamental.mysend(u"上次閉嘴時間為%d分鍾前，超過五小時，已重置。\n" % int((time.time() - my_glob.params.get("time", msg['FromUserName']))/60), msg['FromUserName'])
            my_glob.params.set(task="mode", UserName=msg['FromUserName'], value=None)
        elif my_glob.params.get("mode", msg['FromUserName']) != "shutup" and (time.time() - my_glob.params.get("time", msg['FromUserName']) > 1200.0):
            fundamental.mysend(u"您上次玩耍時間為%d秒前，超過二十分鐘，已重置。\n" % (time.time() - my_glob.params.get("time", msg['FromUserName'])), msg['FromUserName'])
            my_glob.params.set(task="mode", UserName=msg['FromUserName'], value=None) # It's possible that someone stopped choosing the mode and then time elapsed for more than 10 min, so initialize mode
    my_glob.params.set(task="time", UserName=msg['FromUserName'])
    if (len(msg['Text']) <= 3 and msg['Text'].startswith(u"停")) or msg['Text'].upper().startswith("FUCK") or msg['Text'].upper().startswith("STOP") or u"[On Fire]" in msg['Text'] or u"傻逼" in msg['Text']:
        fundamental.mysend("[Silence][Distressed]", msg['FromUserName'])
        return
    if (my_glob.params.get(task="mode", UserName=msg['FromUserName']) is None) or msg['Text'] in my_glob.change_chinese:
        if group: fundamental.mysend("#GREETING1#", msg['FromUserName'], msg) # If group
        else: fundamental.mysend("#GREETING1#", msg['FromUserName'])
        my_glob.params.set(task="mode", UserName=msg['FromUserName'], value="CHANGE")
        my_glob.params.set(task="params", UserName=msg['FromUserName'], value=None, mode="stock") # If change mode from stock, need to reset stock ticker # The set function takes care of the case with no stock
        return
    if my_glob.params.get(task="mode", UserName=msg['FromUserName']) == "shutup":
        if (u"機器人" in msg['Text'] and (u"出來" in msg['Text'] or u"回來" in msg['Text'] or u"出現" in msg['Text'])) or (u"机器人" in msg['Text'] and (u"出来" in msg['Text'] or u"回来" in msg['Text'] or u"出现" in msg['Text'])) or (u"機器人呢" in msg['Text']) or (u"机器人呢" in msg['Text']) or (msg['Text'] in [u"召唤", u"召喚", u"召回", u"召唤!", u"召喚!", u"召回!", u"召唤！", u"召喚！", u"召回！"]):
            fundamental.mysend(u"我在這呢！\n要我回來，請說換！", msg['FromUserName'])
        return
    if msg['Text'].startswith(u"闭嘴") or msg['Text'].startswith(u"閉嘴") or msg['Text'].startswith(u"收皮"):
        my_glob.params.set("mode", msg['FromUserName'], value="shutup")
        fundamental.mysend(my_glob.modes_greeting["shutup"], msg['FromUserName'])
        return
    if msg['Text'] == u"我":
        fundamental.mysend(u"你是" + (my_glob._to_NN(msg['FromUserName']) or u"誰？"), msg['FromUserName'])
        return
    if msg['Text'] == u"你":
        fundamental.mysend(u"我是小異邦人！", msg['FromUserName'])
        return
    #if my_glob.params.get(task="mode", UserName=msg['FromUserName']) == "CHANGE":
    for mode in ["chat", "google_translate", "chiuman", "weather", "stock", "mw", "ytenx", "wiki"]: ## In any mode, if user input is a mode name, switch to that mode
        if msg['Text'] == str(my_glob.modes_indices[mode]) or msg['Text'] in my_glob.modes_alt_names[mode]:
            my_glob.params.set("mode", msg['FromUserName'], mode)
            if mode == "stock":  # If stock, send indices first and then greeting
                fundamental.mysend(stock.get_indices(), msg['FromUserName'])
            fundamental.mysend(my_glob.modes_greeting[mode] + u"\n（此後更換模式請輸入「換」，或直接輸入模式名）", msg['FromUserName']) # Send greeting
            if mode == "chiuman": # If chiuman, send greeting first and then start stories
                fundamental.mysend(chiuman.chiuman(msg), msg['FromUserName'])
            return
    if msg['Text'] == str(my_glob.modes_indices["shutup"]): ## In any mode, if user input is a mode name, switch to that mode
        my_glob.params.set("mode",msg['FromUserName'], value="shutup")
        fundamental.mysend(my_glob.modes_greeting["shutup"] + u"\n（此後更換模式請輸入「換」，或直接輸入模式名）", msg['FromUserName'])
        return
    elif msg['Text'] == str(my_glob.modes_indices["reverse"]) or msg['Text'] in my_glob.modes_alt_names["reverse"]: ## In any mode, if user input is a mode name, switch to that mode
        my_glob.params.set("mode",msg['FromUserName'], value="reverse")
        try: to = my_glob._to_NN(msg['FromUserName']) ## Individual friend chat
        except:
            try: to = msg['ActualNickName'] ## Group chat
            except: to = u"客官"
        fundamental.mysend((u"好的，" + to)[::-1] + u"\n（此後更換模式請輸入「換」，或直接輸入模式名）", msg['FromUserName'])
        return
    elif msg['Text'] == str(my_glob.modes_indices["twitter"]) or msg['Text'] in my_glob.modes_alt_names["twitter"]: ## In any mode, if user input is a mode name, switch to that mode
        my_glob.params.set("mode", msg['FromUserName'], value="twitter")
        try:
            userlangs = [my_glob.lang_names[la] for la in my_glob.params.get("params", msg['FromUserName'], "lang")]
        except:
            userlangs = [u"中文", u"英語"]
        fundamental.mysend(my_glob.modes_greeting["twitter"] % (u"、".join(userlangs[:-1])+u"和"+userlangs[-1]) + u"\n（此後更換模式請輸入「換」，或直接輸入模式名）", msg['FromUserName'])
        return
    elif my_glob.params.get(task="mode", UserName=msg['FromUserName']) == "CHANGE": ## If user really is in the change mode but entered wrong input
        if msg['Text'] == "0":
            fundamental.mysend(u"[Smile]你自己就是個0吧[Smile]說了讓你輸1-%s！[Smile]" % (len(my_glob.modes) - 1), msg['FromUserName'])
            return
        elif msg['Text'] == str(len(my_glob.modes)):
            fundamental.mysend(u"[Smile]你以為我不知道你輸了"+str(len(my_glob.modes))+u"？[Smile]", msg['FromUserName'])
            return
        else: # Really wrong input
            fundamental.mysend("#GREETING2#", msg['FromUserName'])
            return
        #my_glob.params.set("params", msg['FromUserName'], None) # Not sure why this was here
        return # Can return here if user is meant to change mode
    # Otherwise, continue with the current mode
    if my_glob.params.get("mode", msg['FromUserName']) == "chat":
        send_text = auto.auto(msg)
    elif my_glob.params.get("mode", msg['FromUserName']) == "google_translate":
        send_text = translate.google_translate(msg)
    elif my_glob.params.get("mode", msg['FromUserName']) == "chiuman":
        send_text = chiuman.chiuman(msg)
    elif my_glob.params.get("mode", msg['FromUserName']) == "reverse":
        send_text = reverse(msg)
    elif my_glob.params.get("mode", msg['FromUserName']) == "weather":
        send_text = my_weather.weather(msg)
    elif my_glob.params.get("mode", msg['FromUserName']) == "stock":
        send_text = stock.get_stock(msg)
    elif my_glob.params.get("mode", msg['FromUserName']) == "twitter":
        twitter.good_lang = (my_glob.params.get("params", msg['FromUserName'], "lang") or ["zh", "en"])
        send_text = twitter.tweet()
    elif my_glob.params.get("mode", msg['FromUserName']) == "mw":
        send_text = mw.lookup(msg['Text'])
    elif my_glob.params.get("mode", msg['FromUserName']) == "ytenx":
        res = ytenx.ytenx(msg['Text'])
        for send_text in res:
            if send_text != "":
                fundamental.mysend(send_text, msg['FromUserName'])
    elif my_glob.params.get("mode", msg['FromUserName']) == "wiki": ## Immediately reset after wiki is done so that user will not search again by mistake
        try: send_text = safe_exec("wiki.wiki(msg)", msg)
        except: send_text = u"維基百科抓取失敗。"
        signal.alarm(0)
        fundamental.mysend(send_text + u"\n已為您重置回主菜單。", msg['FromUserName'])
        my_glob.params.set(task="mode", UserName=msg['FromUserName'], value="CHANGE")
        if group: fundamental.mysend("#GREETING1#", msg['FromUserName'], msg) # If group
        else: fundamental.mysend("#GREETING1#", msg['FromUserName'])
        return
    fundamental.mysend(send_text, msg['FromUserName'])


@itchat.msg_register([TEXT, MAP, CARD, SHARING])
def textReply(msg):
    try:
        fundamental.display(msg)
    except:
        pass
    if msg['FromUserName'] != my_glob.me and not msg['FromUserName'] in my_glob.fl.UN_to_RN:
        fundamental.send_to_me(u"新しい友達" + msg.get("NickName", "??") +  u"を追加しました。$rfや$ufを入力して友達リストをアップデートしてください。")
        return
    try:
        Revocation_helper(msg)
    except:
        print("Revoke helper unsuccessful.")
    if my_glob.params.get("blocking", msg['FromUserName']):
        print("User blocked")
        return
    if msg['Type'] == 'Text':
        process(msg, group = False)

@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def download_files(msg):
    try:
    	Revocation_helper(msg)
    except:
        print("Revoke helper unsuccessful.")
    if msg['FromUserName'] != my_glob.me and not msg['FromUserName'] in my_glob.fl.UN_to_RN:
        fundamental.send_to_me(u"新しい友達" + msg.get("NickName", "??") +  u"を追加しました。$rfや$ufを入力して友達リストをアップデートしてください。")
        return
    if my_glob.params.get("blocking", msg['FromUserName']) or my_glob.params.get("mode", msg['FromUserName']) == "shutup":
        return
    # msg['Text']是一个文件下载函数
    # 传入文件名，将文件下载下来
    msg['Text'](msg['FileName'])
    # 把下载好的文件再发回给发送者
    itchat.send('@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName']),
                msg['FromUserName'])
    #return '@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName'])


@itchat.msg_register([TEXT, SHARING], isGroupChat=True)
def group_reply(msg):
    fundamental.display(msg, True)
    if msg['IsAt']:
        fundamental.mysend(u"@"+my_glob._group_member_NN(msg)+u"\u2005我替主人收到你的消息啦", msg['FromUserName'])
    if my_glob.params.get("good_group", msg['FromUserName']):
        my_glob.params.set(task="time", UserName=msg['FromUserName'])
        Revocation_helper(msg)
        if msg['Type'] == 'Text':
            process(msg, group = True)
    else: # If not a good group, still call revocation helper but send to myself only
        Revocation_helper(msg, send_back=False)

@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
def group_download_files(msg):
        # msg['Text']是一个文件下载函数
        # 传入文件名，将文件下载下来
        # 把下载好的文件再发回给发送者
        #return '@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName'])
    if my_glob.params.get("good_group", msg['FromUserName']):
        Revocation_helper(msg)
        if my_glob.params.get("mode", msg['FromUserName']) == "shutup":
            return
        msg['Text'](msg['FileName'])
        itchat.send('@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName']),
         msg['FromUserName'])

#ClearTimeOutMsg用于清理消息字典，把超时消息清理掉
#为减少资源占用，此函数只在有新消息动态时调用
def ClearTimeOutMsg():
    if my_glob.msg_dict.__len__() > 0:
        for msgid in list(my_glob.msg_dict): #由于字典在遍历过程中不能删除元素，故使用此方法
            if time.time() - my_glob.msg_dict.get(msgid, None)["msg_time"] > 130.0: #超时两分钟
                item = my_glob.msg_dict.pop(msgid)
                #print("超时的消息：", item['msg_content'])
                #可下载类消息，并删除相关文件
                if item['msg_type'] == "Picture" \
                        or item['msg_type'] == "Recording" \
                        or item['msg_type'] == "Video" \
                        or item['msg_type'] == "Attachment":
                    print("要删除的文件：", item['msg_content'])
                    os.remove(item['msg_content'])

#将接收到的消息存放在字典中，当接收到新消息时对字典中超时的消息进行清理
#没有注册note（通知类）消息，通知类消息一般为：红包 转账 消息撤回提醒等，不具有撤回功能
def Revocation_helper(msg, send_back=True):
    #print("Revocation helper called.")
    mytime = time.localtime()  # 这儿获取的是本地时间
    #获取用于展示给用户看的时间 2017/03/03 13:23:53
    msg_time_touser = mytime.tm_year.__str__() \
                      + "/" + mytime.tm_mon.__str__() \
                      + "/" + mytime.tm_mday.__str__() \
                      + " " + mytime.tm_hour.__str__() \
                      + ":" + mytime.tm_min.__str__() \
                      + ":" + mytime.tm_sec.__str__()
    msg_id = msg['MsgId'] #消息ID
    msg_time = msg['CreateTime'] #消息时间
    ### This doesn't work for groups! Consider reading directly from ###
    msg_from = my_glob._to_NN(msg['FromUserName']) # For friends
    if msg_from == "None": msg_from = msg.get('FromUserName', "") + u" 的 " + my_glob._group_member_NN(msg) # For groups
    if msg_from == u" 的 ": msg_from = u"你" # If some error occurred during retrieving the send-from username
    msg_type = msg['Type'] #消息类型
    msg_content = None #根据消息类型不同，消息内容不同
    msg_url = None #分享类消息有url
    #图片 语音 附件 视频，可下载消息将内容下载暂存到当前目录
    if msg['Type'] == 'Text':
        msg_content = msg['Text']
    elif msg['Type'] == 'Picture':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Card':
        msg_content = msg['RecommendInfo']['NickName'] + u"的名片"
    elif msg['Type'] == 'Map':
        x, y, location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*", msg['OriContent']).group(1,2,3)
        if location is None:
            msg_content = r"緯度->" + x.__str__() + " 経度->" + y.__str__()
        else:
            msg_content = r"" + location
    elif msg['Type'] == 'Sharing':
        msg_content = msg['Text']
        msg_url = msg['Url']
    elif msg['Type'] == 'Recording':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Attachment':
        msg_content = r"" + msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Video':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Friends':
        msg_content = msg['Text']
    #更新字典
    # {msg_id:(msg_from,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
    my_glob.msg_dict.update(
        {msg_id: {"msg_from": msg_from, "msg_time": msg_time, "msg_time_touser": msg_time_touser, "msg_type": msg_type,
                  "msg_content": msg_content, "msg_url": msg_url, "send_back": send_back}})
    #清理字典
    try:
        ClearTimeOutMsg()
    except:
        pass

#收到note类消息，判断是不是撤回并进行相应操作
@itchat.msg_register([NOTE])
def SaveMsg(msg):
    # print(msg)
    #创建可下载消息内容的存放文件夹，并将暂存在当前目录的文件移动到该文件中
    if not os.path.exists(".\\Revocation\\"):
        os.mkdir(".\\Revocation\\")
    print("Something just got revoked.")
    if re.search(r"\<replacemsg\>\<\!\[CDATA\[.*撤回了一条消息\]\]\>\<\/replacemsg\>", msg['Content']) != None or re.search(r"\<replacemsg\>\<\!\[CDATA\[.*rappelé un message.\]\]\>\<\/replacemsg\>", msg['Content'].encode('utf-8')) != None:
        old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)
        old_msg = my_glob.msg_dict.get(old_msg_id, {})
        if old_msg.get('msg_from', "") == my_glob._to_NN(my_glob.me): ## Me !!!!
            return
        #print(old_msg_id, old_msg)
        msg_send = old_msg.get('msg_from', "") \
                   + u" 在 [" + old_msg.get('msg_time_touser', "") \
                   + u"], 撤回了一条 ["+old_msg['msg_type']+u"] 消息, 内容如下:" \
                   + old_msg.get('msg_content', None)
        if old_msg['msg_type'] == "Sharing":
            msg_send += u", 链接: " \
                        + old_msg.get('msg_url', None)
        elif old_msg['msg_type'] == 'Picture' \
                or old_msg['msg_type'] == 'Recording' \
                or old_msg['msg_type'] == 'Video' \
                or old_msg['msg_type'] == 'Attachment':
            msg_send += u", 存储在当前目录下Revocation文件夹中"
            shutil.move(old_msg['msg_content'], u".\\Revocation\\")
        print(msg_send)
        itchat.send(msg_send, toUserName='filehelper') #将撤回消息的通知以及细节发送到文件助手
        if old_msg.get('send_back', True): # If send back to user
            itchat.send(msg_send, toUserName=msg['FromUserName'])
        my_glob.msg_dict.pop(old_msg_id)
        try:
            ClearTimeOutMsg()
        except:
            pass


if "shimizumasami" in os.getcwd():
    itchat.auto_login(True)
else:
    itchat.auto_login(enableCmdQR=2, hotReload=True)
print(u"ログインしました。")
my_glob.init()
if len(sys.argv) >= 2 and (sys.argv[1] == "sleep" or sys.argv[1] == "sleeping"): my_glob.sleeping = True
itchat.send(u"ロボットを起動しました。")
itchat.run()
my_glob.params.write_all()
print u"ロボットを停止しました。"
