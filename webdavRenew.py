comicID = [int(str(line.strip()).split("-")[0]) for line in open('dataList.log', 'r', encoding='utf-8')]
with open('dataList.log', 'w') as f:
    for comic in comicID:
        f.write(str(comic) + ' ')
