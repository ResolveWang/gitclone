#! /usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# -*- coding: cp936 -*-
# -*- coding: gb18030 -*-

import requests
import os


class DownLoadImg(object):
    ImgNum = 0

    def __init__(self, url, Path):
        self.url = url
        self.Path = Path

    def DownImg(self):
        req = requests.get(self.url)
        ImgData = req.content
        ImgWritePath = os.path.join(self.Path, '_%s.png' % self.ImgNum)
        with open(ImgWritePath, 'wb') as ImgWrite:
            ImgWrite.writelines(ImgData)

if __name__ == "__main__":
    ImgWrite = DownLoadImg(
        'http://login.sina.com.cn/cgi/pin.php?r=1486271574&s=0&p=ja-80b1e43b35bc4c940f3e7fa6c0d1a0e04e8f', 'D:\python\SinaCaptha')
    for i in xrange(10000000):
        DownLoadImg.ImgNum = i
        try:
            ImgWrite.DownImg()
        except:
            print 'Error for %sth Img'%i
