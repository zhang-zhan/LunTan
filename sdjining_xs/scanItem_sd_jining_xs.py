# -*- coding: UTF-8 -*-
__author__ = 'jdd'
import urllib
import time
import sys
import downPage_sd_jining_xs
import re
from bs4 import BeautifulSoup


class Down_sd_jining_xs_Forum():
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
        print f_url
        print 'downling from %s' % f_url

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
        mydic = soup.find_all('tbody',attrs={"id":re.compile('normalthread_\d*')})

        #获取next page url

        next_page = None
        next_page = soup.find('div', class_='pg').find('a',class_='nxt')['href']
        #print next_page
        #获取每个帖子的url
        timestamp = 0
        #获取版块主题的帖子
        for htstr in mydic:
            try:
                soup2 = BeautifulSoup((str)(htstr))
                if soup2.find_all('td',class_='by')[1].find('span')!=None:
                    rt=soup2.find_all('td',class_='by')[1].find('span')['title']
                else:
                    rt=soup2.find_all('td',class_='by')[1].find_all('a')[1].get_text()
                #print rt
                purl = soup2.find('a',class_='s xst')['href']
                if((first) and (timestamp == 0)):
                    timeArray = time.strptime(rt, "%Y-%m-%d %H:%M")
                    timestamp = int(time.mktime(timeArray))
                    self.lasttime = timestamp
                timeArray = time.strptime(rt, "%Y-%m-%d %H:%M")
                timestamp = int(time.mktime(timeArray))
                #print timestamp
                if(timestamp < self.lasttime):
                    if(timestamp >= self.deadline):
                        reList.append(purl)
                    else:
                        return False
            except Exception as e:
                continue
        print 'analyze successfully'
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
    turl = 'http://www.xsyjn.com/'

    #截止时间的存储目录文件
    dir = './data/'
    filename = dir+url

    # 获取的帖子URL列表
    urlList = []

    #获取更新时间
    deadline = getDeadline(filename)

    #初始化更新时间
    if deadline is 0:
        deadline = initDeadline
    print deadline

    #顺序读取帖子列表页，获取解析帖子URL直到截止时间
    downlist = Down_sd_jining_xs_Forum(turl, deadline)
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

    print "LEN:", len(urlList2)
    #flag=True
    for myurl in urlList2:
        print 'L:%s' % myurl
		#此处调用downPage-demo.py,当两个程序调试好后，在此处调用
	    #不同版块可能存在相同的帖子，若帖子已在列表中则不读取
	downPage_sd_jining_xs.down_page_run(myurl)

    #写入文件
    write_list(urlList2, './data/postList.txt')

	#更新截止时间
    setDeadline(filename, downlist.getNewTime())

    print 'download FINISH : %s' % url
    return True

def scanItemRun():
    #论坛的版块URL
    section = ['forum-88-1.html','forum-2-1.html','forum-74-1.html']


    #循环下载每个版块
    while True:
        try:
            for sec in section:
                if scanItemUrl(sec,1435680000) is False:
                    time.sleep(30)
                time.sleep(3)
        except Exception as e:
            print 'scanItemRunERROR ', e

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    scanItemRun()
