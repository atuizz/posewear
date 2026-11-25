# AGENTS.md — 衣姿 PoseWear 开发与交接手册

给接手本项目的开发者 / AI 看的运行手册。用户向说明在 README.md（四语：中/英/日/越），这里只讲怎么开发、构建、测试、部署和避坑。

## 项目速览

- 纯静态站：Python 构建 + 原生 JS（无框架、无打包器），部署在 Cloudflare Pages。
- 线上：https://posewear.pages.dev ；图片分发：https://pwimg.0vo.pro （R2 桶 `posewear-assets`）。
- 内容：12 个素材库（姿势/深度姿势/服装/动画服装/人像/表情/发型/历代/场景/光影/道具/家具）+ 浏览器内 AI 试穿/生图（用户自备 API Key，直连或经本站代理转发）+ 生成记录页。
- 仓库不含素材图片：素材在 `assets-raw/`（gitignore），用 `scripts/fetch-assets.py` 从上游公开站抓取；构建产物 `dist/`、`dist-assets/` 同样不入库。

## 目录与职责

| 路径 | 职责 |
|---|---|
| `build.py` | 构建主入口：读 `assets-raw` 数据 → 生成每库 JSON、图片变体，显式调用 `post.run(ctx)` |
| `post.py` | 后处理模块（`post.run(ctx)`）：资源指纹（`/assets/<name>.<hash>.js|json`）、`sw.js` 预缓存、`_headers`（含 CSP）、`index.html` 组装，并调用 `seo.run(ctx)` |
| `seo.py` | 静态 SEO 落地页模块（`seo.run(ctx)`）：中英文首页/分类/标签/详情页与站点地图 |
| `src/index.html` | 单页骨架（所有栏目、试穿台、托盘、弹窗的 DOM 都在这里） |
| `src/catalog.js` | `window.PoseWearCatalog` 单一数据源：12 库注册表、筛选与配色、槽位映射与通用 DOM/存储工具 |
| `src/app.js` | 图库 SPA：栏目切换、筛选、卡片、灯箱、收藏、组合与**悬浮生图工作台**（托盘） |
| `src/palette.js` | 灯箱主色调提取与色卡渲染（`window.PoseWearPalette`） |
| `src/sketch.js` | 全屏速写定时练习工作室（`window.PoseWearSketch`） |
| `src/command-palette.js` | 全局 `⌘K` 命令面板（`window.PoseWearCommandPalette`） |
| `src/board-export.js` | 参考画板高分 PNG 拼贴导出（`window.PoseWearBoardExport`） |
| `src/references.js` | 浏览器与 MCP 共用选定视角、公开图片地址与复制文本的格式 |
| `src/i18n.js` | 中英日越界面词条与语言切换，`pwUiLocale` 独立于提示词设置 |
| `src/studio.js` | 工作台选材、提示词、生成与结果；对外接口是 `window.WB` |
| `src/image-providers.js` | 悬浮及完整工作台共用的生图服务商协议、连接测试和错误解析 |
| `src/theme.js` | 首屏外观、系统主题与用户选择的同步 |
| `src/history.js` | 生成记录页（数据在浏览器 IndexedDB `lk-studio` 的 `h` 表，上限 200 条） |
| `src/extras.js` | `window.X` 工具（下载、ZIP 等）；`src/zip.js` 打包 |
| `functions/api/proxy.js` | Pages Function：CORS 转发代理（只许本站来源、官方域名限标准 https、自定义中转 http/https 任意端口但禁内网地址、只转发必需请求头） |
| `scripts/fetch-assets.py` | 从上游站抓素材到 `assets-raw/`（低并发，勿反复全量抓） |
| `scripts/prep-modules.py` | 新模块（表情/发型等）素材预处理 |
| `scripts/sync-r2.py` | 把图片目录同步到 R2（断点续传，见下） |
| `scripts/catalog-source.mjs` | 本地预览与 MCP 共用的公开目录发现、指纹校验与读取 |
| `mcp/server.mjs` · `.agents/skills/posewear/` | 只读 stdio MCP 与项目选图 Skill。[接入与工具](mcp/README.md) |
| `scripts/local-engine.mjs` | 本地预览的 ComfyUI / stable-diffusion.cpp 适配。[引擎设置与工作流](docs/local-engines.md) |
| `tests/` | 浏览器、协议与构建回归（见「测试」） |

## 构建与部署（标准流程，勿改顺序）

```bash
# 日常开发可直接 npm ci && npm start，预览会联网加载已发布的 12 份目录。
# 从原始素材构建时，先在独立 Python 环境安装 Pillow，再准备素材：
python3 -m pip install Pillow
python3 scripts/fetch-assets.py
python3 scripts/prep-modules.py --archive /path/to/posewear-assets-archive --snapshots /path/to/pw-modules
POSEWEAR_ASSET_HOST=https://pwimg.0vo.pro python3 build.py
export POSEWEAR_STAGING="$(mktemp -d "${TMPDIR:-/tmp}/posewear-staging.XXXXXXXX")"
cp -R dist/. "$POSEWEAR_STAGING/"
python3 tests/check_csp.py "$POSEWEAR_STAGING"
# 在此副本完成下方回归后，从项目根目录发布同一副本：
npm run deploy
```

- 缺扩展档案时可用 `python3 build.py --allow-partial` 本地开发；带缺库标记的产物不能通过发布检查。
- **`--branch main` 不可省**：wrangler 按本地 git 分支决定部署目标，漏了会静默发到分支预览、生产不变。部署后必须线上验活（见清单），不能只看 deploy 成功。
- Pages 单站上限 20,000 文件；`POSEWEAR_ASSET_HOST` 让缩略图/原图走 R2，主站文件数才压得住。
- wrangler 用 OAuth 登录态（约 1 小时过期）：过期时 whoami 报未登录是假象，用 refresh_token 向 `https://dash.cloudflare.com/oauth2/token` 刷新（client_id `54d11594-84e4-41aa-b438-e81b8fa78ee7`，**必须带浏览器 UA**，否则 403/1010），或给 wrangler 传 `CLOUDFLARE_API_TOKEN` 环境变量。
- 图片变体分工：缩略图 `t/` 与原图 `o/` 在 R2（代码里经 `AH` 前缀访问）；中图 `m/`、`i/` 是主站同源文件。**拿 pwimg 测 m/i 会假 404**，别误判。
- 新增图片到 R2：`python3 scripts/sync-r2.py <图片目录>`（并发 ≤8，防 429；只传增量）。

### 部署后线上验活清单

1. 首页 200，铃铛内的公告及素材库菜单中的统计数字与本次改动一致；
2. 线上 `/assets/*.js` 哈希与 staging 一致，关键新代码字符串能 grep 到；
3. 响应头 CSP 的 img-src 覆盖全部图片源站（含热链站）；
4. 任选一库 JSON 条数正确；样本图各一张：pwimg 的 t/o 各 200、同源 m 200、热链图 200；
5. `curl -X OPTIONS https://posewear.pages.dev/api/proxy` 返回 204；
6. 本次改动的功能点在生产页面实际点一遍（或用线上地址跑对应测试套件）。

开发预览的静态 SEO 路由优先读本地 `dist/`，可用 `POSEWEAR_STAGING=/absolute/path npm start` 指向构建副本。没有对应本地页时会读取发布站版本。

## 数据与素材

- 上游五站同作者 @giaaibusi（人像 @agi_aibusi，CC0）；深度姿势数据在 `depth/packs/`（已入库）；新模块素材档案在维护者本地 `posewear-assets-archive/`（不在仓库）。
- 发型与部分动画服装来自 CharaDB：**图片只能热链**（`charadb-2fi.pages.dev`），禁止再分发、不要下载进 R2/dist。
- 新增热链数据源时必须同步 CSP：`build.py` 会从 CharaDB 数据自动收集源站写入 img-src，connect-src 允许 HTTPS 以支持自定义直连，图片展示仍限指定来源。新数据源要照此处理，并跑 `tests/check_csp.py` 守卫（2026-11-23 发型库全灭就是漏了这一步）。
- 条目数据字段：`t/m/i/o` 是四档图片路径，`ext=1` 表示热链外站图，`ref` 为 referrerpolicy。

## 测试

```bash
npm ci
npx playwright install chromium
# 在没有素材档案和 staging 的源码目录也可执行
npm run test:offline
# 完整站点回归请使用上面准备的 staging
# 终端一，从 staging 加载 Pages 响应头和 Functions
npx wrangler pages dev "$POSEWEAR_STAGING" --cwd "$POSEWEAR_STAGING" --ip 127.0.0.1 --port 8902 --compatibility-date 2026-11-19
# 终端二，从项目根目录运行（使用已有浏览器时可设置 CHROME_PATH）
U=http://127.0.0.1:8902 npm test
```

| 套件 | 覆盖 |
|---|---|
| v12 | 图库基础：栏目、筛选、灯箱、收藏、组合 |
| v13 | 试穿台全流程（四家服务商 mock、报错分类、安全审核、重试、多图、ZIP、记录增删） |
| v14-xai | xAI 协议 |
| v15-modules | 新模块各库条数/渲染/筛选 + 表情槽位 |
| v16-proxy | 代理函数单元测试（node 直跑 `.mjs`，不起浏览器） |
| v17-history | 生成记录页冒烟 |
| v18-quick | 悬浮工作台：常驻入口、面板内加素材、托盘内生图全流程 |
| mcp-regressions / reference-regressions | stdio 握手与真实工具调用、指定角度、单条及组合提示词的参考图地址 |
| local-engine-regressions | 本机引擎状态、ComfyUI 工作流、sd.cpp 协议与请求边界 |

- `tests/run.mjs` 按顺序执行 v12–v18 和专项回归（图库、工作台、界面语言等），任一失败会返回非零退出码。
- 测试用 route 拦截把服务商 API 全部 mock 掉（fixtures 是本地假图），不消耗真实额度；**不要**改成真调。
- 已知环境坑：受限沙箱里 Chromium 经代理加载外站图片会 `ERR_TUNNEL_CONNECTION_FAILED`，v15 有 9 项这类基线失败（卡片渲染/页面错误断言），与改动无关；判断回归要和改版前基线逐项对比，新增失败才算回归。
- 改 studio 生成管线必须保 v13 全绿；改托盘/工作台保 v18 全绿。

## 关键机制速记

- **悬浮生图工作台**（app.js 托盘 + studio.js）：点击 `#trayFab` 展开工作台，浏览、切换素材库时面板保持打开。收起后，创作条保留已选素材缩略图。面板内「添加素材」经 `WB.openPicker(type, sink)` 复用 studio 的选择器往组合里加；仅在转入完整工作台时由 `WB.setSel` 同步槽位（服装/动画/历代→服装≤2，姿势/深度→姿势≤6，人像→人物≤1。表情≤1，发型、场景、光影、道具和家具归入「其他素材」，均以参考图随生成请求发送）；生成走 `WB.quick(opts)` = studio `run()` 的 quick 模式（跳过试穿台 UI、结果回托盘并存入生成记录）。试穿台本体是「完整工作台」，两者共用一套生成核心，不要另起炉灶。
- 代理对自定义中转开放（2026-11-24 维护者定版，勿改回登记制）：带 `x-proxy-custom: 1` 的请求可转发到任意公网 http/https 地址与端口，仅禁内网地址与非图片接口路径。服务商配置存 localStorage `wbCfg`；配置只持久化在浏览器。直连时密钥与图片发往所选服务，启用代理时本站 Function 经手并转发请求，不保存请求内容。
- 图片缓存策略：图库图片路径（/p/ /c/ /a/ /r/ /e/ /y/ /s/ /l/ /t/ /f/ /o/）与 R2 对象一律 `max-age=31536000, immutable`（图片按 ID 寻址、内容不变）；只有 HTML 与 sw.js 走 revalidate/no-cache。勿把图片改回 must-revalidate。
- 公告、应用更新和最近操作由 `#noticeMenu` 集中展示。素材来源与许可位于页脚 `#credits`。
- `copyRefs` 默认开启。卡片、灯箱、悬浮及完整工作台复用同一参考图格式。保留选定的 `angles` 视角和原站热链，本地上传图在复制文本中提示用户另附。
- localStorage 键：`wbCfg`、`wbSel`（试穿台选材）、`sel`（组合）、`fav`、`theme`、`lang` 等，改名即丢用户数据，慎改。

## 约定

- 默认 UI 文案简体中文，同时维护英文、日文、越南文词条；品牌红 `#ff2442` 点缀、白底干净、**不用黄色/金色**；页面忌文字堆砌。
- 提交：显式列文件路径提交，**不要 `git add -A`**（工作区常有 dist-assets 等大目录未跟踪）。
- 发版：四语 README 版本号与 `CHANGELOG.md` 同步更新，GitHub Release 用 API 建，tag 形如 `v1.4.0`。
- 生产红线：部署、合并 PR、回议题已获维护者长期授权（2026-11-22）；新功能/动架构/花钱的事先问维护者。
- Web Analytics：代码已支持（`POSEWEAR_WA_TOKEN` 构建注入 + CSP 放行），差 Cloudflare 后台 Pages → posewear → Metrics 开启或给站点令牌，开后验 beacon 上线。
