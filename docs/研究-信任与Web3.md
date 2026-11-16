# 研究：信任方向与 Web3 的关系

> 时间：2026-11-16
> 问题：Web3 与「信任」方向迟早有关联——这个直觉对不对？关联怎么产生？

## 一、先拆「信任」

信任不是一个东西，是四层：

| 层 | 回答的问题 | 谁在做 |
|---|---|---|
| 身份 | 这个 Agent / 人是谁 | ERC-8004、DID、零信任框架 |
| 来源 | 内容从哪来、有没有被改 | C2PA、哈希锚定、Arweave |
| 验证 | 内容对不对、和原文一致吗 | **我们的核验器** |
| 结算 | 用了要不要付、付给谁 | x402、智能合约 |

**Web3 覆盖第 1、2、4 层，不覆盖第 3 层。**

第 3 层才是「内容可不可信」的核心，也是我们唯一有积累的地方。

## 二、文献与行业现状

### 1. ERC-8004：Agent 的信任层

来源：[ERC-8004: Trustless Agents](https://eips.ethereum.org/EIPS/eip-8004)

- 三个链上注册表：身份（Identity）、声誉（Reputation）、验证（Validation）；
- 作者来自 MetaMask、Coinbase、Google；
- 目标是让 Agent 在跨组织交易时能判断对方是否可信。

**但**：2026 年的实证研究 [Can Trustless Agents Be Trusted?](https://www.roboticscenter.ai/research/papers/can-trustless-agents-be-trusted-an-empirical-study-of-the-erc-8004-decentralized-ai-agent-2606) 专门检验「链上记录是否真的能作为信任依据」，说明这个方向仍未被证明。

### 2. x402：Agent 支付

来源：[x402 FAQ](https://docs.x402.org/faq)

- 把 HTTP 402 变成链上支付层；
- 面向 API、网站、自主 Agent，按次付费；
- Apache-2.0，Coinbase 发起。

判断：**结算层在成型**，但前提是「有值得付费的调用」。

### 3. C2PA：内容来源凭证

来源：[IPTC 对 C2PA 的说明](https://iptc.org/std/guidelines/media-provenance/C2PA-FAQs/IPTC-C2PA-FAQs-v1.0-2027-07-08.pdf)

- 机器可读的内容来源声明；
- 微软 Azure OpenAI 生成的图片自带 Content Credentials；
- TikTok 已按 C2PA 元数据自动标注 AI 内容；
- 对应 EU AI Act 的透明度要求。

判断：**内容溯源的主战场在 C2PA，不在公链。**

### 4. 学术侧

- [零信任身份框架 for Agentic AI](https://xplorestaging.ieee.org/document/11486517)：传统 IAM 不适配 Agent，需要去中心化身份与细粒度授权；
- [ZKPoFL](https://ieeexplore.ieee.org/document/11581738)：用零知识证明确保联邦学习的训练数据来源可信；
- [Nature：区块链可能让 AI 更合乎伦理](https://www.nature.com/articles/d44148-025-00154-w)：用链追踪训练数据来源。

判断：学术在解决「来源可证」，但离产品化还有距离。

## 三、评估你的直觉

**方向对，层次要分清。**

- 对的部分：Web3 确实提供「不依赖中心机构的证明」，这正是信任基础设施的一部分；
- 要修正的部分：Web3 证明的是「没被改、是谁签的」，**不证明「内容是真的、对的」**；
- 所以关联不是「上链就有信任」，而是：

> **我们的核验器负责「对不对」，Web3 负责「这份核验结果没被改、能公开验证」。**

两者是「内容层 + 证明层」的关系，不是替代关系。

## 四、五种可能的产品形态

### A. 签名核验报告（最可行）

- 每次核验输出一份报告：内容哈希 + 时间 + 签名；
- 第三方可验证「这份报告确实由我们出具、未被修改」；
- 不需要上链，先做密码学签名；
- 成本：几天；风险：低。

### B. 知识包质量凭证

- 把评测分数、核验结果签成一份凭证；
- 采购方可以验证「这个知识包确实通过了某标准」；
- 与 C2PA 思路一致，但对象是知识包。

### C. Agent 核验凭证（与 ERC-8004 兼容）

- Agent 调用外部知识时，附带「来源已核验」的凭证；
- 未来可注册到 ERC-8004 的 Validation 注册表；
- 现在只做格式兼容，不上链。

### D. 按次核验 + 微支付（x402）

- Agent 每次核验付极小费用；
- 前提：核验本身成为高频动作；
- 现在不做，等调用量。

### E. 文本指纹登记（长期）

- 给每份原文一个指纹，登记「某版本在某时间存在」；
- 类似 DOI，但面向任意文本；
- 依赖机构合作，长期。

## 五、顺序（按序生）

```
A 签名报告 → B 质量凭证 → C Agent 凭证 → D 微支付 → E 指纹登记
```

理由：

- A 不依赖任何外部条件，能立刻做；
- B 依赖 A 的格式；
- C 依赖 ERC-8004 成熟；
- D 依赖真实调用量；
- E 依赖机构合作。

## 六、风险

1. **品牌风险**：沾链容易被当成炒币，与我们「诚实」定位冲突；
2. **标准未定**：ERC-8004 的实证研究还在质疑其可信度；
3. **摩擦**：钱包、Gas、私钥，对出版社是负担；
4. **伪需求**：用户要的是「核对得准」，不是「链上可查」。

## 七、建议

1. **先做 A**：签名核验报告，纯密码学，不上链；
2. **格式向 C2PA / VC 靠**：以后要上链或对接标准，不用重做；
3. **Web3 作为可选层**：默认不用，客户要求审计时再加；
4. **触发条件**：出现「怎么证明这份报告没被改」的真实需求，才引入锚定。

## 八、一句话

**Web3 不是信任的来源，是信任的证明方式；先有可信的核验，再谈可验证的证明。**

## 参考

- [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004)
- [ERC-8004 实证研究](https://www.roboticscenter.ai/research/papers/can-trustless-agents-be-trusted-an-empirical-study-of-the-erc-8004-decentralized-ai-agent-2606)
- [x402](https://docs.x402.org/faq)
- [C2PA / IPTC](https://iptc.org/std/guidelines/media-provenance/C2PA-FAQs/IPTC-C2PA-FAQs-v1.0-2027-07-08.pdf)
- [零信任 Agent 身份框架](https://xplorestaging.ieee.org/document/11486517)
- [Nature：区块链与 AI 伦理](https://www.nature.com/articles/d44148-025-00154-w)

## 变更记录

- 2026-11-16：建立。
