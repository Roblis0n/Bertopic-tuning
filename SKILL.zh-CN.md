# BERTopic Tuning（中文对照版）

> 本文件是供人阅读的完整简体中文对照版。Codex 运行时只以 [SKILL.md](SKILL.md) 为规范入口；如两种语言出现差异，以英文规范为准。命令、路径、字段名、枚举值和文件名均保持原样，便于直接执行和核对。

适用于用户请求 BERTopic 调优、主题建模调参、主题多样性评估、主题语义解释、短文本或长文档主题建模、模型比较、主题稳定性或谱系、同义词、停用词、自定义/领域词典、研究可视化或可复现 BERTopic 报告的场景。

## 核心原则

从原文理解主题含义，只改进一个当前最优模型，并让证据强度与主张强度匹配。原文是判断主题身份、边界、标签、合并、拆分和晋级的权威依据。算法输出只用于诊断分流：它决定哪些内容值得阅读，而不决定主题是什么意思。

始终分开以下四层：

- **结构（structure）**：通过分析单元、嵌入、UMAP 或 HDBSCAN 改变文本分配；
- **表示（representation）**：在分配保持冻结时改变词语和标签；
- **分类体系（taxonomy）**：记录经过审阅的合并、拆分和层级关系；
- **治理（governance）**：记录证据、决策、稳定性、谱系和发布义务。

优化有效主题多样性，而不是原始主题数量、单独的 Topic Diversity、单独的连贯性或较低的 Topic `-1` 比率。

## 选择保证级别

在收集产物前，根据所需结果选择级别。

| 级别 | 适用情形 | 建模授权 | 语义审阅 | 交付 |
|---|---|---|---|---|
| `exploratory` | 用户要求试跑、检查可行性、建立基线，或在不提出研究/发布主张的情况下快速调优 | 建模请求本身即足够 | 阅读当前最优模型以及高风险主题/主题对；把暂定选择标为 `exploratory_only` | 紧凑合同、语料画像、登记表、指标、`tuning-trace.json`、`semantic-review.json`、决策报告 |
| `research` | 用户需要可辩护的比较或实质性主题解释 | 记录建模请求；只有主题侦察暴露出会改变范围的歧义时才暂停 | 阅读每个晋级阶段胜者和所有最终候选；校验最终候选的分组稳定性与缺失主题 | 探索级产物加上所选模型、主题目录、精简侦察和缺失主题证据 |
| `publication_release` | 结果将被投稿、发表、发布，或用作生产分类体系 | 完成预览和显式批准门 | 完整执行主题、主题对、覆盖、离群、谱系和审阅者审计 | 完整的可复现与可视化包 |

如果现有合同没有 `assurance_level`，把它视为旧版 `publication_release`，并发出迁移警告。绝不能静默降低旧数据包的级别。

暂定默认值只能用于探索性工作。记录其来源，保持 `permitted_for_final_selection: false`，并且绝不能用它们论证研究或发布结果。

## 根据语料选择路线

根据内容结构而不是来源标签选择路线。

| 路线 | 可观察条件 | 必须完整阅读 |
|---|---|---|
| `network-short` | 单元短、稀疏、对话化、重复、受平台形态影响或依赖上下文 | `references/network-short-text.md` |
| `long-document` | 单元包含多个主题、超出有效上下文长度，或需要从章节解释到文档 | `references/long-document.md` |
| `mixed` | 两种条件同时出现 | 阅读两个路线参考文档，并保留各路线专属证据 |

对每项建模或比较任务，完整阅读 `references/semantic-review-and-cumulative-tuning.md`。同时阅读：

- `references/diversity-evaluation.md`，用于诊断和合格比较；
- `references/study-contract-and-reporting.md`，用于各保证级别的产物；
- `references/bertopic-implementation.md`，在拟合或审阅代码时使用。

按条件阅读：

- `references/corpus-theme-reconnaissance.md`，用于研究级主题侦察和完整发布预览；
- `references/research-grade-visualization.md`，在用户请求或级别要求图形时使用；
- `references/lexicon-management-and-iteration.md`，用于同义词、停用词、自定义词或领域词典；
- `references/iteration-and-lineage.md`，用于后续快照或新语料；
- `references/scalable-corpus-reading.md`，用于无法直接通读的大规模语料的有界抽取；
- `references/academic-evidence.md` 和 `references/web-research-protocol.md`，在主张依赖当前论文、软件包或模型可用性时使用。

## 建立基线当前最优模型

1. 保留原始文本、稳定单元 ID、父文档 ID、重复组/来源组，并分开保存嵌入文本、词汇文本和展示文本。
2. 完成保证级别要求的证据门：
   - 探索级：刻画语料，并检查足够的原始证据以识别明显主题、伪主题和局限；不要强加第二次批准仪式；
   - 研究级：创建精简主题图；只有主张依赖渐进覆盖时才使用完整阅读台账；
   - 投稿/发布级：遵循 `references/publication-release-workflow.md`，并在拟合前要求显式批准预览。
3. 复制 `assets/study-contract.json`，选择保证级别，定义路线、主张范围、分析单元、最小有意义主题、分组规则、校准计划和暂定设置来源。
4. 获得授权后拟合一个透明基线。导出分配、可用时的概率、主题词、代表性/随机/边界单元、主题嵌入和 Topic `-1` 证据。
5. 在 `tuning-trace.json` 中将其登记为 `baseline_candidate_id` 和 `current_champion_id`。

不要编造操作数值。不要从其他论文或语料导入参数、阈值、候选数量、随机种子数量、样本量、审阅者数量或指标权重。如果目标语料证据不可用，记录 `pending_local_calibration`、尚未解决的估计目标、候选生成规则、校准证据和停止规则。

## 运行累积阶段

沿下面的主阶段顺序只传递一个当前最优模型：

```text
analysis_unit
→ embedding
→ umap
→ hdbscan_min_cluster_size
→ hdbscan_min_samples
→ hdbscan_selection_method
→ representation
→ taxonomy
```

每个阶段只改变一个参数族：

1. 加载当前最优模型。
2. 根据尚未解决的证据生成挑战模型。
3. 把每个挑战模型的 `champion_parent_id` 设为该当前最优模型。
4. 只改变本阶段的参数族。
5. 复用兼容的缓存嵌入、邻接图或分配。
6. 计算算法诊断。
7. 构建原文审阅队列。
8. 阅读证据并记录语义决策。
9. 只晋级一个合格挑战模型，或者保留当前最优模型，或者暂缓。
10. 只把 `champion_after` 传入下一阶段。

被拒绝的挑战模型绝不能成为下一阶段的当前最优父模型。当证据不足以支持某阶段实验时，记录有实质内容的 `skip_reason`。

对于 `representation`，证明分配指纹和主题身份指纹未改变。如果分配发生变化，把该候选重新归类为结构变更。

校验链条：

```text
python scripts/validate_tuning_trace.py <tuning-trace.json> <experiment-registry.csv>
```

## 在判断含义前阅读原文

使用 `evaluate_diversity.py`、词汇重叠、语义最近邻、置信度、Topic `-1` 和稳定性失败来创建审阅队列。绝不能让这些工具给出合并、拆分、标签、伪主题分类或晋级结论。

构建可移植队列：

```text
python scripts/build_semantic_review_queue.py \
  --topics <topics.json> \
  --units <units.csv> \
  --assignments <assignments.csv> \
  --scorecard <scorecard.json> \
  --candidate-id <candidate-id> \
  --route <network-short|long-document|mixed> \
  --output <semantic-review-queue.json>
```

对每张主题卡，阅读已登记的原始文本/展示文本，并写出：

- 对象；
- 主张、行动或功能；
- 语境；
- 立场或视角；
- 定义和标签；
- 纳入与排除规则；
- 反证；
- 边界清晰度和伪主题状态。

对每个进入队列的主题对，比较两侧原始证据，并且只在写明含义差异后作出选择。允许的关系是 `distinct`、`overlapping`、`parent_child`、`merge_candidate`、`split_signal`、`artifact` 和 `uncertain`。

高余弦相似度仍可能代表不同对象、阶段或功能。低词汇重叠仍可能表达相同含义。当算法证据与语义证据冲突时，保留当前最优模型并解决含义不确定性。

## 比较合格候选

按以下顺序执行：

```text
semantic eligibility
→ locally justified hard constraints
→ Pareto or champion-relative diagnostics
→ original-text promotion decision
```

只有在仍有多个语义合格的研究级/发布级候选时才运行 Pareto：

```text
python scripts/select_pareto.py \
  --input <candidate-metrics.csv> \
  --output <pareto.json> \
  --require-field semantic_review_status=pass \
  --champion-id <current-champion> \
  --maximize <registered-objective> \
  --constraint <registered-constraint>
```

Pareto 输出和相对当前最优模型的差值都不能使模型自动晋级。在经验结果打平时保留更简单的当前最优模型，除非原文证据支持变更。

## 确认范围受限的交互

完成主路径后，检查尚未解决的诊断是否存在参数交互。只有存在具名诊断触发器时才运行 `interaction_confirmation`。

- 指明允许改变的参数族。
- 生成能够回答该未解决交互的候选。
- 说明范围受限的候选生成规则和停止规则。
- 把交互前的当前最优模型保留为回滚点。
- 晋级前再次阅读原文。

绝不能把这一步变成笛卡尔网格、穷举扫描或可复用的多参数族搜索。

## 校验最终候选

- 重新检查含义、缺失主题、伪主题和 Topic `-1`。
- 使用分组安全重采样：短文本依赖组始终在一起；长文档分块始终与父文档在一起。
- 对长文档，在父文档层面解释分块支持，并区分单文档内重复与跨文档支持。
- 比较匹配的主题数、已声明区间或等价层级。
- 保留最强反证和尚未解决的局限。

## 按保证级别交付

始终校验研究包：

```text
python scripts/validate_study_bundle.py <study-bundle-directory>
```

对于投稿/发布，还要校验完整的主题侦察和可视化包：

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
python scripts/validate_visualization_bundle.py <study-bundle-directory>
```

决策报告开头依次写明：

1. 保证级别、路线和最终当前最优模型；
2. 各阶段的晋级、保留、暂缓和回滚；
3. 实质性含义变化和尚未解决的边界；
4. 范围受限的交互结果；
5. 最终候选的稳定性、覆盖和反证；
6. 支撑性的数值诊断；
7. 仅列出所选保证级别要求的产物和图形。

不要在探索级或研究级报告中保留空的发布专用标题。不要把表示刷新描述为结构模型。不要声称主题数、连贯性、多样性、相似度或离群率证明了主题含义正确。
