# 深度姿势素材包

每个子目录是一个包，里面要有 `manifest.json`。`depthpack.py` 在构建时读取这些包，生成前端用的 `depths.json`。页面只使用构建结果里的地址，不关心图片是热链还是本站文件。

## 现在：gia-depth（热链）

`source` 为 `hotlink`。`base` 是原站地址，条目里的 `サムネ` / `原寸` 是相对路径，拼在 `base` 后面。

构建不会下载、复制或改写任何图片。热链包里也不能放图片文件，避免把原站图片带进仓库或 `dist/`。

原站：<https://ai-pose-depth-gallery.pages.dev/>  
作者：ギア <https://x.com/giaaibusi>  
本站只做非官方汉化索引。

## 以后换成自己的渲染

1. 新建 `depth/packs/<名字>/`，或改现有包的 `manifest.json`。
2. 把 `source` 改成 `local`，图片按条目里的相对路径放在包目录里。
3. 再运行 `python3 build.py`。本地文件会复制到 `dist/d/<包名>/`，页面改为引用本站地址。
4. `gatedLines` 列出需要放在 18+ 开关后面的系列（日文原名）。

换源时只改包，不必改前端。
