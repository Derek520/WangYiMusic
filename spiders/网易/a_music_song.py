import asyncio,aiohttp
from concurrent.futures._base import TimeoutError
from lxml import etree
import re
from urllib.parse import urljoin
from redis import StrictRedis


class WangYiMusic:
    def __init__(self):

        self.redis = StrictRedis(host="127.0.0.1",port=6379,db=0)
        self.duplicate = {}
        self.item = {}
        self.headers = {
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        }
    async def _request(self,key,url,semaphore):
        async with semaphore:
            async with aiohttp.ClientSession() as sess:
                print(url)
                try:
                    async with sess.get(url,headers=self.headers,timeout=9) as response:
                        if response.status==200:
                            data = await response.read()
                            return url, key, data
                except TimeoutError as e:
                    print("{}:超时".format(url))

    def callback(self,future):
        if future.result():
            url = future.result()[0]
            key = future.result()[1]
            ret = future.result()[-1]
            count = self.item.get(key,0)

            html = etree.HTML(ret)
            li_list = html.xpath("//ul[@class='f-hide']/li")
            print("{}:本次获取到{}首歌".format(key, len(li_list)))
            self.item[key] = count + len(li_list)
            for li in li_list:
                href = li.xpath(".//a/@href")[0]
                id = re.findall("(\d+)", href)[0]
                parse_url = urljoin(url, href)
                self.redis.sadd("music", {id: parse_url})
                print(id, parse_url)
            print("{}:已经爬取了{}条url".format(key, self.item.get(key, 0)))



    def high_concurrent(self,key,res):
        urls = [url.decode() for url in res if len(url) >5]
        loop = asyncio.get_event_loop()
        semaphore = asyncio.Semaphore(500)
        tasks = []
        for url in urls:
            if self.duplicate.get(url,False):
                continue
            self.duplicate[url] = True
            task = asyncio.ensure_future(self._request(key,url,semaphore))
            task.add_done_callback(self.callback)
            tasks.append(task)
        print("{}:异步爬虫开始>>>>>>>>>>".format(key))

        try:
            loop.run_until_complete(asyncio.wait(tasks))
        except (KeyboardInterrupt, SystemExit) as e:

            for task in asyncio.Task.all_tasks():
                task.cancel()
            loop.stop()
            loop.run_forever()
        # finally:
        #     loop.close()


    def redis_keys(self):
        keys_byes = self.redis.keys()
        keys = [key.decode() for key in keys_byes]
        return keys

    def run(self):
        keys = self.redis_keys()
        print(len(keys))
        count = 0
        for key in keys:
            if "music" in key:
                continue
            res = self.redis.lrange(key,0,-1)
            try:
                self.high_concurrent(key,res)
                count += len(res)
            except Exception as e:
                print(e)
                break

            print(key,len(res))
            print("{}:共计{}首歌".format(key, self.item.get(key, 0)))

        print("总共：{}条url".format(count))


if __name__ == '__main__':
    wy = WangYiMusic()
    wy.run()
