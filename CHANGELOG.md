# PoseWear · 版本记录 · Release notes · 更新履歴

[简体中文](#zh) · [English](#en) · [日本語](#ja)

<a id="zh"></a>

## 简体中文

### 2026-11-25 · v1.4.0

- **画师级大图检视台**：新增 2× 缩放拖拽（`Z` / 双击）、水平镜像（`H`）、三分与中心红轴构图参考线（`G`）、灰度明度检查（`B`）、彩色参考图中心加权 5 色自动取色板（点击复制 `#HEX`）及线稿 × 深度图同视角实时卷帘对比（`V`）。
- **全屏速写定时练习（Gesture Studio）**：基于当前筛选结果进入无干扰定时练习，支持 `30s / 60s / 2m / 5m` 与 `5 / 10 / 20 / 无限` 张数、可选柔和提示音、切页防跳帧、镜像 / 参考线 / 灰度 / 线稿深度切换，以及结束后可点击回溯的练习回顾接触表。
- **创作工作台与导航升级**：参考画板显示发送序号（`1/2/3`）与当前机位，支持「换一组」、一键清空并撤销及**一键导出高分参考拼图 PNG**；全局 `⌘K` / `Ctrl+K` 命令面板支持中英日越模糊检索并直达 12 个图库与常用命令；服装/动画服装新增色卡筛选，生成记录页新增模式筛选、关键词搜索与所用参考图溯源。
- **新增越南语（Tiếng Việt）界面与文档**（感谢 [@dung997tb](https://github.com/dung997tb) 贡献 #24）：完整覆盖全部 774 条界面词条、动态格式化文本、CSS 状态文案、移动端 320px/390px 回归测试与 [README.vi.md](README.vi.md)。
- **代码架构重构与文档翻新**：新增 `src/catalog.js` 单一数据源，拆出 `palette.js`、`sketch.js`、`command-palette.js`、`board-export.js` 独立模块并完整解包格式化源码；扁平化去重 `src/style.css`（减少 344 个冗余规则块、统一 12 库 `--cat-color` 色板）；将 `build.py` / `post.py` / `seo.py` 改为显式模块调用并移除 `exec()` 胶水，新增离线构建与 CSP 回归测试接入 CI；四语 README 与高清截图全面翻新。

### 2026-11-24 · v1.3.2

- 官方声明扩围：冒充名单新增 posewear.art（克隆本站并设登录与收费套餐）。重申：官方只有 posewear.pages.dev，免费、无需注册账号、没有收费套餐；凡是要登录、付费的「PoseWear」都是冒充。

### 2026-11-24 · v1.3.1

- 官方声明：官网只有 posewear.pages.dev，没有 Windows / Android 客户端，也不提供 exe、apk 下载；posewear.cn 等站点均为冒充。声明已同步到三语 README 与站内通知区。
- 修复 v1.3.0 的两处回退：本站代理恢复转发任意公网自定义中转（http/https、任意端口，内网地址除外），不再要求部署者逐个登记；图库图片恢复一年期 immutable 缓存，不再每次访问都重新验证。
- 生图请求失败不再静默降级：移除了「自动换接口协议重试」「自动丢掉参考图重试」等多层兜底，只保留图片字段名的一种已知兼容重试，其余错误直接报出。
- 清理失效的三语词条、已下线 UI 的残留样式与过时文案；三语 README 重写。

### 2026-11-24 · v1.3.0

- 在姿势卡片上点编号，可在同一机位的线稿和深度图之间翻面。复制单条或组合提示词会附上所选角度的参考图链接。
- 展开悬浮工作台后仍可浏览图库、切换分类、继续选图。完整工作台默认展示人物、服装和姿势，其余参考图集中在「其他素材」。刷新后可恢复手改提示词、张数和比例。
- 界面支持简体中文、英文和日文。手机支持触屏选材，外观可设为跟随系统、浅色或深色。
- 本地工作台可连接 ComfyUI 或 stable-diffusion.cpp。ComfyUI 内置工作流接受一张参考图，多图可使用自定义工作流。智能体可通过只读 MCP 和选图 Skill 搜索图库、选取机位并组合提示词。

### 2026-11-23 · v1.2.1

- 组合托盘升级为常驻「生图工作台」：常驻悬浮按钮（带已选数量徽章），随时打开拼装；面板内可直接「添加素材」（服装、动画服装、姿势、人像、表情），不必先回图库点选；空组合时有明确的空状态引导。
- 新增 `AGENTS.md` 开发交接手册与 `scripts/sync-r2.py`（R2 图片同步脚本），仓库可完整交付他人接手开发。

### 2026-11-23 · v1.2.0

- 组合托盘新增「简易生图」：在图库里选好服装、姿势、人像、表情，托盘里直接生成图片（可改提示词、选张数和比例），结果可看大图、下载，并自动存入生成记录，不必先进试穿工作台。
- 试穿台打磨：去掉右栏中部的空白占位，生成结果自动滚入视野。
- 全站文案与数据校正：动画服装数量 1320 → 1760（首页统计、meta、公告、页脚统一），页脚补 CharaDB 致谢，隐私说明改正深度姿势分发方式；托盘加高度上限、手机端公告限两行。
- 新增 `tests/v18-quick.js` 覆盖托盘生图全流程。

### 2026-11-23 · v1.1.0

- 修复发型库与动画服装中 CharaDB 部分的图片全部加载失败：本站 CSP 的 `img-src` 白名单漏了热链源站，浏览器直接拦截。构建时改为自动收集数据里的热链源站写入白名单，并新增 `tests/check_csp.py` 守卫，构建后校验全部图片源站。
- 本页 README 同步到当前功能（英文、日文版同步更新）。

### 2026-11-22 · 生成记录页、代理与 Gemini 协议

- 新增「生成记录」页（@OrangeSAM 贡献）：全选批量打包、导出 ZIP（含提示词与参数元数据）、单张重新生成、大图与原图前后对比；记录上限 200 条。
- 修复代理开关对自定义中转不生效：未勾选代理时中转请求直连；代理放行自定义中转的任意端口（官方域名仍限标准 HTTPS，内网地址仍拒绝）。
- 自定义中转新增 Gemini 协议：可选 `models/:generateContent` 调用，鉴权头按协议自动切换。
- 页头宽屏遮挡修复（@yansiao1227 贡献）。

### 2026-11-21 · 七个扩展库上线、图片迁入 R2

- 新增七个栏目：表情 95、发型 122（CharaDB，图片热链原站）、历代服装 57、场景 64、光影 50、道具 32、家具 41；动画服装并入 CharaDB 的 440 套，总数增至 **1760 套**。
- 全站图片改由 Cloudflare R2（`pwimg.0vo.pro`）分发；深度姿势图片改为本站自存，不再热链原站，加载更稳定。
- 修复 Seedream 5.x 参数错误导致生图失败（@COBEZE 贡献）：参数改为仅对 4.x 模型发送。

### 2026-11-19 · 动画服装库上线

- 新增「动画服装」栏目：接入上游 COSTUME-ANIME-DB（[@giaaibusi](https://x.com/giaaibusi)）的 **1320 套**动画风穿搭，与写实服装同为 8 个分类（春 197 / 夏 237 / 秋 230 / 冬 232 / 内衣 197 / 派对礼服 36 / 泳装 52 / 性感 139），每套附中英文提示词。
- 内衣、性感类共 336 套按成人内容处理：默认隐藏，打开顶部「18+」开关后显示（默认公开 984 套）。
- 动画服装支持服装库的全部功能：分类 / 颜色 / 单品筛选、搜索建议、收藏、最近浏览、组合提示词、中英双语详情页与 sitemap；试穿工作台的服装步骤可直接「从动画服装选」。
- 首页新增上线公告条与动画服装计数，页脚与隐私说明补齐来源致谢；`scripts/fetch-assets.py` 新增 `anime` 数据源（顺带修复写实服装漏抓缩略图的问题）。

### 2026-10-31 · 深度姿势

- 新增「深度姿势」栏目：热链上游深度姿势图 288 组 / 1439 张，双人图走 18+ 开关。

<a id="en"></a>

## English

### 2026-11-25 · v1.4.0

- **Artist Lightbox Studio**: added 2× zoom & drag-to-pan (`Z` / double-click), horizontal mirror (`H`), rule-of-thirds and center-axis composition grids (`G`), grayscale luminance study (`B`), center-weighted 5-swatch auto color palette (click to copy `#HEX`), and live same-angle line-art × depth split compare (`V`).
- **Fullscreen Gesture Drawing Studio**: launch distraction-free timed sessions from the current filtered gallery with `30s / 60s / 2m / 5m` timers, `5 / 10 / 20 / Endless` decks, optional chime, tab-switch timer guard, mirror / grid / grayscale / depth-flip tools, and a clickable session recap sheet.
- **Creative Studio & Navigation Upgrades**: reference board cards now show send indices (`1/2/3`) and camera angles, with Shuffle, Clear with Undo, and **one-click high-DPI reference board PNG export**; added the global `⌘K` / `Ctrl+K` Command Palette with multilingual search across all 12 libraries and actions; added visual color swatch filters for outfits, plus mode filters, prompt/model search, and clickable reference thumbnails in Generation History.
- **Vietnamese UI & README (`Tiếng Việt`)** (contributed by [@dung997tb](https://github.com/dung997tb) in #24): full coverage across all 774 UI dictionary keys, dynamic formatters, CSS status copy, 320px/390px mobile locale tests, and [README.vi.md](README.vi.md).
- **Architecture Refactor & README Renovation**: consolidated registries into `src/catalog.js`, extracted `palette.js`, `sketch.js`, `command-palette.js`, and `board-export.js`, unpacked and formatted monolithic scripts, flattened `src/style.css` (−344 redundant blocks, unified `--cat-color` palette), replaced Python `exec()` glue in `build.py` / `post.py` / `seo.py` with explicit module calls and CI pipeline/CSP tests, and renovated all four READMEs with Retina screenshots.

### 2026-11-24 · v1.3.2

- Impersonation notice expanded: posewear.art (a clone with sign-in and paid plans) is now named too. The only official site is posewear.pages.dev — free, with no accounts and no paid plans; any "PoseWear" asking you to sign in or pay is an impostor.

### 2026-11-24 · v1.3.1

- Fixes two v1.3.0 regressions: the site proxy again forwards to any public custom relay (http/https, any port, private addresses excluded) instead of requiring per-endpoint registration, and gallery images are back to one-year immutable caching instead of revalidating on every visit.
- Generation failures no longer degrade silently: the layered fallbacks that switched API protocols or dropped reference images are gone. One known compatibility retry (the alternate image field name) remains; everything else surfaces as an error.
- Removed stale trilingual dictionary entries, dead styles from retired UI, and outdated copy; rewrote the three READMEs.

### 2026-11-24 · v1.3.0

- Click a pose card’s ID to flip between its line drawing and depth map at the same camera angle. Copying a single or mixed prompt includes image links for the selected views.
- Keep the floating studio open while browsing, switching collections and adding references. The full studio groups portraits, outfits and poses first, with other materials in one section. Edited prompts, image count and aspect ratio survive a refresh.
- Choose Simplified Chinese, English or Japanese, and use the touch controls to pick references on a phone. Appearance can follow the system or use light or dark mode.
- Connect the local studio to ComfyUI or stable-diffusion.cpp. The included ComfyUI workflow accepts one reference image. Custom workflows can use multiple images. The read-only MCP server and reference selection skill let agents search the gallery, choose views and assemble prompts.

### 2026-11-23 · v1.2.1

- The combo tray is now a persistent floating "Image Workbench": a floating button (with a selected-count badge) opens it from anywhere; you can add materials (outfits, anime outfits, poses, portraits, expressions) right inside the panel via the picker, with a clear empty state to get started.
- Added `AGENTS.md` (developer handover manual) and `scripts/sync-r2.py` (R2 image sync) so the repo can be handed over wholesale.

### 2026-11-23 · v1.2.0

- The combo tray now generates images directly: pick outfits, poses, portraits and expressions in the galleries, then generate right inside the tray (editable prompt, count and aspect ratio). Results open full-size, download, and are saved to the generation history automatically — no trip to the studio required.
- Studio polish: removed the empty spacer in the right column; results scroll into view when ready.
- Site-wide copy and data corrections: anime outfits 1320 → 1760 (hero stats, meta, announcement, footer), CharaDB credited in the footer, privacy note corrected for depth-pose delivery; tray height capped with internal scrolling, announcement clamped to two lines on mobile.
- New `tests/v18-quick.js` covers the full tray generation flow.

### 2026-11-23 · v1.1.0

- Fixed every hairstyle image (and the CharaDB part of anime outfits) failing to load: the site's CSP `img-src` allowlist was missing the hotlinked origin, so browsers blocked them all. The build now collects hotlink origins from the data automatically, and `tests/check_csp.py` guards the allowlist after each build.
- READMEs (Chinese / English / Japanese) brought up to date with the current feature set.

### 2026-11-22 · History page, proxy fix, Gemini protocol for relays

- New **Generation history** page (contributed by @OrangeSAM): select-all batch download, ZIP export with prompt/parameter metadata, single-item regeneration, before/after comparison; capped at 200 entries.
- Fixed the proxy toggle being ignored for custom relays: unticked now means direct connections; the proxy allows any port for custom relays (official domains stay HTTPS-only, private addresses stay blocked).
- Custom relays gain the Gemini protocol (`models/:generateContent`, auth header switches automatically).
- Wide-screen header overlap fix (contributed by @yansiao1227).

### 2026-11-21 · Seven extension libraries, images move to R2

- Seven new tabs: expressions (95), hairstyles (122, from CharaDB, images hotlinked), historical outfits (57), scenes (64), lighting (50), props (32), furniture (41). Anime outfits absorb 440 CharaDB sets, growing to **1,760**.
- All images are now served from Cloudflare R2 (`pwimg.0vo.pro`); depth-pose images are self-hosted instead of hotlinked, which loads more reliably.
- Fixed Seedream 5.x generation failures (contributed by @COBEZE): 5.x-only parameters are now sent to 4.x models only.

### 2026-11-19 · Anime outfits library

- New **Anime outfits** tab: 1,320 anime-style outfits from COSTUME-ANIME-DB by [@giaaibusi](https://x.com/giaaibusi), in the same 8 categories as the outfit library (spring 197 / summer 237 / autumn 230 / winter 232 / lingerie 197 / party 36 / swimwear 52 / sexy 139), each with Chinese and English prompts.
- Lingerie and sexy categories (336 items) are treated as adult content: hidden by default behind the 18+ toggle (984 public items).
- Anime outfits support the full outfit feature set: category / colour / item filters, search suggestions, favourites, recent views, prompt combos, bilingual detail pages and sitemap; the try-on studio can pick anime outfits directly from the garment step.
- Homepage announcement bar and anime counts added; `scripts/fetch-assets.py` gains an `anime` source (and now also fetches the outfit thumbnails it used to miss).

### 2026-10-31 · Depth poses

- New **Depth poses** tab: 288 sets / 1,439 hotlinked depth-pose images; two-person images sit behind the 18+ toggle.

<a id="ja"></a>

## 日本語

### 2026-11-25 · v1.4.0

- **作画向けプレビュービューア**：2× 拡大＆ドラッグ移動（`Z`／ダブルクリック）、左右反転（`H`）、三分割・中央赤軸構図ガイド（`G`）、グレースケール明度確認（`B`）、カラー写真からの中央重視 5 色自動パレット抽出（クリックで `#HEX` コピー）、同アングル線画 × 深度マップのリアルタイム重ね比較（`V`）を追加。
- **全画面クロッキー練習（Gesture Studio）**：絞り込み中の素材集からそのまま集中練習を開始可能。`30s / 60s / 2m / 5m` タイマー、`5 / 10 / 20 / 無制限` 枚数、チャイム音、タブ切替時のタイマー保護、反転／ガイド／明度／深度切替、終了後のクリック可能な振り返り一覧を搭載。
- **創作スタジオとナビゲーション強化**：リファレンスボードに送信番号（`1/2/3`）とアングルを表示し、「別の組み合わせ」、元に戻せる一括クリア、**高解像度ボード PNG 書き出し**に対応。どこからでも開ける `⌘K` / `Ctrl+K` コマンドパレット、衣装の色スウォッチ絞り込み、生成履歴のモード絞り込み・検索・使用参考画像サムネイルを追加。
- **ベトナム語（Tiếng Việt）UI と README を追加**（[@dung997tb](https://github.com/dung997tb) による #24 コントリビュート）：全 774 件の UI 辞書、動的フォーマット、CSS 文言、320px/390px モバイル回帰テストおよび [README.vi.md](README.vi.md) を完全対応。
- **アーキテクチャ刷新と README 全面改訂**：`src/catalog.js` への設定集約、`palette.js` / `sketch.js` / `command-palette.js` / `board-export.js` のモジュール分離とソース整形、`src/style.css` の平坦化・重複削減（−344 ブロック、`--cat-color` 統一）、`build.py` / `post.py` / `seo.py` の `exec()` 撤廃と CI ビルド／CSP テスト追加、4 言語 README と高解像度スクリーンショットを刷新。

### 2026-11-24 · v1.3.2

- 偽サイト声明を拡充：posewear.art（ログインと有料プラン付きのクローン）を追加。公式は posewear.pages.dev のみ、無料でアカウントも有料プランもありません。ログインや支払いを求める「PoseWear」はすべて偽物です。

### 2026-11-24 · v1.3.1

- v1.3.0 の2つの後退を修正：サイトプロキシは、デプロイ担当者による個別登録を必要とせず、任意の公開カスタム中継（http/https・任意ポート、プライベートアドレス除く）へ再び転送します。ギャラリー画像も、毎回再検証する方式から1年間の immutable キャッシュに戻しました。
- 生成失敗時のサイレントな縮退を廃止：「API 方式を自動で切り替えて再試行」「参照画像を落として再試行」といった多段フォールバックを削除しました。残るのは画像フィールド名の既知の互換リトライのみで、それ以外はエラーとして表示します。
- 古くなった三言語辞書の項目、廃止した UI の残留スタイル、古い文案を整理し、3言語の README を書き直しました。

### 2026-11-24 · v1.3.0

- ポーズカードの番号を押すと、同じアングルの線画と深度画像を切り替えられます。単体または組み合わせたプロンプトをコピーすると、選んだアングルの参考画像リンクも付きます。
- フローティングスタジオを開いたまま、ライブラリを切り替えて素材を追加できます。スタジオでは人物・衣装・ポーズを先頭に置き、それ以外の参考画像を「その他の素材」にまとめました。再読み込み後も編集したプロンプト、枚数、縦横比を復元できます。
- 表示言語を簡体字中国語・英語・日本語から選べます。スマートフォンではタッチ操作で素材を選択でき、外観はシステム設定・ライト・ダークから選べます。
- ローカルスタジオから ComfyUI または stable-diffusion.cpp に接続できます。付属の ComfyUI ワークフローは参考画像 1 枚用です。複数枚を使う場合はカスタムワークフローを指定できます。読み取り専用 MCP と素材選択用スキルを使うと、エージェントから素材の検索、アングルの選択、プロンプトの組み合わせができます。

### 2026-11-23 · v1.2.1

- コンボトレイが常駐の「画像生成ワークベンチ」に：フローティングボタン（選択数のバッジ付き）からいつでも開け、パネル内で素材（衣装・アニメ衣装・ポーズ・ポートレート・表情）を直接追加できます。空のときは空状態の案内が表示されます。
- 開発引き継ぎマニュアル `AGENTS.md` と R2 画像同期スクリプト `scripts/sync-r2.py` を追加し、リポジトリ全体を引き継げるようにしました。

### 2026-11-23 · v1.2.0

- コンボトレイで直接画像生成が可能に：ギャラリーで服・ポーズ・ポートレート・表情を選ぶと、トレイの中でそのまま生成できます（プロンプト編集、枚数と比率の選択に対応）。結果は拡大表示とダウンロードができ、生成履歴にも自動保存されます。
- 試着台の調整：右カラムの空白スペーサーを除去し、生成結果が自動で表示位置までスクロールするようになりました。
- サイト全体の文案とデータを修正：アニメ服の点数を 1320 → 1760 に統一（統計・meta・お知らせ・フッター）、フッターに CharaDB のクレジットを追加、プライバシー説明の深度ポーズ配信方式を修正。トレイに高さ上限を追加し、モバイルのお知らせを 2 行に制限。
- トレイ生成フロー全体をカバーする `tests/v18-quick.js` を追加。

### 2026-11-23 · v1.1.0

- ヘアスタイルの全画像（およびアニメ服の CharaDB 分）が読み込めなかった問題を修正：サイトの CSP の `img-src` 許可リストにホットリンク先のオリジンが欠けており、ブラウザがすべてブロックしていました。ビルド時にデータからホットリンクのオリジンを自動収集して許可リストへ書き込むようになり、`tests/check_csp.py` がビルド後に検証します。
- README（中国語／英語／日本語）を現在の機能に合わせて更新。

### 2026-11-22 · 生成履歴ページ、プロキシ修正、リレーの Gemini プロトコル

- 新しい **生成履歴** ページ（@OrangeSAM によるコントリビュート）：全選択の一括ダウンロード、プロンプト／パラメータのメタデータ付き ZIP エクスポート、1 件ごとの再生成、元写真とのビフォーアフター比較。上限 200 件。
- カスタムリレーでプロキシのトグルが効かなかった問題を修正：オフの場合は直接接続に。プロキシはリレーの任意ポートを許可（公式ドメインは HTTPS のみ、プライベートアドレスは引き続きブロック）。
- カスタムリレーに Gemini プロトコル（`models/:generateContent`、認証ヘッダーは自動切替）を追加。
- ワイド画面でヘッダーが重なる問題を修正（@yansiao1227 によるコントリビュート）。

### 2026-11-21 · 7 つの拡張ライブラリ、画像を R2 へ移行

- 新しいタブ 7 つ：表情 95、ヘアスタイル 122（CharaDB、画像はホットリンク）、歴史服装 57、シーン 64、ライティング 50、小道具 32、家具 41。アニメ服に CharaDB の 440 点が加わり、合計 **1,760 点**に。
- 全画像の配信を Cloudflare R2（`pwimg.0vo.pro`）に移行。深度ポーズ画像はホットリンクをやめて自前ホスティングにし、読み込みが安定しました。
- Seedream 5.x で生成が失敗する問題を修正（@COBEZE によるコントリビュート）：5.x 向けパラメータは 4.x モデルにのみ送るようになりました。

### 2026-11-19 · アニメ服ライブラリ

- 新しい **アニメ服** タブ：[@giaaibusi](https://x.com/giaaibusi) による COSTUME-ANIME-DB から 1,320 点のアニメ風の服装を、服装ライブラリと同じ 8 カテゴリー（春 197 / 夏 237 / 秋 230 / 冬 232 / ランジェリー 197 / パーティー 36 / 水着 52 / セクシー 139）で収録。それぞれ中国語と英語のプロンプト付き。
- ランジェリーとセクシーのカテゴリー（336 点）はアダルトコンテンツとして扱われ、既定では 18+ トグルの背後に隠されています（公開アイテムは 984 点）。
- アニメ服は服装の全機能に対応：カテゴリー／色／アイテムのフィルター、検索候補、お気に入り、最近の閲覧、プロンプトの組み合わせ、バイリンガルの詳細ページとサイトマップ。試着スタジオでは、衣装のステップからアニメ服を直接選べます。
- ホームページのお知らせバーとアニメの点数を追加。`scripts/fetch-assets.py` に `anime` ソースを追加（これまで取得できていなかった服装のサムネイルも取得するようになりました）。

### 2026-10-31 · 深度ポーズ

- 新しい **深度ポーズ** タブ：288 セット / 1,439 点のホットリンクされた深度ポーズ画像。2 人の画像は 18+ トグルの背後にあります。
