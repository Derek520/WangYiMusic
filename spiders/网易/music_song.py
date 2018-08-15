import requests
from lxml import etree
from urllib.parse import urljoin
import re
from redis import StrictRedis

class WangYiMusic:

    def __init__(self):

        self.redis = StrictRedis(host="127.0.0.1",port=6379,db=0)
        self.sess = requests.session()
        self.headers = {
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        }
        self.seen = {}

    def redis_keys(self):
        keys_byes = self.redis.keys()
        keys= [ key.decode() for key in keys_byes]
        return keys

    def request_url(self,url):
        try:
            response = self.sess.get(url,headers=self.headers,timeout=6)
            return response.content
        except Exception as e:
            print("{}:请求超时".format(url))
            return None

    def song_list(self,key,urls):
        item = {}
        for url in urls:
            print(url)
            list1 = []
            count = item.get(key, 0)
            if self.seen.get(url,False):
                continue
            self.seen[url]=True
            res = self.request_url(url)
            if res is None:
                continue
            html = etree.HTML(res)
            li_list = html.xpath("//ul[@class='f-hide']/li")
            print("{}:{}".format(key, len(li_list)))
            item[key] = count + len(li_list)
            for li in li_list:
                href = li.xpath(".//a/@href")[0]
                id = re.findall("(\d+)", href)[0]
                parse_url = urljoin(url.decode(), href)
                self.redis.sadd("music",{id:parse_url})
                print(id, parse_url)
                list1.append({id: url})
            print("{}爬取了{}条url".format(key,item.get(key,0)))
            # dict2[key] = list1
        print("{}:共计{}首歌".format(key,item.get(key,0)))


    def run(self):
        keys = self.redis_keys()
        count = 0
        for key in keys:
            if "music" in key:
                continue
            res = self.redis.lrange(key,0,-1)
            count+=len(res)
            self.song_list(key,res)
            print(key,len(res))
        print("总共：{}条url".format(count))

if __name__ == '__main__':

    dd =  WangYiMusic()
    dd.run()