# -*- coding: UTF-8 -*-
__author__ = 'jdd'
import urllib
import re
import threading
import sys
import socket
import datetime
import os
import time
from bs4 import BeautifulSoup

class Down_sdtainfo_Page(threading.Thread):
    """mullti thread download"""
    """ postid,帖子ID，
        url 帖子url，
        startnum endnum 是本线程下载的帖子的页数范围（根据需要修改），
        lastpage，帖子的最新页码（用于确定下载的是否是最后一页，用于跟新页数和楼数）
        replycount 已经下载的跟帖楼数
        resultdic 保存下载解析后的数据（字典）
    """


    def __init__(self, postid, url, startnum, endnum, lastpage, replycount, resultdic):
        threading.Thread.__init__(self)
        self.url = url
        self.pageurl = url
        self.startnum = startnum
        self.endnum = endnum
        self.lastpage = lastpage
        self.num = startnum  # 用于保存数据
        self.postID = postid
        self.rc = replycount
        # self.originalrc = 14
        self.originalrc = replycount
        self.resultdic = resultdic
        # 保存下载解析后的数据
        # print "RC:%s" % self.rc

    def run(self):
        # 判断是否是最新的一页（最新的数据在最后一页，如果你处理的论坛不是，请自行修改程序
        is_last = False

        # 循环下载本下载线程应当下载的URL page
        for num in range(self.startnum, self.endnum):
            # 根据格式调整url
            # 根据格式调整url
            lasturl=self.pageurl.split('-') #url的最末片段，比如'178165755,1.html'
            self.pageurl = '%s-%s-%s-%s.html' % (lasturl[0], lasturl[1], num, '1')   #根据格式调整url
            self.num = num
            print 'downling from %s' % self.pageurl
            if (num == self.lastpage):
                restmp = self.down_text(True)
                """result.extend(restmp)"""
                if restmp is False:
                    continue
                if len(restmp) is not 0:
                    # restmp 是一个字典列表，num是页码
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

    # 这部分需要自己修改 last_page is boolean
    # 返回值是一个字典列表[{},{}...]，其中的字典元素是{'属性':值}，注意文档中要说明值得类型
    # 以下以天涯论坛为例，需要自己修改
    def down_text(self, last_page):
        """accord the url , download content instert into dic"""
        html_content = 3
        while html_content > 0:
            html_content -= 1
            try:
                html_content = urllib.urlopen(self.pageurl).read()
                print self.pageurl
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

        # 对于帖子不存在了的情况进行判断

        if(soup.find('div', class_='alert_error')):
            titlep = soup.find_all('div', class_='alert_error')[0].find('p').get_text()

            if titlep==u'抱歉，指定的主题不存在或已被删除或正在被审核':
                print '出错了:%s' % self.pageurl
                insert_log('出错了:%s' % self.pageurl)
                return False

        alldata = []
        audic = {}


        """
        由于第一页有主帖，因此第一页的解析会不同，要把主帖的所有信息保存下来，跟帖的信息也是如此
        """
        # 主帖的部分解析
        if ((self.num == 1) and (self.rc == 0)):
            # 题目
            # 报错
            title_section= soup.find('title').get_text()
            #print title_section
            title=title_section.split('-')[0].strip()
            #print title
            section=title_section.split('-')[1].strip()
            #print section
            # 获取作者名字
            unknow=soup.find('div',class_='pi').get_text().strip()
            unknow=unknow.encode('utf-8')
                    #print unknow
            if re.search('匿名',unknow ):
                auname='匿名'
                auid='unknow'
                # 回复时间
                if soup.find_all('div',class_='authi')[0].find('em').find('span')!=None:
                    ctime=soup.find_all('div',class_='authi')[0].find('em').find('span')['title']
                else:
                    ctime1=soup.find_all('div',class_='authi')[0].find('em').get_text().split(' ')[1]
                    ctime2=soup.find_all('div',class_='authi')[0].find('em').get_text().split(' ')[2]
                    ctime=ctime1+' '+ctime2
                    #print rtime
            else:
                auname = soup.find('div',class_='authi').get_text().strip()
                #print auname
                # 得到回复者的id
                auid = soup.find('div',class_='authi').find('a')['href'].split('&')[1].split('=')[1]
                #print type(auid)
                # 回复时间
                if soup.find_all('div',class_='authi')[1].find('em').find('span')!=None:
                    ctime=soup.find_all('div',class_='authi')[1].find('em').find('span')['title']
                else:
                    ctime1=soup.find_all('div',class_='authi')[1].find('em').get_text().split(' ')[1]
                    ctime2=soup.find_all('div',class_='authi')[1].find('em').get_text().split(' ')[2]
                    ctime=ctime1+' '+ctime2
            #print ctime
            audic['title'] = title
            audic['sec'] = section
            audic['uname'] = auname
            audic['uid'] = auid
            audic['ctime'] = ctime
            timeArray = time.strptime(ctime, "%Y-%m-%d %H:%M:%S")
            timestamp = int(time.mktime(timeArray))
            audic['ro'] = timestamp
        # 所有的回复的内容结构
        mydic = soup.find_all('div',attrs={"id":re.compile('post_\d+')})
        mi = 0
        for htstr in mydic:
                try:
                    soup2 = BeautifulSoup((str)(htstr))
                    #作者被禁止或删除，内容自动屏蔽或者游客需要回复查看
                    junk=''
                    if soup2.find('div',class_='locked'):
                        if soup2.find('div',class_='locked').find('a'):
                            junk=soup2.find('div',class_='locked').get_text()
                        else:
                            continue
                    # 如果把self.rc放在外层if中用于判断是否没有记录，则对于有少量回复，而又有更新的情况，便不能跳过第一页的主帖
                    # 解析主帖部分内容
                    if ((mi == 0) and (self.num == 1)and (self.rc==0)):
                        # 回帖的内容
                        strtext = soup2.find('td',class_='t_f')
                        while(strtext.find('i',class_='pstatus')):
                            s=strtext.find('i',class_='pstatus').extract()
                        if strtext:
                            strtext1 = strtext.get_text().strip()
                        #print strtext1
                        if strtext.find('div',class_='attach_nopermission attach_tips'):
                            temp=strtext.find('div',class_='attach_nopermission attach_tips').get_text().strip()
                            temp=str(temp)
                            strtext1=str(strtext1)
                            strtext1=strtext1.replace(temp,'')
                        if soup2.find('td',class_='t_f').find('div',class_='quote'):
                            temp=strtext.find('div',class_='quote').get_text().strip()
                            temp=str(temp)
                            strtext1=str(strtext1)
                            strtext1=strtext1.replace(temp,'')
                            audic['quote']=temp
                        # 对图片的判断
                        imgtext = ''
                        if(strtext.find('ignore_js_op')):
                            img = strtext.find_all('ignore_js_op')
                            for eachimg in img:
                                eachimg1=eachimg.find_all('img')
                                for eim in eachimg1:
                                    if eim.has_attr('file'):
                                        imgtext = imgtext+eim['file']+'\n'
                                temp=eachimg.get_text().strip()
                                strtext1=str(strtext1)
                                temp=str(temp)
                                strtext1=strtext1.replace(temp,'')
                        if strtext.find_all('font',class_='jammer'):
                            for jammer in strtext.find_all('font',class_='jammer'):
                                temp=jammer.get_text().strip()
                                strtext1=str(strtext1)
                                temp=str(temp)
                                strtext1=strtext1.replace(temp,'')
                                if audic.has_key('quote'):
                                    audic['quote']=audic['quote'].replace(temp,'')
                        if strtext.find_all('span'):
                            for span in strtext.find_all('span'):
                                if span.has_attr('style'):
                                    temp=span.get_text().strip()
                                    strtext1=str(strtext1)
                                    temp=str(temp)
                                    strtext1=strtext1.replace(temp,'')
                                    if audic.has_key('quote'):
                                        audic['quote']=audic['quote'].replace(temp,'')
                        strtext1 = imgtext + strtext1

                        # 对视频的判断
                        if soup2.find('td',class_='t_f').find_all('script'):
                            for script in soup2.find('td',class_='t_f').find_all('script'):
                                temp=script.get_text().strip()
                                ps=re.compile(r"http://\S*\'\)")
                                pr=ps.search(temp)
                                #print pr.group(0)
                                if pr:
                                    strtext1=strtext1.replace(temp,pr.group(0).strip(')').strip('\'')+'\n')
                                else:
                                    strtext1=strtext1.replace(temp,'')
                        strtext1=strtext1.replace(junk,'')

                        audic['text'] = strtext1.strip()
                        mi += 1
                        alldata.append(audic)
                        self.rc=audic['ro']
                        continue
                except Exception as e:
                    continue
                # 解析跟帖内容
                redic = {}

                try:
                    # 回帖的内容
                    strtext = soup2.find('td', class_='t_f')
                    while(strtext.find('i',class_='pstatus')):
                            s=strtext.find('i',class_='pstatus').extract()
                    if strtext:
                        strtext1 = strtext.get_text().strip()
                    if strtext.find('div',class_='attach_nopermission attach_tips'):
                        temp=strtext.find('div',class_='attach_nopermission attach_tips').get_text().strip()
                        temp=str(temp)
                        strtext1=str(strtext1)
                        strtext1=strtext1.replace(temp,'')
                    if soup2.find('td',class_='t_f').find('div',class_='quote'):
                        temp=strtext.find('div',class_='quote').get_text().strip()
                        temp=str(temp)
                        strtext1=str(strtext1)
                        strtext1=strtext1.replace(temp,'')
                        redic['quote']=temp
                    # 对图片的判断
                    imgtext = ''
                    if(strtext.find('ignore_js_op')):
                        img = strtext.find_all('ignore_js_op')
                        # print(img)
                        for eachimg in img:
                            for eachimg in img:
                                eachimg1=eachimg.find_all('img')
                                for eim in eachimg1:
                                    if eim.has_attr('file'):
                                        imgtext = imgtext+eim['file']+'\n'
                            temp=eachimg.get_text().strip()
                            strtext1=str(strtext1)
                            temp=str(temp)
                            strtext1=strtext1.replace(temp,'')
                    if strtext.find_all('font',class_='jammer'):
                        for jammer in strtext.find_all('font',class_='jammer'):
                            temp=jammer.get_text().strip()
                            strtext1=str(strtext1)
                            temp=str(temp)
                            strtext1=strtext1.replace(temp,'')
                            if redic.has_key('quote'):
                                redic['quote']=redic['quote'].replace(temp,'')
                    if strtext.find_all('span'):
                        for span in strtext.find_all('span'):
                            if span.has_attr('style'):
                                temp=span.get_text().strip()
                                strtext1=str(strtext1)
                                temp=str(temp)
                                strtext1=strtext1.replace(temp,'')
                                if redic.has_key('quote'):
                                    redic['quote']=redic['quote'].replace(temp,'')
                    strtext1 = imgtext + strtext1

                     # 对视频的判断
                    if soup2.find('td',class_='t_f').find_all('script'):
                        for script in soup2.find('td',class_='t_f').find_all('script'):
                            temp=script.get_text().strip()
                            ps=re.compile(r"http://\S*\'\)")
                            pr=ps.search(temp)
                            #print pr.group(0)
                            if pr:
                                strtext1=strtext1.replace(temp,pr.group(0).strip(')').strip('\'')+'\n')
                            else:
                                strtext1=strtext1.replace(temp,'')

                    strtext1=strtext1.replace(junk,'')
                    redic['text'] = strtext1.strip()

                   # 获取作者名字
                    unknow=soup2.find('div',class_='pi').get_text().strip()
                    unknow=unknow.encode('utf-8')
                    #print unknow
                    if re.search('匿名',unknow ):
                        redic['un']='匿名'
                        redic['uid']='unknow'
                        redic['au']=False
                        # 回复时间
                        if soup2.find_all('div',class_='authi')[0].find('em').find('span')!=None:
                            rtime=soup2.find_all('div',class_='authi')[0].find('em').find('span')['title']
                        else:
                            rtime1=soup2.find_all('div',class_='authi')[0].find('em').get_text().split(' ')[1]
                            rtime2=soup2.find_all('div',class_='authi')[0].find('em').get_text().split(' ')[2]
                            rtime=rtime1+' '+rtime2
                        #print rtime
                    else:
                        uname = soup2.find('div',class_='authi').get_text().strip()
                        redic['un'] = uname
                        #print uname
                        # 得到回复者的id
                        uid = soup2.find('div',class_='authi').find('a')['href'].split('&')[1].split('=')[1]
                        #print type(uid)
                        redic['uid'] = uid
                        # 回复时间
                        if soup2.find_all('div',class_='authi')[1].find('em').find('span')!=None:
                            rtime=soup2.find_all('div',class_='authi')[1].find('em').find('span')['title']
                        else:
                            rtime1=soup2.find_all('div',class_='authi')[1].find('em').get_text().split(' ')[1]
                            rtime2=soup2.find_all('div',class_='authi')[1].find('em').get_text().split(' ')[2]
                            rtime=rtime1+' '+rtime2
                    # 分析是否为楼主的回复内容
                    authorstr=soup2.find_all('div',class_='pi')[1].get_text().strip()
                    authorstr=authorstr.encode('utf-8')
                    if(re.search('楼主', authorstr)):
                        redic['au'] = True
                    else:
                        redic['au'] = False
                    redic['time'] = rtime
                    #print rtime
                    timeArray = time.strptime(rtime, "%Y-%m-%d %H:%M:%S")
                    timestamp = int(time.mktime(timeArray))
                    irorder=timestamp
                    #print irorder
                    redic['ro'] = irorder
                     #当前楼层大于先前爬取的回复数才记录
                    if(redic['ro']>self.originalrc):
                        alldata.append(redic)
                    # update the reply count
                    if (last_page and (irorder > self.rc)):
                        self.rc = irorder

                except AttributeError as e:
                    print(e)
                    alldata.append(redic)
                    continue

        print 'All:%s' % self.pageurl
        return alldata


# 获取帖子的页数，需要自己实现
def page(url):
    """根据第一页地址抓取总页数"""
    data = 3
    while data>0:
        data -= 1
        try:
            data = urllib.urlopen(url).read()
            soup=BeautifulSoup(data)
            if soup.find('div',class_='pg'):
                page_num=soup.find('div',class_='pg').find('label').find('span')['title'].split(' ')[1]
                break
            else:
                return None
        except Exception as e:
            print 'Unable to download the page num in %s' % url
            insert_log('Unable to download the page num in %s' % url)
    if isinstance(data,int):
        print 'Unable to save page num in %s' % url
        insert_log('Unable to save page num in %s' % url)
        #return None
    if page_num:
        page_num=int(page_num)
        return page_num


# 把字典写入文件，fn是文件名，dict是下载数据的字典，postId是帖子ID
def write_text(postId, dict, fn):
    """把字典内容按键（页数）写入文本，每个键值为每页内容的list列表"""
    if(os.path.isfile(fn)):
        tx_file = open(fn, 'r+')
    else:
        tx_file = open(fn, 'w+')

    oldinfo=getUpdateInfo(postId)    #上一次更新的信息
    oldro=oldinfo['rc']

    pg = 1
    rc = 0

    try:
        pg = dict.pop('pg')
        rc = dict.pop('rc')
    except Exception as e:
        print 'ERROR:import_data %s' % postId
        insert_log('ERROR:import_data %s' % postId)
        return
    if(oldro != rc or rc==0):
        tx_file.write(str(postId) + '\r\n')
        tx_file.write('PG:RC  %d:%d' % (pg, rc) + '\r\n')
    tx_file.seek(0,2)
    for k, v in dict.iteritems():
        for dicTmp in v:
            #if('ro'in dicTmp.keys()and dicTmp['ro']> oldro or dicTmp['ro'] == 0):
                for k2, v2 in dicTmp.iteritems():
                    tx_file.write(k2 + ':' + str(v2) + '\r\n')

    tx_file.close()


# 获取更新数据，pg 和 rc
# 需要自己实现，读取相应文件获得这两个值，如果没有，返回pg=1，rc=0
def getUpdateInfo(postid):
    flag = os.path.isfile('./data/'+postid+'.txt')
    if not flag:
        return {'pg': 1, 'rc': 0}
    tx_file = open('./data/'+postid+'.txt', 'r')
    pg = 1
    rc = 0
    authorId = ''
    lines=tx_file.readlines() #读出文件所有行
    if(len(lines)>=2):    #如果文件行数大于等于2
            #读取帖子数据的第二行
            UpdateInfoline=lines[1]

            #获取第二行的后半部分数据
            UpdateInfo_Items=UpdateInfoline.split('  ')[1]
            update = UpdateInfo_Items.split(':')
            pg=int(update[0])  #最新页数，转成int型
            rc=int(update[1])  #最新楼数，转成int型

            #读取文件中的楼主ID
            for line in lines:
                if(re.search('uid:(\S*)', line)):  #读取文件中的楼主ID
                    s=re.search('uid:(\S*)', line)
                    authorId=s.group(1)  #获取楼主ID
                    break
    tx_file.close()
    return {'pg': pg, 'rc': rc}


def down_page_run(urlstr):
    """the number of thread"""
    socket.setdefaulttimeout(120)

    # 设置线程数量
    thread_num = 4
    url = 'http://bbs.tainfo.net/' + urlstr
    """print 'URL:%s' % url"""
    strs = urlstr.split('-')
    postid = strs[1]

    # 需要自己实现
    updic = getUpdateInfo(postid)
    oldpage = updic['pg']
    oldrc = updic['rc']

    my_page = page(url)
    if my_page is None:
        my_page = oldpage

    # my_dict = {}
    print 'page num is : %s ~ %s' % (oldpage, my_page)
    threads = []

    """根据设置的线程数量设置线程"""
    page_num = my_page - oldpage
    if page_num < 10:
        thread_num = 2

    numperthread = 0
    if thread_num is 1:
        numperthread = page_num
    else:
        numperthread = page_num / (thread_num - 1)

    if numperthread is 0:
        numperthread = 1
    """numoflast = my_page%(thread_num-1)"""

    # 保存所有数据的字典{pagenum:[{},{}..]..}
    resultdic = {}
    """根据页数构造urls进行多线程下载"""
    for num in range(0, thread_num - 1):
        downlist = Down_sdtainfo_Page(postid, url, num * numperthread + oldpage, (num + 1) * numperthread + oldpage,
                                  my_page, oldrc, resultdic)
        downlist.start()
        threads.append(downlist)
    downlist = Down_sdtainfo_Page(postid, url, numperthread * (thread_num - 1) + oldpage, my_page + 1, my_page, oldrc,
                              resultdic)
    downlist.start()
    threads.append(downlist)
    """检查下载完成后再进行写入"""
    for t in threads:
        t.join()

    # 写入文件
    fn = './data/%s.txt' % postid
    if resultdic and  (resultdic['rc']!=oldrc):
        write_text(postid, resultdic, fn)


def insert_log(record):
    """
    打印错误日志
   """
    with open('log/downTyData.log', 'a') as log:
        log.write('{time},{record},\r\n'.format(
            time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            record=record
        ))


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    down_page_run("thread-1570573-1-1.html")
