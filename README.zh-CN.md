# Claude Code + Codex 项目规则套件

[English](./README.md) | 简体中文

一份共享的、纯 Markdown 的「项目合同」:让任何来动你项目的智能体——Claude Code、Codex,或者你自己——都遵循同一套规则,以当前代码而不是过时文档为准,并且把活儿一次做完整,而不是只做一半。

零运行时、零依赖。本质就是给智能体读的 Markdown,外加三个小脚本。它就是为「接力式」开发设计的:这个功能 Claude 写,下个功能或者这次审查换 Codex,再换回来。

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

- `AGENTS.md`——每个智能体都先读的共享合同。Codex 启动时原生加载;Claude Code 通过极薄的 `CLAUDE.md` 做 `@AGENTS.md` 导入(官方文档记载的桥接写法)。
- `.agent/`——一组短小的 Markdown:产品承诺、用户路径、已核实的命令、各领域规则,以及一张路由表(什么任务读哪份文档)。大多一开始是模板,由智能体照着你真实的代码填进去。
- `.claude/rules/`——一组 3 行的路径域指针:Claude 一读到匹配的文件,对应领域文档的指针就自动加载。
- `.claude/skills/`——薄薄的工作流加载器;Codex 那份 `.agents/skills/` **在安装时由它生成**,两边永远不会跑偏。
- 两边的钩子:拦截危险命令的 bash 守卫、不让任务在候选(下文会讲的规则更新建议)未裁决时收尾的收尾门禁,以及(仅 Codex)一个编辑后注入同样领域指针的领域路由。
- 三个小 Python 脚本(只用标准库、**零依赖**),扫描仓库后**写出建议**。它们从不修改你的规则。

**分工才是关键:智能体是裁判,脚本只负责收集证据、标出哪些可能过时了。** 这里没有任何东西会自己做决定。

它**一个或两个智能体**都能用,而且**从第一个提交**就能用。详见[安装](#安装)。

## 按需加载(token 账怎么算)

规则只有在不淹没智能体的前提下才有用。这套套件把「常驻」开销压到一个小文件,其余全部按需路由:

- **常驻加载:** `AGENTS.md`(约 35 行)。固定成本就这一项。
- **碰到文件才加载:** Claude Code 读到匹配文件时自动加载 `.claude/rules/` 里那条 3 行指针(比如 `components/` 下的任何文件都指向 `.agent/domains/ui-copy.md`)。Codex 没有这种自动加载,就由 PostToolUse 钩子在编辑后注入同样的指针——每个区域每次会话只提示一次,每次一行。
- **被调用才加载:** 技能在被使用前只占名字和描述;每个技能只负责路由到一份共享工作流文档。
- **机械地列清单:** 编辑之后,`python3 scripts/check-doc-drift.py` 会精确列出当前 diff 对应哪些共享文档。智能体读这份清单——而不是整个 `.agent/` 目录。

所以一个普通任务的开销 = 合同 + 实际碰到的领域 + 一段任务结束时的固定检查(文档漂移报告和候选收件箱,几千 token,与任务大小无关)。同一张映射表 drift-map(`.agent/drift-map.yml`)同时驱动路由和漂移检测,而且匹配是词边界级精确的:`ProductCard.tsx` 不会触发盯着生产环境路径的那条规则,UI 目录之外的工具类 `.tsx` 文件也不会被唠叨文案问题。

## 快速上手

```bash
# 1. 把套件 clone 到机器上任意位置
git clone https://github.com/liyuhao957/agent-rules-kit.git

# 2. 在你的项目里,对智能体(Claude Code 或 Codex)说:
#    「为这个项目安装并适配 /path/to/agent-rules-kit。」
#    它会执行:
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project
```

安装器拷贝文件,并对你的仓库做一次找线索的初始扫描(bootstrap)。然后由智能体阅读你的真实代码,**把模板填成已核实的事实**——这一步是智能体的活,不是脚本的。从此之后,任何智能体都从 `AGENTS.md` 起步,而不是把项目重新摸一遍。

装完后有两个一次性步骤:重启智能体会话(让新技能被发现),并在首次使用时批准项目钩子——Claude Code 会询问项目设置;Codex 需要信任 `.codex/` 层并在 `/hooks` 里审核。**在信任之前,钩子是不生效的。**

## 「适配完成」长什么样

刚装完时,规则文件还是通用模板,`.agent/adaptation-review.md` 写着 `Status: pending`。智能体的任务是把它们变成真实的、已核实的项目事实。例如:

```text
之前(模板)                  之后(智能体照真实代码核实后填入)
─────────────                ───────────────────────────────
product-invariants.md        免费档最多 3 个项目。
  <持久的产品承诺>             删除账号后 24 小时内清除同步数据。

user-journeys.md             注册 → 验证邮箱 → 创建首个项目 → 进入仪表盘。
  <主流程>

command-contract.md          测试:npm test(跑过,通过)
  <已核实的命令>               构建:npm run build(跑过,成功)

drift-map.yml                glob 收紧到这个仓库的真实路径,
  <默认 glob>                  并镜像进 .claude/rules/* 的 frontmatter。
```

凡是智能体**无法**从代码、测试或工具证明的——线上计费状态、生产配置、凭据——一律不会被晋升进规则,而是进入 `.agent/adaptation-review.md` 的 `needs-user` 区等你确认。不允许猜。

## 代码一直在变,它怎么保持诚实

这是防止规则腐烂的那一个机制。非琐碎改动之后,智能体运行:

```bash
python3 scripts/check-doc-drift.py       # 报告这次改动可能弄旧了哪些文档
python3 scripts/suggest-rule-updates.py  # 把候选写进 .agent/rule-candidates.md
```

两个脚本**只报告、只建议**。随后智能体逐条裁决:

- `promoted`——核实为真,写进规则。
- `checked-unchanged`——看过了,无需改动。
- `rejected`——过时或过于具体。
- `needs-user`——高风险且无法核实,问人。

脚本永远不会自己晋升任何东西。什么能成为规则,决定权在你。`.agent/rule-candidates.md` 就像一个收件箱,而且它的构造让捷径走不通:

- 每个候选都和触发它的那批文件绑定(`drift:ui-copy@a1b2c3d` 里的 `@a1b2c3d` 后缀)。裁决只对这批文件有效——同一条规则之后命中**新文件**时,会出现一条新的 `pending` 项,而不是继承上周的结论。
- `pending` 项既不会被重新扫描丢掉,也不会因提交而消失。提交不等于解决;哪怕未裁决的项已经随代码提交,收尾门禁照样拦截。
- 只翻状态、不写真实裁决记录,是不算数的——下次扫描会自动打回 `pending`。
- 裁决完的候选挪到文件底部的归档区,决策历史一直可读;标了 `rejected` 的就一直是 rejected,不会每次运行卷土重来。
- 依赖和构建产物(`node_modules/`、`dist/` 等)永远不产生候选;套件自身安装文件触发的候选由安装器直接处理掉——新装的项目从干净的收件箱开始。

## 哪些是真强制,哪些不是

对「强制」诚实,比看起来强制更重要。精确的分界:

| 机制 | 触发条件 | 拦截? |
| --- | --- | --- |
| bash 守卫(PreToolUse,两边都有) | force push、`git reset --hard`、`rm -rf`(`node_modules`、`dist` 这类可随时重建的目录除外)、release/deploy/publish/submit——包括 `npx vercel deploy`、`sh -c "npm publish"` 这类包装写法——改动生产环境状态的命令、通过真实数据库 CLI(`psql`、`mysql`)执行的破坏性 SQL | **拦** —— exit 2;旁路 `RULES_HOOK_ALLOW_RISK=1` |
| 收尾门禁(Stop,两边都有) | `.agent/rule-candidates.md` 里还有未裁决的候选——无论来自当前 diff,还是早前已经随代码提交 | **拦** —— 列出 pending 的 ID 和复查命令;智能体会继续干活并逐条解决(Stop 拦截的语义是「接着做完」,不是「停机」);旁路 `RULES_HOOK_ALLOW_PENDING=1` |
| 文档漂移报告 | 按需运行;收尾门禁拦截时也会一并给出 | 不拦 —— 仅列出待复查文档 |
| 映射表自检 | (适配后)drift-map 里某条具体路径在仓库中匹配不到任何文件——通常意味着目录被改名 | 不拦 —— 一行警告,提示映射表本身过时了 |
| 领域路由(PostToolUse,仅 Codex) | 首次编辑触及某个映射区域 | 不拦 —— 一行指针 |
| 其余一切——质量闭环、事实来源顺序、工作流 | 文字合同 | 不拦 —— 靠智能体判断,这是设计如此 |

也就是说:真正的硬门只有窄范围的 bash 守卫和收尾门禁。「别信过时文档」「闭环才算完成」是智能体因为合同这么写而遵守的指引——套件让正确的时机更容易被抓住,但它不证明正确性。两个钩子都带防循环开关(`stop_hook_active`),不会无限拦下去。

## 安装

上面那一条命令(`agent-install-rules.sh --target <project>`)覆盖绝大多数情况。几个具体说明:

**只用一个智能体(Claude *或* Codex)。** 按正常方式装——安装器总是写入两边的文件。用你的那套就行;另一套在对应工具不运行时完全无感,校验也要求两套都存在。

**全新 / 空仓库。** 从第一个提交就能用。初始扫描会报告 `none detected`,适配很轻:智能体主要是和你确认产品意图,把未知项标成 `needs-user`。项目刚起步时正是装它的最佳时机。

**已有规则的存量项目。** 加 `--force`;旧的 `AGENTS.md`、`CLAUDE.md`、`.agent/` 等会备份到 `.rules-kit/backups/`,并在适配时被当作线索读取。如果旧的 `.claude/settings.json` 或 `.codex/hooks.json` 里有你自定义的钩子、权限或命令,安装器会明确警告,适配工作流会从备份把它们合并回来:

```bash
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project --force
```

**升级套件。** `--upgrade` 只替换套件自身的工具文件(三个脚本、钩子、技能、工作流文档),绝不碰智能体适配过的内容(`product-invariants.md`、`user-journeys.md`、`command-contract.md`、`drift-map.yml`,以及正在生效的 `settings.json`/`hooks.json`)。被替换的文件会先备份:

```bash
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project --upgrade
```

**卸载。** 把安装器写入的文件删掉,需要的内容从最早的那份备份恢复(较新的备份里可能是上一次套件安装,不是你的原始文件):`AGENTS.md`、`CLAUDE.md`、`.agent/`、`.agents/`、`.claude/`、`.codex/`、`scripts/` 下的三个套件脚本(`check-doc-drift.py`、`bootstrap-project-context.py`、`suggest-rule-updates.py`——`scripts/` 里其余文件是你自己的),最后删 `.rules-kit/`。

**校验安装:**

```bash
# 结构就位:
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project
# 智能体真的适配过了,而不是只装了个壳:
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

校验查的是**形式,不是正确性**——状态字段填了没有、模板占位符清没清干净、drift-map 的 glob 是否仍与 `.claude/rules/*` 镜像一致、候选带着真实的裁决记录解决了没有。它无法判断智能体写的事实对不对;那是智能体和你的责任。

## 适配之后的日常使用

日常工作中,智能体读 `AGENTS.md`,经 `.agent/index.md` 路由,只加载任务需要的部分——碰到文件时领域指针会自动送上门。它动手前先查真实代码,跑 `.agent/command-contract.md` 里已核实的命令,收尾前把候选收件箱处理干净。

双智能体接力时:一个智能体中途停下,就写 `.agent/work/current.md`(目标、基线 commit、哪些核实了、哪些没有)。下一个接手的——Claude 或 Codex——从 `git status` 和 diff 重建状态,把交接笔记当意图参考,不当事实证明。

当规则本身开始显得吵闹或过时,`.agent/rule-health.md` 是修剪、合并、删除的指南。这套套件的本意是保持小巧,而不是长成百科全书。

## 设计哲学

一切的底层是一个想法:**智能体是裁判,套件是证据收集员。**

- 事实来源顺序:你的当前指令 → 当前代码/配置/测试/工具/线上状态 → 共享的 `.agent/` 文档 → README、issue、旧交接和记忆。
- Claude 或 Codex 的私有记忆是个人提示,永远不是共享项目事实。持久事实放在仓库里,每个智能体都看得见。
- Context 不是强制(Anthropic 官方的提法):Markdown 引导智能体;两个窄钩子负责拦;测试和真实工具负责证明。
- 技能、领域指针、MCP/工具都是加载器和证据通道,不是规则本体。持久规则待在仓库可见的 Markdown 里。
- 嘈杂的探测器喂一个会拦截的门,只会训练出「无脑盖章」——所以探测做到词边界级精确,警告和报告永远不拦。

## 参考

<details>
<summary><strong>安装清单(文件地图)</strong></summary>

```text
AGENTS.md                     共享合同;Codex 启动时读,Claude 经 @import 读
CLAUDE.md                     极薄的 Claude 入口,导入 @AGENTS.md
.agent/
  index.md                    路由表:只加载任务需要的
  adaptation-review.md        Status: pending | adapted;以及 needs-user 项
  product-invariants.md       持久的产品承诺
  user-journeys.md            主流程与待闭合的链路
  command-contract.md         已核实的命令(+ 生成的候选)
  quality-gates.md            定义「完成」的那些闭环
  domains/*.md                ui-copy、data-sync、build-test、release、localization、performance
  workflows/*.md              adapt-rules、implement、review、continue、release
  drift-map.yml               改动路径 → 待复查文档;同时驱动按需路由
  rule-candidates.md          候选收件箱:脚本写入,智能体裁决
  rule-health.md              何时修剪、合并、删除规则
.claude/
  rules/*.md                  3 行的路径域指针;读到匹配文件时自动加载
  skills/*/SKILL.md           规范的薄工作流加载器(8 个)
  agents/*.md                 reviewer / qa / docs-drift-checker 子智能体
  hooks/*.py + settings.json  bash 守卫 + 收尾门禁
.agents/skills/*              Codex 技能树——安装时由 .claude/skills 生成
.codex/
  hooks/*.py + hooks.json     bash 守卫 + 收尾门禁 + 领域路由
scripts/*.py                  bootstrap-project-context、check-doc-drift、suggest-rule-updates
```

建议提交进 git:`AGENTS.md`、`CLAUDE.md`、`.agent/`、`.agents/`、`.claude/`、`.codex/`、`scripts/`。`.agent/work/*`(交接笔记)保持本地,除非你有意共享:

```gitignore
.agent/work/*
!.agent/work/README.md
```

</details>

<details>
<summary><strong>完整生命周期:安装 → 初始扫描 → 适配 → 校验 → 生长</strong></summary>

1. **安装** —— `agent-install-rules.sh` 拷贝模板,由规范的 Claude 技能树生成 Codex 技能树,在 `.agent/rules-kit.json` 记录元数据,备份已有规则文件,并运行初始扫描。此时项目是「已安装」,不是「已适配」:`.agent/adaptation-review.md` 仍是 `Status: pending`。
2. **初始扫描(bootstrap)** —— `bootstrap-project-context.py` 扫描当前文件/配置,**只写线索**到 `project-map.md`、`command-contract.md`、`bootstrap-report.md` 和 `rule-candidates.md`。一个叫 `sync.ts` 的文件是*信号*,不是「云同步已核实」的证明。
3. **适配**(智能体驱动)—— 按 `.agent/workflows/adapt-rules.md`,智能体检查当前代码、配置、测试和旧备份,只把**核实过的事实**晋升进 `.agent/*`,把 drift-map 的 glob 收紧到项目真实路径,并镜像进 `.claude/rules/*`。无法证明的高风险事实标 `needs-user`。
4. **校验** —— `validate-installed-project.sh` 检查结构齐全、`CLAUDE.md` 导入了 `@AGENTS.md`、Codex 技能树与规范树一致、脚本可执行,以及(带严格参数时)适配状态和候选都已解决。查形式,不查正确性。
5. **生长**(智能体驱动)—— 代码变化时,两个扫描脚本浮出可能过时的文档和新的规则候选;智能体逐条晋升、确认未变、拒绝,或标 `needs-user`。

</details>
