# Relay Rules(接力规则)

[English](./README.md) | 简体中文

给在你项目里干活的 agent 立一套共同的规矩——不管你只用 Claude Code 一个,还是 Claude 和 Codex 换着用:谁接手,都先读同一份约定;动手前看当前代码,而不是过时文档;活做完整了才能收工。

零运行时、零依赖——本质就是一组拷进你仓库的 Markdown 文件,外加三个小脚本。名字里的「接力」,首先指会话与会话之间:只用一个 agent 时,今天的会话和下周的会话就是一场接力,这套规则就是接力棒。两个 agent 换班——这个功能 Claude 写,下个功能或这次审查换 Codex——只是同一件事的双人版。

## 它帮你解决什么

不管是一个 agent 跨多次会话,还是两个轮流上手,真实项目里反复翻车的就是这三件事。

**坑一:每次重新开始,都把项目怎么干重新发明一遍。**
新会话冷启动打开仓库:不记得之前的决定,只能猜约定、起不同的名字、把「事情该怎么做」重新推导一遍。接手的不管是同一个 agent、另一个 agent,还是一个月后的你,都一样——两次 Claude 会话之间的分歧,和 Claude 与 Codex 之间一样大。时间一长,代码就裂开了。
*解法:* 把长期有效的决定写进仓库里一份谁都先读的文件(`AGENTS.md`)。下一个接手的人从同一套标准起步,而不是从猜开始。
> 就像一个谁都不做记录的工地:每拨工人来——哪怕是下周回来的同一拨——都把「活该怎么干」重新发明一遍。把一份《工地须知》钉在墙上,大家就按同一套盖。

**坑二:信了过时文档,照着错的目标动手。**
文档写「登录接口是 `/api/login`」,但代码几个月前就改成了 `/api/v2/auth`。agent 信了文档,就对着一个早已不存在的目标写代码。
*解法:* 动手前先看当前的代码、配置、测试。当下的真实状态,优先于旧文档和记忆。

**坑三:只做半截活,就说「完成了」。**
最经典的一幕:本地能跑、不报错,交差。可数据没存、页面没显示、文档没更新——用户真正要走的那条路,从头到尾走不通。
*解法:* 一个改动,要等**功能、逻辑、数据、UI、文档**全部接上,才算做完。

以「给用户加一个『昵称』字段」为例:

| 链路 | 只做一半(常态) | 做完(才算数) |
| --- | --- | --- |
| 功能 | 加了输入框 | 加了输入框 |
| 逻辑 | 没写保存逻辑 | 提交时真能存进去 |
| 数据 | 数据库没加这列 | 加了字段,能读能写 |
| UI | 个人主页不显示 | 该显示的地方都显示了 |
| 文档 | API 文档还是旧的 | 文档同步更新 |

一句话:别让每次会话各自发挥(一份共享约定)、别信过时文档(以当前代码为准)、别只交半截活(全部接通才算数)。

## 怎么用

```bash
# 1. 把仓库 clone 到机器上任意位置
git clone https://github.com/liyuhao957/relay-rules.git

# 2. 在你的项目里,对 agent(Claude Code 或 Codex)说:
#    「为这个项目安装并适配 /path/to/relay-rules。」
#    它会执行:
/path/to/relay-rules/scripts/agent-install-rules.sh --target /path/to/project
```

按你项目的状态,一共三种装法:

- **第一次装**——就用上面这条命令。装完是一堆模板,外加一次找线索的初始扫描,等着 agent 适配(「装完之后」一节讲适配是什么)。空仓库也能装,而且项目刚起步正是装它的最佳时机。只用一个 agent?这本来就是最常见的用法——照常装,属于另一个工具的那些文件放着不碍事。
- **项目里已经有自己的 `AGENTS.md` / `CLAUDE.md` / `.claude/`**——加 `--force`。你的旧文件会先原样备份到 `.rules-kit/backups/` 再被替换,适配时当线索翻出来用;旧 settings 里有你自定义的钩子或权限的话,安装器会提醒你,适配流程会把它们合并回来。
- **以前装过,现在出了新版**——加 `--upgrade`。只更新自带的脚本、钩子、技能、工作流文档,你已经填好的项目事实一个字不动,被换掉的文件也先备份。旧安装缺的新结构(比如 `.claude/rules/` 指针)会自动补上,globs 直接照你的 drift-map 镜像生成。如果新版往你已适配的文件里加了新契约内容,升级末尾的校验会逐条列出缺什么——让 agent 照模板合并一次,再跑校验即可。

装完还有两个一次性动作:重启 agent 会话(让新技能被发现),并批准项目钩子——Claude Code 会询问项目设置;Codex 需要信任项目里的 `.codex/` 目录,并在 `/hooks` 里过一眼。**没批准之前,钩子不生效。**

想确认装好了没:

```bash
# 结构都在:
/path/to/relay-rules/scripts/validate-installed-project.sh /path/to/project
# agent 真的适配过了,不是只装了个壳:
/path/to/relay-rules/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

校验查的是**形式,不是正确性**——字段填了没有、模板占位符清没清干净、每个决定有没有写真实理由。事实本身对不对,要靠 agent 和你。

**卸载**:把安装时写入的文件删掉——`AGENTS.md`、`CLAUDE.md`、`.agent/`、`.agents/`、`.claude/`、`.codex/`、`scripts/` 下的三个脚本(`check-doc-drift.py`、`bootstrap-project-context.py`、`suggest-rule-updates.py`,其余文件是你自己的),最后删 `.rules-kit/`。需要恢复的内容从最早那份备份里取(较新的备份可能是上一次安装,不是你的原始文件)。

## 它到底是什么

先把分量说清楚:这**不是框架、不是引擎、也没有运行时**。就是一堆拷进你仓库的文件:

- `AGENTS.md`——谁都先读的那份共享约定。Codex 启动时原生加载;Claude Code 通过极薄的 `CLAUDE.md` 做一行 `@AGENTS.md` 导入(官方文档记载的桥接写法)。
- `.agent/`——一组短小的 Markdown:产品承诺、用户路径、验证过的命令、各领域的规矩,以及一张「什么任务读哪份文档」的索引。大多一开始是模板,由 agent 照你的真实代码填。
- `.claude/rules/`——一组小指针文件(正文就一行,外加路径匹配规则):Claude 一读到匹配的文件,对应领域的文档就自动加载。
- `.claude/skills/`——薄薄的工作流入口;Codex 那份 `.agents/skills/` 在安装时由它生成,两边永远一致。
- 两边各一套钩子。bash 守卫拦危险命令;收尾门禁管收工——收件箱里还有没处理的「候选」(下文讲)就不让结束;Codex 还多一个路由钩子,编辑后补送领域指针。
- 三个小 Python 脚本(只用标准库、零依赖),扫描仓库、写出建议。它们从不直接改你的规则。

分工是关键:**agent 是裁判,脚本只收集证据、标出哪里可能过时了**。这里没有任何东西会自己做决定。

## 装完之后:适配 → 日常 → 保持新鲜

**适配,说白了就是把模板填成你项目的真话。** 刚装完时 `.agent/adaptation-review.md` 写着 `Status: pending`,agent 的任务是读你的真实代码,把通用模板变成验证过的项目事实:

```text
之前(模板)                  之后(agent 照真实代码核实后填入)
─────────────                ───────────────────────────────
product-invariants.md        免费档最多 3 个项目。
  <持久的产品承诺>             删除账号后 24 小时内清除同步数据。

user-journeys.md             注册 → 验证邮箱 → 创建首个项目 → 进入仪表盘。
  <主流程>

command-contract.md          测试:npm test(跑过,通过)
  <验证过的命令>               构建:npm run build(跑过,成功)

drift-map.yml                glob 收紧到这个仓库的真实路径,
  <默认 glob>                  并镜像进 .claude/rules/* 的 frontmatter。
```

凡是 agent **没法**从代码、测试、工具里证明的——线上计费状态、生产配置、凭据——一律不会被写进规则,而是标成 `needs-user` 等你确认。不允许猜。

**日常使用,你基本不用管。** agent 读 `AGENTS.md`,按索引只加载这个任务用得上的文档——改到哪个区域,哪个领域的指针自动送上门。动手前查真实代码,跑 `.agent/command-contract.md` 里验证过的命令。中途停下时——不管接棒的是下次会话的自己,还是另一个 agent——写一份交接记录(`.agent/work/current.md`:目标、基线 commit、哪些核实了、哪些没有),接手的从 `git status` 和 diff 重建现场——交接记录只当参考,不当证据。

**保持新鲜,靠一个收件箱。** 防止规则慢慢烂掉,靠的就是这一个机制。每次像样的改动之后,agent 跑两个脚本:

```bash
python3 scripts/check-doc-drift.py       # 列出这次改动可能弄旧了哪些文档
python3 scripts/suggest-rule-updates.py  # 往收件箱(.agent/rule-candidates.md)里写「候选」
```

**「候选」就是脚本写给 agent 的待办便条**:「代码这里变了,某条规则可能跟着过时了,去看一眼,做个决定。」脚本只提醒、从不直接改规则;agent 逐条处理,四选一:

- `promoted`——查实了,写进规则;
- `checked-unchanged`——看过了,不用改;
- `rejected`——不值得成为规则;
- `needs-user`——查不了(比如涉及线上状态),留给你确认。

这个收件箱专门防糊弄:

- 每条候选跟触发它的那批文件绑定(`drift:ui-copy@a1b2c3d` 里的 `@a1b2c3d` 后缀)。同一条规则之后碰到**新文件**,会生成新的待办,不会沿用上周的结论。
- 没处理的候选不会因为提交代码就消失——提交不等于解决,收尾门禁照样拦。
- 只改状态、不写真实理由,不算数——下次扫描自动打回待办。
- 处理完的挪到文件底部的归档区,历史一直可查;拒过的不会反复纠缠。
- 依赖和构建产物(`node_modules/`、`dist/` 等)永远不产生候选;安装自身触发的候选由安装器直接处理掉——新装的项目从干净的收件箱开始。

当规则本身开始变得啰嗦或过时,`.agent/rule-health.md` 是修剪、合并、删除的指南。这套规则的本意是保持小巧,不是长成百科全书。

## 哪些是真拦,哪些只是提醒

对「强制」诚实,比看起来强制更重要。精确的分界:

| 机制 | 触发条件 | 拦截? |
| --- | --- | --- |
| bash 守卫(PreToolUse,两边都有) | force push;`git reset --hard`;`rm -rf`(`node_modules`、`dist` 这类可随时重建的目录除外);发布/部署类命令(release、deploy、publish、submit,包括 `npx vercel deploy`、`sh -c "npm publish"` 这类包装写法);改动生产环境状态的命令;通过真实数据库 CLI(`psql`、`mysql`)执行的破坏性 SQL | **拦** —— exit 2;旁路 `RULES_HOOK_ALLOW_RISK=1` |
| 收尾门禁(Stop,两边都有) | 收件箱里还有没处理的候选——无论来自当前 diff,还是早前已经随代码提交 | **拦** —— 列出待办的 ID 和复查命令;agent 会继续干活并逐条处理(Stop 拦截的语义是「接着做完」,不是「停机」);旁路 `RULES_HOOK_ALLOW_PENDING=1` |
| 文档漂移报告 | 按需运行;收尾门禁拦截时也会一并给出 | 不拦 —— 仅列出待复查文档 |
| 映射表自检 | (适配后)drift-map 里某条具体路径在仓库中匹配不到任何文件——通常意味着目录被改名 | 不拦 —— 一行警告,提示映射表本身过时了 |
| 领域路由(PostToolUse,仅 Codex) | 首次编辑触及某个映射区域 | 不拦 —— 一行指针 |
| 其余一切——质量闭环、事实优先级、工作流 | 文字约定 | 不拦 —— 靠 agent 判断,这是设计如此 |

也就是说:真正会拦下来的只有两道——窄范围的 bash 守卫,和收尾门禁。「别信过时文档」「把活做完整」靠的是 agent 守约定——这套规则让正确的时机更容易被抓住,但它不证明正确性。收尾门禁带防循环开关(`stop_hook_active`),不会无限拦下去。

## token 账

规则要是把上下文塞满了,就帮了倒忙。所以:

- **常驻的只有一份约 35 行的 `AGENTS.md`**,固定成本就这一项。
- 领域文档**碰到对应文件才加载**:Claude 靠读到匹配文件时自动加载的小指针,Codex 靠编辑后钩子注入的同一条指针(每个区域每次会话只提示一次)。
- 技能**被调用才展开**;收尾时脚本**机械地列出**「这次 diff 对应哪几份文档」,agent 照单取用,不用整个目录都读。

一个普通任务的开销 = 约定本身 + 实际碰到的领域 + 一段任务结束时的固定检查(文档漂移报告和收件箱,一两千 token,与任务大小无关)。匹配按词边界算:`ProductCard.tsx` 不会因为带着 "prod" 就触发盯生产环境的规则,UI 目录之外的工具文件也不会被唠叨文案问题。

## 设计哲学

一句话:**agent 是裁判,这套规则是证据收集员。**

- 事实优先级:你现在的指令 → 当前代码/配置/测试/工具/线上状态 → 仓库里的共享文档 → README、issue、旧交接和记忆。
- Claude 或 Codex 的私有记忆是个人小抄,不是共享事实。要让两边都遵守的事,写进仓库里谁都看得见的文件。
- 文字负责引导,两个范围很窄的钩子负责拦,测试和真实工具负责证明——三件事不混为一谈(Context 不是强制,这也是 Anthropic 官方的提法)。
- 探测要是不准,拦截就成了「狼来了」,agent 学会的只有无脑盖章——所以探测求准(词边界级),警告和报告永远不拦人。

## 参考

<details>
<summary><strong>安装清单(文件地图)</strong></summary>

```text
AGENTS.md                     共享约定;Codex 启动时读,Claude 经 @import 读
CLAUDE.md                     极薄的 Claude 入口,导入 @AGENTS.md
.agent/
  index.md                    索引:只加载任务需要的
  adaptation-review.md        Status: pending | adapted;以及 needs-user 项
  product-invariants.md       持久的产品承诺
  user-journeys.md            主流程与要接通的链路
  command-contract.md         验证过的命令(+ 生成的候选)
  quality-gates.md            定义「做完」的那些链路
  domains/*.md                ui-copy、data-sync、build-test、release、localization、performance
  workflows/*.md              adapt-rules、implement、review、continue、release
  drift-map.yml               改动路径 → 待复查文档;同时驱动按需加载
  rule-candidates.md          候选收件箱:脚本写入,agent 决定
  rule-health.md              何时修剪、合并、删除规则
  project-map.md 等           初始扫描的产出(还有 bootstrap-report.md,都是线索)
  handoff-template.md / work/ 交接记录的模板和存放处
  decisions/                  值得留给后来者的持久决策
  doc-drift.md、*-policy.md   机制与策略说明,按需读
.claude/
  rules/*.md                  路径指针;读到匹配文件时自动加载
  skills/*/SKILL.md           薄工作流入口(8 个,Codex 那份由这边生成)
  agents/*.md                 reviewer / qa / docs-drift-checker 子 agent
  hooks/*.py + settings.json  bash 守卫 + 收尾门禁
.agents/skills/*              Codex 技能树——安装时由 .claude/skills 生成
.codex/
  hooks/*.py + hooks.json     bash 守卫 + 收尾门禁 + 领域路由
scripts/*.py                  bootstrap-project-context、check-doc-drift、suggest-rule-updates
```

建议提交进 git:`AGENTS.md`、`CLAUDE.md`、`.agent/`、`.agents/`、`.claude/`、`.codex/`、`scripts/`。`.agent/work/*`(交接记录)保持本地,除非你有意共享:

```gitignore
.agent/work/*
!.agent/work/README.md
```

</details>

<details>
<summary><strong>完整生命周期:安装 → 初始扫描 → 适配 → 校验 → 生长</strong></summary>

1. **安装** —— `agent-install-rules.sh` 拷贝模板,以 Claude 技能树为准生成 Codex 技能树,在 `.agent/rules-kit.json` 记录元数据,备份已有规则文件,并运行初始扫描。此时项目是「已安装」,不是「已适配」:`.agent/adaptation-review.md` 仍是 `Status: pending`。
2. **初始扫描(bootstrap)** —— `bootstrap-project-context.py` 扫描当前文件/配置,**只写线索**到 `project-map.md`、`command-contract.md`、`bootstrap-report.md` 和 `rule-candidates.md`。一个叫 `sync.ts` 的文件是*信号*,不是「云同步已核实」的证明。
3. **适配**(agent 驱动)—— 按 `.agent/workflows/adapt-rules.md`,agent 检查当前代码、配置、测试和旧备份,只把**核实过的事实**写进 `.agent/*`,把 drift-map 的 glob 收紧到项目真实路径,并镜像进 `.claude/rules/*`。无法证明的高风险事实标 `needs-user`。
4. **校验** —— `validate-installed-project.sh` 检查结构齐全、`CLAUDE.md` 导入了 `@AGENTS.md`、Codex 技能树与 Claude 那份一致、脚本可执行,以及(带严格参数时)适配状态、占位符和候选都已处理。查形式,不查正确性。
5. **生长**(agent 驱动)—— 代码变化时,两个扫描脚本浮出可能过时的文档和新的候选;agent 逐条查实、确认未变、拒绝,或标 `needs-user`。

</details>
