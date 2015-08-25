#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'jdd'

import urllib
import urllib2
import time
import sys
import re
from bs4 import BeautifulSoup
import downPage_Baidu

def get_last_time(turl,url,current_time):
    print '遍历获得最后回复时间'
    last_time = '0000-00-00 00:00'
    url = turl+get_final_page_url(url)
    time = get_time(url,current_time)
    last_time=time
    rt=str(last_time)
    day=rt[0:10]
    ti=rt[-5::]
    last_time=day+' '+ti
    return last_time
        
def time_format(time):
    date = time[:-5]
    date.strip()
    d = date.split('-')
    if len(d[1])==1:
        d[1]='0'+d[1]
    if len(d[2])==1:
        d[2]='0'+d[2]
    datetime = d[0]+'-'+d[1]+'-'+d[2]+time[-5:]
    return datetime

def get_final_page_url(url):

    f_url = 'http://tieba.baidu.com' + url
    html_content = 3
    while html_content > 0:
        html_content -= 1
        try:
            html_content = urllib.urlopen(f_url).read()
            break
        except Exception as e:
            print('unable to download data [Time:%d][%s]' % (html_content, url))

        #判断是否爬去成功
        if isinstance(html_content, int):
            print('Unable to save data [%s]' % f_url)
            return False

        print 'downling successfully'

    soup = BeautifulSoup(html_content)
    #获取final page url
    final_page = url
    try:
        fps = soup.find('li', class_="l_pager pager_theme_4 pb_list_pager").find_all('a')
        for fp in fps:
            if fp.get_text().strip()=='尾页':
                final_page = fp['href']
                break
    except Exception as e:
        final_page = url
    return final_page

def get_time(url,current_time):
    last_time = '0000-00-00 00:00'
    html_content = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html_content)
    print 'final_page url: '+url
    contents = soup.find_all('div',class_='l_post l_post_bright ')
    for content in contents:
        times = re.findall(r'\d{4}-\d{1,2}-\d{1,2}\W+\d{2}:\d{2}',str(content))
        for time0 in times:
            time0 = time_format(time0)
            if time0>last_time and time0<current_time:
                last_time=time0
    return last_time

class Down_Baidu_Forum():
    """mullti thread download"""
    def __init__(self, url, totime):
        #threading.Thread.__init__(self)
        self.url = url
        self.deadline = totime
        self.lasttime = 0

    def getNewTime(self):
        return self.lasttime

    #return the Next page url or False
    def start_load(self, p_url, reList, first, turl,current_time):
        f_url = self.url + p_url
        print 'downling from %s' % f_url
        
       #爬去网页
        html_content = 3
        while html_content > 0:
            html_content -= 1
            try:
                html_content =urllib.urlopen(f_url).read()
                break
            except Exception as e:
                print('Unable to download data [Time:%d][%s]' % (html_content, f_url))

        #判断是否爬去成功
        if isinstance(html_content, int):
            print('Unable to save data [%s]' % f_url)
            return False

        print 'downling successfully'

        #解析网页
        soup = BeautifulSoup(html_content)
        all_div = soup.find_all('div',class_='threadlist_lz clearfix') #baobao:各个帖子主贴的标题和作者

        #获取next page url
        next_page = None
        try :
            nps = soup.find('div', class_="pager clearfix").find_all('a')  #baobao：帖子列表的页码（1，2，下一页）
        except Exception as e:
            nps = soup.find('div', class_="pagination-default clearfix").find_all('a')

        next_page = soup.find('a', class_="next")['href']  #baobao：下一页

        #获取每个帖子的url
        timestamp = 0
        for div in all_div:
            try:
                Normal=1
                post_url = div.find('a')['href']
                if post_url[0]!='/':
                    post_url = post_url[22:]

                time_div=div.next_sibling.next_sibling
                if(time_div==None): #讨论贴和置顶帖不显示最后回复时间
                    if(div.next_sibling.find('div')!=-1):
                        print '====讨论贴found!===='
                        Normal=0
                        rt = get_last_time(turl, post_url,current_time)
                        #rt = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()))
                    else:
                        print '====置顶帖found!===='
                        Normal=0
                        rt = get_last_time(turl, post_url,current_time)
                        #rt = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()))
                else: #普通贴显示最后回复时间
                    print '====普通帖found!===='
                    Normal=1
                    time_get=time_div.find('span',{'title':'最后回复时间'}).get_text().strip()
                    #print time_get
                    if(time_get.find(':')==2): #显示格式为12:12
                        today=time.strftime('%Y-%m-%d ',time.localtime(time.time()))
                        rt = today+time_get
                    elif(time_get==''):
                        continue
                    else: #显示格式为01-12
                        rt = get_last_time(turl, post_url,current_time)

                if((first) and (self.lasttime == 0) and Normal==1):
                    timeArray = time.strptime(rt, "%Y-%m-%d %H:%M")
                    timestamp = int(time.mktime(timeArray))
                    self.lasttime = timestamp
                timeArray = time.strptime(rt, "%Y-%m-%d %H:%M")
                timestamp = int(time.mktime(timeArray))
                print '最后回复时间为：'+str(rt)+' '+str(timestamp)
                
                #判断截止时间
                if(Normal!=1):
                    if(timestamp >= self.deadline):
                        reList.append(post_url)
                        print 'join in!'
                elif(timestamp < self.lasttime):
                    if(timestamp >= self.deadline):
                        reList.append(post_url)
                        print 'join in!'
                    else:
                        return False
            except Exception as e:
                continue
        return next_page
        print 'analyze successfully'

#更新截止时间
def setDeadline(filename, toTime):
    tx_file = open(filename.decode('utf-8'), 'w')
    tx_file.write(str(toTime))
    tx_file.close()

#获取截止时间
def getDeadline(filename):
    try:
        filename=filename.split('=')[-1].decode('utf-8')
        tx_file = open(filename, 'r')
        toTime = tx_file.readline()
        tx_file.close()
    except Exception as e:
        return 0
    return int(toTime.strip())

def write_list(tx_list, fn):
    """把列表内容写入文本"""
    tx_file = open(fn, 'a+')
    for tx in tx_list:
        tx_file.write(tx.strip()+'\n')
    tx_file.close()

def scanItemUrl(url, current_time, initDeadline = 1439019000):
 
    print 'start。。。'
    #sys.exit()
    #the root url
    turl = 'http://tieba.baidu.com'

    #截止时间的存储目录文件
    dir = r'./data/'
    filename = dir+url[1:].split('=')[-1]
    print "filename="+filename
    # 获取的帖子URL列表
    urlList = []

    #获取更新时间
    deadline = getDeadline(filename)

    #初始化更新时间
    if deadline is 0:
        deadline = initDeadline
    print deadline

    #顺序读取帖子列表页，获取解析帖子URL直到截止时间
    downlist = Down_Baidu_Forum(turl, deadline)
    next_page = downlist.start_load(url, urlList, True, turl,current_time)

    print "NEXT Page:%s" % next_page
    if not isinstance(next_page, bool):
        while True:
            next_page = downlist.start_load(next_page, urlList, False, turl,current_time)
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

    for myurl in urlList2:
        print "当前的帖子url：" + myurl
        downPage_Baidu.down_page_run(myurl)

	#更新截止时间
    setDeadline(filename, downlist.getNewTime())

    print 'download FINISH : %s' % url
    return True

def scanItemRun():
    #百度的版块URL
    section =['/f?kw=%C9%BD%B6%AB','/f?ie=utf-8&kw=德州','/f?ie=utf-8&kw=聊城','/f?ie=utf-8&kw=临沂','/f?ie=utf-8&kw=菏泽','/f?ie=utf-8&kw=莱芜','/f?ie=utf-8&kw=青岛','/f?ie=utf-8&kw=济南','/f?ie=utf-8&kw=淄博','/f?ie=utf-8&kw=枣庄','/f?ie=utf-8&kw=东营','/f?ie=utf-8&kw=烟台','/f?ie=utf-8&kw=潍坊','/f?ie=utf-8&kw=济宁','/f?ie=utf-8&kw=泰安','/f?ie=utf-8&kw=威海','/f?ie=utf-8&kw=日照','/f?ie=utf-8&kw=滨州','/f?ie=utf-8&kw=胶州','/f?ie=utf-8&kw=平度','/f?ie=utf-8&kw=城阳','/f?ie=utf-8&kw=即墨']

    #循环下载每个版块
    while True:
        try:
            for sec in section:
                current_time = time.strftime('%Y-%m-%d %H:%M',time.localtime())
                print current_time
                #sys.exit()
                if scanItemUrl(sec,current_time,1439363400) is False:
                    time.sleep(30)
                time.sleep(3)
        except Exception as e:
            print 'scanItemRunERROR ', e

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    scanItemRun()
