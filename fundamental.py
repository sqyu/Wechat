#coding=utf-8
import my_glob
import itchat
import user


def remove_dup(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def display(msg, group=False):
    if msg['FromUserName'] == my_glob.me:
        print(u"Me: " + msg['Text'])
    else:
        remark_name = my_glob._from_UN(msg['FromUserName'])
        if remark_name is None:
            remark_name = msg['FromUserName']
        if group:
            remark_name = my_glob._from_UN(msg['FromUserName']) + u" 的 " + msg['ActualNickName']
        print(remark_name + ": " + msg['Text'])
    return

def save_output(text): ## So that no newline will be written into system output file causing an error in reading
    return text.replace("\n","!NEWLINE!").replace("\t","!TAB!").replace("\r","!RETURN!").replace(" :: "," COLONCOLON ").replace(" %% "," PERCENTPERCENT ")

def send_to_me(text):
    itchat.send(text, my_glob.redirect_me_to) # Possibly redirect to someone else for fun

def mysend(text, to, msg = None):
    #msg when greeting for the first time to a group, need to print the name of the sender
    if text == "": ## Do not send empty string
        return
    transformed_text = save_output(text)
    if transformed_text == "#GREETING2#" and my_glob.params.get("params", to, "prev_message")  == "#GREETING2#" and my_glob.params.get("params", to, "prev_prev_message") == "#GREETING1#":   # If sent greetings twice, shut up immediately
        my_glob.params.set("mode", to, "shutup")
        return
    elif transformed_text != my_glob.params.get("params", to, "prev_message") or transformed_text != my_glob.params.get("params", to, "prev_prev_message"): # In other modes, if not repeated twice then okay, send
        if text == "#GREETING1#": text = first_greeting(to, msg)
        elif text == "#GREETING2#": text = second_greeting()
        if to == my_glob.me: send_to_me(text + u"（自動回覆）")
        else: itchat.send(text + u"（自動回覆）", to)
        print(u"I sent: " + text + u"（自動回覆）")
        my_glob.params.set("params", to, False, "silence")
        my_glob.params.set("params", UserName=to, value=my_glob.params.get("params", to, "prev_message"), mode="prev_prev_message") # Assign prev message to prev prev message
        my_glob.params.set("params", UserName=to, value=transformed_text, mode="prev_message")
    elif not my_glob.params.get("params", to, "silence"): # Otherwise remain silent. If not already silent, compalin and remain silent; otherwise keep silent
        if to == my_glob.me: send_to_me(u"你老讓我重複一樣的話，我不說了，哼！（自動回覆）")
        else: itchat.send(u"你老讓我重複一樣的話，我不說了，哼！（自動回覆）", to)
        print(u"Me: 你老讓我重複一樣的話，我不說了，哼！（自動回覆）")
        my_glob.params.set("params", to, True, "silence")
    return

def first_greeting(to, msg=None):
    #msg when greeting for the first time to a group, need to print the name of the sender
    if msg is None: # Friend
        sig = user.get_signature(username = to)
        itchat.send('@%s@%s' % ('img', user.profile_pic(username = to)), to)
        to = my_glob._to_NN(to)
    else: # Group chat
        sig = user.get_signature(username = msg['ActualUserName'])
        itchat.send('@%s@%s' % ('img', user.profile_pic(username = msg['ActualUserName'])), msg['FromUserName'])
        to = my_glob._group_member_NN(msg)
    if to == "None":
        to = ""
    return u"你好" + to + bool(sig)*"(" + sig + bool(sig)*")" + u"，我是小異邦人，請從以下模式中選擇（數字或關鍵字）：" + my_glob.greeting_modes+u"\n\n你還可以嘗試發送語音，撤回消息，或者撤回定位和好友名片！" + u"\n\nP.S. 我主人在睡覺！zZ" * my_glob.sleeping + (my_glob.prompt_message!="") * "\n\n" + my_glob.prompt_message


def second_greeting():
    return u"現在只支持以上1-" + str(len(my_glob.modes)-1) + u"模式。（繼續無視此句將自動閉嘴）"



