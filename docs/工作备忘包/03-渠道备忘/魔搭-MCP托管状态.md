# 魔搭 MCP 托管状态：纠偏记录

> 日期：2026-11-21
> 结论：我们此前认为「魔搭已部署成功」是误判。旧条目一直是 Local，不是 Hosted。

## 一、事实

| 条目 | ID | 状态 |
|---|---|---|
| 旧条目 | `Metaconsciousness/mcai-knowledge-mcp` | `is_hosted=false`，`DeployedUrl` 为空 |
| 新条目 | `Metaconsciousness/mcai-knowledge-mcp-remote` | `is_hosted=false`，页面显示「不可部署」 |

旧条目页面徽标一直是 **Local**，配置是 `uvx` 本地启动；它从未生成过魔搭的远程地址。

## 二、Local 与 Hosted 的区别

| 类型 | 含义 | 用户怎么用 |
|---|---|---|
| Local | 魔搭只做展示，用户在本机用 `uvx` 启动 | 需要本地 Python/uvx |
| Hosted | 魔搭实际运行服务，生成远程 URL | 客户端直接连 URL |

我们一直是 Local，不是 Hosted。

## 三、为什么之前会误判

- 看到「已收录」就以为「已部署」；
- 页面有 `uvx` 配置，看起来像托管配置；
- 没有核对 `is_hosted` / `DeployedUrl` 字段；
- 没有实际用远程 URL 连接测试过。

## 四、新条目为什么「不可部署」

页面显示：

- 服务配置解析：通过；
- 校验服务配置可用性：失败；
- 结果：不可部署。

可能是：

1. 魔搭 `uvx` 运行环境的 Python 版本不满足包要求；
2. 包安装或启动超时；
3. 账号没有托管额度/权限；
4. 平台对自定义创建的服务限制托管。

目前没有拿到具体报错，不能确定。

## 五、影响

- 魔搭渠道的真实状态是：**有 Local 展示，无远程托管**；
- 对外不能说「魔搭已托管」；
- 远程 MCP 仍以我们自己的 CloudBase 端点为准。

## 六、后续

1. 渠道台账改为「Local，非 Hosted」；
2. 对外描述不再写「魔搭托管」；
3. 若继续尝试 Hosted，先拿到「校验失败」的具体原因，再决定；
4. 新条目是否保留，待定。

## 变更记录

- 2026-11-21：建立，纠正「已部署」误判。

## 七、2026-11-21 追加：根因与最终决定

### 根因

- 校验失败的直接原因：PyPI 0.4.1 的 wheel 里只有 `mcai`、`mcai-mcp` 两个命令，没有 `mcai-knowledge`；
- 魔搭按包名执行 `mcai-knowledge`，所以启动失败；
- 把配置改成 `uvx --from mcai-knowledge==0.4.1 mcai-mcp` 后，三项校验全部通过，徽标变为 Hosted。

### 但托管仍未真正可用

- 平台生成的 Remote URL 是 `https://mcp.api-inference.modelscope.net/mcp`，没有专属 ID，实测 404；
- `operational_urls` 仍为空；
- 继续部署要绑定阿里云账号，并授予 `AliyunRAMFullAccess` 管理员权限；
- 魔搭托管的底层是阿里云函数计算（FC），免费资源也是 FC 免费额度，超出按量计费。

### 决定

- 不授予阿里云 RAM 管理员权限；
- 不接受按量计费；
- 魔搭托管停止；
- 旧条目保留 Local；新条目已于 2026-11-21 删除；
- 远程 MCP 继续使用我们自己的 CloudBase 端点。

### 教训

1. 命令名要核对构建产物里的 `entry_points.txt`，不能只看 `pyproject.toml`；
2. 校验通过 ≠ 平台有资源部署；
3. 托管底层若绑定云账号高权限，要先评估风险，不因“免费”就授权。

## 八、旧条目最终维护（2026-11-21）

- 服务描述、顶部摘要、README 均已更新为 65 术语 / 126 问答 / 273 关系 / 207 引证；
- Stdio 配置改为 `uvx --from mcai-knowledge mcai-mcp`，与 0.4.1 实际命令一致；
- 托管类型仍为「仅本地可用」；
- 远程版试点条目已删除。
