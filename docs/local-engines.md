# 在本机工作台生图

本地预览默认使用云端服务商，也可以连接本机的 ComfyUI 或 stable-diffusion.cpp。两种工作台共用同一份服务商设置。

## 用 ComfyUI 和一张参考图开始

1. 启动 ComfyUI，默认地址为 `http://127.0.0.1:8188`。从 PoseWear 仓库根目录运行 `npm ci` 和 `npm start`。
2. 打开[本地工作台](http://127.0.0.1:8787/#studio)，进入服务商设置，选择「ComfyUI」，点「测试连接」。从返回的列表中选一个已安装、兼容的 checkpoint，点击保存。
3. 在「生图」模式选一套服装，将画幅设为「自动」或选择所需比例，即可用这张图生成。也可以从悬浮工作台选择一件服装生成。

自带工作流加载你在界面上选定的 checkpoint，使用一张参考图。画幅选「自动」会沿用参考图比例，手动选比例会居中裁切到对应画幅。[查看工作流](comfyui/img2img-api.json)

### 自定义多参考图工作流

若要同时使用人物、服装与姿势，请在 ComfyUI 中连接自己的多图工作流，按下表设置节点标题，导出为 API 格式的 JSON，再重新启动 PoseWear。

```sh
POSEWEAR_LOCAL_ENGINE=comfyui \
POSEWEAR_COMFY_WORKFLOW=/absolute/path/to/workflow-api.json \
npm start
```

| 节点标题 | 工作台如何使用 |
| --- | --- |
| `PoseWear Prompt` | 把最终提示词写入该节点的 `text` 输入。 |
| `PoseWear Image 1`、`PoseWear Image 2` … | 按顺序绑定到 `LoadImage` 节点。输入顺序为人物、服装、姿势、表情、其他素材。节点数量须匹配本次生成实际传入的图片数量。 |
| `PoseWear Output` | 从这个输出节点读取一张生成图片。 |
| `PoseWear Size`（可选） | 选择指定画幅时写入 `width` 和 `height`。自动画幅使用工作流本身的尺寸设置。 |
| `PoseWear Seed`（可选） | 为该节点的 `seed` 输入写入新的随机种子。 |

取消生成会停止工作台等待，并尝试删除本次尚在队列中的任务。正在 GPU 上执行的任务可能继续完成。上传的输入和生成的文件按自己的 ComfyUI 存储策略保留。[ComfyUI 服务端路由](https://docs.comfy.org/development/comfyui-server/comms_routes)

## stable-diffusion.cpp

使用提供图片编辑接口的 `sd-server`，加载支持参考图的模型。服务默认位于 `127.0.0.1:1234`。

```sh
npm ci
POSEWEAR_LOCAL_ENGINE=sd-cpp npm start
```

工作台通过 `/v1/models` 检查连接，有参考图时把每张图作为一个 `image[]` 字段交给 `/v1/images/edits`，纯提示词则使用 `/v1/images/generations`。模型和构建版本决定可以使用的参考图数量与出图效果。[sd-server 接口文档](https://github.com/leejet/stable-diffusion.cpp/blob/master/examples/server/api.md)

### 核显参考耗时（社区实测）

在 AMD 780M 核显 + Vulkan 后端上的参考表现（来自议题 #23 实测）：

| 模型 | 分辨率 | 纯文生图 | 带 1 张参考图 |
| --- | --- | --- | --- |
| SD 1.5 | `512×768` | ~20 秒 | ~1 分钟 |
| Flux-2-Klein-4B-Q4_K_S | `1024×1024` | ~1 分钟 | ~2 分钟以上 |

在显存或内存带宽受限的本机设备上，建议优先使用**单张参考图**（尤其是深度姿势图配合提示词），比同时送入多张参考图更稳、更快。

两个引擎都可以通过 `POSEWEAR_LOCAL_URL` 指定其他回环端口。工作台通过本机预览进程把提示词和选中图片送给本机服务。首次载入公开图库仍需联网。[GitHub 议题 #23](https://github.com/atuizz/posewear/issues/23)
