import codecs
from redis import StrictRedis
import requests
from Crypto.Cipher import AES
import base64
import json
import os
from jsonpath import jsonpath


class MusicComment:

    def __init__(self):
        self.aes = WangYiMusicAES()
        self.redis = StrictRedis(host="127.0.0.1",port=6379,db=0)
        self.headers = {
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        }

    def _request(self,url,data):
        res = requests.post(url,headers=self.headers,data=data)
        return res.json()

    def comments(self,json_data):
        # 抓取评论
        contents = jsonpath(json_data,"$..comments")[0]
        print("获取到{}条评论".format(len(contents)))
        for content in contents:
            nickname = jsonpath(content,"$..nickname")[0]
            content = jsonpath(content,"$..content")[0]
            print("{}:{}".format(nickname,content))
            # TODO 需要将评论存在哪里看自己了

        more = jsonpath(json_data,"$..more")
        if len(more)>0:
            return more[0]
        return False

    def comment_page(self,song_id):
        # 评论页码
        url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_{}?csrf_token='.format(song_id)
        page = 0
        more = True
        while more:
            data = self.aes(page)
            print("{}:第{}页评论".format(song_id, page + 1))
            json_data = self._request(url,data)
            more = self.comments(json_data)
            page += 1

    def run(self):
        song = self.redis.srandmember("music",1000)
        if song:
            for sg in song:
                s = eval(sg)
                for id,url in s.items():
                    print(url)
                    self.comment_page(id)


class WangYiMusicAES:

    def __init__(self):
        # 网易音乐的固定参数
        self.encSecKey = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        self.iv = "0102030405060708"
        self.pubKey = "010001"
        self.fourth_param = "0CoJUm6Qyw8W8jud"

    def create_random_char(self):
        # "随机16个字符"
        return (''.join(map(lambda xx: (hex(ord(xx))[2:]), str(os.urandom(16)))))[0:16]

    def aesEncrypt(self,text,key):
        """params加密"""
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(key, AES.MODE_CBC, self.iv)
        encrypt_text = encryptor.encrypt(text)
        encrypt_text = base64.b64encode(encrypt_text)
        encrypt_text = str(encrypt_text, encoding="utf-8")
        return encrypt_text

    def rsaEncrypt(self,text):
        """加密encSecKey"""
        text = text[::-1]
        rs = int(codecs.encode(text.encode('utf-8'), 'hex_codec'), 16) ** int(self.pubKey, 16) % int(self.encSecKey, 16)
        return format(rs, 'x').zfill(256)


    def __call__(self, page):
        "返回加密结果"
        text = {
            'username': '',
			'password': '',
			'rememberLogin': 'true',
			'offset': page * 20
        }
        text = json.dumps(text)
        secKey = self.create_random_char()
        # 需要加密两次，params
        encText = self.aesEncrypt(self.aesEncrypt(text,self.fourth_param),secKey)
        encSecKey = self.rsaEncrypt(secKey)
        data = {
            'params': encText,
            'encSecKey': encSecKey
        }
        return data

if __name__ == '__main__':

    wy = MusicComment()
    wy.run()
