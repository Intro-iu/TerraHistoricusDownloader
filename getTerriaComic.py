import requests, json, os, sys
from multiprocessing.dummy import Pool
import multiprocessing
from tqdm import tqdm

class Comic:
    def __init__(self, comicID):
        self.comicID = comicID
        self.CID = []
        self.title = []
        self.info = []
        self.cover_url = []
        self.episodes = []
        self.totalChapter = []
        self.base_url = "https://terra-historicus.hypergryph.com/api/comic/"
        self.get_info()

    def get_info(self):
        for id in self.comicID:
            data = json.loads(requests.get(self.base_url + str(id)).text)["data"]
            self.CID.append(data["cid"])
            self.title.append(data["title"])
            self.info.append(data["introduction"])
            self.cover_url.append(data["cover"])
            self.episodes.append(data["episodes"][::-1])            

            os.chdir(os.path.dirname(__file__))
            try:
                os.makedirs('Comic/' + self.CID[-1] + '_' + data["title"])
            except Exception:
                pass

    def remove_chars(self, s):
        return ''.join(x for x in s if x.isprintable())

    def get_download_list(self, chapter, option):
        self.existentChapter = []
        self.inexistentChapter = []
        for n in range(0, len(self.CID)): # 讨论单个漫画
            self.existentChapter.append([])
            self.totalChapter.append([])
            if option:
                data = []
                os.system('rclone lsf CloudDrive:' + self.comic_path + '/' + self.CID[n] + '_' + self.title[n] + ' > dataList.log && cat dataList.log' )
                with open('dataList.log', 'r', encoding='UTF-8') as f:
                    for line in f:
                        if line.strip('\n')[-1] == '/':
                            data.append(line.strip('\n')[:-1])
            else:
                data = os.listdir('Comic/' + self.CID[n] + '_' + self.title[n])

            for name in data:
                if option:
                    cond = name in data
                else:
                    cond = os.path.isdir(os.path.join('Comic/' + self.CID[n] + '_' + self.title[n], name))
                
                if cond:
                    name = str(name)
                    if '「' in name:
                        name = name.replace(name[name.index('「'):name.index('」')+3], '')
                    else:
                        name = name.split('_')[1]
                    self.existentChapter[n].append(self.remove_chars(name))
                       
            if len(chapter) == 0:   # 全部补全
                for i in range(0, len(self.episodes[n])):
                    self.totalChapter[n].append(self.episodes[n][i]["title"])
                self.inexistentChapter.append([i for i in self.totalChapter[n] if i not in self.existentChapter[n]])
            else:   # 指定补全
                self.inexistentChapter.append([self.episodes[n][i]["title"] for i in chapter if i not in self.existentChapter[n]])
        # print(self.existentChapter)
        # print(self.inexistentChapter)
        # print(self.totalChapter)
        return self.inexistentChapter  # 需补全章节

    def download(self, inexistentChapter):
        L = 0
        for n in range(0, len(inexistentChapter)):
            L += len(inexistentChapter[n])
            print(self.title[n], ':', len(inexistentChapter[n]), 'Chapter(s)') # 章节数量
        print(L, "is downloading, using", 6*multiprocessing.cpu_count(), "processes") # 需补全数量
        pageNum = []
        totalPages = 0
        ALL_ID = []
        for n in range(0, len(comicID)):
            TMP = -1
            for ep in self.episodes[n]:
                TMP += 1
                if ep["title"] not in inexistentChapter[n]:
                    continue
            
                try:
                    if self.remove_chars(ep["shortTitle"]) == "预告":
                        tmp = '00'
                    elif ep["type"] == 2:
                        tmp = 'SP' + self.remove_chars(ep["shortTitle"]).replace(' ', '')
                    else:
                        tmp = self.remove_chars(ep["shortTitle"]).replace(' ', '')
                    os.makedirs('Comic/' + self.CID[n] + '_' + self.title[n] + '/' + tmp + '_' + ep["title"])
                except Exception:
                    pass
                page = len(json.loads(requests.get(self.base_url + self.CID[n] + "/episode/" + ep['cid']).text)["data"]["pageInfos"])
                print("Chapter: {:<5} ID: {:<8} pageNum: {:<5} Title: {:<15}".format(tmp, ep["cid"], page, ep["title"]))
                totalPages = totalPages + page
                pageNum.append(page)

                for i in range(1, page + 1):
                    ALL_ID.append([n, TMP, i, tmp])
        # print(ALL_ID)
        # self.download_page(ALL_ID[0])
                
        pbar = tqdm(total=totalPages)
        update = lambda *args: pbar.update()
        pool = Pool(processes=6*multiprocessing.cpu_count())
        for i in ALL_ID:
            pool.apply_async(self.download_page, args=(i,), callback=update)
        pool.close()
        pool.join()

    def download_page(self, ID):
        CID = ID[0]
        PID = ID[1]
        imgID = ID[2]
        PTITLE = ID[3].replace(' ', '')
        ep = self.episodes[CID][PID]
        picUrl = json.loads(requests.get(self.base_url + str(self.comicID[CID]) + "/episode/" + ep['cid'] + "/page?pageNum=" + str(imgID)).text)["data"]["url"]
        picFile = requests.get(picUrl).content
        path = 'Comic/' + self.CID[CID] + '_' + self.title[CID] + '/' + PTITLE + '_' + ep["title"] + '/' + 'P' + str(imgID).rjust(3, '0') + ".jpg"
        with open(path, "wb") as f:
            f.write(picFile)

    def save_info(self, option):
        for n in range(0, len(self.comicID)):
            if option:
                with open('dataList.log', 'r', encoding='UTF-8') as f:
                    data = f.readlines()
                    data = [x.strip() for x in data]
                    cond = 'info.txt' in data
            else:
                cond = os.path.exists('Comic/' + self.CID[n] + '_' + self.title[n] + "/info.txt")
            if cond:
                return
            with open('Comic/' + self.CID[n] + '_' + self.title[n] + "/info.txt", "w", encoding="UTF-8") as f:
                f.write(str(self.info[n]))
    def save_cover(self, option):
        for n in range(0, len(self.comicID)):
            if option:
                with open('dataList.log', 'r', encoding='UTF-8') as f:
                    data = f.readlines()
                    data = [x.strip() for x in data]
                    cond = 'cover.jpg' in data
            else:
                cond = os.path.exists('Comic/' + self.CID[n] + '_' + self.title[n] + "/cover.jpg")
            if cond:
                return
            cover = requests.get(self.cover_url[n]).content
            with open('Comic/' + self.CID[n] + '_' + self.title[n] + "/cover.jpg", "wb") as f:
                f.write(cover)

if __name__ == "__main__":
    print("Loading...")
    option = sys.argv[1]
    comicID = []
    if option == "-m":
        k = False
        comicID = [int(s) for s in sys.argv[2:]]
        chapter = []
    if option == "-s":
        k = False
        comicID = [int(sys.argv[2])]
        chapter = [int(i) for i in sys.argv[3:]]

    if option == "-w":
        k = True
        comicID = [int(s) for s in sys.argv[3:]]
        chapter = []

    comic = Comic(comicID)
    if k:
        comic.comic_path = sys.argv[2]
    inexistentChapter = comic.get_download_list(chapter, k)
    comic.download(inexistentChapter)
    comic.save_info(k)
    comic.save_cover(k)
    print("Mission Accomplished")
