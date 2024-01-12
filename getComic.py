import requests, json, os
from multiprocessing.dummy import Pool
from tqdm import tqdm

comicID = 2864
start = 0
end = -1

os.chdir(os.path.dirname(__file__))
data = json.loads(requests.get(f"https://terra-historicus.hypergryph.com/api/comic/{comicID}").text)["data"]
title = data["title"]
info = data["introduction"]
cover_url = data["cover"]
episodes = data["episodes"][::-1]

if end == -1:
	end = len(episodes)-1

print(str(len(episodes)), " in total.")
print(end-start+1, "is downloading.")

cnt = -1
pageNum = []
totalPages = 0
SIZE = 0

try:
	os.makedirs(title)
except Exception:
	pass

for ep in episodes:
	cnt = cnt + 1
	if cnt < start or cnt > end:
		continue
	try:
		os.makedirs(title + '\\' + ep["shortTitle"] + '-' + ep["title"])
	except Exception:
		pass
	page = len(json.loads(requests.get(f"https://terra-historicus.hypergryph.com/api/comic/{comicID}/episode/{ep['cid']}").text)["data"]["pageInfos"])
	print("Num: {:<5} ID: {:<8} pageNum: {:<5} Title: {:<15}".format(cnt, ep["cid"], page, ep["title"]))

	totalPages = totalPages + page
	pageNum.append(page)
	
def download(ID):
	PID = ID[0]
	imgID = ID[1]
	ep = episodes[PID]
	picUrl = json.loads(requests.get(f"https://terra-historicus.hypergryph.com/api/comic/{comicID}/episode/{ep['cid']}/page?pageNum={imgID}").text)["data"]["url"]
	picFile = requests.get(picUrl).content
	with open(title + '\\' + ep["shortTitle"] + '-' + ep["title"] + '\\' + 'P' + str(imgID).rjust(3, '0') + ".jpg", "wb") as f:
 		f.write(picFile)


ALL_ID = []
for i in range(0, len(pageNum)):
	for j in range(1, pageNum[i]+1):
		ALL_ID.append([i, j])

pbar = tqdm(total=totalPages)
update = lambda *args: pbar.update()
pool = Pool(totalPages)
for i in ALL_ID:
	pool.apply_async(download, args = (i,), callback = update)
pool.close()
pool.join()

with open(title + '\\' + "info.txt", "w") as f:
	f.write(str(info))

cover = requests.get(cover_url).content
with open(title + '\\' + "cover.jpg", "wb") as f:
	f.write(cover)