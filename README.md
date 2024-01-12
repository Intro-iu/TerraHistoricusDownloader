# TerraHistoricusDownloader
泰拉记事社的爬虫下载器，支持多线程下载与进度条显示

`getComic.py` 是一开始写的原始代码，或许可以来提供一个线性的思路？

`getTerraComic.py` 是经过函数封装的代码，可能可读性稍微好一些

## Usge
- 下载部分支持库 `pip install requests tqdm multiprocessing`
- 修改主函数中的comicID参数，表示漫画的ID，可以在漫画链接中找到
- 修改主函数中的start和end参数，表示漫画章节的选择范围(索引从0开始)

> start和end默认分别为0和-1，表示下载全部（-1表示末尾）

## 举个例子
- `https://terra-historicus.hypergryph.com/comic/2864`对应的comicID就是2864

## 就是为了这碟醋包的饺子（乐）
