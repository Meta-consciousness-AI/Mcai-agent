# 经典语料 RDF 打包（P5，内部）

> 状态：内部资产，**未发布**。
> 时间：2026-11-14
> 命名空间：`urn:mcai:classic:{work}:`（不占用 w3id，不假装可解析）

## 一、为什么做

- 预印本声称「四语料复现」（元意识 + 道德经 + 孙子 + 荀子），但没有可机读产物；
- 打包后，这个声称可以被验证；
- 成本低，复用现有导出脚本；
- 将来项目恢复、有人问、有合作时，资产是现成的。

## 二、为什么还不发布

| 门槛 | 现状 |
|---|---|
| 质量 | 道德经 4/10 thin，孙子 1/13，荀子 9/12 |
| 版本 | 每部只有 1 个底本 |
| 署名 | 整理者未标注 |
| 受众 | 无信号 |
| 部署 | 账号卡住（需付费组织账号） |

五条没有一条达标，公开只会拉低整体可信度。

## 三、产物

```
dist_pkg/classics-rdf/
├─ daodejing.ttl / .nt    236 三元组
├─ sunzi.ttl / .nt        278 三元组
├─ xunzi.ttl / .nt        267 三元组
└─ manifest.json          计数、thin 比例、核验、sha256
```

每条 KB 都通过引文核验（`verify_ok: true`），三元组自检 0 错误。

## 四、复现

```bash
python tools/export_classics_rdf.py
```

单独导出任意工作区：

```bash
python tools/export_rdf.py --kb workspaces/sunzi/data/kb.json \
  --base urn:mcai:classic:sunzi: --out dist_pkg/demo --name sunzi
```

## 五、质量说明

- thin 定义指「定义过短，可能不足以被 AI 直接引用」；
- 荀子 9/12 thin，说明它的定义层还没做够；
- 打包不改变质量，只是把现状变成可读的 RDF。

## 六、发布门槛（以后）

1. thin 比例降到 20% 以下；
2. 至少标注底本与整理者；
3. 有多版本时接入 `edition_variants`；
4. 出现真实需求（有人问、有合作、项目恢复）；
5. 解决部署账号与备案。

## 变更记录

- 2026-11-14：建立，三库打包完成，未发布。
