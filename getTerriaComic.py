import requests, json, os
from multiprocessing.dummy import Pool
from tqdm import tqdm

class Comic:
    def __init__(self, comicId):
        self.comicId = comicId
        self.base_url = "https://terra-historicus.hypergryph.com/api/comic/"
        self.get_info()

    def get_info(self):
        data = json.loads(requests.get(self.base_url + str(self.comicId)).text)["data"]
        self.title = data["title"]
        self.info = data["introduction"]
        self.cover_url = data["cover"]
        self.episodes = data["episodes"][::-1]

    def download(self, start=0, end=-1):
        os.chdir(os.path.dirname(__file__))
        try:
            os.makedirs(self.title)
        except Exception:
            pass
        if end == -1:
            end = len(self.episodes) - 1
        print(str(len(self.episodes)), "in total.")
        print(end - start + 1, "is downloading.")
        cnt = -1
        pageNum = []
        totalPages = 0
        ALL_ID = []
        for ep in self.episodes:
            cnt = cnt + 1
            if cnt < start or cnt > end:
                continue
            try:
                os.makedirs(self.title + '\\' + ep["shortTitle"] + '-' + ep["title"])
            except Exception:
                pass
            page = len(json.loads(requests.get(self.base_url + str(self.comicId) + "/episode/" + ep['cid']).text)["data"]["pageInfos"])
            print("Num: {:<5} ID: {:<8} pageNum: {:<5} Title: {:<15}".format(cnt, ep["cid"], page, ep["title"]))
            totalPages = totalPages + page
            pageNum.append(page)
            for i in range(1, page + 1):
                ALL_ID.append([cnt, i])
        pbar = tqdm(total=totalPages)
        update = lambda *args: pbar.update()
        pool = Pool(totalPages)
        for i in ALL_ID:
            pool.apply_async(self.download_page, args=(i,), callback=update)
        pool.close()
        pool.join()

    def download_page(self, ID):
        PID = ID[0]
        imgID = ID[1]
        ep = self.episodes[PID]
        picUrl = json.loads(requests.get(self.base_url + str(self.comicId) + "/episode/" + ep['cid'] + "/page?pageNum=" + str(imgID)).text)["data"]["url"]
        picFile = requests.get(picUrl).content
        with open(self.title + '\\' + ep["shortTitle"] + '-' + ep["title"] + '\\' + 'P' + str(imgID).rjust(3, '0') + ".jpg", "wb") as f:
            f.write(picFile)

    def save_info(self):
        with open(self.title + '\\' + "info.txt", "w") as f:
            f.write(str(self.info))

    def save_cover(self):
        cover = requests.get(self.cover_url).content
        with open(self.title + '\\' + "cover.jpg", "wb") as f:
            f.write(cover)

if __name__ == "__main__":
    comicId = 2864
    start = 0
    end = -1
    comic = Comic(comicId)
    comic.download(start, end)
    comic.save_info()
    comic.save_cover()
