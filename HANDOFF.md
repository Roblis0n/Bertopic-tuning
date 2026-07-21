# BERTopic Tuning 项目交接指南

更新时间：2026-07-21

适用对象：下一次 Codex 对话中的执行助手，以及后续维护本仓库的人。

## 新对话直接复制这段

```text
请先完整读取以下两个文件，再开始行动：

1. F:\Skill\Codex\.agents\skills\bertopic-tuning\HANDOFF.md
2. F:\Skill\Codex\.agents\skills\bertopic-tuning\SKILL.md

继续维护 bertopic-tuning 技能。不要重新初始化仓库，不要重新命名技能，
不要安装或使用 GitHub CLI。先检查本地状态，再根据本次具体任务读取对应
references 文件。所有 BERTopic 建模与调优以“有效主题多样性”为中心，
必须区分短网络文本与长文本两条路线，离群率只能作为诊断护栏，不能成为
单一优化目标。用户词表必须编译为可审计资源包，只作用于词法表示，并验证
刷新前后分配不变。完成修改后运行全部测试和技能验证；若修改了技能功能文件，
同时更新便携压缩包；需要发布时使用标准 git 推送到现有 origin/main。
```

如果新对话无法访问本机工作区，先提供本仓库地址：

```text
https://github.com/Roblis0n/Bertopic-tuning.git
```

## 一、项目身份与位置

| 项目 | 当前值 |
|---|---|
| 技能名称 | `bertopic-tuning` |
| GitHub 仓库 | `https://github.com/Roblis0n/Bertopic-tuning` |
| Git 远程 | `origin = https://github.com/Roblis0n/Bertopic-tuning.git` |
| 主分支 | `main`，跟踪 `origin/main` |
| 本地技能目录 | `F:\Skill\Codex\.agents\skills\bertopic-tuning` |
| 便携压缩包 | `F:\Skill\Codex\bertopic-tuning.skill.zip` |
| 开源许可证 | MIT License，版权名 `Roblis0n` |
| GitHub CLI | 不安装、不使用 |

不要再使用旧名称 `academic-bertopic-tuning`。旧目录和旧压缩包已经清理，当前唯一正式名称是 `bertopic-tuning`。

## 二、用户要求与不可偏离的原则

后续工作必须继续遵守以下要求：

1. 默认用中文交流，先给结果，再说明关键依据。
2. 不要拆成 `v1`、`v2` 等半成品；一次性把当前范围内能完成的内容做完。
3. 不问不影响结果的意见；只有缺少关键授权或关键材料时才暂停。
4. BERTopic 调优的中心目标是**有效主题多样性**，不是原始主题数量最大化。
5. 必须分别处理：
   - 短网络文本、社交媒体文本、平台文本；
   - 字数较多、可能包含多个主题的长文本。
6. 离群率只用于诊断缺失主题、来源伪影和真实噪声，不能作为主要或唯一优化目标。
7. 不从论文、教程或示例中直接复制固定参数、阈值、网格、样本数、权重或主题数。
8. 数值选择必须来自研究问题、目标语料、最小有意义主题、验证标注、经验邻域图、稳定性曲线或预先登记的校准方案。
9. 区分四个层次：结构聚类、主题表示、主题分类体系、模型治理。
10. `update_topics()`、MMR 或标签生成只改变表示，不能描述为改变了聚类结构。
11. 模型选择使用显式约束与 Pareto 前沿，不能用一个综合分数掩盖权衡。
12. 研究型结论必须保留证据、反证、失败候选、阈值依据、审计记录和主题谱系。
13. 同义词、停用词和自定义词默认只作用于 `lexical_text`；自定义词是分词/短语保护资源，不是封闭词汇白名单。
14. 词表变化必须保留内容哈希、候选审核、表示前后比较和独立词表谱系；分配改变时转入结构实验。

## 三、两条建模路线

### 1. `network-short`：短网络文本

适用条件：文本短、稀疏、口语化、重复率高、受平台格式影响，或单条文本依赖上下文。

必须重点处理：

- 完全重复与近重复文本分组；
- 转发、账号、线程、来源、时间和平台上下文；
- 模板、广告、机器人内容、网址、话题标签、表情、俚语和领域短语；
- 同主题、易混淆异主题、明显异主题语义对；
- 按重复组、线程、账号或来源进行分组验证，避免信息泄漏；
- 小簇审计，区分真实小众主题与模板、来源或语言风格伪影。

执行前完整读取：`references/network-short-text.md`。

### 2. `long-document`：长文本

适用条件：单篇文档包含多个主题、超过有效嵌入上下文，或需要从段落/章节解释整篇文档。

必须重点处理：

- 优先按自然章节、段落、话语边界或语义单元切分；
- 保留永久 `parent_document_id`、段落顺序、章节名和来源；
- 在片段层发现主题，在文档层聚合为多主题分布；
- 以父文档为重采样和验证单位，不能随机抽取同一文档的片段；
- 同时审计片段层与文档层解释；
- 在需要时比较主题层级，而不是强迫每篇长文只有一个主题。

执行前完整读取：`references/long-document.md`。

### 3. `mixed`：混合语料

先按分析单元拆分语料，分别走两条路线。只有研究问题确实要求共享主题空间时，才对两个分类体系做后续对齐。

## 四、主题多样性评估框架

候选模型至少从以下五个维度比较：

| 维度 | 核心问题 |
|---|---|
| 词汇区分度 | 排名关键词是否真正不同，而不是表面换词？ |
| 语义区分度 | 最近邻主题在语义上是否仍可清楚区分？ |
| 主题覆盖 | 已知主题、新兴主题和重要子群体是否被遗漏？ |
| 稳定性 | 主题能否在随机种子、分组重采样和新数据中保持？ |
| 人工可解释性 | 审阅者能否稳定地命名、区分并界定主题？ |

同时使用一致性和可标注性作为质量底线。主题数量比较必须在匹配主题数、预先声明的主题数区间或等价层级进行。

完整规则见：`references/diversity-evaluation.md`。

## 五、当前仓库内容

### 核心入口

- `SKILL.md`：技能核心工作流、约束与输出合同。
- `agents/openai.yaml`：Codex 界面名称、中文简介和默认提示词。
- `README.md`：GitHub 英文首页，包括安装、使用、两条路线、脚本和许可证。
- `LICENSE`：MIT License。
- `.gitignore`：Python、虚拟环境、编辑器、系统和临时文件忽略规则。

### 参考文件

- `references/network-short-text.md`：短网络文本路线。
- `references/long-document.md`：长文本切分、父文档聚合与验证路线。
- `references/diversity-evaluation.md`：多维主题多样性和 Pareto 选择。
- `references/iteration-and-lineage.md`：新语料、重训、合并、拆分与主题谱系。
- `references/bertopic-implementation.md`：BERTopic 实现和代码审查边界。
- `references/study-contract-and-reporting.md`：研究合同和报告要求。
- `references/academic-evidence.md`：学术证据地图与可迁移边界。
- `references/web-research-protocol.md`：需要联网核验时的检索和证据记录协议。
- `references/lexicon-management-and-iteration.md`：同义词、停用词、自定义词资源包及模型结果驱动的表示迭代。

### 命令行工具

- `scripts/evaluate_diversity.py`：评估词汇与语义主题多样性。
- `scripts/select_pareto.py`：按明确目标和约束筛选 Pareto 前沿。
- `scripts/align_snapshots.py`：对齐前后模型的主题快照。
- `scripts/validate_study_bundle.py`：验证研究资料包是否完整。
- `scripts/build_lexicon_bundle.py`：校验并编译用户词表资源包。
- `scripts/lexicon_tools.py`：词表规范化、短语保护、同义词归一、停用词过滤和向量器适配。
- `scripts/evaluate_representation_update.py`：验证分配不变并比较词表刷新前后的表示结果。
- `scripts/tests/test_tools.py`：上述工具与技能关键约束的单元测试。
- `scripts/tests/test_lexicon_tools.py`、`test_representation_update.py`：词表功能与端到端命令测试。

### 研究模板

`assets/` 中已经包含研究合同、语料画像、实验登记、候选指标、模型选择、主题目录、人工审计、遗漏主题审计、主题对审计、谱系、证据日志和决策报告模板，以及词表配置、同义词、停用词、自定义词、候选审核、表示迭代和词表谱系模板。

## 六、已完成事项

以下事项已经完成，后续不要重复：

- 技能已从旧名称改为 `bertopic-tuning`。
- `SKILL.md` 的 frontmatter、标题和内部引用已经同步。
- `agents/openai.yaml` 已改为 `BERTopic Tuning`，默认提示词使用 `$bertopic-tuning`。
- 已建立短网络文本和长文本两条独立路线。
- 已建立多维主题多样性、Pareto 选择和主题谱系框架。
- 六个命令行脚本、测试、参考资料和研究模板已经存在。
- 用户可编辑词表已经形成“编译校验—词法应用—冻结分配比较—候选审核—词表谱系”闭环。
- 多样性评估和主题对齐支持冻结词表下的概念归一关键词证据。
- Git 仓库已经初始化，远程 `origin` 已配置，`main` 已推送。
- GitHub 已有完整英文 README、`.gitignore` 和 MIT License。
- 当前功能测试共 47 项；最近一次验证全部通过。
- 技能结构最近一次通过 `quick_validate.py`。

## 七、下一次对话的启动顺序

下一位助手按以下顺序开始，不要跳过状态核对：

1. 完整读取本文件和 `SKILL.md`。
2. 运行 `git status -sb`，确认没有未识别的用户修改。
3. 根据任务类型只读取必要的 `references/` 文件。
4. 如果用户要求文献综述、最新论文、软件版本或模型可用性，联网核验并记录证据，不依赖记忆。
5. 如果用户提供语料，先做语料画像和路线判断，再提出模型实验。
6. 如果用户要求修改技能，保留现有设计原则，不做无关重构。
7. 完成后运行全部测试、技能验证、词表端到端示例和差异检查。
8. 功能文件发生变化时，重新生成并验证便携压缩包。
9. 只有在用户要求发布或当前任务明确延续发布流程时，才提交和推送。

## 八、验证命令

在 PowerShell 中运行：

```powershell
$repo = 'F:\Skill\Codex\.agents\skills\bertopic-tuning'

python -B -m unittest discover -s "$repo\scripts\tests" -v
python -X utf8 'D:\Codex work\.codex\skills\.system\skill-creator\scripts\quick_validate.py' $repo
git -C $repo diff --check
git -C $repo status -sb
```

完成标准：

- 单元测试没有失败或错误；
- 输出包含 `Skill is valid!`；
- `git diff --check` 没有空白错误；
- 所有修改都能解释为本次任务的一部分；
- 发布后本地 `HEAD` 与 `origin/main` 一致。

## 九、标准 Git 操作

本目录所在文件系统可能触发 Git 的 `dubious ownership` 检查。如果再次出现，执行一次：

```powershell
git config --global --add safe.directory F:/Skill/Codex/.agents/skills/bertopic-tuning
```

查看状态：

```powershell
$repo = 'F:\Skill\Codex\.agents\skills\bertopic-tuning'
git -C $repo status -sb
git -C $repo remote -v
git -C $repo diff
```

发布修改时只暂存本次涉及的文件：

```powershell
$repo = 'F:\Skill\Codex\.agents\skills\bertopic-tuning'
git -C $repo add -- <明确的文件路径>
git -C $repo diff --cached --check
git -C $repo diff --cached
git -C $repo commit -m "<简洁准确的英文提交说明>"
git -C $repo push origin main
```

不要执行以下操作：

- 不要重新运行 `git init`；
- 不要重新添加 `origin`；
- 不要安装或调用 `gh`；
- 不要使用 `git add -A` 混入无关文件；
- 不要使用 `git reset --hard` 或覆盖用户修改；
- 不要创建 `v1`、`v2` 之类的重复目录或分支来规避一次性完成。

## 十、便携压缩包

当前压缩包路径：

```text
F:\Skill\Codex\bertopic-tuning.skill.zip
```

README、许可证和本交接文件属于仓库维护资料；模型技能的功能来源是 `SKILL.md`、`agents/`、`references/`、`scripts/` 和 `assets/`。

如果这些功能文件发生变化，应重新生成压缩包，并执行以下核验：

1. 解压到临时目录；
2. 对解压后的技能目录运行 `quick_validate.py`；
3. 对解压后的 `scripts/tests` 运行全部单元测试；
4. 确认压缩包中不存在旧名称 `academic-bertopic-tuning`。

## 十一、后续工作边界

当前仓库已经是可用的技能和研究框架。以下工作只有在用户提出时才开展：

- 针对一批真实语料执行完整建模与调优；
- 扩展或更新学术文献证据矩阵；
- 增加真实 BERTopic 拟合流水线或新的评估脚本；
- 根据新数据设计模型更新、主题映射和谱系审计；
- 为特定中文领域填充和审核具体分词、短语、停用词及同义词内容；
- 修改 GitHub 仓库页面元数据或增加发布材料。

不要在没有目标语料或研究问题的情况下发明统一参数。若本地证据不足，写明 `pending_local_calibration`，同时给出需要估计的量、校准数据、候选生成规则和停止规则。

## 十二、交接完成判据

下一次对话结束前，交付说明至少包括：

1. 本次改变了什么；
2. 改变属于结构、表示、分类体系还是治理层；
3. 主题多样性的哪些维度改善、下降或仍不确定；
4. 使用了哪些目标语料证据或外部文献证据；
5. 运行了哪些验证，结果如何；
6. 修改后的文件路径；
7. 如果发布，给出提交号和 GitHub 链接。
8. 如果启用了词表功能，给出资源包 ID、分配指纹、候选审核和词表谱系路径。
