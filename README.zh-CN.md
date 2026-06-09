# Claude Code + Codex 项目规则套件

[English](./README.md) | 简体中文

这个仓库是一套可复用的项目模板，适用于由 Claude Code 和 Codex 共同协作的项目。

它的设计目标不是再堆出一本更厚的项目百科，而是让不同的智能体遵循同一套协作约定：动手前先核实当下的事实，并把功能、逻辑、UI、数据和文档这几条链路都做成闭环。

## 这套套件做什么

它给 Claude Code 和 Codex 提供了一套共用的「项目操作系统」：

- 一个简短的共享入口：`AGENTS.md`。
- 一个 Claude Code 专用入口，导入同一套协作约定：`CLAUDE.md`。
- 放在 `.agent/` 下的共享项目规则。
- Codex 与 Claude Code 的技能、钩子，会在合适的时机加载这些共享规则。
- 一组脚本，负责安装、引导扫描（bootstrap）、校验、检测漂移，并生成规则维护的候选项。

核心思路是这样：

```text
智能体在某个项目里启动
  -> 安装 Rules
  -> 扫描当前仓库里的证据
  -> 把通用规则适配成经过核实的项目规则
  -> 用这些规则做开发、评审
  -> 当项目里长期有效的事实发生变化时，更新规则
```

规则应当从核实过的证据里长出来，而不是只凭旧文档、记忆或文件名。

## 目录结构

```text
templates/project/
  AGENTS.md                 Codex 等智能体的共享入口
  CLAUDE.md                 导入 AGENTS.md 的 Claude Code 入口
  .agent/                   共享项目协议与质量标准
  .agents/skills/           加载共享 .agent 协议的 Codex 技能
  .claude/skills/           加载共享 .agent 协议的 Claude Code 技能
  .claude/agents/           Claude Code 子智能体模板
  .claude/hooks/            Claude Code 钩子脚本（生命周期提醒、护栏）
  .codex/hooks/             Codex 钩子脚本（生命周期提醒、护栏）
  .codex/hooks.example.json Codex 钩子示例
  .claude/settings.example.json Claude Code 钩子、设置示例
```

## 各文件的职责

| 路径 | 作用 | 使用者 |
| --- | --- | --- |
| `AGENTS.md` | 简短的项目共享入口，定义事实来源策略。 | Codex、经 `CLAUDE.md` 接入的 Claude Code、其他智能体 |
| `CLAUDE.md` | 极薄的 Claude Code 入口，只负责导入 `@AGENTS.md`。 | Claude Code |
| `.agent/index.md` | 把智能体导向对应的工作流、领域文档。 | 两个智能体 |
| `.agent/source-of-truth.md` | 定义什么算证据、什么必须重新核实。 | 两个智能体 |
| `.agent/adaptation-review.md` | 说明已安装的规则还停留在通用状态，还是已经适配到本项目。 | 两个智能体 |
| `.agent/product-invariants.md` | 后续工作都应守住的产品长期承诺。 | 两个智能体 |
| `.agent/user-journeys.md` | 主要的用户路径，以及预期要走通的闭环。 | 两个智能体 |
| `.agent/domains/*` | 针对 UI/文案、数据/同步、构建/测试、发布、本地化、性能这些领域的专项规则。 | 两个智能体 |
| `.agent/command-contract.md` | 已核实的命令，加上生成的命令候选。 | 两个智能体 |
| `.agent/drift-map.yml` | 把改动的代码路径映射到可能需要复查的文档。 | 漂移脚本与智能体 |
| `.agent/rule-candidates.md` | 「自动生长」的收件箱：脚本投递候选，智能体决定取舍。 | 两个智能体 |
| `.agent/project-map.md` | 根据当前仓库文件、配置生成的地图。它是线索，不是最终事实。 | 两个智能体 |
| `.agent/bootstrap-report.md` | 生成的引导扫描摘要、旧规则线索，以及待适配的 TODO。 | 两个智能体 |
| `.agents/skills/*` | 封装并加载 `.agent` 工作流的 Codex 技能。 | Codex |
| `.claude/skills/*`、`.claude/agents/*`、`.claude/hooks/*` | Claude Code 专用的加载器与提醒。 | Claude Code |
| `.codex/hooks.example.json` | 可选的 Codex 钩子配置示例。 | Codex |
| `scripts/bootstrap-project-context.py` | 扫描仓库证据，刷新生成的地图与候选项。 | 智能体 |
| `scripts/check-doc-drift.py` | 报告代码改动后可能需要复查的文档。 | 智能体、钩子 |
| `scripts/suggest-rule-updates.py` | 从 diff、命令候选、旧备份和风险信号里生成规则候选。 | 智能体、钩子 |

## 推荐的「智能体优先」流程

别把一条直接的 shell 安装命令当成完整的项目配置。理想的流程是：

1. 在目标项目里启动 Claude Code 或 Codex。
2. 给智能体下达这样的指令：

   > 为这个项目安装并适配 `/Users/ct/code/Rules`。
   > 如果项目里已经有 `AGENTS.md` 或 `CLAUDE.md`，先备份。
   > 旧规则、Claude 记忆、Codex 记忆、交接记录和历史总结都只是线索，不是事实。
   > 只把能从当前代码、配置、测试、文档或工具输出中核实的事实写入 `.agent/*`。
   > 无法核实或高风险的事实标成 `needs-user`；普通候选项不要回头问用户。
   > 把 `.agent/adaptation-review.md` 标记为 adapted，并通过严格校验。

3. 智能体执行：

```bash
/Users/ct/code/Rules/scripts/agent-install-rules.sh --target /path/to/project
```

4. 智能体按 `.agent/workflows/adapt-rules.md` 操作：阅读当前代码、配置、文档，复查可能存在的旧备份，把核实过的项目事实写进 `.agent/*`。
5. 智能体运行 `python3 scripts/suggest-rule-updates.py`，并对 `.agent/rule-candidates.md` 里的每一条候选给出处置：采纳、确认未变、拒绝，或标为 `needs-user`。
6. 智能体把 `.agent/adaptation-review.md` 标记为 `Status: adapted`。
7. 智能体做最终校验：

```bash
/Users/ct/code/Rules/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

如果项目里已经有一套智能体规则，使用：

```bash
/Users/ct/code/Rules/scripts/agent-install-rules.sh --target /path/to/project --force
```

旧规则文件会被备份到 `.rules-kit/backups/rules-install-<timestamp>/`，并且在适配时必须当作线索来读。

## 常见用法

### 全新项目

在新项目里启动 Claude Code 或 Codex，把上面推荐的指令交给智能体。

预期结果：

- 规则被安装好。
- 引导扫描扫过了当前仓库。
- 智能体依据真实的代码、配置适配 `.agent/*`。
- 严格校验通过。
- 后续的智能体可以直接从 `AGENTS.md` 起步，而不必从零重新摸清项目。

### 已有旧规则的项目

在前面那条面向智能体的安装命令后加上 `--force` 即可。

预期结果：

- 旧的 `AGENTS.md`、`CLAUDE.md`、`.agent`、`.agents`、`.claude`、`.codex` 等路径被移入 `.rules-kit/backups/`。
- 旧规则被当作线索来复查。
- 核实过、长期有效的事实被写入新的 `.agent/*`。
- 过时、矛盾或无法证实的旧事实被拒绝，或写进 `needs-user`。

当旧的 Claude/Codex 记忆或旧项目文档可能有误时，这是安全的路径。

### 日常功能开发

做普通的实现或评审时，智能体应当：

1. 读 `AGENTS.md`。
2. 打开 `.agent/index.md`。
3. 只加载相关的工作流、领域文档。
4. 改动前先查看当前的代码、配置、测试。
5. 运行 `.agent/command-contract.md` 里对应的校验命令。
6. 在收尾非琐碎的工作前，跑一遍漂移检查和规则候选检查。
7. 只有当改动确实产生或改变了长期有效的项目知识时，才更新 `.agent/*`。

举个例子：如果某个功能改变了同步里的删除行为，智能体应当先查看真实的同步、数据代码，完成实现并验证，然后再判断 `.agent/domains/data-sync.md` 或 `.agent/user-journeys.md` 是否需要更新规则。

### Claude Code 与 Codex 的交接

两个智能体不需要共享各自的私有记忆，也能保持一致。

它们通过仓库里可见的文件来对齐：

- `AGENTS.md` 和 `CLAUDE.md` 负责入口。
- `.agent/*` 负责长期有效的项目事实。
- `.agent/work/*` 负责可选的交接笔记。
- `.agent/rule-candidates.md` 负责尚未处置的规则维护决策。

如果是 Claude 实现、Codex 评审，Codex 应当查看真实的 diff 和证据；反过来 Codex 实现、Claude 接手时也一样。交接笔记表达的是意图，不是证据。

### 大型重构或项目形态变化

发生大的结构变化后，重新跑一遍引导扫描：

```bash
python3 scripts/bootstrap-project-context.py
python3 scripts/check-doc-drift.py
python3 scripts/suggest-rule-updates.py
```

然后智能体应重新核对 `.agent/project-map.md`、`.agent/command-contract.md`、`.agent/drift-map.yml` 和 `.agent/rule-candidates.md`。

### 当规则开始变得嘈杂

使用 `.agent/rule-health.md`。

规则在长期有效、确实有用时应当保留；当它过时、重复、过于具体，或导致漂移检查频繁误报时，就应当被重写、迁移或删除。

## 实际运转过程

### 1. 安装

`agent-install-rules.sh` 会调用更底层的安装器，并开启引导扫描。

它写入模板文件，把安装元数据记录到 `.agent/rules-kit.json`，在替换已有规则文件前先把它们备份（除非传入 `--no-backup`），并运行引导扫描器。

走完这一步，项目只是「装好了」，还没有适配。`.agent/adaptation-review.md` 此时应当仍是 `Status: pending`。

### 2. 引导扫描

`scripts/bootstrap-project-context.py` 扫描当前仓库的文件和配置，写出保守、可复查的线索：

- `.agent/project-map.md`：检测到的项目类型、本地化信号、路径信号、命令候选。
- `.agent/command-contract.md`：生成的命令候选，同时保留已核实的命令清单。
- `.agent/bootstrap-report.md`：检测到了什么、存在哪些旧备份、智能体必须复查什么。
- `.agent/rule-candidates.md`：规则维护的初始候选项。

引导扫描并不能证明产品意图。比如，名为 `sync.ts` 的文件只是一个「同步」信号，并不能证明产品真的具备经过验证的云同步。

### 3. 适配

Claude Code 或 Codex 按 `.agent/workflows/adapt-rules.md` 操作。

智能体查看当前的代码、配置、测试、脚本、文档、生成文件、旧备份，以及可用的工具输出，然后只把核实过、长期有效的事实写入 `.agent/*`。

典型的适配产物：

- `product-invariants.md`：产品必须守住的事实。
- `user-journeys.md`：主要用户路径，即智能体改动行为时应当做成闭环的那些路径。
- `domains/*.md`：各领域的事实与验证规则。
- `command-contract.md`：智能体实际验证过、或有意保留为候选的命令。
- `drift-map.yml`：项目专属的「路径 → 文档」归属关系，经过精简，让漂移检查有用而不嘈杂。
- `tool-policy.md`：项目用到的工具、CLI、MCP，以及设备、浏览器、数据库、远端依赖。
- `adaptation-review.md`：最终状态、已复查的证据，以及高风险的未知项。

旧的 `AGENTS.md`、`CLAUDE.md`、Claude 记忆、Codex 记忆、交接记录和历史总结都只是线索。如果一个事实无法从当前证据中核实，就不会被写进正式规则。

### 4. 校验

严格校验会检查：

- 已安装的目录结构存在。
- `CLAUDE.md` 导入了 `@AGENTS.md`。
- 必需的脚本可执行。
- `.agent/adaptation-review.md` 写着 `Status: adapted`。
- `.agent/adaptation-review.md` 里不再残留 `pending` 字段，例如 `Adapted by:` 或 `Last reviewed:`。
- 适配清单的每一项都已勾选。
- `.agent/rule-candidates.md` 里没有普通的 `Status: pending` 候选。

使用：

```bash
/Users/ct/code/Rules/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

### 5. 日常开发

适配完成后，正常开发就基于这套共享约定进行：

- 实现者先读相关的工作流、领域文档，再在改动前查看真实代码。
- 评审者查看当前的 diff、代码路径和验证证据，而不是轻信交接记录。
- 接手者从 git、文件和笔记中重建状态。
- 发布相关的工作要先用真实工具核实线上远端状态，再下任何结论。

智能体不应每次都加载所有规则文件。它应当从 `AGENTS.md` 和 `.agent/index.md` 起步，只打开当前任务需要的工作流、领域文档。

### 6. 生长

当代码改动可能影响长期有效的项目知识时，Rules 会以候选项的形式生长：

```text
代码、配置、文档发生改动
  -> check-doc-drift.py 报告可能受影响的文档
  -> suggest-rule-updates.py 写出规则候选
  -> 智能体查看证据
  -> 智能体决定：采纳、确认未变、拒绝，或标为 needs-user
```

脚本本身不会去改动正式规则。证据足够时，由智能体自主决定。只有当某个高风险事实无法证实、又与当前任务相关时，才需要让用户介入。

## 哪些是自动的

自动完成：

- 在强制安装时备份旧规则文件。
- 安装共享入口、`.agent` 协议、技能、钩子示例和辅助脚本。
- 从文件、配置中识别项目形态。
- 生成命令候选。
- 从备份里生成旧规则的复查候选。
- 从改动路径里检测可能的文档漂移。
- 生成规则维护候选。
- 校验适配与候选复查是否完成。

由智能体驱动：

- 判断哪些旧规则事实是真的。
- 在把命令写进命令契约前先验证它。
- 精简嘈杂的 `drift-map.yml` 条目。
- 把有用的候选采纳进 `.agent/*`。
- 拒绝过时或过于具体的规则。
- 把高风险、无法核实的事实标为 `needs-user`。

不会自动发生：

- 在没有真实工具的情况下证明 App Store、生产环境、计费、远端、设备、凭据或用户数据的实时状态。
- 把旧的 `AGENTS.md` / `CLAUDE.md` 原样照搬进新规则。
- 把每个被检测到的文件、或某次一次性事件都变成长期规则。
- 保证 Claude 私有记忆和 Codex 私有记忆是正确或彼此同步的。

## 会写入哪些文件

安装器会把这套共享约定和辅助脚本写进目标项目：

- `AGENTS.md`：Codex 等智能体的共享入口。
- `CLAUDE.md`：导入 `AGENTS.md` 的极薄 Claude Code 入口。
- `.agent/`：共享项目规则、工作流、领域文档、适配状态、命令契约、漂移映射和规则候选。
- `.agents/skills/`：加载共享 `.agent/` 协议的 Codex 技能。
- `.claude/skills/`、`.claude/agents/`、`.claude/hooks/`：Claude Code 专用的辅助文件。
- `.codex/`：Codex 钩子示例。
- `scripts/check-doc-drift.py`、`scripts/suggest-rule-updates.py`、`scripts/bootstrap-project-context.py`。

建议的版本控制策略：

- 提交 `AGENTS.md`、`CLAUDE.md`、`.agent/`、`.agents/`、`.codex/` 和 `scripts/`。
- 是否提交 `.rules-kit/backups/` 由各项目自行决定：它是有用的迁移证据，但可能包含过时或体积庞大的旧规则。
- 是否提交 `.claude/` 由各项目自行决定：有些团队会忽略它，因为 Claude Code 还有自己的本地私有记忆；但共享约定仍必须存在于 `.agent/`。
- `.agent/work/*` 通常保留在本地，除非团队有意共享交接笔记。

## 底层安装命令

这条更底层的命令只安装模板和可选的引导扫描候选，它本身不会把规则适配到项目。

```bash
/Users/ct/code/Rules/scripts/install-rules.sh --target /path/to/project --bootstrap
```

如果项目里已经有 `AGENTS.md`、`CLAUDE.md`、`.agent`、`.agents`、`.claude` 或 `.codex`，安装器默认拒绝覆盖。要安全替换：

```bash
/Users/ct/code/Rules/scripts/install-rules.sh --target /path/to/project --force
```

对已有项目，两个参数一起用：

```bash
/Users/ct/code/Rules/scripts/install-rules.sh --target /path/to/project --force --bootstrap
```

已有的规则文件会备份到：

```text
.rules-kit/backups/rules-install-<timestamp>/
```

底层安装之后，智能体仍需按 `.agent/workflows/adapt-rules.md` 操作，复查并定制：

- `AGENTS.md`
- `CLAUDE.md`
- `.agent/adaptation-review.md`
- `.agent/product-invariants.md`
- `.agent/user-journeys.md`
- `.agent/domains/*`
- `.agent/tool-policy.md`
- `.agent/command-contract.md` 的命令清单与生成候选
- `.agent/drift-map.yml`
- `.agent/rule-candidates.md`
- `.agent/project-map.md`
- `.agent/bootstrap-report.md`

校验一个已安装的项目：

```bash
/Users/ct/code/Rules/scripts/validate-installed-project.sh /path/to/project
```

校验一个项目是否已被智能体适配（而不仅仅是安装）：

```bash
/Users/ct/code/Rules/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

如果安装时没带 `--bootstrap`，再运行：

```bash
/Users/ct/code/Rules/scripts/bootstrap-project.sh /path/to/project
```

如果你想让交接笔记只留在本地，把下面这段加进目标项目的 `.gitignore`：

```gitignore
.agent/work/*
!.agent/work/README.md
```

## 设计理念

- Claude 私有记忆和 Codex 私有记忆只是提示，不是共享的项目事实。
- 旧的 `AGENTS.md`、`CLAUDE.md`、交接、总结和记忆都只是线索，一切以当前证据为准。
- 共享的项目规则存放在仓库里。
- 文档负责把智能体导向正确的检查；真正能证明事实的，是当前的代码、配置、测试、构建、工具和线上远端状态。
- 技能让工作流的自动加载更顺畅，但高风险的工作仍需要显式验证和工具输出。
- 钩子能拦住反复犯的错，但替代不了智能体的判断。
- 漂移检查能从改动路径中发现可能需要复查文档的地方；是否采纳、拒绝，或把高风险事实留作 `needs-user`，由智能体自主决定。
- 命令契约把已核实的校验命令集中在一处；引导扫描只刷新有明确标记的候选。
- 规则健康检查让这套套件不至于膨胀成一本嘈杂的百科。

## 漂移检查

安装进项目后，在收尾非琐碎的改动前先运行：

```bash
python3 scripts/check-doc-drift.py
python3 scripts/suggest-rule-updates.py
```

`check-doc-drift.py` 通过 `.agent/drift-map.yml` 把改动的文件映射到 `.agent` 文档，它不会自动改文档。

`suggest-rule-updates.py` 写出 `.agent/rule-candidates.md`。智能体应自主处置每一条候选：

- `promoted`（已采纳）
- `checked-unchanged`（已确认未变）
- `rejected`（已拒绝）
- `needs-user`（需用户确认）

只有当某个事实高风险、且无法从仓库或工具证据中核实时，才标 `needs-user`。不要把已完成的普通工作留下 `Status: pending` 的候选。

安装后，针对每个真实项目定制 `.agent/drift-map.yml`。默认映射有意做得比较宽泛，开箱就能派上用场，但它替代不了项目专属的路径归属。

## 可选：启用钩子

钩子文件以示例形式安装，方便项目有意识地选择启用。

要启用 Codex 钩子，复查后复制：

```bash
cp .codex/hooks.example.json .codex/hooks.json
```

要启用 Claude Code 钩子，复查后复制：

```bash
cp .claude/settings.example.json .claude/settings.json
```

只在为项目复查过钩子命令之后再这么做。钩子是提醒和护栏，替代不了真正的验证。

## 这套套件借鉴了哪些智能体工具实践

- 简短入口：`AGENTS.md` 和 `CLAUDE.md` 保持小巧。
- 渐进式披露：Claude 与 Codex 的技能只在相关时才加载任务工作流。
- 共享协议：两个智能体都读 `.agent/`，而不是各自维护一长串规则。
- 工具即证据：MCP、CLI、浏览器、设备、数据库和远端工具都被当作证据来源。
- 钩子：生命周期提醒会在智能体最容易遗忘的那一刻，把质量门禁和漂移检查推到面前。
- 记忆边界：私有记忆归个人，长期有效的共享事实归仓库。
- 命令清单：校验命令集中在 `.agent/command-contract.md`，使用前必须验证。
- 规则维护：`.agent/rule-health.md` 说明何时该精简、迁移、重写或删除规则。
