# Claude Code + Codex 项目规则套件

[English](./README.md) | 简体中文

一份共享的、纯 Markdown 的「项目合同」:让任何来动你项目的智能体——Claude Code、Codex,或者你自己——都遵循同一套规则,以当前代码而不是过时文档为准,并且把活儿一次做完整,而不是只做一半。

零运行时、零依赖。本质就是给智能体读的 Markdown,外加三个小脚本。

## 它要堵的三个坑

无论是一个智能体跨越多次会话,还是好几个轮流上手,在真实项目里都会反复撞上同样三种翻车。

**坑一:每次重新开始,都把项目怎么干重新发明一遍。**
新的一次会话是「冷启动」打开仓库的:它对上一次的决定没有可靠记忆,于是只能猜约定、起不同的命名、把「事情该怎么做」重新推导一遍。下一次接手的不管是同一个智能体、另一个智能体,还是一个月后的你,都会这样——两次 Claude 会话之间的分歧,和 Claude 与 Codex 之间一样大。时间一长,代码就裂开了。
*堵法:* 把长期有效的决定写进仓库里一份大家都先读的文件(`AGENTS.md`)。下一个接手的人,从同一套标准起步,而不是从猜开始。
> 就像一个谁都不做记录的工地:每拨人来——哪怕是下周回来的同一拨——都把「活该怎么干」重新发明一遍。把一份《工地须知》钉在墙上,大家就按同一套盖。

**坑二:信了过时文档,照着错的目标动手。**
文档写「登录接口是 `/api/login`」,但代码几个月前就改成了 `/api/v2/auth`。智能体信了文档,就对着一个早已不存在的目标写代码。
*堵法:* 动手前先看当前的代码、配置、测试。真实的当下状态,优先于旧文档和记忆。

**坑三:只做半截活,就说「完成了」。**
最经典的一幕:本地能跑、不报错,交差。可数据没存、页面没显示、文档没更新——整条用户路径从头到尾根本走不通。
*堵法:* 一个改动,要等**功能、逻辑、数据、UI、文档**这几条线全部接通,才算做完。

以「给用户加一个『昵称』字段」为例:

| 链路 | 只做一半(常态) | 闭环(才算完成) |
| --- | --- | --- |
| 功能 | 加了输入框 | 加了输入框 |
| 逻辑 | 没写保存逻辑 | 提交时真能存进去 |
| 数据 | 数据库没加这列 | 加了字段,能读能写 |
| UI | 个人主页不显示 | 该显示的地方都显示了 |
| 文档 | API 文档还是旧的 | 文档同步更新 |

**一句话:** 别让每次会话各自发挥(用一份共享合同)、别信过时文档(以当前代码为准)、别只交半截活(UI → 逻辑 → 数据 → 文档全部接通才算数)。

## 它到底是什么

先把分量说清楚:这**不是框架、不是引擎、也不是运行时**。它就是一堆你拷进仓库的文件:

- `AGENTS.md`——每个智能体都先读的共享合同。
- `CLAUDE.md`——极薄的 Claude Code 入口,只负责导入 `AGENTS.md`。
- `.agent/`——一组短小的 Markdown:产品承诺、用户路径、已核实的命令、各领域规则,以及项目的「事实来源」策略。大多一开始是模板,由智能体照着你真实的代码填进去。
- 给 Claude Code 和 Codex 两边的技能、钩子桩文件,把它们指向共享的 `.agent/` 规则。
- 三个小 Python 脚本(只用标准库、**零依赖**——连解析 YAML 都是手写的,就为了不引入依赖),扫描仓库后**写出建议**。它们从不修改你的规则。

**分工才是关键:智能体是裁判,脚本只负责收集证据、标出哪些可能过时了。** 这里没有任何东西会自己做决定。

它**一个或两个智能体**都能用,而且**从第一个提交**就能用——不需要 Claude 和 Codex 都在,也不需要已有的代码库。详见[安装](#安装)。

## 快速上手

```bash
# 1. 把这套工具 clone 到机器上任意位置
git clone https://github.com/liyuhao957/agent-rules-kit.git

# 2. 在你的项目里,对智能体(Claude Code 或 Codex)说:
#    「为这个项目安装并适配 /path/to/agent-rules-kit。」
#    它会执行:
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project
```

安装器拷好文件,并扫描仓库找线索。然后由智能体阅读你真实的代码,**把模板填成核实过的事实**——这一步是智能体的活,不是脚本的。从此以后,任何智能体都从 `AGENTS.md` 起步,而不必从零重新摸清项目。

## 「适配后」长什么样

刚装完时,规则文件还是通用模板,`.agent/adaptation-review.md` 写着 `Status: pending`。智能体的任务,就是把它们变成真实、核实过的项目事实。举个例子:

```text
适配前(模板)               适配后(智能体照真实代码填好、并核实过)
─────────────              ───────────────────────────────────────
product-invariants.md       免费版上限为 3 个项目。
  <长期承诺>                注销账号后,已同步数据在 24 小时内清除。

user-journeys.md            注册 → 验证邮箱 → 创建第一个项目 → 进入仪表盘。
  <主要流程>

command-contract.md         测试:npm test       (跑过,通过)
  <已核实命令>              构建:npm run build  (跑过,成功)
```

凡是智能体**无法**从代码、测试或工具中证明的——线上计费状态、生产配置、凭据——一律不写进规则,而是放进 `.agent/adaptation-review.md` 的 `needs-user`,交给你确认。不允许靠猜。

## 代码变了,它怎么保持不过时

这是防止规则腐烂的那个唯一机制。完成一处非琐碎改动后,智能体会运行:

```bash
python3 scripts/check-doc-drift.py       # 报告这次改动可能让哪些文档过时了
python3 scripts/suggest-rule-updates.py  # 把候选写进 .agent/rule-candidates.md
```

两个脚本**只报告、只建议**。然后由智能体逐条处置每个候选:

- `promoted`——核实为真,写进规则。
- `checked-unchanged`——看过了,无需改动。
- `rejected`——过时或过于具体。
- `needs-user`——高风险且无法核实,问人。

脚本从不自己采纳任何东西。什么能成为规则,主动权在你手里。

## 安装

上面那条命令(`agent-install-rules.sh --target <project>`)已覆盖大多数情况。几个细节:

**只用一个智能体(Claude 或 Codex)。** 照常安装即可——没有「只装某一个」的参数,安装器总会把两边的文件都写上。你只用自己那套就行;另一套是惰性的(永远不会被执行),而且应当留着别删,因为校验会要求两套都在。可选地,只给你自己的智能体接钩子:

```bash
cp .claude/settings.example.json .claude/settings.json   # Claude
cp .codex/hooks.example.json     .codex/hooks.json       # Codex
```

只用 Claude 还会多出 `.claude/agents/` 下的子智能体(reviewer、qa、docs-drift-checker);只用 Codex 则保留除此之外的一切。

**全新或空白仓库。** 从第一个提交就能装。即使没有任何代码,扫描也能跑——它只会报 `none detected`、写出空的候选列表。这时适配很轻:智能体主要跟你确认产品意图,把未知项标成 `needs-user`。全新项目其实是最适合安装的时机,因为规则会随项目一起生长,而不是事后再硬补。

**已经有旧规则的项目。** 加上 `--force`;旧的 `AGENTS.md`、`CLAUDE.md`、`.agent/` 等会备份到 `.rules-kit/backups/`,并在适配时当作线索来读:

```bash
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project --force
```

**校验一次安装:**

```bash
# 结构是否就位:
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project
# 是否真的被智能体适配过,而不只是装上:
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

校验查的是**格式,而不是对错**——只看状态字段填没填、候选有没有处置完。它判断不了智能体填的事实对不对,那是智能体和你的责任。如果想绕过 agent 包装直接装,还有更底层的 `install-rules.sh`(支持 `--bootstrap`、`--force`、`--dry-run`、`--no-backup`)。

## 适配之后的日常用法

做普通工作时,智能体会读 `AGENTS.md`、打开 `.agent/index.md`,只加载当前任务需要的工作流/领域文档——而不是每次都把所有文件读一遍。它在改动前查看真实代码,运行 `.agent/command-contract.md` 里已核实的命令,并在收尾非琐碎工作前跑一遍漂移/候选脚本。

当规则本身开始变得嘈杂或过时,`.agent/rule-health.md` 是精简、合并、删除规则的指南。这套工具的本意是保持小巧,而不是长成一本百科。

## 设计理念

底层只有一句话:**智能体是裁判,这套工具是证据采集器。**

- 事实来源的优先级:你当前的指令 → 当前的代码/配置/测试/工具/线上状态 → 共享的 `.agent/` 文档 → README、issue、旧交接和记忆。
- Claude 或 Codex 的私有记忆是个人提示,绝不等于共享的项目事实。长期有效的事实存在仓库里,让每个智能体都看得到。
- 文档负责把智能体导向正确的检查;真正能证明事实的,是当前代码和真实的工具输出。
- 技能、钩子、漂移脚本只是让该检查的时刻更容易被抓住——它们替代不了判断。

## 参考

<details>
<summary><strong>会装进哪些文件(文件地图)</strong></summary>

```text
AGENTS.md                     共享合同,每个智能体先读
CLAUDE.md                     极薄的 Claude 入口,导入 @AGENTS.md
.agent/
  index.md                    把智能体导向对应的工作流/领域文档
  source-of-truth.md          什么算证据、什么必须重新核实
  adaptation-review.md        Status: pending | adapted;以及 needs-user 项
  product-invariants.md       产品的长期承诺
  user-journeys.md            主要流程,以及要闭合的链路
  command-contract.md         已核实命令(+ 生成的候选)
  domains/*.md                ui-copy、data-sync、build-test、release、localization、performance
  workflows/*.md              adapt-rules、implement、review、continue、release
  drift-map.yml               把改动路径 → 可能需要复查的文档
  rule-candidates.md          脚本写入的收件箱;智能体逐条处置
  rule-health.md              何时精简、合并、删除规则
.agents/skills/*              加载共享 .agent 规则的 Codex 技能桩
.claude/skills,agents,hooks   Claude Code 对应物(+ reviewer/qa/drift 子智能体)
.codex/hooks*                 Codex 钩子桩 + 示例配置
scripts/*.py                  bootstrap-project-context、check-doc-drift、suggest-rule-updates
```

建议提交到版本库:`AGENTS.md`、`CLAUDE.md`、`.agent/`、`.agents/`、`.codex/`、`scripts/`。交接笔记 `.agent/work/*` 通常留在本地,除非你有意共享:

```gitignore
.agent/work/*
!.agent/work/README.md
```

</details>

<details>
<summary><strong>完整生命周期:安装 → 引导扫描 → 适配 → 校验 → 生长</strong></summary>

1. **安装**——`agent-install-rules.sh` 拷入模板,把元数据记到 `.agent/rules-kit.json`,备份已有规则文件(除非 `--no-backup`),并运行引导扫描。此时项目只是「装好了」,还没「适配」:`.agent/adaptation-review.md` 仍是 `Status: pending`。
2. **引导扫描**——`bootstrap-project-context.py` 扫描当前文件/配置,**只写线索**,落到 `project-map.md`、`command-contract.md`、`bootstrap-report.md`、`rule-candidates.md`。名为 `sync.ts` 的文件只是个*信号*,并不能证明产品真有经过验证的云同步。
3. **适配**(*由智能体驱动*)——按 `.agent/workflows/adapt-rules.md`,智能体查看当前代码、配置、测试以及任何旧备份,然后**只把核实过的事实**写进 `.agent/*`。无法证明的高风险事实变成 `needs-user`。
4. **校验**——`validate-installed-project.sh` 检查结构是否存在、`CLAUDE.md` 是否导入 `@AGENTS.md`、脚本是否可执行,并(配合 `--require-adapted --require-candidates-reviewed`)检查适配状态与候选是否处置完。查的是格式,不是对错。
5. **生长**(*由智能体驱动*)——代码变化时,漂移/候选脚本浮出可能过时的文档;智能体决定 promote、checked-unchanged、rejected,或标 `needs-user`。

</details>

<details>
<summary><strong>启用钩子(可选)</strong></summary>

钩子以示例形式提供,让你有意识地选择开启。它们是提醒和护栏——替代不了校验。先审阅其中的命令,再:

```bash
cp .codex/hooks.example.json     .codex/hooks.json        # Codex
cp .claude/settings.example.json .claude/settings.json    # Claude Code
```

其中的 Stop 钩子在存在时还会运行 `python3 scripts/check-doc-drift.py`。

</details>
