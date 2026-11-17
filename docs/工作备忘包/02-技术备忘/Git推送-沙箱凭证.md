# 技术备忘：沙箱环境下的 Git 推送

> 时间：2026-11-17
> 问题：在 DSH 沙箱内推送 GitHub / Gitee 时，git 的凭证助手无法工作。

## 一、现象

- `git push` 报 `schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS`；
- 改用 `http.sslBackend=openssl` 后，GitHub 报 `Recv failure: Connection was reset`；
- 使用 `manager` 或 `wincred` 助手时报：

```
sh.exe: *** fatal error - couldn't create signal pipe, Win32 error 5
error: failed to execute prompt script (exit code 66)
fatal: could not read Username
```

原因：沙箱限制进程间管道，git 无法启动凭证助手或 askpass。

## 二、可用做法

### 1. Gitee / GitHub 均可用 openssl 后端

```
git -c http.sslBackend=openssl push ...
```

（schannel 在沙箱下取不到凭证。）

### 2. 凭证从 Windows 凭据管理器读取，嵌入推送 URL

```powershell
# 用 CredRead 读取 git:https://github.com 的凭据
# 然后：
git -c http.sslBackend=openssl push https://USER:TOKEN@github.com/OWNER/REPO.git main
```

注意：

- URL 含 token，不要打印到日志；
- 推送完成后不要在 shell 历史中保留；
- 任何时候不要把 token 写进仓库文件。

### 3. 若 GitHub 连接被重置

- 属于网络问题，不是权限；
- 隔几分钟重试，或改到晚间；
- 可写成后台重试循环，成功即停。

## 三、验证

```
git rev-parse --short HEAD
git ls-remote origin refs/heads/main
git ls-remote gitee refs/heads/master
```

三者一致即同步完成。

## 四、当前状态（2026-11-17）

- 本地、GitHub `main`、Gitee `master` 均在 `266a1a7`；
- 66 个提交已推送。

## 变更记录

- 2026-11-17：建立。
