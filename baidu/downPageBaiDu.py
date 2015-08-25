# -*- coding: UTF-8 -*-
__author__ = 'zhangzhan'
import urllib
import re
import threading
import sys
import socket
import time
import datetime
import json
from bs4 import BeautifulSoup

class Down_BaiDu_Post(threading.Thread):
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
        self.pageurl = url
        self.startnum = startnum
        self.endnum = endnum
        self.lastpage = lastpage
        self.num = startnum #用于保存数据
        self.postID = postid
        self.rc = replycount
        self.resultdic = resultdic #保存下载解析后的数据
        self.uid = None
        #print "RC:%s" % self.rc
    def run(self):
        #判断是否是最新的一页（最新的数据在最后一页，如果你处理的论坛不是，请自行修改程序
        is_last = False

        #循环下载本下载线程应当下载的URL page
        for num in range(self.startnum, self.endnum):
            #根据格式调整url
            urlsplit=""
            urlsplit = self.pageurl
            self.pageurl = urlsplit.split("?")[0]+"?pn="+str(num)#'%s-%s-%s-%s' % (urlsplit[0],urlsplit[1], num,urlsplit[3])
            self.num = num
            print 'downling from %s' % self.pageurl
            if(num == self.lastpage):
                restmp = self.down_text(True)
                """result.extend(restmp)"""
                if restmp is False:
                    continue
                if restmp == "locked":
                    break
                if len(restmp) is not 0:

                    #restmp 是一个字典列表，num是页码
                    self.resultdic[num] = restmp
                    is_last = True
            else:
                restmp = self.down_text(False)
                if restmp == "locked":
                    break
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
                i_headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1) Gecko/20090624 Firefox/3.5",\
                 "Referer": 'http://www.baidu.com'}
                req = urllib2.Request(self.pageurl, headers=i_headers)

                html_content = urllib2.urlopen(req).read()
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
        try:

            titlep = soup.find("div",id="errorText").find("h1").get_text()
            if titlep is '很抱歉，该贴被删除。':
                print '出错了:%s' % self.pageurl
                insert_log('出错了:%s' % self.pageurl)
                return []
        except:
            pass
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
                    try:
                        mainpost = soup.find('div',class_="pb_content clearfix").find('div', {'class': 'l_post l_post_bright '})
                        data_field = json.loads(mainpost['data-field'])
                    except:
                        return []

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


            # title = soup.find('div', id='pb_content').find("h1",class_="core_title_txt ").get_text().strip("\r\t\n").strip()
            # print title
            # section = soup.find("div",id="container").find("a",class_="card_title_fname").get_text().strip("\r\t\n").strip()
            # print section
            # #try:
            # auname = soup.find('li', class_='d_name').find('a').get_text().strip("\r\t\n")
            # print auname
            # #except:
            #     #auname = soup.find('div', class_='pi').get_text().strip("\r\t\n")
            # #try:
            #
            # auid = soup.find('li', class_='d_name')["data-field"].split(":")[1].split("}")[0]
            # print auid
            #except:
                #auid = "000000"


            #try:
            #soup = soup.replace
            #ctime = soup.find("div", class_=re.compile(r'"core_reply_tail\"'))#.find_all("li")[1].find("span").get_text()
            #print ctime
            #timeArray = time.strptime(ctime, "%Y-%m-%d %H:%M:%S")
            #except:
                #ctime = soup.find_all('td', class_='plc')[2].find("div",class_="authi").find("span")["title"]
                #timeArray = time.strptime(ctime, "%Y-%m-%d %H:%M:%S")
            self.uid = auid
            audic['title'] = title
            audic['sec'] = section
            audic['uname'] = auname
            audic['uid'] = auid
            audic['ctime'] = ctime
            audic['ro'] = 0
        try:
            mydic = soup.find('div',id="j_p_postlist").find_all("div",class_="l_post l_post_bright  ")
        except:
            return []
        mi = 0
        soup3 = soup.find('div',id="j_p_postlist").find("div",class_="l_post l_post_bright noborder ")
        #print mydic
        if((mi == 0) and (self.num == 1)):
                mi +=1
                if(self.rc == 0):

                    strtext = soup3.find('div',class_="d_post_content j_d_post_content  clearfix").get_text()
                    # videoSource = ""
                    # try:
                    #     scriptCode = soup3.find('td', class_="plc").find("td",class_="t_f").find_all("script")
                    #     for scc in scriptCode:
                    #         strtext = strtext.replace(scc.get_text(),"")
                    #         patternSearch = re.compile(r"http://\S*.swf")
                    #         patternResult = patternSearch.search(scc.get_text())
                    #         videoSource += patternResult.group(0)+"\n"
                    # except Exception as e:
                    #     pass
                    # blockQuote = None
                    # try:
                    #     blockQuote = soup3.find('td',class_="plc").find("td",class_="t_f").find("blockquote").get_text()
                    #     audic["quote"] = blockQuote
                    #     strtext = strtext.replace(blockQuote,"")
                    # except Exception as e:
                    #     pass
                    imgsrc =""
                    # try:
                    #     imgFile= soup3.find('td', class_='plc').find("div",class_="pattl").find_all("ignore_js_op")
                    #     for img in imgFile:
                    #         for im in img.find_all("img"):
                    #             try:
                    #                 imgsrc += im["file"]+"\n"
                    #             except Exception as e:
                    #                 print (e)
                    #                 continue
                    # except Exception as e:
                    #     pass
                    try:
                        tdimg = soup3.find('div', class_='d_post_content j_d_post_content  clearfix').find_all("img")
                        for im in tdimg:
                            try:
                                imgsrc += im["src"]+"\n"
                            except Exception as e:
                                continue
                    except Exception as e:
                        pass


                    # infoText = ""
                    # try:
                    #     oinfoText = soup3.find('td', class_='plc').find("div",class_="pattl").find_all("ignore_js_op")
                    #     for info in oinfoText:
                    #         strtext = strtext.replace(info.get_text(),"")
                    # except Exception as e:
                    #     pass


                    audic['text'] = strtext.strip("\r\t\n").strip() + "\n"+imgsrc

                    alldata.append(audic)

        for htstr in mydic:
            soup2 = BeautifulSoup((str)(htstr))
            # if soup2.find("td",class_="plc").find("div",class_="locked"):
            #     return "locked"
            #如果把self.rc放在外层if中用于判断是否没有记录，则对于有少量回复，而又有更新的情况，便不能跳过第一页的主帖
            #解析主帖部分内容
            # if((mi == 0) and (self.num == 1)):
            #     mi +=1
            #     if(self.rc == 0):
            #
            #         strtext = soup2.find('div',class_="d_post_content j_d_post_content  clearfix").get_text()
            #         print strtext
            #         videoSource = ""
            #         try:
            #             scriptCode = soup2.find('td', class_="plc").find("td",class_="t_f").find_all("script")
            #             for scc in scriptCode:
            #                 strtext = strtext.replace(scc.get_text(),"")
            #                 patternSearch = re.compile(r"http://\S*.swf")
            #                 patternResult = patternSearch.search(scc.get_text())
            #                 videoSource += patternResult.group(0)+"\n"
            #         except Exception as e:
            #             pass
            #         blockQuote = None
            #         try:
            #             blockQuote = soup2.find('td',class_="plc").find("td",class_="t_f").find("blockquote").get_text()
            #             audic["quote"] = blockQuote
            #             strtext = strtext.replace(blockQuote,"")
            #         except Exception as e:
            #             pass
            #         imgsrc =""
            #         try:
            #             imgFile= soup2.find('td', class_='plc').find("div",class_="pattl").find_all("ignore_js_op")
            #             for img in imgFile:
            #                 for im in img.find_all("img"):
            #                     try:
            #                         imgsrc += im["file"]+"\n"
            #                     except Exception as e:
            #                         print (e)
            #                         continue
            #         except Exception as e:
            #             pass
            #         try:
            #             tdimg = soup2.find('td', class_='t_f').find_all("img")
            #             for im in tdimg:
            #                 try:
            #                     imgsrc += im["src"]+"\n"
            #                 except Exception as e:
            #                     continue
            #         except Exception as e:
            #             pass
            #
            #
            #         infoText = ""
            #         try:
            #             oinfoText = soup2.find('td', class_='plc').find("div",class_="pattl").find_all("ignore_js_op")
            #             for info in oinfoText:
            #                 strtext = strtext.replace(info.get_text(),"")
            #         except Exception as e:
            #             pass
            #
            #
            #         audic['text'] = strtext.strip("\r\t\n") + "\n"+imgsrc+"\n"+videoSource
            #
            #         alldata.append(audic)
            #         print "**************"
            #     continue

            #解析跟帖内容
            redic = {}
            try:

                rInfo = json.loads(htstr['data-field'],encoding="utf8")
                #print rInfo
                # rorder = soup2.find("td",class_="plc").find("div",class_="pi").find("a").get_text()
                # rorder = rorder.strip("\r\t\n")
                # if rorder == "沙发":
                #     irorder = 1
                # elif rorder == "板凳":
                #     irorder = 2
                # elif rorder == "地板":
                #     irorder = 3
                # else:
                #     rorder = rorder[:-1]
                #     irorder = int(rorder)-1

                irorder = int(rInfo["content"]["post_no"])-1
                redic['ro'] = irorder

                #update the reply count
                if(last_page and (irorder > self.rc)):
                    self.rc = irorder
                strtext = soup2.find('div', class_='d_post_content j_d_post_content  clearfix').get_text()
                #print strtext
                # videoSource = ""
                # try:
                #     scriptCode = soup2.find('td', class_="plc").find("td",class_="t_f").find_all("script")
                #     for scc in scriptCode:
                #         strtext = strtext.replace(scc.get_text(),"")
                #         patternSearch = re.compile(r"http://\S*.swf")
                #         patternResult = patternSearch.search(scc.get_text())
                #         videoSource += patternResult.group(0)+"\n"
                # except Exception as e:
                #         print (e)
                # blockQuote = None
                # try:
                #     blockQuote = soup2.find('td',class_="plc").find("td",class_="t_f").find("blockquote").get_text()
                #     redic["quote"] = blockQuote
                #     strtext = strtext.replace(blockQuote,"")
                # except Exception as e:
                #         print (e)
                # oinfo = None
                # try:
                #     oinfo = soup2.find("td",class_="plc").find('div', class_="pattl").find_all("ignore_js_op")
                #     for info in oinfo:
                #         strtext = strtext.replace(info.get_text(),"")
                # except Exception as e:
                #         print (e)
                imgsrc = ""
                try:
                    tdimg = soup2.find('div', class_='d_post_content j_d_post_content  clearfix').find_all("img")
                    for im in tdimg:
                        try:
                            imgsrc += im["src"]+"\n"
                        except Exception as e:
                            continue
                except Exception as e:
                    pass

                #imgsrc =""
                # try:
                #     imginfo = soup2.find("td",class_="plc").find('div', class_="pattl").find_all("ignore_js_op")
                #     for img in imginfo:
                #         for im in img.find_all("img"):
                #             try:
                #                 imgsrc += im["file"] + "\n"
                #             except Exception as e:
                #                 print (e)
                #                 continue
                # except Exception as e:
                #         print (e)
                #         print (e)

                redic['text'] = strtext.strip("\r\t\n").strip()+"\n"+imgsrc

                uname =  rInfo["author"]["user_name"]

                redic['un'] = uname

                try:
                    uid = rInfo["author"]["user_id"]
                except:
                    uid =None

                redic['uid'] = uid
                if(self.uid == uid):
                    redic['au'] = True
                else:
                    redic['au'] = False
                rtime = rInfo["content"]["date"]

                redic['time'] = rtime

                alldata.append(redic)
            except AttributeError as e:
                alldata.append(redic)
                continue
        print 'All:%s' % self.pageurl
        return alldata

#获取帖子的页数，需要自己实现
import urllib2
def page(url):
    """根据第一页地址抓取总页数"""
    data = 3
    while data>0:
        data -= 1
        try:
            i_headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1) Gecko/20090624 Firefox/3.5",\
                 "Referer": 'http://www.baidu.com'}
            req = urllib2.Request(url, headers=i_headers)

            data = urllib2.urlopen(req).read()
            #data = urllib.urlopen(url).read()
            '''page_pattern = re.compile(r'<a href="\S*?">(\d*)</a>\s*<a href="\S*?" class="\S*?">下页</a>')
            page_result = page_pattern.search(data)'''
            soup = BeautifulSoup(data)
            totalpage = soup.find("li",class_="l_reply_num").find_all("span")[1].get_text()
            break
        except Exception as e:
            #print 'Unable to download the page num in %s' % url
            #insert_log('Unable to download the page num in %s' % url)
            return 1
    if isinstance(data,int):
        print 'Unable to save page num in %s' % url
        insert_log('Unable to save page num in %s' % url)
        return None

    '''if page_result:
        page_num = int(page_result.group(1))'''
    return int(totalpage)

#把字典写入文件，fn是文件名，dict是下载数据的字典，postId是帖子ID
def write_text(postId,dict, fn,oldrc):
    """把字典内容按键（页数）写入文本，每个键值为每页内容的list列表"""
    import os
    if os.path.exists("./data/") is False:
        os.mkdir("./data/")
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

    tx_file.write(str(postId)+'\n')
    tx_file.write('PG:RC  %d:%d' %(pg,rc) + '\n')
    for k,v in dict.iteritems():
        for dicTmp in v:
            if dicTmp["ro"] >= oldrc:
                for k2,v2 in dicTmp.iteritems():
                    tx_file.write(k2+':'+str(v2)+'\n')

    tx_file.close()

#获取更新数据，pg 和 rc
#需要自己实现，读取相应文件获得这两个值，如果没有，返回pg=1，rc=0
def getUpdateInfo(postid):
    try:
        fp = open("./data/%s.txt"%(postid),"r")
        lines = fp.readlines()
        fp.close()
        for line in lines:
            line = line.strip("\r\t\n")
            if "PG:RC " in line:
                pg,rc = line.split()[1].split(":")
                return {"pg":pg,"rc":rc}

    except Exception as e:
        print "Error Info  %s"%e.message

    return {'pg':1, 'rc':0}

def down_page_run(urlstr):
    """the number of thread"""
    socket.setdefaulttimeout(120)

    #设置线程数量
    thread_num = 4
    url = 'http://tieba.baidu.com'+ urlstr
    strs = urlstr.split('/')
    postid = strs[-1]
    print postid
    #需要自己实现
    updic = getUpdateInfo(postid)

    oldpage = int(updic['pg'])
    oldrc = int(updic['rc'])

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
        downlist = Down_BaiDu_Post(postid, url, num*numperthread+oldpage, (num+1)*numperthread+oldpage, my_page, oldrc, resultdic)
        downlist.start()
        threads.append(downlist)
    downlist = Down_BaiDu_Post(postid, url, numperthread*(thread_num-1)+oldpage, my_page+1, my_page, oldrc, resultdic)
    downlist.start()
    threads.append(downlist)
    """检查下载完成后再进行写入"""
    for t in threads:
        t.join()

    #写入文件
    fn = './data/%s.txt' % postid
    write_text(postid, resultdic, fn,oldrc)

def insert_log(record):
    '''
    打印错误日志
    '''
    import os
    if os.path.exists("./log/") is False:
        os.mkdir("./log/")
    with open('log/downYanQingData.log', 'a') as log:
        log.write('{time},{record},\r\n'.format(
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            record = record
        ))


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    #down_page_run("thread-26344-1-1.html")
    down_page_run("/p/3992835244")
