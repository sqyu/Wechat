#coding=utf-8
from datetime import datetime, timedelta
#import locale
from weather import Weather

import translate

#def change_month_to_chinese(text):
#    return text.replace("Jan",u"一月").replace("Feb",u"二月").replace("Mar",u"三月").replace("Apr",u"四月").replace("May",u"五月").replace("Jun",u"六月").replace("Jul",u"七月").replace("Aug",u"八月").replace("Sep",u"九月").replace("Oct",u"十月").replace("Nov",u"十一月").replace("Dec",u"十二月")
def num_to_chinese(text):
    return text.replace("0",u"天").replace("1",u"一").replace("2",u"二").replace("3",u"三").replace("4",u"四").replace("5",u"五").replace("6",u"六")

def datetime_to_zh(condition, forecast = False):
    #locale.setlocale(locale.LC_TIME, "en_us")
    if forecast:
        da = datetime.strptime(condition["date"], "%d %b %Y")
        #locale.setlocale(locale.LC_TIME, "zh_hk") # does not work on cluster
        #trans = da.strftime("%B%d日，%A").decode("utf-8") # does not work on cluster
        trans = da.strftime("%-m月%-d日，星期").decode("utf-8") + num_to_chinese(da.strftime("%w"))
    else:
        da = datetime.strptime(" ".join(condition["date"].split(" ")[:-1]), "%a, %d %b %Y %I:%M %p")
        #locale.setlocale(locale.LC_TIME, "zh_hk") # does not work on cluster
        #trans = da.strftime("%Y年%B%d日（%A）的%H時%M分").decode("utf-8") # does not work on cluster
        trans = da.strftime("%Y年%-m月%-d日（星期").decode("utf-8") + num_to_chinese(da.strftime("%w")) + da.strftime("）的%H時%M分").decode("utf-8")
    #locale.setlocale(locale.LC_TIME, "en_us")
    return trans

def f_to_c(temp):
    return str(int((float(temp)-32.0)*5/9))

def others(location): ## For current weather only
    return u"氣壓" + str(float(location.atmosphere()["pressure"]) / 10) + u"千帕，能見度" + str(location.atmosphere()["visibility"]) + u"公里，相對濕度" + str(location.atmosphere()["humidity"]) + u"%" + \
    u"\n日出時間"+datetime.strptime(location.astronomy()["sunrise"], "%I:%M %p").strftime("%H時%M分").decode("utf-8") + u"，日落時間"+datetime.strptime(location.astronomy()["sunset"], "%I:%M %p").strftime("%H時%M分").decode("utf-8") + \
    u"\n風向角度" + str(location.wind()["direction"]) + u"°，風速每小時" + str(location.wind()["speed"]) + u"公里"

def condition_to_zh(text):
    return text.replace("Sunny",u"晴朗").replace("Scattered ", u"零星").replace("Mostly ", u"大部分").replace("Clear", u"晴朗能見度高").replace("Cloudy", u"多雲").replace("Heavy ", u"大").replace("Partly ", u"部分").replace("Showers", u"陣雨").replace("Rain", u"雨").replace("Snow",u"雪").replace("Thunderstorms", u"雷雨")

def city_name(loc):
    if loc["city"] == loc["country"]:
        return translate.translate(loc["city"],tolang="zh-TW")[0]
    else:
        return (translate.translate(loc["country"],tolang="zh-TW")[0] + translate.translate(loc["city"],tolang="zh-TW")[0]).replace(u"香港中央", u"香港中環")

def interpret_weather(condition, loc, forecast = False):
    if forecast:
        return (datetime_to_zh(condition, True) + u"：" + condition_to_zh(condition["text"]) + u"，最高溫度" + f_to_c(condition["high"]) + u"℃，最低溫度" + f_to_c(condition["low"]) + u"℃")
    else:
        return (u"截至當地時間" + datetime_to_zh(condition, False) + u"，" \
                + city_name(loc) + " (" + ", ".join([loc["city"], loc["region"], loc["country"]]) + ")" \
                + u"的天氣是" + condition_to_zh(condition["text"]) + u"，溫度是" + f_to_c(condition["temp"]) + u"℃")

def weather(msg):
    try:
        weather_ = Weather()
        city = translate.translate(msg['Text'], "auto", "en")[0].replace("Hong Kong", "hong-kong-island")
        location = weather_.lookup_by_location(city)
        condition = location.condition()
        forecasts = location.forecast()
        text = interpret_weather(condition, location.location(), False)
        text = text + "\n" + others(location) + u"\n\n一週天氣預報:\n"
        for forecast in forecasts[0:7]:
            text = text + interpret_weather(forecast, None, True) + "\n"
        text = text + u"\n歡迎查詢下一個城市天氣，或輸入「換」退出天氣查詢。"
    except:
        text = u"天氣查詢出錯，請重新輸入。"
    return text

