# PyPI 注册、2FA 与 API Token（逐步操作）

> 目标：拿到一个能上传包的 token，交给 `发布到PyPI.cmd` 使用。
> 全程约 10–15 分钟。建议在电脑浏览器上做，不要在手机上。

---

## 第 0 步：准备

- 一个能收邮件的邮箱（建议用常用邮箱，不要临时邮箱）；
- 密码管理器（Bitwarden / 1Password / 浏览器自带均可）；
- 手机（装认证器 App：Microsoft Authenticator、Google Authenticator、1Password 等）。

---

## 第 1 步：注册账号

1. 打开 <https://pypi.org/account/register/>；
2. 填写：

| 字段 | 提示 |
|---|---|
| Username | 会成为你的包命名空间，建议用英文+数字，如 `mcai-labs` |
| Email | 常用邮箱 |
| Password | 至少 12 位，建议密码管理器生成 |
| Confirm password | 再输一次 |

3. 勾选条款 → 点 **Create account**。

**提示**：用户名一旦注册不能改，想好再填。

---

## 第 2 步：验证邮箱

1. 去邮箱找 PyPI 发来的邮件（主题含 "Verify your email"）；
2. 点邮件里的验证链接；
3. 页面显示验证成功。

**提示**：
- 没收到就查垃圾邮件；
- 没验证邮箱**不能生成 token**，这一步必须做。

---

## 第 3 步：开启 2FA（强制）

> PyPI 现在要求所有上传者必须启用 2FA，不开启无法创建 token。

1. 登录后打开 <https://pypi.org/manage/account/>；
2. 找到 **Two-factor authentication** 区块；
3. 点 **Add 2FA**（或 "Set up 2FA"）；
4. 选择方式：

| 方式 | 适合 | 说明 |
|---|---|---|
| **Authenticator app（TOTP）** | 大多数人 | 用手机 App 扫码，最省事 |
| Security device（WebAuthn） | 有硬件密钥 | 需要 YubiKey 等 |

5. 选 **Authenticator app**：
   - 页面出现二维码；
   - 用认证器 App 扫码；
   - 输入 App 显示的 6 位数字；
   - 点确认。
6. **保存恢复码**：页面会显示一组一次性恢复码，抄到密码管理器里。
   （手机丢了、App 没了，只能靠它。）

**提示**：
- 二维码只显示一次，扫完再关；
- 恢复码不要截图发群里。

---

## 第 4 步：生成 API Token

1. 打开 <https://pypi.org/manage/account/token/>；
2. 点 **Add API token**；
3. 填写：

| 字段 | 填什么 | 说明 |
|---|---|---|
| Token name | `mcai-upload` | 随便起，方便以后识别 |
| Scope | **Entire account (all projects)** | 第一次必须选这个，因为项目还不存在 |

4. 点 **Create token**；
5. 页面显示一串以 `pypi-` 开头的长字符串——**只显示这一次**；
6. 立刻复制，存进密码管理器。

**提示**：
- 不要关页面再回来找，找不回来，只能重新生成；
- 复制时注意别漏掉开头 `pypi-` 或结尾字符；
- 不要把 token 贴到聊天、代码、Git 仓库里。

---

## 第 5 步：把 token 交给发布脚本

1. 双击 `发布到TestPyPI.cmd`（演练）或 `发布到PyPI.cmd`（正式）；
2. 窗口提示：

```
请粘贴 PyPI API Token（输入不显示，回车确认）：
```

3. 右键粘贴（或 Ctrl+V），**屏幕不会显示任何字符**，这是正常的；
4. 按回车。

脚本会自动上传，成功会打印：

```
✅ 上传完成
```

**提示**：
- 粘贴后看不到内容，别以为没粘上；
- 如果报 `Invalid or non-existent authentication information`，多半是 token 复制不全或已撤销，重新生成一个。

---

## 第 6 步：发布后收紧权限（推荐）

首次上传成功后，项目就存在了：

1. 回到 <https://pypi.org/manage/account/token/>；
2. 删掉刚才那个 **Entire account** token；
3. 新建一个 **Project: mcai-knowledge** 范围的 token；
4. 以后发布只用这个。

这样即使 token 泄露，也只能动这一个项目。

---

## 附：TestPyPI（可选演练）

TestPyPI 是独立站点，账号和 token 都要单独注册：

1. <https://test.pypi.org/account/register/> 注册；
2. 同样验证邮箱、开 2FA；
3. 生成 token（同样先选 Entire account）；
4. 双击 `发布到TestPyPI.cmd`，粘贴 TestPyPI 的 token。

TestPyPI 上的包不会同步到正式 PyPI，随便折腾。

---

## 常见错误对照

| 报错 | 原因 | 处理 |
|---|---|---|
| `Invalid or non-existent authentication information` | token 不完整 / 已撤销 / 用错站点 | 重新生成，确认是 pypi.org 的 token |
| `The user 'xxx' isn't allowed to upload to project` | token 范围不含该项目 | 换 Entire account 或对应项目 token |
| `File already exists` | 同版本号已上传 | 改 `pyproject.toml` 版本号，重新构建 |
| `403 Forbidden` | 未开 2FA / 邮箱未验证 | 完成第 2、3 步 |
| 一直要求 2FA 验证 | 认证器时间不对 | 校准手机时间，或用恢复码 |

---

## 安全清单

- [ ] token 只存在密码管理器里
- [ ] 不写进代码、不提交 Git、不发聊天
- [ ] 首次发布后换成项目级 token
- [ ] 恢复码已保存
- [ ] 怀疑泄露：立刻在 token 页面撤销并重建
