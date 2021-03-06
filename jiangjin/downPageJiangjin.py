# -*- coding: UTF-8 -*-
__author__ = 'jdd'
import urllib
import re
import threading
import sys
import socket
import datetime
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

        #循环下载本下载线程应当下载的URL page
        for num in range(self.startnum, self.endnum):
            #根据格式调整url
            self.pageurl = '%s%s.shtml' % (self.url[:-7], num)
            self.num = num
            print 'downling from %s' % self.pageurl
            if(num == self.lastpage):
                restmp = self.down_text(True)
                """result.extend(restmp)"""
                if restmp is False:
                    continue
                if len(restmp) is not 0:
                    #restmp 是一个字典列表，num是页码
                    self.resultdic[num] = restmp
                    is_last = True
            else:
                restmp = self.down_text(False)
                if restmp is False:
                    continue
                if len(restmp) is not 0:
                    self.resultdic[num] = restmp
                """result.extend(restmp)"""

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

        #对于帖子不存在了的情况进行判断
        titlep = soup.title.string
        if titlep is '出错了_天涯社区':
            print '出错了:%s' % self.pageurl
            insert_log('出错了:%s' % self.pageurl)
            return []

        alldata =[]
        audic = {}

        """
        由于第一页有主帖，因此第一页的解析会不同，要把主帖的所有信息保存下来，跟帖的信息也是如此
        """
        #主帖的部分解析
        if((self.num == 1) and (self.rc == 0)):
            title = soup.find('span', class_='s_title').get_text()
            section = soup.find('p', class_='crumbs').find_all('a')[1].get_text()
            auname = soup.find('div', class_='atl-info').find('span').find('a').get_text()
            auid = soup.find('div', class_='atl-info').find('span').find('a')['uid']
            ctime = soup.find('div', class_='atl-info').find_all('span')[1].get_text().split('：')[1]

            audic['title'] = title
            audic['sec'] = section
            audic['uname'] = auname
            audic['uid'] = auid
            audic['ctime'] = ctime
            audic['ro'] = 0

        mydic = soup.find_all('div',class_="atl-item")
        mi = 0
        for htstr in mydic:
            soup2 = BeautifulSoup((str)(htstr))
            #如果把self.rc放在外层if中用于判断是否没有记录，则对于有少量回复，而又有更新的情况，便不能跳过第一页的主帖
            #解析主帖部分内容
            if((mi == 0) and (self.num == 1)):
                mi +=1
                if(self.rc == 0):
                    strtext = soup2.find('div', class_='bbs-content').get_text()
                    audic['text'] = strtext.strip()

                    if 'reportme' not in soup2.find('div', class_='atl-reply').find('a')['class']:
                        asrc = soup2.find('div', class_='atl-reply').find('a').get_text()
                        audic['src'] = asrc.strip()
                    alldata.append(audic)
                continue

            #解析跟帖内容
            redic = {}
            try:
                rorder = htstr['id']
                irorder = (int)(rorder)
                redic['ro'] = irorder

                #update the reply count
                if(last_page and (irorder > self.rc)):
                    self.rc = irorder

                strtext = soup2.find('div', class_='bbs-content').get_text()
                redic['text'] = strtext.strip()

                if 'reportme' not in soup2.find('div', class_='atl-reply').find('a')['class']:
                    rsrc = soup2.find('div', class_='atl-reply').find('a').get_text()
                    redic['src'] = rsrc.strip()

                uname = soup2.find('div', class_='atl-info').find('span').get_text().split('：')
                """text.append('UNAME'+ soup2.find('div', class_='atl-info').find('span').get_text())"""
                redic['un'] = uname[1]

                if(uname[0] == '作者'):
                    redic['au'] = False
                else:
                    redic['au'] = True

                uid = soup2.find('div', class_='atl-info').find('a')['uid']
                redic['uid'] = uid

                rtime = soup2.find('div', class_='atl-info').find_all('span')[1].get_text().split('：')[1]
                redic['time'] = rtime

                alldata.append(redic)
            except AttributeError as e:
                alldata.append(redic)
                continue
        print 'All:%s' % self.pageurl
        return alldata

#获取帖子的页数，需要自己实现
def page(url):
    """根据第一页地址抓取总页数"""
    data = 3
    while data>0:
        data -= 1
        try:
            data = urllib.urlopen(url).read()
            page_pattern = re.compile(r'<a href="\S*?">(\d*)</a>\s*<a href="\S*?" class="\S*?">下页</a>')
            page_result = page_pattern.search(data)
            break
        except Exception as e:
            print 'Unable to download the page num in %s' % url
            insert_log('Unable to download the page num in %s' % url)
    if isinstance(data,int):
        print 'Unable to save page num in %s' % url
        insert_log('Unable to save page num in %s' % url)
        return None

    if page_result:
        page_num = int(page_result.group(1))
        return page_num

#把字典写入文件，fn是文件名，dict是下载数据的字典，postId是帖子ID
def write_text(postId,dict, fn):
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
    for k,v in dict.iteritems():
        for dicTmp in v:
            for k2,v2 in dicTmp.iteritems():
                tx_file.write(k2+':'+str(v2)+'\r\n')

    tx_file.close()

#获取更新数据，pg 和 rc
#需要自己实现，读取相应文件获得这两个值，如果没有，返回pg=1，rc=0
def getUpdateInfo(postid):
    return {'pg':1, 'rc':0}

def down_page_run(urlstr):
    """the number of thread"""
    socket.setdefaulttimeout(120)

    #设置线程数量
    thread_num = 4
    url = 'http://bbs.tianya.cn'+ urlstr
    """print 'URL:%s' % url"""
    strs = urlstr.split('-')
    postid = strs[2]

    #需要自己实现
    updic = getUpdateInfo(postid)
    oldpage = updic['pg']
    oldrc = updic['rc']

    my_page = page(url)
    if my_page is None:
        my_page = oldpage

    #my_dict = {}
    print 'page num is : %s ~ %s' % (oldpage, my_page)
    threads = []

    """根据设置的线程数量设置线程"""
    page_num = my_page - oldpage
    if(page_num < 10):
        thread_num = 2

    numperthread = 0
    if thread_num is 1:
        numperthread = page_num
    else:
        numperthread = page_num/(thread_num-1)

    if numperthread is 0:
        numperthread = 1
    """numoflast = my_page%(thread_num-1)"""

    #保存所有数据的字典{pagenum:[{},{}..]..}
    resultdic = {}
    """根据页数构造urls进行多线程下载"""
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
    write_text(postid, resultdic, fn)

def insert_log(record):
    '''
    打印错误日志
    '''
    with open('log/downTyData.log', 'a') as log:
        log.write('{time},{record},\r\n'.format(
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            record = record
        ))


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    down_page_run("/post-free-4736150-1.shtml")
