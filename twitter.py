#coding=utf-8
#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import codecs
import glob
import json
import os
import re
import shutil
import signal
import time

import my_glob


#Variables that contains the user credentials to access Twitter API
#You need to get your own API keys from Twitter
access_token = "1"
access_token_secret = "2"
consumer_key = "3"
consumer_secret = "4"

global texts, lang, good_lang
texts = None
lang = None # To store the lang of each tweet
good_lang = ["zh", "en"] # List of languages accepted by user

class OkayStop(Exception):
    pass

class TimeoutException(Exception):   # Custom exception class
    pass

def timeout_handler(signum, frame):   # Custom signal handler
    raise TimeoutException

class StdOutListener(StreamListener):
    def on_data(self, data):
        global texts, lang
        json_load = json.loads(data)
        try:
            if 'lang' in json_load and json_load['lang'] in good_lang:
                texts = json_load['text']
                lang = json_load['lang']
                raise OkayStop
        except OkayStop:
            raise OkayStop
        else:
            pass
    
    def on_error(self, status):
        print(status)

def start_stream(auth, l):
    return_text = ""
    global texts, lang
    if time.time() - my_glob.last_tweet_time < 3:
        return_text = u"上一次為三秒前，等待三秒\n"
        time.sleep(3)
    start_time = time.time()
    while lang is None:
        if time.time() - start_time > 3.0:
            my_glob.last_tweet_time = time.time()
            return return_text + u"超過三秒鐘沒有找到推特，請稍後再試"
        try:
            stream = Stream(auth, l)
            stream.sample()
        except OkayStop:
            my_glob.last_tweet_time = time.time()
            return return_text+ texts
        else:
            continue

def tweet():
    global texts, lang, good_lang
    texts = None
    lang = None
    #This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return start_stream(auth, l)
