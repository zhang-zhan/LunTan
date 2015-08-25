# -*- coding: UTF-8 -*-
__author__ = 'jdd'
import urllib
import urllib2
import re
import threading
import sys
import socket
import time
import datetime
import json
import os
from bs4 import BeautifulSoup

class Down_Post(threading.Thread):
    """mullti thread download"""
    """ postid,帖子ID，
        url 帖子url，
        startnum endnum 是本线程下载的帖子的页数范围（根据需要修改），
        lastpage，帖子的最新页码（用于确定下载的是否是最后一页，用于跟新页数和楼数）
        replycount 已经下载的跟帖楼数
        resultdic 保存下载解析后的数据（字典）
    """
    def __init__(self, postid, url, startnum,endnum, lastpage, replycount,resultdic):
        threading.Thread.__init__(self)
        self.url = url
        self.pageurl = url
        self.startnum = startnum
        self.endnum = endnum
        self.lastpage = lastpage
        self.num = startnum #用于保存数据
        self.postID = postid
        self.rc = replycount
        self.resultdic = resultdic #保存下载解析后的数据
        #print "RC:%s" % self.rc
    def run(self):
        #判断是否是最新的一页（最新的数据在最后一页，如果你处理的论坛不是，请自行修改程序
        is_last = False
        tempurl = self.pageurl
        for num in range(self.startnum, self.endnum):
            self.pageurl = '%s?pn=%s.html' % (tempurl, num)
            self.num = num
            print 'downing from %s ' % self.pageurl
            if(num == self.lastpage):
                restmp = self.down_text(True)
                if restmp is False:
                    continue
                if len(restmp) is not 0:
                    self.resultdic[num] = restmp
                    is_last = True
            else:
                restmp = self.down_text(False)
                if restmp is False:
                    continue
                if len(restmp) is not 0:
                    self.resultdic[num] = restmp

        """如果是最后一页，则将页数和最后的楼数写入返回字典中"""
        if is_last is True:
            """self.client.UpdateInfo(self.postID, self.lastpage, self.rc)"""
            self.resultdic['pg'] = self.lastpage
            self.resultdic['rc'] = self.rc

    #这部分需要自己修改 last_page is boolean
    #返回值是一个字典列表[{},{}...]，其中的字典元素是{'属性':值}，注意文档中要说明值得类型
    #以下以天涯论坛为例，需要自己修改
    def down_text(self, last_page):
        """accord the url , download content instert into dic"""
        html_content = 3
        while html_content > 0:
            html_content -= 1
            try:
                html_content =urllib.urlopen(self.pageurl).read()
                break
            except Exception as e:
                print('Unable to download data [Time:%d][%s]' % (html_content, self.pageurl))
                insert_log('Unable to download data [Time:%d][%s]' % (html_content, self.pageurl))

        if isinstance(html_content, int):
            print('Unable to save data [%s]' % self.pageurl)
            insert_log('Unable to save data [%s]' % self.pageurl)
            return False

        print 'downling successfully from %s' % self.pageurl
        soup = BeautifulSoup(html_content)

        alldata =[]
        audic = {}

        """
        由于第一页有主帖，因此第一页的解析会不同，要把主帖的所有信息保存下来，跟帖的信息也是如此
        """
        #主帖的部分解析
        if((self.num == 1) and (self.rc == 0)):
            if(soup.find('div', {'class': 'l_post l_post_bright noborder '})is not None):
                mainpost = soup.find('div', {'class': 'l_post l_post_bright noborder '})
                data_field = json.loads(mainpost['data-field'])

                if soup.find('h1',class_="core_title_txt ") is not None:
                    title = soup.find('h1',class_="core_title_txt ")['title']
                else:
                    title = soup.find('h1',class_="core_title_txt member_thread_title_pb ")['title']

                if soup.find('a',class_='card_title_fname') is not None:
                    section = soup.find('a',class_='card_title_fname').get_text().strip()
                else:
                    section = soup.find('a',class_='j_plat_picbox plat_picbox')['alt']

                auname =data_field['author']["user_name"]

                try:
                    auid = data_field['author']["user_id"]
                except Exception as e:
                    auid = data_field['content']["post_id"]

                ctime =data_field['content']['date']
            else:
                mainpost = soup.find('div', {'class': 'l_post l_post_bright noborder'})

                try:
                    data_field = json.loads(mainpost['data-field'])
                except Exception as e:
                    mainpost = soup.find('div',class_="pb_content clearfix").find('div', {'class': 'l_post l_post_bright '})
                    data_field = json.loads(mainpost['data-field'])

                try:
                    title = soup.find('div', {'class': 'core_title core_title_theme_bright'}).find("h1").text
                except Exception as e:
                    title = soup.find('title').get_text()

                section = soup.find('a', {'class': 'card_title_fname'});
                if section is None:
                    section = soup.find('a',{'class': 'plat_title_h3'}).text
                else:
                    section = section.text.strip();

                auname = data_field['author']['user_name']

                try:
                    auid = data_field['author']['user_id']
                except Exception as e:
                    auid = data_field['content']['post_id']

                t = mainpost.find("span", class_ = "j_reply_data")
                if t is None:
                    ctime = data_field['content']['date']
                else:
                    ctime =  t.text

            audic['title'] = title
            audic['sec'] = section
            audic['uname'] = auname
            audic['uid'] = auid
            print soup
            print ctime
            audic['ctime'] = ctime
            audic['ro'] = 1
            audic['text'] = mainpost.find("div", id = re.compile("post_content_[0-9]+")).text.strip()

            try:
                imgs=mainpost.find("div", id = re.compile("post_content_[0-9]+")).find_all("img")
                for img in imgs:
                    audic['text'] = audic['text'] + '\n图片 URL:' +img["src"]
            except Exception as e:
                pass

            alldata.append(audic)

        mydic = soup.find_all("div", class_ = "l_post l_post_bright ")
        for soup2 in mydic:
            #解析跟帖内容
            redic = {}
            try:
                data_field = json.loads(soup2['data-field'])
                rorder =  data_field['content']['post_no']
                irorder = (int)(rorder)
                redic['ro'] = irorder

                #update the reply count
                if(last_page and (irorder > self.rc)):
                    self.rc = irorder

                strtext = soup2.find('div', class_='d_post_content j_d_post_content  clearfix')
                redic['text'] = strtext.text.strip()

                try:
                    imgs=strtext.find_all('img')
                    for img in imgs:
                        redic['text'] = redic['text'] + '\n图片 URL:' +img["src"]
                except Exception as e:
                    pass

                uname = data_field['author']['user_name']
                """text.append('UNAME'+ soup2.find('div', class_='atl-info').find('span').get_text())"""
                redic['un'] = uname

                try:
                    uid = data_field['author']['user_id']
                except Exception as e:
                    uid = data_field['content']['post_id']

                redic['uid'] = uid
                t = soup2.find("span", class_ = "j_reply_data")
                if t is None:
                    rtime = data_field['content']['date']
                else:
                    rtime = t.text
                redic['time'] = rtime
                tmp = soup2.find_all("ul", class_ = "j_lzl_m_w")
                if len(tmp) > 0:
                    for li in tmp[0].find_all("li"):
                        lst = li.find_all("span")
                        if len(lst) > 0:
                            redic['text'] += "re-text:" + lst[0].text + '\r\n'
                        lst = li.find_all("span", class_ = "lzl_time")
                        if len(lst) > 0:
                            redic['text'] += "re-time:" + lst[-1].text + '\r\n'
                        lst = li.find_all("a", username = True)
                        if len(lst) > 0:
                            redic['text'] += "re-author:" + lst[0]['username'] + '\r\n'
                alldata.append(redic)
            except AttributeError as e:
                alldata.append(redic)
                continue
        print 'All:%s' % self.pageurl
        return alldata

#获取帖子的页数，需要自己实现
def page(url):
    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page)
    wrap1 = soup.find('div', {'class': 'wrap1'})
    li = wrap1.find('li', {'class': 'l_reply_num'})
    count = li.find(lambda tag: len(tag.attrs) == 2)      #the length of tag is 2 这个函数可以取有几个属性，len = 2即取属性长度为2的标签
    page= li.find(lambda tag: len(tag.attrs) == 1)
    return int(page.text)

#把字典写入文件，fn是文件名，dict是下载数据的字典，postId是帖子ID
def write_text(postId,dict, fn, oldrc):
    """把字典内容按键（页数）写入文本，每个键值为每页内容的list列表"""
    tx_file = open(fn, 'w+')
    pg = 1
    rc = 0
    try:
        pg = dict.pop('pg')
        rc = dict.pop('rc')
    except Exception as e:
        print 'ERROR:import_data %s' % postId
        insert_log('ERROR:import_data %s' % postId)
        return

    tx_file.write(str(postId)+'\r\n')
    tx_file.write('PG:RC  %d:%d' %(pg,rc) + '\r\n')
    for k, v in dict.iteritems():
        for dicTmp in v:
            if len(dicTmp) > 0:
                if (dicTmp['ro']) > oldrc or dicTmp['ro'] == 0:
                    for k2, v2 in dicTmp.iteritems():
                        #str(v2).decode("UTF-8", 'ignore')
                        tx_file.write(k2 + ':' + str(v2) + '\r\n')

    tx_file.close()

#获取更新数据，pg 和 rc
#需要自己实现，读取相应文件获得这两个值，如果没有，返回pg=1，rc=0
def getUpdateInfo(postid):
    updic = {}
    try:
        file = open('data/' + postid + '.txt')
    except Exception as e:
        updic['pg'] = 1
        updic['rc'] = 0
        return updic
    try:
        file.readline()
        page_count = file.readline()

        #PG:RC  1:41
        #print page_count
        searchObj = re.search( r'PG:RC  (.+):(.+)', page_count, re.M|re.I)
        if searchObj:
            updic['pg'] = int(searchObj.group(1))
            updic['rc'] = int(searchObj.group(2))
        else:
            updic['pg'] = 1
            updic['rc'] = 0
        return updic
    finally:
        file.close()

def down_page_run(urlstr):
    socket.setdefaulttimeout(120)
    thread_num = 4
    threads = []
    url = 'http://tieba.baidu.com' + urlstr
    print url

    #对于帖子不存在了的情况进行判断
    html_content =urllib.urlopen(url).read()
    soup = BeautifulSoup(html_content,from_encoding='utf-8')
    titlep = ''
    try:
        titlep = soup.find('title').get_text().strip()
    except Exception as e:
        pass

    if titlep == '':
        return
    if titlep == '贴吧404':
        print '%s 帖子不存在' %url
        insert_log('%s 帖子不存在' %url)
        return

    strs = urlstr.split('/')
    postid = strs[-1]

    fn = './data/%s.txt' % postid
    try:
        os.remove(fn)
    except  WindowsError:
        pass

    updic = getUpdateInfo(postid)
    oldpage = updic['pg']
    oldrc = updic['rc']
    print oldpage, oldrc
    my_page = page(url)
    if my_page is None:
        my_page = oldpage
    print 'page num is : %s ~ %s' %(oldpage, my_page)
    #page_num是有几页数据
    page_num = my_page - oldpage
    if(page_num < 10):
        thread_num = 2

    numperthread = 0
    if thread_num is 1:
        numperthread = page_num
    else:
        numperthread = page_num/(thread_num - 1)
        #还有剩余的一个线程来爬去余数
    if numperthread is 0:
        numperthread = 1

    resultdic = {}
    for num in range(0, thread_num-1):
        downlist = Down_Post(postid, url, num*numperthread+oldpage, (num+1)*numperthread+oldpage, my_page, oldrc, resultdic)
        downlist.start()
        threads.append(downlist)
    downlist = Down_Post(postid, url, numperthread*(thread_num-1)+oldpage, my_page+1, my_page, oldrc, resultdic)
    downlist.start()
    threads.append(downlist)
    """检查下载完成后再进行写入"""
    for t in threads:
        t.join()

    #写入文件
    fn = './data/%s.txt' % postid
    write_text(postid, resultdic, fn, oldrc)

def insert_log(record):
    #打印错误日志
    with open('log/downTyData.log', 'a') as log:
        log.write('{time},{record},\r\n'.format(
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            record = record
        ))

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    down_page_run("/p/3966793199")