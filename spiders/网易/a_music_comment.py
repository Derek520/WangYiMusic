from jsonpath import jsonpath
from concurrent.futures import ThreadPoolExecutor
from redis import StrictRedis
from music_comments import WangYiMusicAES
import requests

class MusicComment:
    def __init__(self):
        self.aes = WangYiMusicAES()
        self.redis = StrictRedis(host="127.0.0.1",port=6379,db=0)
        self.headers = {
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        }

    def _request(self,url,data,id):
        return requests.post(url,data=data,headers=self.headers).json()


    def comment_page(self,song_id):
        # 评论页码
        url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_{}?csrf_token='.format(song_id)
        page = 0
        more = True

        while more:
            data = self.aes(page)
            print("{}:第{}页评论".format(song_id, page + 1))
            json_data = self._request(url, data, song_id)
            more = self.comments(json_data,song_id)
            page += 1



    def comments(self,json_data,id):
        # 抓取评论
        contents = jsonpath(json_data, "$..comments")[0]
        if len(contents)==0:
            return False
        # print("<<<<<<<<<<<<<<<[{}]:获取到{}条评论>>>>>>>>>>>>>>>".format(id,len(contents)))
        for content in contents:
            nickname = jsonpath(content, "$..nickname")[0]
            content = jsonpath(content, "$..content")[0]
            print("歌曲id:[{}]>用户:[{}]>评论:{}".format(id,nickname, content))
            # TODO 需要将评论存在哪里看自己了

        more = jsonpath(json_data, "$..more")
        if len(more) > 0:
            return more[0]
        return False


    def run(self):

        song = self.redis.srandmember("music", 1000)
        if song:
            with ThreadPoolExecutor(max_workers=4) as thd:
                for sg in song:
                    # song_id = list(song)[0]
                    s = eval(sg)
                    for id, url in s.items():
                        print(url)
                        # self.comment_page(id)
                        thd.submit(self.comment_page,id)

if __name__ == '__main__':
    mc = MusicComment()
    mc.run()