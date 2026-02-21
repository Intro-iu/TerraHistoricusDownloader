# TerraHistoricusDownloader

泰拉记事社的爬虫下载器，支持 WebDav 自动同步更新/多线程下载/进度条显示

> 已完成 《明日方舟》 & 《明日方舟：终末地》 适配

## Usage

### 环境准备

本项目使用 [uv](https://github.com/astral-sh/uv) 进行依赖管理和运行。请先安装 `uv`：

**Windows:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 基础食用方式

1.  **获取 comicID**

    例如 `https://comic.hypergryph.com/terra-historicus/comic/2864`  对应的 `comicID` 就是  `2864`

    > [明日方舟示例] 对没错，我是洁厨

     例如 `https://comic.hypergryph.com/talos-ii-historicus/comic/5032` 对应的 `comicID`  就是 `5032`

    > [终末地示例] 小鹈鹕也可爱捏

2.  **进入程序目录**

    ```bash
    cd TerraHistoricusDownloader
    ```

3.  **运行程序**

    无需手动安装依赖，使用 `uv run` 即可自动处理环境和依赖。

    指令存在三个选项：

    -   `-m`: 下载多个漫画，后接 `comicID` (多个 ID 用空格隔开)
    -   `-s`: 下载单个漫画，后接 `comicID` 与指定章节（多个章节用空格隔开，索引从 0 开始）
    -   `-w`: WebDav 模式，后接 WebDav 存放文件夹地址与多个 `comicID` (多个 ID 用空格隔开)

4.  **示例 & 效果**

    -   **自动补全所有章节** (会跳过已有章节，comID 自行获取)

        ```bash
        uv run getTerriaComic.py -m 2864 6253
        ```

    -   **选择下载章节** (输入要下载的章节，空格隔开，索引从 0 开始)

        ```bash
        uv run getTerriaComic.py -s 2864 0 2 6
        ```

    > 以上指令均自检测排除已经下载的章节

    -   程序会在当前目录的 `Comic` 文件夹下创建一个以漫画名字命名的文件夹，里面存放着的就是漫画资源

---

### [高级玩法] WebDAV 上传食用说明

-   **原理:** 白嫖 `Github Actions` + `Rclone` 自动上传WebDav
-   **步骤：**

    1.  将本仓库 fork 到自己的仓库
    2.  进入 `Settings -> Secrets and Variables -> Actions`
    3.  在 `Secrets` 选项卡下 `Repository secrets` 添加加密变量：
        -   `COMIC_PATH`: 填入你想要存放漫画的文件夹的地址
        -   `RCLONE_CONFIG`: 将自己的 `rclone.conf` 配置文件加密: `base64 -w 0 rclone.conf` 得到的内容填入
        -   `RCLONE_CONFIG_PASS`: (如有) 阅读自己的 `rclone.conf` 配置文件，找到末尾的 `pass` 的值并填入（看下方注意事项）
    4. 在 `Variables` 选项卡下 `Repository variables` 添加环境变量：
        -   `COMIC_ID`: 填入 `comicID` (一个或多个，空格隔开)
    5.  自动脚本名为 `autoUpdate.yml`，默认在每天凌晨四点同步更新

-   **注意事项：**
    -   Rclone 配置文件有一定的格式要求，其名称必须是 `CloudDrive`，例如：
        1. pass 验证（这种情况下需要填写RCLONE_CONFIG_PASS变量）
        ```ini
        [CloudDive]
        type = webdav
        url = https://cloud.xxxx.com:114514/dav
        vendor = your_type
        user = username
        pass = s_xxxxxxxxxxxxxxx
        ```
        2. token 验证（这种情况下只需要填写RCLONE_CONFIG）
        ```ini
        [CloudDive]
        type = drive
        client_id = xxx
        client_secret = xxx
        scope = drive
        token = {"access_token":"xxx","token_type":"Bearer","refresh_token":"xxx","expiry":"2025-07-19T01:42:01.0070802+08:00"}
        team_drive =
        ```

    -   关于 WebDav 路径：
        -   假如你 WebDav 地址是 `https://example.com/dav/`
        -   用于存放的文件夹地址是 `https://example.com/dav/Media/Comic/Arknights`
        -   那么你的 COMIC_PATH 应该是: `Media/Comic/Arknights`

## 就是为了这碟醋包的饺子（乐）
