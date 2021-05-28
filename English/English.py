#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
from bs4 import BeautifulSoup as BS
from urllib.request import urlretrieve
import pandas as pd
from collections import deque

anki_media_path = os.environ["ANKI_MEDIA_PATH"]

class Website():
    def __init__(self,home_url,search_url,result_link,data_tag):
        self.home_url = home_url
        self.search_url = search_url
        self.result_link = result_link
        self.data_tag = data_tag
        self.headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:76.0) Gecko/20100101 Firefox/76.0",'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*,q=0.8'}
        self.session = requests.Session()
            
        
    def get_search_html(self,word):
        url = self.search_url.format(word)
        req = self.session.get(url, headers=self.headers)
        return BS(req.text, "html.parser")
        
    def extract_result_html(self, bs,word):
        if self.result_link == None:
            return bs, self.search_url.format(word)
        tag, clss, cont = self.result_link
        result_url = bs.find(tag,clss)[cont]
        if self.home_url not in result_url: #relative to absolute
            result_url = self.home_url +result_url
        req = self.session.get(result_url, headers=self.headers)
        return BS(req.text, "html.parser"), result_url
    
    def extract_content(self,bs,word):
        tag, clss, cont = self.data_tag
        
        if "TEXT" in cont:
            if "ALLEX" in cont: #need a smarter way to extract gap
                lines = bs.find_all(tag,clss,limit=3)
                if lines == None: return None
                contents = []
                for line in lines:
                    line = line.get_text().strip()
                    if line not in contents: contents.append(line)
                contents = "<br><br>".join(contents)
                contents = contents.replace(word,"__")
                    
            elif "ALL" in cont:
                lines = bs.find("h2",class_="h2 c_hh")
                if lines == None: return None
                lines = lines.find_all_previous(tag,clss)
                contents = deque()
                for number,line in zip(range(len(lines),0,-1),lines):
                    line = str(number) + ". "+ line.get_text().strip()
                    if line not in contents: contents.appendleft(line)
                contents = "<br>".join(contents)
                
            else:
                lines = bs.find(tag,clss)
                if lines == None: return None
                contents = lines.get_text()
                contents = contents.replace("\n\n","<br>") #anki reads as html
            return contents
                
        if "IMAGE" in cont:
            img_url = bs.find(tag,clss)
            if img_url == None: return None
            img_url = img_url.img["data-src"] #hardcoded for yahoo-image
            contents = urlretrieve(img_url,f"{anki_media_path}/{word}.jpg")
            return '<img src="{}.jpg">'.format(word)
        
        if "AUDIO" in cont:
            audio_url = bs.find(tag,clss)["data-src-mp3"]
            contents = urlretrieve(audio_url,f"{anki_media_path}/{word}.mp3".format(word))
            return "[sound:{}.mp3]".format(word)
        
        else:
            #return bs.find(tag,clss)[cont]
            return None
        
    
    def scrape(self,word):
        search_html = self.get_search_html(word)
        time.sleep(1)
        result_html, result_url = self.extract_result_html(search_html,word)
        content = self.extract_content(result_html,word)
        return content




words = []
path = "English Words.txt"
with open(path) as f:
    lines = f.readlines()[4 :]
    for line in lines:
        if line == "\n": break
        word = line.strip().lower()
        words.append(word)


sites = [
    
    ["https://dictionary.cambridge.org/example/english","https://dictionary.cambridge.org/dictionary/english/{}",None, ("span",{"class":"deg"},"TEXTALLEX")],
    ["https://images.search.yahoo.com","https://images.search.yahoo.com/search/images;_ylt=Awr9FqpXQi9d.wsAgi.LuLkF?ei=UTF-8&iscqry=&fr=sfp&p={}&_guc_consent_skip=1590733731", None, ('ul',{"id":"sres"},"IMAGE")],
    # ["https://dictionary.cambridge.org/dictionary/english-japanese","https://dictionary.cambridge.org/dictionary/english-japanese/{}",None, ]
    
    ["https://www.thefreedictionary.com","https://www.thefreedictionary.com/{}",None,("section",{"data-src":"hm"},"TEXT")],
    ["https://dictionary.goo.ne.jp/word/en","https://dictionary.goo.ne.jp/freewordsearcher.html?MT={}&mode=1&kind=en",None, ("div",{"class":"content-box content-box-ej"},"TEXT")],
    ["https://dictionary.cambridge.org/dictionary/english","https://dictionary.cambridge.org/dictionary/english/{}",None,("div",{"class":"def ddef_d db"},"TEXTALL")],
    ["https://www.oxfordlearnersdictionaries.com", "https://www.oxfordlearnersdictionaries.com/search/english/?q={}",None,("div",{"class":"sound audio_play_button pron-uk icon-audio"},"AUDIO")]
    ]
# home url, search url, login, result link, tag to get data on page  (tag, class, info)

websites = []
for site in sites:
    websites.append(Website(*site))
    
    
    
    
cards = []
for word in words:
    content = [word]
    for website in websites:
        content.append(website.scrape(word))
    cards.append(content)


card_df = pd.DataFrame(cards)
card_df.to_csv("new_cards.csv",index=False,header=False)


    