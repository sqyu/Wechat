#coding=utf-8
import os
import time

import itchat

def _to_UN(name): # Remark Name (friend) or Nick Name (group) to Username
    return ((fl.RN_to_UN.get(name, None) or fl.GNN_to_GUN.get(name, None)) or u"None")

def _from_UN(name): # Username to Remark Name (friend) or Nick Name (group)
    return ((fl.UN_to_RN.get(name, None) or fl.GUN_to_GNN.get(name, None)) or u"None")

def _to_NN(name): # For friends, User Name to Nick Name
    return fl.UN_to_NN.get(name, u"None")

def _group_member_NN(msg):
    sentfrom = _to_NN(msg['ActualUserName']) # See if it is my friend (in which case ActualNickName is my remark name)
    if sentfrom == "None": # If not, ActualNickName really is his own nick name
        return msg['ActualNickName']
    return sentfrom

def search_friend(string): # Search friends with remark names that contain string and return (remark name, username)
    return [(s, fl.RN_to_UN[s]) for s in fl.RN_to_UN if string in s]

def search_chatroom(string): # Search chatrooms with nick names that contain string and return (nick name, username)
    return [(s, fl.GNN_to_GUN[s]) for s in fl.GNN_to_GUN if string in s]


class friend_lists:
    friends = []
    UN_to_RN = {}
    RN_to_UN = {}
    UN_to_NN = {}
    chatrooms = [] 
    GUN_to_GNN = {}
    GNN_to_GUN = {}
    def __init__(self):
        self.friends = itchat.get_friends()
        self.UN_to_RN = {s["UserName"] : s["RemarkName"] for s in self.friends if s['UserName'] != me}
        self.UN_to_RN[me] = itchat.originInstance.storageClass.nickName
        self.RN_to_UN = {s["RemarkName"] : s["UserName"] for s in self.friends if s['UserName'] != me}
        self.RN_to_UN[itchat.originInstance.storageClass.nickName] = itchat.originInstance.storageClass.userName
        self.UN_to_NN = {s["UserName"] : s["NickName"] for s in self.friends}
        #self.NN_to_UN = {s["NickName"] : s["UserName"] for s in self.friends}
        self.chatrooms = itchat.get_chatrooms()
        self.GUN_to_GNN = {s["UserName"] : s["NickName"] for s in self.chatrooms if s["NickName"] != itchat.originInstance.storageClass.nickName and s["NickName"] != ""}
        self.GNN_to_GUN = {s["NickName"] : s["UserName"] for s in self.chatrooms if s["NickName"] != itchat.originInstance.storageClass.nickName and s["NickName"] != ""}
        if "" in self.UN_to_RN.values() : itchat.send(u"下記のユーザはRemarkNameがありません：" + u"\n".join([self.UN_to_NN[a] for a in self.UN_to_RN.keys() if self.UN_to_RN[a] == ""])); self.UN_to_RN.pop("")
        if len(set(self.GNN_to_GUN.keys() + self.RN_to_UN.keys())) != len(self.GNN_to_GUN.keys() + self.RN_to_UN.keys()): itchat.send(u"下記のユーザはRemarkNameとGroupNickNameが名前衝突が起こりました：" + u"\n".join([a for a in self.GNN_to_GUN.keys() if a in self.RN_to_UN.keys()]))
        return
            

class system_params:
    good_groups = []
    friend_mode = {} ## Indices in modes
    friend_params = {} ### Dictionary of dictionaries of single elts or lists
    friend_times = {}
    blocking_list = []
    def __init__(self):
        for file in ["good_groups", "friend_mode", "friend_params", "friend_times", "blocking_list"]:
            file = "System/" + file
            if not os.path.exists(file+".txt"):
                print(u"！！警告：ファイル" + file + u".txtが見つかりません。！！\n")
                open(file+".txt", "a").close()
            else:
                open(file+".backup.txt", "w").write("".join(open(file+".txt","r").readlines()))
        self.good_groups = [r.rstrip().decode("utf-8") for r in open("System/good_groups.txt", "r").readlines() if not r.startswith("##NOT##")]
        self.friend_mode = {line.split(" :: ")[0].decode("utf-8"):modes_indices[line.split(":: ")[1].rstrip().decode("utf-8")] for line in open("System/friend_mode.txt", "r").readlines()}
        for line in open("System/friend_params.txt", "r").readlines():
            username = line.split(" :: ")[0].decode("utf-8")
            usermode = line.split(" :: ")[1].decode("utf-8")
            userparam = map(mode_param_types[usermode], line.split(" :: ")[2].rstrip().decode("utf-8").split(" %% "))
            if len(userparam) == 1: userparam = userparam[0]
            if not username in self.friend_params: self.friend_params[username] = {}
            self.friend_params[username][usermode] = userparam  ### Only support single elts or lists
        self.friend_times = {line.split(" :: ")[0].decode("utf-8"):float(line.split(" :: ")[1].rstrip()) for line in open("System/friend_times.txt", "r").readlines()}
        self.blocking_list = [r.rstrip().decode("utf-8") for r in open("System/blocking_list.txt", "r").readlines() if not r.startswith("##NOT##")]
    def write(self, file):
        if file == "good_groups":
            gg_to_write = "\n".join(self.good_groups).encode("utf-8")
            open("System/good_groups.txt", "w").write(gg_to_write)
        elif file == "friend_mode":
            mm_to_write = "\n".join([i[0] + " :: " + modes[i[1]] for i in self.friend_mode.items()]).encode("utf-8")
            open("System/friend_mode.txt", "w").write(mm_to_write) # Find mode name by indexing modes
        elif file == "params":
            pp_to_write = ""
            for username in self.friend_params:
                for mode in self.friend_params[username]:
                    try:
                        if type(self.friend_params[username][mode]) == type([]):
                            pp_to_write = pp_to_write + username + " :: " + mode + " :: " + u" %% ".join(map(str, self.friend_params[username][mode])) + "\n"
                        else:
                            pp_to_write = pp_to_write + username + " :: " + mode + " :: " + unicode(self.friend_params[username][mode]) + "\n"
                    except: print("Error occurred when writing file. Possibly due to nonexistance of username.")
            open("System/friend_params.txt", "w").write(pp_to_write.encode("utf-8"))
        elif file == "times":
            tt_to_write = "\n".join([i[0] + " :: " + str(i[1]) for i in self.friend_times.items()]).encode("utf-8")
            open("System/friend_times.txt", "w").write(tt_to_write)
        elif file == "blocking_list":
            bb_to_write = "\n".join(self.blocking_list).encode("utf-8")
            open("System/blocking_list.txt", "w").write(bb_to_write)
        else:
            print("Invalid write.")
    def write_all(self):
        self.write("good_groups"); self.write("friend_mode"); self.write("params"); self.write("times"); self.write("blocking_list")
    def get(self, task, UserName, mode = ""):
        NickName = _from_UN(UserName)
        if task == "mode":
            try: return modes[self.friend_mode[NickName]]
            except: return None
        elif task == "params":
            if NickName in self.friend_params:
                return self.friend_params[NickName].get(mode, None)
            else:
                return None
        elif task == "time":
            return self.friend_times.get(NickName, None)
        elif task == "good_group":
            return NickName in self.good_groups
        elif task == "blocking":
            return NickName in self.blocking_list
        else:
            print("Invalid get.")
            return None
    def set(self, task, UserName, value=None, mode="", save=False):
        # value = None indicated DELETION
        # save: If save changes to local file or not -- No need to save to local every time a change happens. Just do it regularly and *when necessary* (important params or when exiting)
        NickName = _from_UN(UserName)
        if task == "mode":
            if value is None:
                self.friend_mode.pop(NickName, None)
            else:
                self.friend_mode[NickName] = modes_indices[value]
            if save: self.write("friend_mode")
        elif task == "params":
            if NickName in self.friend_params: # If "self.friend_params[NickName]" valid
                if value is None: self.friend_params[NickName].pop(mode, None) # Remove parameter
                else: self.friend_params[NickName][mode] = value # Assign parameter
            else: # If NickName does not have parameters
                self.friend_params[NickName] = {} # Create empty list
                if not value is None: self.friend_params[NickName][mode] = value # Assign parameter as long as not None
            if save: self.write("params")
        elif task == "time":
            self.friend_times[NickName] = time.time()
            if save: self.write("times")
        elif task == "good_group":
            if value == "remove" and NickName in self.good_groups:
                self.good_groups.remove(NickName)
                if save: self.write("good_groups")
            elif value == "add" and not NickName in self.good_groups:
                self.good_groups.append(NickName)
                if save: self.write("good_groups")
        elif task == "blocking":
            if value == "remove" and NickName in self.blocking_list:
                self.blocking_list.remove(NickName)
                if save: self.write("blocking_list")
            elif value == "add" and not NickName in self.blocking_list:
                self.blocking_list.append(NickName)
                if save: self.write("blocking_list")
        else:
            print("Invalid set.")

def init():
    global me, redirect_me_to
    me = itchat.originInstance.storageClass.userName
    global msg_dict, symbols, funny_files, funny_text, modes, modes_indices, mode_param_types, modes_chinese, modes_alt_names, modes_greeting, change_chinese, greeting_modes, last_tweet_time, params, sleeping, lang_names, last_save_time, fl, prompt_message
    redirect_me_to = me
    msg_dict = {}
    symbols = {} #Stocks
    funny_files = sorted([f for f in os.listdir("chiuman") if f.endswith(".txt")])
    funny_text = ["".join(open("chiuman/"+f).readlines()).decode("utf-8") for f in funny_files]
    modes = ["CHANGE", "chat", "google_translate", "chiuman", "reverse", "weather", "stock", "twitter", "mw", "ytenx", "wiki","shutup"]
    modes_indices = {modes[i]:i for i in range(len(modes))}
    mode_param_types = {"chiuman": type(1), "stock": type(u""), "prev_message": type(u""), "prev_prev_message": type(u""), "silence" : type(True), "lang": type(u""), "wiki_lang": type(u"")} # If mode has user-specific, parameters, which type
    modes_chinese = [u"", u"自動聊天", u"谷歌翻譯", u"高登潮文（廣東話）", u"反轉", u"天氣預報", u"股票及K線圖", u"推特監聽Alpha", u"韋氏字典", u"韻典韻書", u"維基百科", u"閉嘴"]
    modes_alt_names = {"chat":["chat", u"聊天", u"自動聊天", u"自动聊天"], "google_translate": ["google translate", "google_translate", "google", u"谷歌翻譯", u"谷歌翻译",u"翻译",u"翻譯"], "chiuman": ["golden","Golden","GOLDEN",u"高登",u"潮文",u"高登潮文", u" 高登潮文（廣東話）", u" 高登潮文（广东话）"], "reverse": [u"反轉", u"翻转", u"反转", u"翻轉"], "weather": ["weather", u"天氣", u"天气", u"天気", u"날씨", u"天气预报", u"天氣預報"], "stock": [u"股票", u"株", u"股市", u"股", u"查股票", u"查詢股票", u"查询股票", u"股票查询", u"股票查詢"], "twitter": [u"推", u"推特", "twitter", "tweet", "tweets", u"監聽", u"推特監聽"], "mw": [u"字典", u"辭典", u"詞典", u"辞典", u"词典", u"韋氏", u"韦氏", u"韋伯字典", u"韋氏字典", u"韋伯斯特字典", u"韋伯詞典", u"韋氏詞典", u"韋伯斯特詞典", u"韋伯辭典", u"韋氏辭典", u"韋伯斯特辭典", u"韦伯字典", u"韦氏字典", u"韦伯斯特字典", u"韦伯词典", u"韦氏词典", u"韦伯斯特词典", u"韦伯辞典", u"韦氏辞典", u"韦伯斯特辞典", u"梅里亞姆-韋伯斯特字典", u"梅里亞姆-韋伯斯特詞典", u"梅里亞姆-韋伯斯特辭典", u"梅里亚姆-韦伯斯特字典", u"梅里亚姆-韦伯斯特词典", u"梅里亚姆-韦伯斯特辞典", u"MW", u"Merriam-Webster", u"Merriam", u"Webster", u"Merriam Webster", u"Merriam-webster", u"merriam-webster"], "ytenx": ["ytenx", u"韻", u"韵", u"韻典", u"韻書", u"漢語", u"中古漢語", u"韻典韻書", u"韻典網", u"韵典", u"韵书", u"汉语", u"中古汉语", u"韵典韵书", u"韵典网"], "wiki": ["wiki","wikipedia",u"wikipédia",u"Wikipédia",u"WIKIPÉDIA","Wiki","WIKI","Wikipedia","WIKIPEDIA",u"维基百科",u"维基",u"維基百科",u"維基",u"ウィキペディア",u"ウィキ",u"ウイキ",u"ウイキペディア",u"위키백과",u"위키"]}
    change_chinese =  [u"换模式", u"換模式", u"换一个", u"換一個", u"换", u"換", u"换！", u"換！", u"换!", u"換!", u"换。", u"換。", u"换.", u"換.", u"菜單", u"菜单", u"主菜单", u"主菜單", u"主頁", u"主页", u"换掉", u"換掉"]
    modes_greeting = {u"chat":u"現在進入聊天模式！跟我說話吧！", u"google_translate": u"現在進入谷歌翻譯模式！跟我說話吧", u"chiuman": u"Hi Auntie! 依家開始講鬼故。", u"shutup":u"[On Fire][On Fire][On Fire]\n好的，臣妾退下了\n要召回時，請說「換」", u"weather":u"請用任意語言輸入要查詢天氣的城市名。退出天氣模式，請輸入「換」。", u"stock":u"請輸入五隻以內想查詢的股票公司名稱或股票代碼，以空格分隔，支持語言搜索\n如\"臉書 Amazon GOOG 微軟\"或\"FB 亞馬遜 MSFT Tesla UVXY\"", u"twitter":u"根據您的語言能力抓取最新%s的推特中，Alpha版暫不支持用戶名和關鍵字查詢。\n", u"mw": u"請輸入要查的英文單詞（五個以內），以逗號（可包含空格）分隔。\n", u"ytenx": u"請輸入想要查詢的漢字，請限制在五字以內",u"wiki":u"請輸入想要查詢的關鍵詞。回覆速度較慢，敬請諒解。請勿反覆查詢！"}
    lang_names = {"en": u"English", "zh": u"中文", "ja":u"日本語", "ko":u"한국어", "fr": u"Fraçais", u"es":u"Español", u"eo":u"Esperanto", "ru":u"Русский", "ar":u"العَرَبِيَّة", "el": u"Ελληνικά"}
    greeting_modes = u"，".join([str(i)+u". "+modes_chinese[i] for i in range(1,len(modes))]) + u"。" # range(1,len(modes)) because CHANGE is not for user
    last_tweet_time = 0
    params = system_params()
    fl = friend_lists()
    sleeping = False
    last_save_time = time.time()
    prompt_message = ""


