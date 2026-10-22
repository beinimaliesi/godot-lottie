# Lottie 动画文件格式

## 1 两种格式

| 格式 | 本质 | 内容 | 常见用途 |
|---|---|---|---|
| `.json` | JSON 文本 | 动画数据，资源可内嵌或外置 | 编辑、调试 |
| `.lottie`（dotLottie） | ZIP 压缩包 | 清单、一个或多个动画 JSON、相关资源 | 打包、分发 |

`.lottie` 中的动画仍然是 Lottie JSON，压缩主要减少存储体积，不会自动提高画质或播放性能。参见 [Lottie 格式定义](https://lottie.github.io/lottie-spec/dev/specs/format/) 和 [dotLottie 规范](https://www.dotlottie.io/spec/1.0/)。

## 2 动画文件结构

### `.json`

以下示例描述一个 512 × 512、30 FPS、时长 2 秒的动画。`layers` 为空，因此没有可见图形。

```json
{
  "v": "5.7.4",
  "nm": "loading",
  "w": 512,
  "h": 512,
  "fr": 30,
  "ip": 0,
  "op": 60,
  "assets": [],
  "layers": []
}
```

| 字段 | 含义 |
|---|---|
| `v`、`nm` | 导出版本标识、动画名称 |
| `w`、`h` | 画布宽、高 |
| `fr` | 帧率（帧/秒） |
| `ip`、`op` | 起始帧、结束边界（不包含结束帧） |
| `assets` | 图片、预合成等资源 |
| `layers` | 图层，包含形状、变换、关键帧等数据 |

正常速度下，时长为 `(op - ip) / fr` 秒。外置图片需要随 JSON 一起交付，并保持引用路径有效。参见 [Animation 文档](https://lottiefiles.github.io/lottie-docs/composition/) 和 [Assets 文档](https://lottiefiles.github.io/lottie-docs/assets/)。

### `.lottie`

以 dotLottie v1 为例：

```text
loading.lottie
├── manifest.json           # 包清单
├── animations/
│   └── loading.json        # Lottie 动画数据
└── images/                # 可选图片资源
```

`manifest.json` 登记动画，`id` 对应动画文件名：

```json
{
  "version": "1",
  "animations": [{ "id": "loading" }]
}
```

v2 使用 `"version": "2"`，动画目录改为 `a/`，图片目录改为 `i/`，还可包含 `s/`（状态机）、`t/`（主题）和 `f/`（字体）。参见 [v1 规范](https://www.dotlottie.io/spec/1.0/) 与 [v2 规范](https://www.dotlottie.io/spec/2.0/)。

本插件当前优先按 v1 的 `animations/` 结构查找动画，不能据此认为完整支持 v2。

## 3 .lottie 和 .json 相互转换

主要使用 `@dotlottie/dotlottie-js` 完成双向转换。运行以下示例请使用 Node.js 22 或 24，安装依赖：

```bash
npm install @dotlottie/dotlottie-js@1.8.1
```

### `.json` → `.lottie`

保存为 `json-to-lottie.mjs`，执行 `node json-to-lottie.mjs`。为适配本插件，使用 `DotLottieV1` 输出 v1 包：

```javascript
import { readFile, writeFile } from 'node:fs/promises';
import { DotLottieV1 } from '@dotlottie/dotlottie-js';

const data = JSON.parse(await readFile('loading.json', 'utf8'));
const archive = new DotLottieV1({ version: '1' });
archive.addAnimation({ id: 'loading', data });
await archive.build();
await writeFile('loading.lottie', Buffer.from(await archive.toArrayBuffer()), {
  flag: 'wx', // 避免覆盖已有文件
});
```

示例适用于纯矢量或资源已内嵌的 JSON。有本地外置图片时，应先将其转成 Data URI，或按库的资源加载方式处理；仅解析 JSON 不会提供本地资源的基础路径。参见 [DotLottieV1 API](https://docs.lottiefiles.com/en/tools/dotlottie-js/reference/dotlottie-v1-class)。

### `.lottie` → `.json`

保存为 `lottie-to-json.mjs`，执行 `node lottie-to-json.mjs`：

```javascript
import { readFile, writeFile } from 'node:fs/promises';
import { DotLottie } from '@dotlottie/dotlottie-js';

const bytes = await readFile('loading.lottie');
const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
const archive = await new DotLottie().fromArrayBuffer(buffer);
console.log('动画列表：', archive.animations.map((item) => item.id));

const animation = await archive.getAnimation('loading'); // 改为包内实际动画 ID
if (!animation) throw new Error('未找到指定动画');
const data = await animation.toJSON({ inlineAssets: true });
await writeFile('loading-extracted.json', JSON.stringify(data, null, 2), {
  flag: 'wx',
});
```

`DotLottie` 可读取 v1/v2 包；`inlineAssets: true` 将相关资源内嵌，便于单独交付 JSON。多动画包按 ID 分别导出，包级主题和状态机不包含在单个动画 JSON 中。参见 [DotLottie API](https://docs.lottiefiles.com/en/tools/dotlottie-js/reference/dotlottie-class)。

该库可能调整资源存储方式和 JSON 序列化结果，因此转换前后不保证字节一致。应保留源文件，并对比动画数据和播放效果。

### 踩坑：转换工具改写切线数据

曾遇到 `lottietools.online` 转换后遮罩膨胀、图形放大的情况：路径的 `i`、`o` 切线从相对顶点 `v` 的偏移被改成绝对坐标，渲染时再次加上顶点，造成几何变形。此外还出现位置关键帧 `ti`、`to` 被置为 `null`、注入 `__complete` / `_render` / `completed` 字段，以及重复内联预合成图层的问题。

[fix_lottie_tangents.py](../scripts/fix_lottie_tangents.py) 针对这类数据执行以下处理：

- 检测到 `__complete` 或 `_render` 标记后，对符合数值结构的路径执行 `i -= v`、`o -= v`。
- 清除上述运行时字段，以及带 `ty` 的对象中重复内联的 `layers`。
- 修改前生成 `<文件名>.lottie.bak`，随后原地重写包；没有标记的文件保持不变。
- 若旁边存在同名源 `.json`，输出修复结果与源文件的差异数量；差异不为零不会阻止写入。

在仓库根目录运行：

```bash
python3 -I scripts/fix_lottie_tangents.py damaged.lottie
# 支持一次传入多个文件
python3 -I scripts/fix_lottie_tangents.py first.lottie second.lottie
```

这些标记只是识别线索，不能证明所有切线都已被改写。该脚本不是通用修复器，只应用于确认符合上述损坏模式的文件。已经丢失的 `ti` / `to` 无法由脚本恢复，应从源 JSON 重新打包；修复后仍需比对源数据和实际播放效果。
