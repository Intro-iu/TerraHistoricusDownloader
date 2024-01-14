# TerraHistoricusDownloader
泰拉记事社的爬虫下载器，支持多线程下载与进度条显示

## Usage
1. 获取comicID，获取示例详见下方
2. 进入程序目录 
    ```bash
    cd TerraHistoricusDownloader
    ``` 
3. 下载依赖库
    ```bash
    pip install -r requirements.txt
    ```
4. 运行程序
    - 自动补全所有章节(会跳过已有章节，comID自行获取)
    ```bash
    python getTerriaComic.py comicID    
    ```
    - 选择下载章节(输入要下载的章节，空格隔开，索引从0开始)
    ```bash
    python getTerriaComic.py comicID 0 2 6
    ```
5. 程序会在当前目录的comic文件夹下创建一个以漫画名字命名的文件夹，里面存放着的就是漫画资源


## Example
- `https://terra-historicus.hypergryph.com/comic/2864` 对应的comicID就是2864

## 就是为了这碟醋包的饺子（乐）
