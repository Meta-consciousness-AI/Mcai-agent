# 上线手册

目标：让其他机器上的 AI / Agent 能访问到这个知识库，同时不把内部数据暴露给全世界。

两条路，先试隧道，稳定后再上云主机。

---

## 路线 A：临时公网（Cloudflare 隧道，推荐先用）

适合演示、试用、给一两个合作方接入。电脑关机就断。

```powershell
# 1. 装 cloudflared（一次即可）
winget install --id Cloudflare.cloudflared

# 2. 生成令牌
python -m mcai token

# 3. 启动服务 + 隧道（会打印一个 https://xxx.trycloudflare.com）
.\deploy\cloudflared.ps1 -Port 8787 -Token <令牌>
```

复制隧道地址后，**另开一个窗口**：

```bash
python -m mcai set-url https://xxx.trycloudflare.com
python -m mcai doctor --url https://xxx.trycloudflare.com --token <令牌>
```

体检全绿之后，把这两样东西发给接入方：

- 地址：`https://xxx.trycloudflare.com/api/v1`
- 令牌：`<令牌>`

他们用一行命令就能验证：

```bash
curl -H "Authorization: Bearer <令牌>" \
  "https://xxx.trycloudflare.com/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86"
```

注意：隧道地址每次重启都变，变了要重新 `set-url` 再 `build`。

---

## 路线 B：云主机（长期在线）

适合 7×24 被调用。1 核 1G 足够，月费约 30–60 元。

```bash
# 1. 传代码
scp -r mcai-agent user@server:/opt/mcai-knowledge

# 2. 安装
cd /opt/mcai-knowledge
python3 -m pip install .
mcai init .            # 如果还没配置
mcai build

# 3. 配令牌
export MCAI_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# 4. 交给 systemd
sudo cp deploy/mcai.service /etc/systemd/system/mcai.service
sudo systemctl daemon-reload
sudo systemctl enable --now mcai
sudo systemctl status mcai
```

前面加一层 HTTPS（Nginx / Caddy 反代到 8787），然后用域名：

```bash
mcai set-url https://kb.example.com
mcai doctor --url https://kb.example.com --token <令牌>
```

---

## 上线检查清单

- [ ] `mcai build` 通过，`mcai report` 无冲突
- [ ] `mcai set-url <真实地址>` 后已重建（清单里的地址对得上）
- [ ] `mcai doctor --url <地址> --token <令牌>` 五项全绿
- [ ] 没有令牌时访问 `/api/v1/answer` 返回 401
- [ ] `/api/rebuild`、`/api/v1/stats` 从外网访问返回 403
- [ ] HTTPS 已启用（隧道自带；云主机需反代）
- [ ] 令牌只发给接入方，不写进代码仓库
- [ ] 定期看 `data/access.log` 与 `mcai stats`

---

## 常见问题

**Q：接入方说连不上。**
先在本机执行 `mcai doctor --url <地址>`。若 health 失败，检查服务是否在跑、端口是否映射；若 manifest 失败，重新 `set-url` + `build`。

**Q：地址变了怎么办？**
重新 `mcai set-url <新地址>` 并 `build`。旧地址的清单会失效，但数据库结构不变。

**Q：能不能不用令牌？**
能，但不建议。启动时若监听 `0.0.0.0` 且无令牌，程序会打印警告。没有令牌时任何人可查询，且会消耗你的调用统计。
