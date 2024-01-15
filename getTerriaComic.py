import requests, json, os, sys
from multiprocessing.dummy import Pool
import multiprocessing
from tqdm import tqdm

class Comic:
    def __init__(self, comicID):
        self.comicID = comicID
        self.base_url = "https://terra-historicus.hypergryph.com/api/comic/"
        self.get_info()

    def get_info(self):
        data = json.loads(requests.get(self.base_url + str(self.comicID)).text)["data"]
        self.title = data["title"]
        self.info = data["introduction"]
        self.cover_url = data["cover"]
        self.episodes = data["episodes"][::-1]
        os.chdir(os.path.dirname(__file__))
        try:
            os.makedirs('comic/' + self.title)
        except Exception:
            pass

    def get_download_list(self, chapter):
        existentChapter = [int(name[:2]) for name in os.listdir('./comic/' + self.title) if os.path.isdir(os.path.join('./comic/' + self.title, name))]
        if len(chapter) == 0:
            chapter = [i for i in range(0, len(self.episodes)) if i not in existentChapter]
        else:
            chapter = [i for i in chapter if i not in existentChapter]
        return chapter

    def download(self, chapter):
        if len(chapter) == 0:
            return
        print(str(len(self.episodes)), "in total.")
        print(len(chapter), "is downloading, using", 4*multiprocessing.cpu_count(), "processes")
        pageNum = []
        totalPages = 0
        ALL_ID = []
        cnt = -1
        for ep in self.episodes:
            cnt = cnt + 1
            if cnt not in chapter:
                continue
            try:
                if ep["shortTitle"][:2] == "预告":
                    os.makedirs('comic/' + self.title + '/00' + ep["shortTitle"][2:] + '-' + ep["title"])
                else:
                    os.makedirs('comic/' + self.title + '/' + ep["shortTitle"] + '-' + ep["title"])
            except Exception:
                pass
            page = len(json.loads(requests.get(self.base_url + str(self.comicID) + "/episode/" + ep['cid']).text)["data"]["pageInfos"])
            print("Num: {:<5} ID: {:<8} pageNum: {:<5} Title: {:<15}".format(cnt, ep["cid"], page, ep["title"]))
            totalPages = totalPages + page
            pageNum.append(page)
            for i in range(1, page + 1):
                ALL_ID.append([cnt, i])
        pbar = tqdm(total=totalPages)
        update = lambda *args: pbar.update()
        pool = Pool(processes=4*multiprocessing.cpu_count())
        for i in ALL_ID:
            pool.apply_async(self.download_page, args=(i,), callback=update)
        pool.close()
        pool.join()

    def download_page(self, ID):
        PID = ID[0]
        imgID = ID[1]
        ep = self.episodes[PID]
        picUrl = json.loads(requests.get(self.base_url + str(self.comicID) + "/episode/" + ep['cid'] + "/page?pageNum=" + str(imgID)).text)["data"]["url"]
        picFile = requests.get(picUrl).content
        if ep["shortTitle"][:2] == "预告":
            with open('comic/' + self.title + '/00' + ep["shortTitle"][2:] + '-' + ep["title"] + '/' + 'P' + str(imgID).rjust(3, '0') + ".jpg", "wb") as f:
                f.write(picFile)
        else:
            with open('comic/' + self.title + '/' + ep["shortTitle"] + '-' + ep["title"] + '/' + 'P' + str(imgID).rjust(3, '0') + ".jpg", "wb") as f:
                f.write(picFile)

    def save_info(self):
        if os.path.exists('comic/' + self.title + "/info.txt"):
            return
        with open('comic/' + self.title + "/info.txt", "w") as f:
            f.write(str(self.info) + "\n")
    def save_cover(self):
        if os.path.exists('comic/' + self.title + "/cover.jpg"):
            return
        cover = requests.get(self.cover_url).content
        with open('comic/' + self.title + "/cover.jpg", "wb") as f:
            f.write(cover)

if __name__ == "__main__":
    comicID = int(sys.argv[1])
    chapter = [int(i) for i in sys.argv[2:]]
    comic = Comic(comicID)
    chapter = comic.get_download_list(chapter)
    comic.download(chapter)
    comic.save_info()
    comic.save_cover()
    print("Mission Accomplished")
