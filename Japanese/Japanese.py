#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Japanese Scraping 
"""

import os
import requests
import time
from bs4 import BeautifulSoup as BS
from urllib.request import urlretrieve
import re
import pandas as pd

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
            if "ALL" in cont:
                lines = bs.find_all(tag,clss)
                contents = []
                for line in lines:
                    line = line.find_next(class_="the-sentence").get_text()
                    contents.append(line)
                contents = "<br>".join(contents)
                contents = contents.replace(word,"__")
                    # hardcoded for yorei.com
            else:
                lines = bs.find(tag,clss)
                contents = lines.get_text()
                contents = contents.replace("\n\n","<br>") #anki reads as html
            return contents
                
        if "IMAGE" in cont:
            img_url = bs.find(tag,clss).img["data-src"] #hardcoded for yahoo-image
            contents = urlretrieve(img_url,"{}}/{}.jpg".format(anki_media_path, word))
            return '<img src="{}.jpg">'.format(word)
        
        else:
            return bs.find(tag,clss)[cont]
    
    def scrape(self,word):
        search_html = self.get_search_html(word)
        time.sleep(3)
        result_html, result_url = self.extract_result_html(search_html,word)
        content = self.extract_content(result_html,word)
        return content
    

def get_audio(word,reading):
    audio_source = os.environ["AUDIO_SOURCE"] #can't reveal 
    r = requests.get(f"{audio_source}?kana={reading}&kanji={word}")

    
    with open(f"{anki_media_path}/{word}.mp3", "wb") as f:
        f.write(r.content)
    return "[sound:{}.mp3]".format(word)
#jisho.org also looks like it has pretty scrapable audio
    

path = "./Japanese words to add to anki.txt"
words = []
with open(path) as f:
    lines = f.readlines()[3 :]
    for line in lines:
        if line == "\n": break
        word, reading = line.strip().split('、')
        words.append((word,reading))
   

sites = [
    ["https://www.wadoku.de","https://www.wadoku.de/search/{}",("a",{"href":re.compile("^(/entry/view).*")},"href"),("small",{"class":"accent label label-accent label-accent-active"},"TEXT")],
    ["http://yourei.jp", "http://yourei.jp/{}",None, (True,{"id":re.compile("sentence-(1|2|3)$")},"TEXTALL")],
    ["https://images.search.yahoo.com","https://images.search.yahoo.com/search/images;_ylt=Awr9FqpXQi9d.wsAgi.LuLkF?ei=UTF-8&iscqry=&fr=sfp&p={}&_guc_consent_skip=1590733731", None, ('ul',{"id":"sres"},"IMAGE")],
    ["https://dictionary.goo.ne.jp", "https://dictionary.goo.ne.jp/srch/all/{}/m1u/", ("a",{"href":re.compile("^/word/.*")},"href"),("div",{"class":"contents"},"TEXT")]
      ]
# home url, search url, login, result link, tag to get data on page  (tag, class, info)

websites = []
for site in sites:
    websites.append(Website(*site))
    
    
cards = []
for word,reading in words:
    content = [word]
    for website in websites:
        content.append(website.scrape(word))
    content.append(get_audio(word,reading))
    cards.append(content)


card_df = pd.DataFrame(cards)
card_df.to_csv("./new_cards.csv",index=False,header=False)


    

    
        
        