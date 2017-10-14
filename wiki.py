#coding=utf-8
import wikipedia
#from hanziconv import HanziConv
import my_glob
#import translate
#import requests
#import json
#import urllib
import urllib2
import re
from googleapiclient.discovery import build
from googleapiclient import errors

max_results = 2
max_return = 5

def wiki0(msg):
    """\
        First detect language by google translate
        If not in language accepted by user, use all user-specific languages
        Look for results using original text and also suggested text in each language
        Then rank them and pick the first max_results items
        Then go over each of them to print out all language versions for each item
    """
    text = msg['Text']
    userlangs = (my_glob.params.get("params", msg['FromUserName'], "wiki_lang") or my_glob.params.get("params", msg['FromUserName'], "lang") or ["zh","en"])
    return_text = ""
    text_lang = translate.translate(text)[1]
    all_res = []
    if not text_lang in userlangs:
        for lang in userlangs:
            wikipedia.set_lang(lang)
            res = wikipedia.search(text, results=max_results)
            sug = wikipedia.suggest(text)
            if sug: res = res + wikipedia.search(sug, results=max_results);
            if res: all_res = all_res + [(t, lang) for t in res]
    else:
        wikipedia.set_lang(text_lang)
        res = wikipedia.search(text, results=max_results)
        sug = wikipedia.suggest(text)
        if sug: res = res + wikipedia.search(sug, results=max_results);
        if res: all_res = all_res + [(t, text_lang) for t in res]
    all_res = sorted(all_res, key=lambda x:HanziConv.toSimplified(text.lower()) in HanziConv.toSimplified(x[0].lower()), reverse=True)[0:max_results]
    titles = []
    all_titles = []
    for title,lang in all_res:
        try:
            return_text = return_text + "*"*20 + "\n"
            title_safe = urllib.quote(title.encode("utf-8"), safe='')
            url = "https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json" % (lang,title_safe)
            s = json.loads(requests.post(url).text, encoding="utf-8")["query"]["pages"].values()[0]
            titles = [(title, lang)] # Title for this language
            if "langlinks" in s:
                titles = titles + [(ss["*"], ss["lang"]) for ss in s["langlinks"] if ss["lang"] in userlangs]
            for title0,lang0 in titles:
                if not (title0, lang0) in all_titles:
                    try:
                        try:
                            wikipedia.set_lang(lang0)
                            return_text = return_text + wikipedia.summary(title0, sentences=2) + "\n"  + "*"*20 + "\n"
                        except wikipedia.exceptions.DisambiguationError as e: return_text = return_text + str(e).decode("utf-8") + "\n" + "*"*20 + "\n"
                    except Exception as e: print("Suberror occurred in wiki.py: "); print (e)
            all_titles = all_titles + titles
        except Exception as e: print("Error occurred in wiki.py: "); print(e)
    return return_text


my_api_keys = ["AIzaSyA-GWs1PmRi9cWgj0Cf_cpBPb8xwGIWaDI", "AIzaSyAWJHxr0NU0NyUWiEDyNgvVptkjfF2vPDc"]
my_cse_ids = ["001012814276132725208:peezibta2ho", "003746443543527737292:tniay4upnbg"]
# sqyu, masami
which_api = 0

def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']

#def lang_to_wiki(lang):
#    if lang in ["zh-hk","zh-tw","zh-mo","zh-cn","zh-sg"]:
#        return "site:"+"zh.wikipedia.org/"+lang+"/"
#    else:
#        return "site:"+lang+".wikipedia.org/wiki/"

def filter_res(title):
    ## If interwiki link to non-wikipedia or a namesapce, return False
    ## should fix this to support wiktionary
    return (not re.match("wiktionary:|talk:|user:|user_talk:|wikipedia:|wikipedia_talk:|file:|file_talk:|mediawiki:|mediawiki_talk:|template:|template_talk:|help:|help_talk:|category:|category_talk:|portal:|portal_talk:|book:|book_talk:|draft:|draft_talk:|education_program:|education_program_talk:|timedtext:|timedtext_talk:|module:|module_talk:|gadget:|gadget_talk:|gadget_definition:|gadget_definition_talk:|wikt:|wikinews:|n:|wikibooks:|b:|wikiquote:|q:|wikisource:|s:|oldwikisource:|species:|wikispecies:|wikiversity:|v:|betawikiversity:|wikivoyage:|voy:|wikimedia:|foundation:|wmf:|commons:|c:|meta:|metawikipedia:|m:strategy:|incubator:|mediawikiwiki:|mw:|quality:|otrswiki:|otrs:|ticket:|phabricator:|bugzilla:|mediazilla:|phab:|nost:|testwiki:|wikidata:|outreach:|outreachwiki:|boollabs:", title.lower()))

def process_results(results):
    ## Returns [(lang1,title1), (lang2,title2)]
    cleaned_results = []
    for result in results:
        url = urllib2.unquote(str(result["link"])).decode("utf-8") ##result["formattedUrl"]: this does not work if e.g. search for एलिज़ाबेथ द्वितीय and get nonsense links for files for Queen Elizabeth
        match_title = "org/wiki/".join(url.split("org/wiki/")[1:])
        if not filter_res(match_title) or match_title == "":
            continue
        match_lang = re.match("(https://)?[^.]+.wikipedia", url).group(0).split("https://")[1].split(".wikipedia")[0]
        cleaned_results.append((match_title, match_lang))
    return cleaned_results

def wiki(msg):
    global which_api
    userlangs = (my_glob.params.get("params", msg['FromUserName'], "wiki_lang") or my_glob.params.get("params", msg['FromUserName'], "lang") or ["zh","en"])
    return_text = []
    results = []
    try: # Try user-specific languages
        try:
            results = process_results(google_search(msg['Text'] + " " + " OR ".join(["site:%s.wikipedia.org/wiki/" % la for la in userlangs]), my_api_keys[which_api], my_cse_ids[which_api], num=2*max_return))
        except errors.HttpError: # If reached search limit
            which_api = 1-which_api # Change API
            try:
                results = process_results(google_search(msg['Text'] + " " + " OR ".join(["site:%s.wikipedia.org/wiki/" % la for la in userlangs]), my_api_keys[which_api], my_cse_ids[which_api], num=2*max_return))
            except errors.HttpError: return u"24小時內查詢次數已達上限，再會。\n" # If still limit
    except Exception as e: print("Error occurred trying to fetch results for user-specific languages"); print (e); pass
    if len(results) < 5:
        try: # If no results for user-specific langs, try other langs
            try:
                results = results + process_results(google_search(msg['Text'] + " site:wikipedia.org/wiki/", my_api_keys[which_api], my_cse_ids[which_api], num=2*max_return))
            except errors.HttpError: # If reached search limit
                which_api = 1-which_api # Change API
                try:
                    results = results + process_results(google_search(msg['Text'] + " site:wikipedia.org/wiki/", my_api_keys[which_api], my_cse_ids[which_api], num=2*max_return))
                except errors.HttpError: return u"24小時內查詢次數已達上限，再會。\n" # If still limit
        except Exception as e: print("Error occurred trying to fetch results for all languages"); print (e); pass
    if results == []: return u"很抱歉，找不到相關結果。\n"
    for match_title, match_lang in results:
        try:
            try:
                wikipedia.set_lang(match_lang)
                summ = re.split("={2,5} .* ={2,5}", wikipedia.summary(match_title, sentences=2))[0].rstrip().lstrip() ## If summary contains == SECTION ==, truncate
                if summ:
                    return_text.append(summ)
            except wikipedia.exceptions.DisambiguationError as e: return_text.append(str(e).decode("utf-8"))
        except Exception as e: print("Suberror occurred in wiki.py: "); print (e)
        if len(return_text) == max_return:
            break
    return ("\n"+"*"*20+"\n").join(return_text)



#�㰍  एलिज़ाबेथ द्वितीय jajajajaja

