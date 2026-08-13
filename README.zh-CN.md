# BERTopic Tuning（BERTopic 调优）

[English](README.md) · [简体中文](README.zh-CN.md) · [English Skill](SKILL.md) · [中文 Skill](SKILL.zh-CN.md)

[![CI](https://github.com/Roblis0n/Bertopic-tuning/actions/workflows/validate.yml/badge.svg)](https://github.com/Roblis0n/Bertopic-tuning/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/Roblis0n/Bertopic-tuning?display_name=tag&sort=semver)](https://github.com/Roblis0n/Bertopic-tuning/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![BERTopic Tuning：语义优先的主题调优](assets/social-preview.png)

把短文本、长文档或混合语料转化为可审计的 BERTopic 当前最优模型，并让主题含义建立在原文审阅之上。

它不同于只看指标的调参方式：这个 Codex skill 只用相似度、多样性、连贯性、稳定性和 Topic `-1` 诊断来决定“哪些内容值得读”；最终由有记录的语义审阅判断主题身份、边界，以及一个受控挑战模型是否应替换当前最优模型。

## 安装

需要支持 skill 的 [Codex](https://developers.openai.com/codex/skills/)、Git，以及用于运行内置离线工具的 Python 3。请在下面两种安装范围中选择一种。每条命令都可原样用于 PowerShell、命令提示符和 POSIX shell。

安装到用户账户，使该 skill 在所有仓库中可用：

```text
python -c "import pathlib, subprocess; p=pathlib.Path.home()/'.agents'/'skills'/'bertopic-tuning'; p.parent.mkdir(parents=True, exist_ok=True); subprocess.run(['git','clone','https://github.com/Roblis0n/Bertopic-tuning.git',str(p)], check=True)"
```

或者只安装到当前仓库：

```text
python -c "import pathlib, subprocess; p=pathlib.Path('.agents/skills/bertopic-tuning'); p.parent.mkdir(parents=True, exist_ok=True); subprocess.run(['git','clone','https://github.com/Roblis0n/Bertopic-tuning.git',str(p)], check=True)"
```

Codex 会自动检测 skill 变更；只有在 skill 没有出现时才需要重启。

克隆后的仓库根目录是可安装的 skill 源，而不是独立插件根目录。要构建独立插件和确定性的发布压缩包，请在仓库外选择全新的输出路径：

```text
python -X utf8 -B scripts/build_plugin.py --output <outside-repository-path>/bertopic-tuning --archive <outside-repository-path>/bertopic-tuning.zip --codex-home <codex-home-path>
```

构建器从 Git 索引读取策略和每个源文件，只复制显式白名单；它把索引中的根目录 `SKILL.md` 逐字节投影到 `skills/bertopic-tuning/SKILL.md`，并把供人阅读的 `SKILL.zh-CN.md` 对照版放在其旁边。它会拒绝未解决的合并或符号链接索引项、不安全路径、已存在目标、错误插件名以及源树内部的目标。内置插件合同始终运行；提供 `--codex-home` 后，还会在发布任何输出前运行两个官方 Codex 校验器。CI 会在 Linux 和 Windows 上检查内置合同以及目录/ZIP 的确定性构建。

## 调用

复制下面的提示词并替换尖括号中的值：

```text
Use $bertopic-tuning to analyze <corpus-path> for <research-question> at the <exploratory|research|publication_release> assurance level. Preserve stable unit and parent-document IDs, choose the route from the corpus structure, read the required original-text evidence, tune one cumulative champion one parameter family at a time, and deliver the required semantic-review, tuning-trace, and study-bundle artifacts with limitations.
```

## 离线验证

[可执行快速示例](examples/quickstart/README.md) 不需要 BERTopic、嵌入模型下载或网络连接。在 `examples/quickstart` 中运行构建命令，会写出确定性的审阅队列：

```text
python ../../scripts/build_semantic_review_queue.py --topics inputs/topics.json --units inputs/units.csv --assignments inputs/assignments.csv --scorecard inputs/scorecard.json --candidate-id candidate-semantic-test --route network-short --output output/semantic-review-queue.json
```

已验证的提交夹具结果：

```text
topic review cards: 3
diagnostic-triggered pair reviews: 2
Topic -1 coverage reviews: 1
semantic verdict produced: false
fresh output vs. committed expected output: byte-identical
```

最后的 `false` 是有意设计：工具负责构造审阅证据，而不会假装算法已经理解主题。请按快速示例中的步骤执行干净运行和逐字节比较。

## 建模合同

该 skill 按顺序回答三个问题：

1. 这个结果能够支撑多强的主张？
2. 阅读原文后，这些主题究竟是什么意思？
3. 一项受控变更是否改善了当前最优模型？

它不会把余弦相似度、词汇重叠、连贯性、主题数、Topic Diversity 或 Topic `-1` 比率当成理解主题含义的替代品。

### 设计上发生了哪些变化

- 根据 `exploratory`、`research` 或 `publication_release` 保证级别选择审计强度。
- 算法生成审阅队列；Codex 或具名人工审阅者阅读原文并判断主题身份和边界。
- 调优过程始终向前传递一个当前最优模型。
- 每个主阶段只改变一个参数族。
- 被拒绝的变更自动回滚，因为保留的当前最优模型仍是下一阶段的父模型。
- 多参数族检查仅限最后一个由证据触发、范围受限的交互确认阶段。
- 完整的主题侦察、谱系和可视化包继续严格用于发布，而不会阻塞每一次试验。

## 保证级别

| 级别 | 预期用途 | 必需结果 |
|---|---|---|
| `exploratory` | 冒烟测试、可行性检查、早期调优 | 暂定基线或当前最优模型、紧凑语义审阅、有限主张 |
| `research` | 可辩护的模型比较和实质性主题解释 | 经过语义审阅的阶段胜者/最终候选，以及分组稳定性与覆盖证据 |
| `publication_release` | 投稿、公开发布、生产分类体系 | 完整预览批准、审计、谱系、可视化、哈希与可复现包 |

明确的建模请求足以授权探索性工作和普通研究工作。投稿/发布仍保留单独的预览与批准门。

缺少 `assurance_level` 的现有数据包在迁移前继续按旧版严格模式处理。

## 哪些工作可以自动完成

内置脚本可以：

- 解析各保证级别所需的产物；
- 计算词汇和语义诊断记分卡；
- 识别可疑主题和主题对；
- 构建可追溯的原文审阅队列；
- 过滤语义上不合格的 Pareto 候选；
- 计算相对于当前最优模型的目标差值；
- 校验单参数族候选差异；
- 校验晋级、保留、暂缓和回滚；
- 强制执行范围受限的交互确认；
- 规划并校验与保证级别匹配的可视化包；
- 校验最终研究包中的链接。

自动化永远不会给出实质性的合并、拆分、标签、伪主题或模型晋级结论。

## 哪些工作必须阅读原文

Codex 或具名人工审阅者需要阅读原始文本/展示文本，并记录：

- 主题对象、功能、语境和视角；
- 定义、标签、纳入规则和排除规则；
- 反证和边界清晰度；
- 主题对关系；
- 缺失主题和伪主题判断；
- 挑战模型应当或不应当替换当前最优模型的理由。

规范决策产物是 `semantic-review.json`。

## 当前最优模型路径

```text
baseline
→ analysis_unit
→ embedding
→ umap
→ hdbscan_min_cluster_size
→ hdbscan_min_samples
→ hdbscan_selection_method
→ representation
→ taxonomy
→ bounded interaction confirmation
```

在每个主阶段：

```text
current champion
→ one-family challengers
→ diagnostic triage
→ original-text semantic review
→ promote one, retain, or defer
→ next-stage champion
```

`tuning-trace.json` 记录完整链条。表示层变更必须保持分配指纹和主题身份指纹不变。

## 主要资产

| 产物 | 用途 |
|---|---|
| `assets/study-contract.json` | 保证级别、主张、路线、校准、语义与调优策略 |
| `assets/tuning-trace.json` | 阶段顺序、父子关系、决策、当前最优模型和交互 |
| `assets/semantic-review.json` | 基于原文的主题、主题对和覆盖判断 |
| `assets/experiment-registry.csv` | 完整候选配置与阶段身份 |
| `assets/candidate-metrics.csv` | 诊断、语义资格和当前最优模型比较 |
| `assets/selected-model.json` | 最终当前最优模型及其证据链接 |
| `assets/decision-report.md` | 与保证级别匹配的结果叙述 |

用于投稿/发布的兼容性审计表仍然可用。

## 核心命令

构建语义审阅队列：

```text
python scripts/build_semantic_review_queue.py --topics <topics.json> --units <units.csv> --assignments <assignments.csv> --scorecard <scorecard.json> --candidate-id <candidate-id> --route <network-short|long-document|mixed> --output <semantic-review-queue.json>
```

评估诊断性多样性：

```text
python scripts/evaluate_diversity.py --input <topics.json> --output <scorecard.json> --top-k <registered-k> --rbo-p <registered-p>
```

比较合格候选：

```text
python scripts/select_pareto.py --input <candidate-metrics.csv> --output <pareto.json> --require-field semantic_review_status=pass --champion-id <candidate-id> --maximize <registered-objective>
```

启用词汇资源时，编译并校验已登记的数据包：

```text
python scripts/build_lexicon_bundle.py --config <lexicon-config.json> --output <lexicon-manifest.json>
python scripts/evaluate_representation_update.py <registered-arguments>
```

校验当前最优模型链和研究包：

```text
python scripts/validate_tuning_trace.py <tuning-trace.json> <experiment-registry.csv>
python scripts/validate_study_bundle.py <study-bundle-directory>
```

投稿/发布还要运行：

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
python scripts/validate_visualization_bundle.py <study-bundle-directory>
```

## 局限

- 本仓库提供 Codex 工作流、可移植校验器和产物模板；它不是自动拟合 BERTopic 的软件包。快速示例展示的是语义审阅队列构建，而不是模型拟合。
- 主题身份、边界、标签、合并、拆分、伪主题和晋级仍需审阅已登记的原文。数值诊断不能确立语义正确性。
- 该 skill 不安装或锁定 BERTopic、嵌入模型、分词器或建模技术栈，也不提供通用阈值或参数网格。这些选择必须在目标语料环境中获得论证。
- 有界阅读可以带着已记录的残余风险结束，或形成 `interim` 结果。投稿/发布主张需要更严格的批准和数据包检查；校验器通过只能证明合同完整性，不能证明科学真理。

## 配套项目

在 BERTopic 建模前，可使用 [Research Project Builder](https://github.com/Roblis0n/research-project-builder) 完成上游研究问题界定和项目设计。两个项目保持独立，避免彼此复制工作流。

## 参考文档

始终阅读：

- [`references/semantic-review-and-cumulative-tuning.md`](references/semantic-review-and-cumulative-tuning.md)；
- 所选路线对应的参考文档：[`network-short-text.md`](references/network-short-text.md)、[`long-document.md`](references/long-document.md)，或在 `mixed` 路线下两者都读；
- [`references/diversity-evaluation.md`](references/diversity-evaluation.md)；
- [`references/study-contract-and-reporting.md`](references/study-contract-and-reporting.md)。

仅在 `publication_release` 下阅读 [`references/publication-release-workflow.md`](references/publication-release-workflow.md)。

## 校验

运行：

```text
python -X utf8 -B -m unittest discover -s scripts/tests -v
```

测试套件覆盖旧版严格行为、三个保证级别、语义队列、当前最优模型链、选择完整性、路线证据、可视化完整性、词汇迭代、主题侦察和文档合同。完整发布记录见[更新日志](CHANGELOG.md)。
