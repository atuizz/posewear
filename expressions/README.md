# 衣姿 PoseWear 表情参考库 v0.2.0

面向 AI 生图的标准化表情参考：同一颗中性、无发、无纹理的灰色人头，统一机位/比例/光照/命名，每个表情×角度单独一张图，提供 **深度图** 与 **MediaPipe 风格线稿**（可直接用于 CrucibleAI/ControlNetMediaPipeFace）。

## 目录
```
general/   通用包（24 个表情）
adult/     18+ 包（12 个表情，仅面部形变，无身体），标签含 18+ / adult
  source/<id>.png      灰模渲染（平涂灰 Lambert，浅灰背景）
  depth/<id>.png       8-bit 深度图，白=近，黑=背景
  depth16/<id>.png     16-bit 深度图（同一归一化）
  landmarks/<id>.png   线稿（黑底，ControlNetMediaPipeFace 配色，2px）
  contact_sheets/<angle>_{source,depth,landmarks}.png  按角度分组的联系表
  manifest.json
  THIRD_PARTY_LICENSES.txt
tools/     渲染脚本与表情定义
```
id 规则：`<表情>_<角度>`，角度 ∈ front / three_quarter（朝观者左转 40°）/ side（朝观者左 90°）/ high（俯拍 30°）/ low（仰拍 25°）。

## 规格
- 900×1200（3:4），85mm 等效镜头，相机距离固定，相机与灯光固定，旋转的是头部。
- 深度：Cycles Z 通道；按头部包围球统一 near/far（见 manifest.spec.depth），所有图可直接比较；反相为白=近。
- 线稿：固定 ICT 顶点（Multi-PIE 68 点 + 额头弧线）映射为 MediaPipe 轮廓组（脸轮廓、眉、眼、内外唇、瞳孔点），按深度做遮挡剔除；闭眼只画一条眼睑线，不画瞳孔。
- 模型：ICT-FaceKit Light `generic_neutral_mesh`（平均脸，identity 系数全 0，未读取/导出任何 identity 形状），53 个 ARKit 式 blendshape 驱动；隐藏睫毛/泪液等，眼球与牙齿保留为灰色几何。
- 自定义参数：`eyeRollUp`（眼球上翻）、`tongueOut`（原模型无舌头 blendshape，用简易灰色舌形代替）。

## 新增表情（一条命令）
1. 在 `tools/expressions.json` 的 `general` 或 `adult` 数组追加：
```json
{"id":"grin","name_zh":"咧嘴笑","name_en":"Grin","tags":["开心","露齿"],
 "prompt_zh":"咧嘴笑","prompt_en":"wide grin","weights":{"mouthSmile":1,"mouthStretch":0.4}}
```
   权重名不带 _L/_R 时左右对称；标签不要写角度词。
2. 运行：`python3 tools/build.py --only grin`（可加 `--angles front,three_quarter`、`--force`）。manifest 与联系表会自动重建。
依赖：Blender 4.2（默认 /workspace/blender/blender，可用环境变量 BLENDER 指定）、ICT-FaceKit 仓库（环境变量 ICT_FACEKIT）、Python3 + numpy + Pillow。

## 许可与署名
上游：ICT-FaceKit（MIT），https://github.com/ICT-VGL/ICT-FaceKit ，commit `da5f95a607f5e6b37755b38d3385d7f2853732e5`。
本产品部分面部表情基于 ICT-FaceKit（ICT Face Model Light）生成，https://github.com/ICT-VGL/ICT-FaceKit 。Copyright (c) 2020 USC Institute for Creative Technologies。依 MIT 许可使用。完整许可见各包 THIRD_PARTY_LICENSES.txt。
