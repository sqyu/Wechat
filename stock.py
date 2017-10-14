#coding=utf-8
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
#import locale
import itchat
from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday, nearest_workday, USMartinLutherKingJr, USPresidentsDay, GoodFriday, USMemorialDay, USLaborDay, USThanksgivingDay
from pandas.tseries.holiday import get_calendar, HolidayCalendarFactory, GoodFriday
import os
import pytz
import re
import urllib

import my_glob
import translate
import stock_candle
import fundamental


from pandas_datareader.nasdaq_trader import get_nasdaq_symbols
import pandas_datareader.data as web

class USTradingCalendar(AbstractHolidayCalendar):
    rules = [Holiday('NewYearsDay', month=1, day=1, observance=nearest_workday),
             USMartinLutherKingJr,
             USPresidentsDay,
             GoodFriday,
             USMemorialDay,
             Holiday('USIndependenceDay', month=7, day=4, observance=nearest_workday),
             USLaborDay,
             USThanksgivingDay,
             Holiday('Christmas', month=12, day=25, observance=nearest_workday)]
tradedays = USTradingCalendar()
global previous_trade_today, today, yesterday
previous_trade_today = None  ## Assignment below
today = datetime.strptime(datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d"), "%Y%m%d")
yesterday = today - timedelta(1)
indices = {"INDEXNASDAQ%3A.IXIC": u"納斯達克綜合指數(NASDAQ)", "INDEXDJX%3A.DJI": u"道瓊斯工業平均指數(DJIA)", "INDEXSP%3A.INX": u"標準普爾500指數(S&P 500)"}
    
#now_names = [u"現在", u"现在", u"最新", u"最后", u"最後"]
today_names = ["TODAY", u"今天", u"今日", u"きょう", u"오늘", u"금일"]
yesterday_names = ["YESTERDAY", u"昨天", u"昨日", u"きのう", u"尋日", u"琴日", u"어제"]
beforeyes_names = ["DAYBEFOREYESTERDAY", "THEDAYBEFOREYESTERDAY", u"前天", u"前日", u"おととい", u"一昨日", u"いっさくじつ", u"그제"]

if "shimizumasami" in os.getcwd(): # For getting last quotes, not sure why
    add_hours = 9
else:
    add_hours = 0


def get_indices():
    return_text = ""
    for index in indices.keys():
        if index + "." + previous_trade_today.strftime("%Y%m%d") in os.listdir("System"): # If today's end prices cached
            return_text = return_text + "".join(open("System/" + index + "." + previous_trade_today.strftime("%Y%m%d")).readlines()).decode("utf-8")
            continue
        try:
            r = urllib.urlopen("http://www.google.com/finance/historical?q=%s&startdate=" % (index) + previous_trade_today.strftime("%b+%dPERCENT2c+%Y").replace("PERCENT", "%"))
            soup = BeautifulSoup(r, "html.parser")
            data = soup.find("table", {"class": "gf-table historical_price"}).find("td", {"class": "lm"}).text
            new_text = previous_trade_today.strftime("%Y年%-m月%-d日\n").decode("utf-8") + indices[index] + u"開市報" + data.split("\n")[1] + u"點，收" + data.split("\n")[4] + u"點，最高" + data.split("\n")[2] + u"點，最低" + data.split("\n")[3] + u"點。\n\n"
            return_text = return_text + new_text
            open("System/" + index + "." + previous_trade_today.strftime("%Y%m%d"), "w").write(new_text.encode("utf-8")) # Cache today's end prices
        except:
            try:
                r = urllib.urlopen("https://www.google.com/finance?q=%s" % (index))
                soup = BeautifulSoup(r, "html.parser")
                price = soup.find(itemprop="price")['content'].rstrip()
                quote_time = soup.find(itemprop="quoteTime")['content'].rstrip()
                rang = soup.find('td',{'data-snapfield':"range"}).next_sibling.next_sibling.text.rstrip()
                open_p = soup.find('td',{'data-snapfield':"open"}).next_sibling.next_sibling.text.rstrip()
                return_text = return_text + u"截至" + datetime.strptime(quote_time, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y年%-m月%-d日%H時%M分%S秒，").decode("utf-8") + indices[index] + u"報" + price + u"點，今日開市報" + open_p + u"點，區間" + rang + u"點。\n\n"
            except Exception as e: print("Error happend in stock.get_indices():\n"); print(e)
    return return_text ## Else, return

def get_ticker(name):
    if name in my_glob.symbols: # If is a ticker, return the ticker
        return [name]
    # If not, search by company name
    # Translate to English if necessary
    if not name.encode("utf-8").isalnum():
        name = translate.translate(name)[0]
    name = u" ".join(map(lambda n:n[0].upper()+n[1:].lower(), filter(None, name.split(" ")))) ## Bug occurred when u"好像出BUG了。。" was translated into "It seems like a BUG. " with an empty space
    name = name.replace("Class", "").replace("Common", "").replace("Stock", "").replace("Index", "").replace("Dividend", "")#.replace("Fund", "").replace("Share", "")
    if name == "Google":
        return ["GOOGL", "GOOG"]
    elif "American Telephone" in name and "Telegraph" in name:
        return ["T"]
    results = []
    for key, value in my_glob.symbols.items():
        if name in value:
            results.append(key)
    return results

def detect_date(msgtext):
    msgtext = msgtext.encode("utf-8").replace("/", "-")
    for format in ["%Y-%m-%d", "%y-%m-%d", "%Y年%m月%d日", "%y年%m月%d日", "%Y年%m月%d号", "%y年%m月%d号", "%Y年%m月%d號", "%y年%m月%d號", "%Y年%m月%d", "%y年%m月%d", "%m-%d-%Y", "%m-%d-%y"]:
        try:
            search_day = datetime.strptime(msgtext, format)
            break
        except:
            try:
                search_day = datetime.strptime(today.strftime("%Y-")+msgtext, format)
                break
            except:
                try:
                    search_day = datetime.strptime(today.strftime("%Y年")+msgtext, format)
                    break
                except:
                    search_day = None
    return search_day

def wrong_date_prompt():
    return u"日期有誤，請輸入您想要查詢的日期，格式為%s或%s或%s或%s（今年），或輸入今天，昨天或前天（紐約時間）" % (previous_trade_today.strftime("%Y-%m-%d").decode("utf-8"), previous_trade_today.strftime("%y年%-m月%-d日").decode("utf-8"), previous_trade_today.strftime("%-m月%-d(號)").decode("utf-8"), previous_trade_today.strftime("%-m/%-d"))

k_prompt = u"若要繪畫K線圖，請直接輸入長度並將將時間限制在十天和十年之間，輸入格式：431天 貳拾壹週 叄拾柒個月 半年 兩年）。"

cn_to_ar = {u"一": 1, u"二": 2, u"兩":2, u"两":2, u"三":3, u"四": 4, u"五": 5, u"六": 6, u"七": 7, u"八": 8, u"九": 9, u"十": 10, u"壹": 1, u"弍": 2, u"貳": 2, u"參":3, u"弎": 3, u"叁": 3, u"叄":3, u"肆": 4, u"伍": 5, u"陸": 6, u"柒": 7, u"捌": 8, u"玖": 9, u"拾": 10} # Okay to standalone
cn_to_ar2 = {u"十": 10, u"百": 100, u"千": 1000}

#tests = [u"一天", u"两天", u"兩天", u"二天", u"三天", u"四天", u"五天", u"六天", u"七天", u"八天", u"九天", u"十天", u"十一天", u"十两天", u"十兩天", u"十二天", u"十三天", u"十四天", u"十五天", u"十六天", u"十七天", u"十八天", u"十九天", u"十十天", u"十百天", u"十千天", u"二十一天", u"二十两天", u"二十兩天", u"二十二天", u"二十三天", u"二十四天", u"二十五天", u"二十六天", u"二十七天", u"二十八天", u"二十九天", u"二十十天", u"二十百天", u"二十千天", u"两十一天", u"两十两天", u"两十兩天", u"两十二天", u"两十三天", u"两十四天", u"两十五天", u"两十六天", u"两十七天", u"两十八天", u"两十九天", u"两十十天", u"两十百天", u"两十千天", u"一一天", u"一两天", u"一兩天", u"一二天", u"一三天", u"一四天", u"一五天", u"一六天", u"一七天", u"一八天", u"一九天", u"一十天", u"一十一天", u"一十两天", u"一十兩天", u"一十二天", u"一十三天", u"一十四天", u"一十五天", u"一十六天", u"一十七天", u"一十八天", u"一十九天", u"一十十天", u"一十百天", u"一十千天", u"一二十一天", u"一二十两天", u"一二十兩天", u"一二十二天", u"一二十三天", u"一二十四天", u"一二十五天", u"一二十六天", u"一二十七天", u"一二十八天", u"一二十九天", u"一二十十天", u"一二十百天", u"一二十千天", u"一十十一天", u"一十十两天", u"一十十兩天", u"一十十二天", u"一十十三天", u"一十十四天", u"一十十五天", u"一十十六天", u"一十十七天", u"一十十八天", u"一十十九天", u"一十十十天", u"一十十百天", u"一十十千天", u"一十二十一天", u"一十二十两天", u"一十二十兩天", u"一十二十二天", u"一十二十三天", u"一十二十四天", u"一十二十五天", u"一十二十六天", u"一十二十七天", u"一十二十八天", u"一十二十九天", u"一十二十十天", u"一十二十百天", u"一十二十千天", u"一百一天", u"一百两天", u"一百兩天", u"一百二天", u"一百三天", u"一百四天", u"一百五天", u"一百六天", u"一百七天", u"一百八天", u"一百九天", u"一百十天", u"一百十一天", u"一百十两天", u"一百十兩天", u"一百十二天", u"一百十三天", u"一百十四天", u"一百十五天", u"一百十六天", u"一百十七天", u"一百十八天", u"一百十九天", u"一百十十天", u"一百十百天", u"一百十千天", u"一百二十一天", u"一百二十两天", u"一百二十兩天", u"一百二十二天", u"一百二十三天", u"一百二十四天", u"一百二十五天", u"一百二十六天", u"一百二十七天", u"一百二十八天", u"一百二十九天", u"一百二十十天", u"一百二十百天", u"一百二十千天", u"三千六百一天", u"三千六百两天", u"三千六百兩天", u"三千六百二天", u"三千六百三天", u"三千六百四天", u"三千六百五天", u"三千六百六天", u"三千六百七天", u"三千六百八天", u"三千六百九天", u"三千六百十天", u"三千六百十一天", u"三千六百十两天", u"三千六百十兩天", u"三千六百十二天", u"三千六百十三天", u"三千六百十四天", u"三千六百十五天", u"三千六百十六天", u"三千六百十七天", u"三千六百十八天", u"三千六百十九天", u"三千六百十十天", u"三千六百十百天", u"三千六百十千天", u"三千六百二十一天", u"三千六百二十两天", u"三千六百二十兩天", u"三千六百二十二天", u"三千六百二十三天", u"三千六百二十四天", u"三千六百二十五天", u"三千六百二十六天", u"三千六百二十七天", u"三千六百二十八天", u"三千六百二十九天", u"三千六百二十十天", u"三千六百二十百天", u"三千六百二十千天", u"三千六百七十天", u"三十六個月", u"一百三十個月", u"五百週", u"六百週"]

#for day in tests:
#    print day + u": " + unicode(chinese_days(day)) + "\n"

def chinese_days(text):
    ## Can only take a valid number + any of 年月週天
    if not text: return None
    text = text.replace(u"个月", u"月").replace(u"個月", u"月")
    if text[-1] == u"年":
        multiplier = 365
    elif text[-1] == u"月":
        multiplier = 30
    elif text[-1] in [u"週", u"周"]:
        multiplier = 7
    elif text[-1] == u"天":
        multiplier = 1
    else:
        return None
    text = text[:-1]
    if text == u"半": # 半年，半(個)月
        if multiplier >= 30:
            return multiplier / 2
        else:
            return None
    try:
        res = int(text) * multiplier
        if res > 3650 or res < 10:
            return -1 ## Over 10 years or less than 10 days
        else:
            return res
    except: pass
    text = text.replace(u"零", "").replace(u"仟", u"千").replace(u"佰", u"百").replace(u"拾",u"十")
    ma = re.match(u"^([一壹两兩二貳三參四肆五伍六陸七柒八捌九玖]千)?([一壹两兩二貳三參四肆五伍六陸七柒八捌九玖]百)?([一壹二貳三參四肆五伍六陸七柒八捌九玖]十)?([一壹二貳三參四肆五伍六陸七柒八捌九玖]|)$|^(十)([一壹二貳三參四肆五伍六陸七柒八捌九玖]?)$|^(两)$|^(兩)$", text)  ## Actually [一壹两兩二貳三參]千 is enough, but prefer 四千天 to return "longer than 3650 days" than "invalid input"
    if ma is None:
        return None
    ma = filter(None, ma.groups())
    res = 0
    for m in ma:
        if len(m) == 2:
            res = res + cn_to_ar[m[0]] * cn_to_ar2[m[1]]
        else:
            res = res + cn_to_ar[m]
    res = res * multiplier
    if res > 3650 or res < 10:
        return -1 ## Over 10 years or less than 10 days
    else:
        return res


def is_holiday(date): ## Returns "" for trade days, or Sat or Sun or holiday accordingly
    if date.strftime("%w") in ["0", "6"]:
        return {"0": u"星期天", "6": u"星期六"}[date.strftime("%w")]
    if len(tradedays.holidays(date, date)) == 1:
        return u"節假日"
    else:
        return ""

def last_trade_day(date):
    if date == today:  ## If not
        now = datetime.now(pytz.timezone('US/Eastern'))
        if now.hour < 9 or (now.hour == 9 and now.min.minute < 30):
            return last_trade_day(yesterday)
    if is_holiday(date) == "":
        return date
    else:
        if date == today:
            now = datetime.now(pytz.timezone('US/Eastern'))
        return last_trade_day(date - timedelta(1))

previous_trade_today = last_trade_day(today)

def send_candlestick(ticker, time_lag, today, to):
    if to == my_glob.me:
        to = my_glob.redirect_me_to
    itchat.send('@%s@%s' % ('img', stock_candle.pandas_candlestick(web.DataReader(ticker, "google", today-timedelta(time_lag), today), time_lag, ticker)), to)
    return


def setstock(input, user):
    tickers = []
    for inp in filter(None, input.split(" ")):
        if inp.replace(u" ", u"").replace(u"　", u"").replace(",", "").replace(u"，", ""): tickers = tickers + get_ticker(inp.replace(u" ", u"").replace(u"　", u"").replace(",", "").replace(u"，", "")) # Possibly more white spaces
    tickers = fundamental.remove_dup(tickers)
    if tickers == []: # Ticker not valid
        return u"您輸入的股票有誤，請重新輸入，如如\"臉書 Amazon GOOG 微軟\"或\"FB 亞馬遜 MSFT Tesla UVXY\"\n"
    if len(tickers) > 5:
        return u"返回的結果超過五個（頭五個為" + u"，".join(tickers[0:5]) + u"），請重新查詢\n"
    my_glob.params.set("params", user, tickers, "stock") ## Passed test, then choose date
    for ticker in tickers:
        try:
            send_candlestick(ticker, 92, today, user)
        except Exception as e: print(e)
#    pass
    return_text = u""
    for ticker in tickers:
        try:
            ress = web.get_quote_google(ticker)
            return_text = return_text + u"截至" + (ress["time"].dt.to_pydatetime()[0]+timedelta(hours=add_hours)).strftime("%-m月%-d日%H時%M分").decode("utf-8") + u"，" + ticker + " (" + my_glob.symbols[ticker] + u")的股價為$" + str(ress["last"].item()) + "\n" ###!!! Not sure why wrong time zone, so added 9 hours
        except Exception as e: print("Error happend in stock.setstock() in finding last quotes:\n"); print(e)
    if return_text: return_text = return_text + "\n" # If not empty, add a new line
    return return_text + u"現在請輸入您想要查詢的日期，格式為%s或%s或%s或%s（今年），或今天，昨天或前天（紐約時間）" % (previous_trade_today.strftime("%Y-%m-%d").decode("utf-8"), previous_trade_today.strftime("%y年%-m月%-d日").decode("utf-8"), previous_trade_today.strftime("%-m月%-d(號)").decode("utf-8"), previous_trade_today.strftime("%-m/%-d")) + "\n\n" + k_prompt

def format_volume(vol):
    line = str(vol)
    # locale.setlocale(locale.LC_ALL, 'en_US') and then "%s%.format(vol, grouping=True) does not work on cluster so redefine
    return ",".join(filter(None,[line[0:len(line)%3]] + [line[i:i+3] for i in range((len(line))%3, len(line)+1, 3)]))

def get_stock(msg):
    ### To make sure dates are up-to-date (possible change of date)
    global previous_trade_today, today, yesterday
    today = datetime.strptime(datetime.now(pytz.timezone('US/Eastern')).strftime("%Y%m%d"), "%Y%m%d")
    yesterday = today - timedelta(1)
    previous_trade_today = last_trade_day(today)
    ### Date assignments end
    msg['Text'] = msg['Text'].upper()
    if my_glob.symbols == {}: # Load ticker - security name as into dictionary
        my_glob.symbols = get_nasdaq_symbols().ix.obj["Security Name"].to_dict()
    if msg['Text'] in [u"換股", u"换股", u"股票", u"换股票", u"換股票"] and (not (my_glob.params.get("params",msg['FromUserName'],"stock") is None)): # If customer wants to change stock
        my_glob.params.set("params", msg['FromUserName'], None, "stock")
        return my_glob.modes_greeting["stock"]
    if my_glob.params.get("params", msg['FromUserName'], "stock") is None: # If no pre-selected stock, see if this text is meant for choosing one
        return setstock(msg['Text'], msg['FromUserName'])
    # Ticker okay and already chosen. Then choose date or change stock
    tickers = my_glob.params.get("params", msg['FromUserName'], "stock")
    # Customer will be choosing a new date no matter if he already has chosen a date (another query) or not (first query)
    return_text = ""
    if msg['Text'].upper() in today_names:
        now = datetime.now(pytz.timezone('US/Eastern'))
        if now.hour < 9 or now.hour == 9 and now.min.minute < 30:
            return_text = return_text + u"現在未開市，為您返回上一交易日結果\n"
            search_day = last_trade_day(yesterday)
        else:
            search_day = today
    elif msg['Text'].upper() in yesterday_names:
        search_day = yesterday
    elif msg['Text'].upper().replace(" ","") in beforeyes_names:
        search_day = yesterday - timedelta(1)
    elif not (re.search(u"[年月週周天]$", msg['Text']) is None): ## If contains 年,月,週,周,天 at the end of the string, then test if it is a length for drawing candle stick. Cannot be a date since a date must ends in 日,號,号, or number.
        k_period = chinese_days(msg['Text'])
        if k_period is None:
            return wrong_date_prompt() + "\n\n" + k_prompt
        elif k_period == -1:
            return u"日期長度有誤，" + k_prompt
        else:
            for ticker in tickers:
                send_candlestick(ticker, k_period, today, msg['FromUserName'])
            return u"請輸入日期（紐約時間）查詢其它日期，或其他日期長度繪畫K線圖，或輸入其它股票名或交易代碼，或輸入「換」退出股票模式。"
    # But he will probably want to directly change the stock ticker: if numeric or numeric+chinese -> date, (any alphabet+$ or pure chinese) == (any alphabet+$ or not contain numbers) -> stock; "3M" is okay
    # Placed this step here so that u"今天" would not be treated as a stock
    elif (not re.search('[a-zA-Z$]', msg['Text']) is None) or (re.search('\d', msg['Text']) is None):
        return setstock(msg['Text'], msg['FromUserName']) ## Stock
    else:  ## Date
        search_day = detect_date(msg['Text'])
    if search_day is None: # If cannot find date
        return wrong_date_prompt()
    # If everything is in place
    holi = is_holiday(search_day) # See if is a holiday
    if holi != "":
        return_text = return_text + search_day.strftime("%Y年%-m月%-d日").decode("utf-8") + u"是一個" + holi + u"，已為您改為上一交易日\n\n"  ## SHOULD ONLY APPEAR TO BE THE FIRST IN RETURN_TEXT THOUGH
        search_day = last_trade_day(search_day)
    for ticker in tickers:
        try:
            stock = web.DataReader(ticker, "google", search_day, search_day).values[0]
        except:
            if search_day == today:
                return_text = return_text + u"今天尚未有" + ticker + u"的股票收盤信息\n"
            else:
                return_text = return_text + u"找不到" + ticker + " (" + my_glob.symbols[ticker] + u") " + search_day.strftime("%Y年%-m月%-d日").decode("utf-8") + u"的股票信息\n"
            continue
        return_text = return_text + ticker + " (" + my_glob.symbols[ticker] + u"):\n" + search_day.strftime("%Y年%-m月%-d日").decode("utf-8") + u"的開市價為$" + str(stock[0]) + u"，最高價為$" + str(stock[1]) + u"，最低價為$" + str(stock[2]) + u"，收市價為$" + str(stock[3]) + u"，成交量為" + format_volume(stock[4]) + u"股。\n\n"
    return return_text + u"\n請輸入日期（紐約時間）查詢其它日期，或時間長度（431天/貳拾壹週/叄拾柒個月/半年/兩年）繪畫K線圖，或輸入其它股票名或交易代碼，或輸入「換」退出股票模式。"



