#! /usr/bin/env python2.7
# -*- coding:utf-8-*-
# -*- coding: cp936 -*-
# -*- coding: gb18030 -*-


#--------------------------------------------------#
#     Author:guchao
#     mail  :guchaonemo@163.com
#     time  :2016.10.27 15:00
#     USAEG :draw data
#--------------------------------------------------#

import time
import urllib
import sys
import re
import requests
from bs4 import BeautifulSoup
import simplejson
import base64
import rsa
import binascii
import random
import MySQLdb
import warnings
import Queue
warnings.filterwarnings("ignore")


reload(sys)
sys.setdefaultencoding("utf-8")


def getbasicinfo(soup):
    result = {'uid': '', 'nickname': '', 'fans': '',
              'follow': '', 'weibo': ''}
    soup = BeautifulSoup(str(soup), 'html.parser')
    nick = soup.find_all('a', class_='S_txt1')[0]
    result['nickname'] = nick.string
    info = soup.find_all('span', class_=True)
    result['follow'] = info[0].em.a.string
    result['fans'] = info[1].a.string
    result['weibo'] = info[2].a.string
    uid = info[0].a['href']
    uid = re.findall('/(\d*)/', uid)[0]
    result['uid'] = uid
    return result


class Weibo(object):

    """docstring for Weibo"""

    def __init__(self, username, password):
        url = 'http://login.sina.com.cn/sso/prelogin.php?entry=sso&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.15)' % base64.encodestring(
            urllib.quote(username))[:-1]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3', 'Accept-Encoding': 'gzip, deflate'}
        self.url = url
        self.username = username
        self.password = password
        self.sql = '''INSERT INTO wb_user (nick,fans,follow,uid,wbnum) values('%s',%s,%s,'%s',%s);'''
        self.conn = MySQLdb.Connect(
            host='127.0.0.1', user='root', passwd='guchao', db='wb', charset='utf8')
        self.cursor = self.conn.cursor()
        self.count = 0

    def encrypt_passwd(self, pubkey, serverTime, nonce):
        rsaPublickey = int(pubkey, 16)
        key = rsa.PublicKey(rsaPublickey, 65537)
        message = str(serverTime) + '\t' + str(nonce) + \
            '\n' + str(self.password)
        self.encodedPassWord = binascii.b2a_hex(rsa.encrypt(message, key))

    def weibologin(self):
        sess = requests.Session()
        req = sess.get(self.url, headers=self.headers)
        html = req.text
        with open('test.html', 'w') as filewrite:
            filewrite.writelines(html)
        argument = re.findall('\{.*?\}', html)[0]
        dictweibo = simplejson.loads(argument)
        serverTime = dictweibo['servertime']
        nonce = dictweibo['nonce']
        rsakv = dictweibo['rsakv']
        pubkey = dictweibo['pubkey']
        # 加密用户名
        encodedUserName = base64.encodestring(urllib.quote(self.username))[:-1]
        # 加密Password
        self.encrypt_passwd(pubkey, serverTime, nonce)
        postPara = {'entry': 'weibo',
                    'gateway': '1',
                    'from': '',
                    'savestate': '7',
                    'userticket': '1',
                    'ssosimplelogin': '1',
                    'vsnf': '1',
                    'vsnval': '',
                    'su': encodedUserName,
                    'service': 'miniblog',
                    'servertime': serverTime,
                    'nonce': nonce,
                    'pwencode': 'rsa2',
                    'sp': self.encodedPassWord,
                    'encoding': 'UTF-8',
                    'prelt': '115',
                    'rsakv': rsakv,
                    'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
                    'returntype': 'META'}
        pincode = ''
        if dictweibo['showpin'] == 1:
            pinurl = "http://login.sina.com.cn/cgi/pin.php?r=%d&s=0&p=%s" % (
                serverTime, dictweibo['pcid'])
            self.DownImg(pinurl)
            pincode = raw_input('请输入验证码:')
            postPara['door'] = pincode
            postPara['pcid'] = dictweibo['pcid']
        url = r'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)'
        req = sess.post(url, data=postPara, headers=self.headers)
        login_url = re.search(
            r'replace\([\"\']([^\'\"]+)[\"\']', req.text).group(1)
        req = sess.get(login_url)
        req = sess.get('http://weibo.com')
        self.uid = re.findall(
            'u/([0-9]*)/', req.url)[0]
        print self.uid
        with open('test.html', 'w') as writehtml:
            writehtml.writelines(req.content)
        self.sess = sess

    def getForm(self, u):
        t = ''
        req = self.sess.get(url=u)
        if req.url == u:
            t = req.text
        else:
            req = self.sess.get(url=req.url)
        t = "".join(t.split())
        t = t.replace('\\', '')
        rst = re.findall(
            'action-data="uid=(.*?)&fnick=(.*?)&f=(.*?)&refer_flag=(.*?)&refer_lflag=(.*?)"', t)
        form = {'uid': '', 'objectid': '', 'f': '1', 'extra': '', 'refer_sort': '', 'refer_flag': '',
                'location': '', 'oid': '', 'wforce': '1', 'nogroup': 'false', 'fnick': '', 'refer_lflag': ''}
        if rst:
            form['uid'] = rst[0][0]
            form['oid'] = rst[0][0]
            form['fnick'] = rst[0][1]
            form['f'] = rst[0][2]
            form['refer_flag'] = rst[0][3]
            form['refer_lflag'] = rst[0][4]
        rst = re.findall("page_\d{6}_home", t)
        if rst:
            form['location'] = rst[0]
        return form

    def follow(self, u):
        follow_url = 'http://weibo.com/aj/f/followed?ajwvr=6&__rnd=%s' % (
            str(int(1000*time.time())))
        form = self.getForm(u)
        self.headers['Referer'] = u
        req = self.sess.post(url=follow_url, data=form, headers=self.headers)
        self.headers.pop('Referer')
        if req.url == follow_url:
            return True
        else:
            return False

    def unfollow(self, u):
        #----------------------------------------------------
        #               u为需要关注的微博链接
        #               取消关注
        #----------------------------------------------------
        unfollow_url = 'http://weibo.com/aj/f/unfollow?ajwvr=6'
        form = self.getForm(u)
        self.headers['Referer'] = u
        req = self.sess.post(url=unfollow_url, data=form, headers=self.headers)
        self.headers.pop('Referer')
        if req.url == unfollow_url:
            return True
        else:
            return False

    def getFans(self, uid):
        #----------------------------------------------------
        #               maxpages 粉丝的页数
        #               pagesurl 每页粉丝的路径
        #----------------------------------------------------
        pagelists = []
        fansurl = 'http://weibo.com/%s/fans' % (uid)
        req = self.sess.get(fansurl)
        text = req.content
        try:
            pages = re.findall(
                r'<div class=\\"W_pages\\">(.*?)<\\/div>', text)[0]
        except:
            return pagelists.extend(self.getfansuid(text))
        pagesnums = re.findall(r'page=(\d+)#Pl', pages)
        maxpages = min(max([int(pnum) for pnum in pagesnums]), 5)
        pages = pages.replace('\\', '')
        pagesurl = re.findall(r'href="(.*?)"', pages)[0]
        for i in xrange(1, maxpages+1):
            newpage = 'http://weibo.com' + \
                pagesurl.replace('page=2#Pl', 'page=%s#Pl' % str(i))
            reqfans = self.sess.get(newpage)
            try:
                pagelists.extend(self.getfansuid(reqfans.content))
            except:
                print 'page error for no text'
        return pagelists

    def getfansuid(self, html):
        #----------------------------------------------------
        #               获取每一页面的粉丝信息
        #               uid, fans, follows, address, nickname
        #----------------------------------------------------
        infolists = []
        argument = re.findall('FM.view\((\{.*?\})\)', html)
        for each in argument:
            each = simplejson.loads(each)
            try:
                if 'relation.fans' in each['ns'] or 'content.followTab' in each['ns']:
                    text = each
                    break
            except:
                text = each
        try:
            text = text['html']
        except:
            return infolists
        soup = BeautifulSoup(text, 'html.parser')
        result = soup.find_all('dd', class_="mod_info S_line1")
        insertsql = lambda para, sql: sql % para
        for each in result:
            try:
                faninfo = getbasicinfo(each)
                if int(faninfo['fans']) > 15:
                    nickname = str(faninfo['nickname'])
                    nickname = nickname.encode('utf-8')
                    para = (nickname, str(faninfo['fans']), str(
                        faninfo['follow']), str(faninfo['uid']), str(faninfo['weibo']))
                    isql = insertsql(para, self.sql)
                    self.cursor.execute(isql)
                    self.count += 1
                    print isql
                    if self.count % 100 == 0:
                        self.conn.commit()
                    infolists.append(str(faninfo['uid']))
            except:
                print 'Page Error'
        return infolists

    def send_weibo(self, uid, text):
        send_url = 'http://weibo.com/aj/mblog/add?ajwvr=6&__rnd=%s' % str(
            int(time.time() * 1000))
        post_data = {"location": "v6_content_home",
                     "appkey": "",
                     "style_type": "1",
                     "pic_id": "", "text": text,
                     "pdetail": "",
                     "rank": "0", "rankid": "",
                     "module": "stissue",
                     "pub_type": "dialog",
                     "pub_source": "main_",
                     "_t": "0"}
        self.headers[
            'Referer'] = "http://weibo.com/u/%s/home?wvr=5" % str(uid)
        req = self.sess.post(
            url=send_url, data=post_data, headers=self.headers)
        self.headers.pop('Referer')

    def SendImgWeibo(self, uid, text, imgurl):
        send_url = 'http://weibo.com/aj/mblog/add?ajwvr=6&__rnd=%s' % str(
            int(time.time() * 1000))
        Img = UploadImg(self.sess)
        # 此处插入uid 和 nick_name
        req = Img.getJpegRequest(
            imgurl, uid, 'nemo_ini')
        html = req.content
        matches = re.search('.*"code":"(.*?)".*"pid":"(.*?)"', html)
        pid = matches.group(2)
        post_data = {"location": "v6_content_home",
                     "appkey": "",
                     "style_type": "1",
                     "pic_id": pid, "text": text,
                     "pdetail": "",
                     "rank": "0", "rankid": "",
                     "module": "stissue",
                     "pub_type": "dialog",
                     "pub_source": "main_",
                     "_t": "0"}
        self.headers[
            'Referer'] = "http://weibo.com/u/%s/home?wvr=5" % str(uid)
        req = self.sess.post(
            url=send_url, data=post_data, headers=self.headers)
        self.headers.pop('Referer')

    def closebrowser(self):
        self.conn.commit()
        self.conn.close()

    def DownImg(self, pinurl):
        req = requests.get(pinurl)
        ImgData = req.content
        captcha = './captcha.png'
        with open(captcha, 'wb') as ImgWrite:
            ImgWrite.writelines(ImgData)


class UploadImg(object):

    def __init__(self, sess):
        self.sess = sess
        self.APIURL = 'http://picupload.service.weibo.com/interface/pic_upload.php?app=miniblog&data=1'
        self.MAXPICNUM = 9
        self.MAXSIZE = 20971520

    def getUniqueKey(self):
        return str(time.time()*1000)

    def getRandom(self):
        return str(random.random())

    def getBuildRequet(self, uid, nick='nemo_ini'):
        return {
            'url': 'weibo.com/u/' + str(uid),
            'markpos': 1,
            'logo': 1,
            'nick': nick,
            'marks': 1,
            'mime': 'image/jpeg',
                    'ct': self.getRandom(),
        }

    def buildRequest(self, url, data):
        return self.sess.post(self.APIURL + "&" + url, data=data, headers={'Content-type': "application/octet-stream", "Referer": "http://js.t.sinajs.cn/t6/home/static/swf/MultiFilesUpload.swf?version=34b8c801c2750df1", "X-Requested-With": "ShockwaveFlash/17.0.0.188", "Accept-Encoding": "gzip, deflate", "Connection": "keep-alive", "Content-Length": len(data), 'Host': 'picupload.service.weibo.com'})

    def ensmbelUrl(self, data):
        res = ""
        for key in data:
            res += str(key) + "=" + str(data[key]) + "&"
        return res[0: len(res) - 1]

    def getJpegRequest(self, imgpath, uid, nick):
        # 获取post 参数
        urldata = self.getBuildRequet(uid, nick)
        # 将参数编码在url里面
        enurl = self.ensmbelUrl(urldata)
        # 读取图片数据
        req = requests.get(imgpath)
        data = req.content

        if len(data) > self.MAXSIZE:
            return None
        else:
            return self.buildRequest(enurl, data)

if __name__ == '__main__':
    username = r'khrvpbu06623@163.com'
    password = r'tttt5555'
    sina = Weibo(username, password)
    sina.weibologin()
    sina.follow(
        'http://weibo.com/u/2850809427')
    sina.unfollow(
        'http://weibo.com/u/2850809427')
    #sina.SendImgWeibo('6100220963', u'青云志俩部全集视频，粉我私信')
'''    pagelists = sina.getFans('1988330463')
    uidQue = Queue.Queue(maxsize=500000)
    for each in pagelists:
        uidQue.put(each)
    while not uidQue.empty():
        pagelists = sina.getFans(uidQue.get())
        try:
            for uid in pagelists:
                if not uidQue.full():
                    uidQue.put(uid)
                else:
                    break
        except:
            print pagelists
    sina.closebrowser()
'''


#…………………………………………………………………………………………………………………………………………………………………………………………………
#               异步加载数据，需要从 XHR json 数据里面找加载的请求链接
#               如果需要访问数据，可以用 user-agent = 'Baiduspider' 因为微博允许
#
#…………………………………………………………………………………………………………………………………………………………………………………………………
