#coding:utf-8
__author__ = 'zhangzhan'

import urllib
import os
import time
import sys
from bs4 import BeautifulSoup
from downPageBaiDu import *


class Down_BaiDu_Forum():
    """mullti thread download"""
    def __init__(self, url, totime):
        #threading.Thread.__init__(self)
        self.url = url
        self.deadline = totime
        self.lasttime = 0

    def getNewTime(self):
        return self.lasttime

    #return the Next page url or False
    def start_load(self, p_url, reList, first):
        f_url = self.url + p_url
        print 'downling from %s' % f_url
        import urllib2
        #爬去网页
        html_content = 3
        while html_content > 0:
            html_content -= 1
            try:
                # i_headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1) Gecko/20090624 Firefox/3.5",\
                #  "Referer": 'http://www.baidu.com'}
                # req = urllib2.Request(f_url, headers=i_headers)
                #
                # html_content = urllib2.urlopen(req).read()
                html_content = urllib.urlopen(f_url).read()
                # opener = urllib2.build_opener(urllib2.ProxyHandler({'http':proxy}), urllib2.HTTPHandler(debuglevel=1))
                # urllib2.install_opener(opener)
                #
                # i_headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1) Gecko/20090624 Firefox/3.5", \
					# "Referer": 'http://www.baidu.com'}
                #
                # req = urllib2.Request(f_url, headers=i_headers)
                # content = urllib2.urlopen(req).read()
                # return content
                # html_content =urllib.urlopen(f_url).read()
                break
            except Exception as e:
                print('Unable to download data [Time:%d][%s]' % (html_content, f_url))

        #判断是否爬去成功
        if isinstance(html_content, int):
            print('Unable to save data [%s]' % f_url)
            return False

        print 'downling successfully'

        #解析网页
        import re
        soup = BeautifulSoup(html_content)

        mydic = soup.find("div",id="content_leftList").find_all("li",class_="j_thread_list clearfix")
        next_page = None
        next_page = soup.find("a",class_="next")['href']
        print next_page
        '''if len(nps) == 3:
            next_page = soup.find('div', class_="links").find_all('a')[2]['href']
        elif len(nps) == 2:
            next_page = soup.find('div', class_="links").find_all('a')[1]['href']'''

        #获取每个帖子的url
        timestamp = 0
        for htstr in mydic:
            try:
                #print htstr
                soup2 = BeautifulSoup((str)(htstr))
                try:
                    rTime = soup2.find("div",class_="threadlist_detail clearfix").find("div",class_="threadlist_author").find("span",class_="threadlist_reply_date j_reply_data").get_text().strip("\r\t\n").strip()
                    if ":" in rTime:
                        ymd = time.strftime('%Y-%m-%d',time.localtime(time.time()))
                        rt = ymd+" "+rTime
                        timeArray = time.strptime(rt, "%Y-%m-%d %H:%M")
                    elif "-" in rTime:
                        ymd = time.strftime('%Y',time.localtime(time.time()))
                        rt = ymd+"-"+rTime+" "+"00:00"
                        timeArray = time.strptime(rt, "%Y-%m-%d %H:%M")

                except:
                    continue
                    #rt = soup2.find_all("a")[-1].get_text()
                print rt
                purl = soup2.find("div", class_="threadlist_text threadlist_title j_th_tit  ").find("a",class_="j_th_tit")['href']
                print purl
                if((first) and (timestamp == 0)):
                    timeArray = time.strptime(rt, "%Y-%m-%d %H:%M")
                    timestamp = int(time.mktime(timeArray))
                    self.lasttime = timestamp
                timeArray = time.strptime(rt, "%Y-%m-%d %H:%M")
                timestamp = int(time.mktime(timeArray))

                #判断截止时间
                if(timestamp < self.lasttime):
                    if(timestamp >= self.deadline):
                        reList.append(purl)
                    else:
                        return False
            except Exception as e:
                continue
        return next_page


#更新截止时间
def setDeadline(filename, toTime):
    tx_file = open(filename, 'w')
    tx_file.write(str(toTime))
    tx_file.close()

#获取截止时间
def getDeadline(filename):
    try:
        tx_file = open(filename, 'r')
        toTime = tx_file.readline()
        tx_file.close()
    except Exception as e:
        return 0
    if toTime is "":
        return 0
    return int(toTime.strip())

def write_list(tx_list, fn):
    """把列表内容写入文本"""
    tx_file = open(fn, 'a+')
    for tx in tx_list:
        tx_file.write(tx.strip()+'\n')
    tx_file.close()

def scanItemUrl(url, initDeadline = 1414640120):
    print 'start。。。'

    #the root url
    turl = 'http://tieba.baidu.com'

    #截止时间的存储目录文件

    if os.path.exists("./data/") is False:
        os.mkdir("./data/")
    dir = './data/'
    filename = dir+url[1:].split("?")[1]

    # 获取的帖子URL列表
    urlList = []

    #获取更新时间
    deadline = getDeadline(filename)
    #初始化更新时间
    if deadline is 0:
        deadline = initDeadline
    print deadline

    #顺序读取帖子列表页，获取解析帖子URL直到截止时间
    downlist = Down_BaiDu_Forum(turl, deadline)
    next_page = downlist.start_load(url, urlList, True)

    print "NEXT Page:%s" % next_page
    if not isinstance(next_page, bool):
        while True:
            next_page = downlist.start_load(next_page, urlList, False)
            print "NEXT:%s" % next_page
            if next_page is None:
                break
            if isinstance(next_page, bool):
                break
    if len(urlList) == 0:
        print 'THE LEN of urlList is 0'
        return False


    #去除帖子列表中的重复项，更新过快的原因
    urlList2 = {}.fromkeys(urlList).keys()

    #写入文件
    write_list(urlList2, './data/postList.txt') 

    print "LEN:", len(urlList2)
     #此处调用downPage-demo.py,当两个程序调试好后，在此处调用
    for myurl in urlList2:
        print 'L:%s' % myurl
        down_page_run(myurl)

	#更新截止时间
    setDeadline(filename, downlist.getNewTime())

    print 'download FINISH : %s' % url
    return True

def scanItemRun():
    #延庆的版块URL
    #section = ['forum-65-1.html','forum-77-1.html',"forum-145-1.html","forum-107-1.html","forum-106-1.html"]
    section =['/f?kw=%C9%BD%B6%AB','/f?ie=utf-8&kw=德州','/f?ie=utf-8&kw=聊城','/f?ie=utf-8&kw=临沂','/f?ie=utf-8&kw=菏泽','/f?ie=utf-8&kw=莱芜','/f?ie=utf-8&kw=青岛','/f?ie=utf-8&kw=济南','/f?ie=utf-8&kw=淄博','/f?ie=utf-8&kw=枣庄','/f?ie=utf-8&kw=东营','/f?ie=utf-8&kw=烟台','/f?ie=utf-8&kw=潍坊','/f?ie=utf-8&kw=济宁','/f?ie=utf-8&kw=泰安','/f?ie=utf-8&kw=威海','/f?ie=utf-8&kw=日照','/f?ie=utf-8&kw=滨州','/f?ie=utf-8&kw=胶州','/f?ie=utf-8&kw=平度','/f?ie=utf-8&kw=城阳','/f?ie=utf-8&kw=即墨']

    #循环下载每个版块
    while True:
        try:
            for sec in section:
                if scanItemUrl(sec, 1440259200) is False:
                    time.sleep(30)
                time.sleep(3)
        except Exception as e:
            print 'scanItemRunERROR ', e

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    scanItemRun()

