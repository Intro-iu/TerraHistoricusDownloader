# TerraHistoricusDownloader

泰拉记事社的爬虫下载器，支持 WebDav 自动同步更新/多线程下载/进度条显示

## Usage

### 基础食用方式

1. 获取 comicID

    例如 `https://terra-historicus.hypergryph.com/comic/2864` 对应的 `comicID` 就是 `2864`

    > 对没错，我是洁厨

2. 进入程序目录

    ```bash
    cd TerraHistoricusDownloader
    ```

3. 下载依赖库

    ```bash
    pip install -r requirements.txt
    ```

4. 运行程序

    指令存在三个选项：

    - `-m`: 下载多个漫画，后接 `comicID` (多个 ID 用空格隔开)

    - `-s`: 下载单个漫画，后接 `comicID` 与指定章节（多个章节用空格隔开，索引从 0 开始）

    - `-w`: 后接 WebDav 存放文件夹地址与多个 `comicID` (多个 ID 用空格隔开)

5. 示例 & 效果

    - 自动补全所有章节(会跳过已有章节，comID 自行获取)

    ```bash
    python getTerriaComic.py -m 2864 6253
    ```

    - 选择下载章节(输入要下载的章节，空格隔开，索引从 0 开始)

    ```bash
    python getTerriaComic.py -s 2864 0 2 6
    ```

    > 以上指令均自检测排除已经下载的章节

    > `python getTerriaComic.py -m comicID` 等价于 `python getTerriaComic.py -s comicID`

    - 程序会在当前目录的 Comic 文件夹下创建一个以漫画名字命名的文件夹，里面存放着的就是漫画资源

---

### [高级玩法]WebDav 上传食用说明

- 原理: 白嫖 `Github Actions`

- 步骤：

    1. 将本仓库 fork 到自己的仓库

    2. 进入 `Settings -> Secrets -> Actions -> New repository secret`

    3. 添加四个环境变量：

        - `COMIC_ID`: 填入 `comicID` (一个或多个，空格隔开)

        - `COMIC_PATH`: 填入你想要存放漫画的文件夹的地址

        - `RCLONE_CONFIG`: 将自己的 `rclone.conf` 配置文件加密: `base64 -w 0 rclone.conf` 得到的内容填入

        - `RCLONE_CONFIG_PASS`: 阅读自己的 `rclone.conf` 配置文件，找到末尾的 `pass` 的值并填入

    4. 自动脚本名为 `autoUpdate.yml`，默认在每天凌晨四点同步更新

- 注意事项：

    - 举个栗子：
        - 假如你 WebDav 地址是 `https://example.com/dav/`
        - 用于存放的文件夹地址是 `https://example.com/dav/Media/Comic/Arknights`
        - 那么你的 COMIC_PATH 应该是: `Media/Comic/Arknights`

    - 脚本中执行的是 `-w` 选项

    - 第一次同步的下载比较大，不建议一次性添加太多

    - 运行如果顺利，你将能在 WebDav 中你设置的文件夹下看到你的漫画

## 就是为了这碟醋包的饺子（乐）

### 代码写得很乱，封装的不大好，后续有待完善
