# -*- coding: utf-8 -*-
"""Headroom 仪表盘中文语言包（单文件版）。

部署：把本文件放到 Python 的 user-site 目录（`python -m site` 查看），重启
headroom 代理即可看到中文界面；删除本文件即恢复英文。headroom 升级覆盖模板
后无需任何操作——代理会在返回页面前按模板哈希自动重译（新出现的英文词条
保持原样，不会硬套旧翻译）。

原理：Python 启动时自动导入 usercustomize；本文件向 sys.meta_path 注册一个
惰性钩子，仅在 headroom.dashboard 被导入（即代理进程）时把
get_dashboard_html / get_settings_html 包装为"读官方英文模板 → 套用下方
映射表 → 返回中文"，按 (mtime, size) 缓存，任何异常都回退英文原版。
"""
import sys

_ZH_MARKERS = {"dashboard.html": "仪表盘", "settings.html": "Headroom 设置"}


class _HeadroomZhFinder:
    """meta_path 钩子：只在导入 headroom.dashboard 时介入，其余零开销。"""

    _NAME = "headroom.dashboard"

    def find_spec(self, fullname, path=None, target=None):
        if fullname != self._NAME:
            return None
        import importlib.util

        try:
            sys.meta_path.remove(self)
            spec = importlib.util.find_spec(fullname)
        finally:
            try:
                sys.meta_path.insert(0, self)
            except ValueError:
                pass
        if spec is None or spec.loader is None:
            return spec
        spec.loader = _ZhLoaderWrapper(spec.loader)
        return spec


class _ZhLoaderWrapper:
    """包装真实 loader：模块执行完立即打补丁。"""

    def __init__(self, loader):
        self._loader = loader

    def __getattr__(self, name):
        return getattr(self._loader, name)

    def create_module(self, spec):
        return self._loader.create_module(spec)

    def exec_module(self, module):
        self._loader.exec_module(module)
        try:
            _apply_patch(module)
        except Exception:
            pass


def _apply_patch(module):
    templates_dir = getattr(module, "TEMPLATES_DIR", None)
    if templates_dir is None:
        return
    orig_dashboard = module.get_dashboard_html
    orig_settings = module.get_settings_html
    cache = {}

    def serve(name, original):
        try:
            stat = (templates_dir / name).stat()
            key = (stat.st_mtime_ns, stat.st_size)
            hit = cache.get(name)
            if hit is not None and hit[0] == key:
                return hit[1]
            html = original()
            zh = translate(html, name)
            cache[name] = (key, zh)
            return zh
        except Exception:
            return original()

    module.get_dashboard_html = lambda: serve("dashboard.html", orig_dashboard)
    module.get_settings_html = lambda: serve("settings.html", orig_settings)


def translate(html, name):
    """英文模板 → 中文。已是中文（幂等标记）则原样返回。"""
    marker = _ZH_MARKERS.get(name)
    if marker and marker in html:
        return html
    import re

    out = html
    for en, zh in sorted(TEXT_MAPS.get(name, ()), key=lambda pair: -len(pair[0])):
        out = re.sub(
            r">(\s*)" + re.escape(en) + r"(\s*)<",
            lambda m, zh=zh: ">" + m.group(1) + zh + m.group(2) + "<",
            out,
        )
    for en, zh in TITLE_MAPS.get(name, ()):
        needle = 'title="' + en + '"'
        if needle in out:
            out = out.replace(needle, 'title="' + zh + '"')
    for en, zh in LITERAL_MAPS.get(name, ()):
        if en in out:
            out = out.replace(en, zh)
    for en, zh in TARGETED_MAPS.get(name, ()):
        if en in out:
            out = out.replace(en, zh)
    return out


sys.meta_path.insert(0, _HeadroomZhFinder())

TEXT_MAP_DASH = [
    ("&#9881; Settings", "&#9881; 设置"),
    ("1h Cache Writes", "1h 缓存写入"),
    ("5-Hour Window", "5 小时窗口"),
    ("5m Cache Writes", "5m 缓存写入"),
    ("7-Day Window", "7 天窗口"),
    ("Active Days", "活跃天数"),
    ("Active Requests", "活跃请求"),
    ("Active WebSockets", "活跃 WebSocket"),
    ("Actual cost (with Headroom)", "实际成本（经 Headroom）"),
    ("After Compression (sent)", "压缩后（实际发送）"),
    ("After", "之后"),
    ("Agent usage appears after Cursor, Claude, Codex, or another client sends traffic through this proxy.",
     "当 Cursor、Claude、Codex 等客户端经此代理发送流量后，这里会显示 Agent 用量。"),
    ("Agent Usage", "Agent 用量"),
    ("All time", "全部时间"),
    ("Anon Telemetry", "匿名遥测"),
    ("Anthropic Subscription Window", "Anthropic 订阅窗口"),
    ("Attempted Input", "尝试的输入"),
    ("Average / month", "月均"),
    ("Average Saved / Day", "日均节省"),
    ("Average Saved / Week", "周均节省"),
    ("Based on persisted daily buckets", "基于持久化的按日统计"),
    ("Based on persisted weekly buckets", "基于持久化的按周统计"),
    ("Before and after token usage by detected client", "各客户端压缩前后 token 用量"),
    ("Before Compression", "压缩前"),
    ("Before", "之前"),
    ("Bucket Mix", "桶间占比"),
    ("Cache Busts", "缓存失效次数"),
    ("Cache Efficiency", "缓存效率"),
    ("Cache Miss Attribution", "缓存未命中归因"),
    ("Cache Reads (lifetime)", "缓存读取（累计）"),
    ("Cache Reads", "缓存读取"),
    ("Cache Writes", "缓存写入"),
    ("Cache bust", "缓存失效"),
    ("Cached", "已缓存"),
    ("Completed", "已完成"),
    ("Compressed Tokens", "压缩后 token"),
    ("Compression (p50 / p95)", "压缩耗时 (p50 / p95)"),
    ("Compression Queued", "压缩已排队"),
    ("Compression saved", "压缩节省"),
    ("Compression vs Cache", "压缩与缓存对比"),
    ("Compression", "压缩"),
    ("Cost Saved", "节省成本"),
    ("Cost with Headroom", "经 Headroom 的成本"),
    ("Cost", "成本"),
    ("Credits", "余额"),
    ("Cumulative proxy compression savings", "代理压缩累计节省"),
    ("Current 5m (active p50):", "当前 5m（活跃 p50）："),
    ("Current proxy process · runtime counters reset on restart", "当前代理进程 · 运行时计数器重启后清零"),
    ("Daily Savings", "每日节省"),
    ("Documentation", "文档"),
    ("Durable local savings history from", "本地持久化节省历史，来源："),
    ("Efficiency", "效率"),
    ("Enforced", "已生效"),
    ("Every decision on record, by requested → served pair", "全部决策记录，按请求 → 实际服务模型排列"),
    ("Exact tokens saved per model", "各模型精确节省 token 数"),
    ("Expected cost (without Headroom)", "预期成本（不经 Headroom）"),
    ("Expected cost without Headroom", "不经 Headroom 的预期成本"),
    ("Export CSV", "导出 CSV"),
    ("Export JSON", "导出 JSON"),
    ("Extra Usage (Overage)", "超额用量"),
    ("Failed Requests", "失败请求"),
    ("Failed", "失败"),
    ("Forward (p50 / p95)", "转发耗时 (p50 / p95)"),
    ("Forwarded to Anthropic", "转发给 Anthropic"),
    ("Generation (p50 / p95)", "生成耗时 (p50 / p95)"),
    ("GitHub Copilot Quota", "GitHub Copilot 配额"),
    ("Headroom Contribution This Window", "Headroom 在此窗口的贡献"),
    ("Headroom Dashboard", "Headroom 仪表盘"),
    ("Headroom compression savings", "Headroom 压缩节省"),
    ("Headroom-attributable, rolling display session", "Headroom 归因，滚动显示会话"),
    ("Historical Proxy Compression", "历史代理压缩"),
    ("Historical Savings Trend", "历史节省趋势"),
    ("Historical Summary", "历史汇总"),
    ("Historical", "历史"),
    ("Hit Rate", "命中率"),
    ("Hit rate", "命中率"),
    ("Hits / requests", "命中 / 请求"),
    ("Holdout", "对照组"),
    ("In:", "输入："),
    ("Input (wall / active p50)", "输入（全部 / 活跃 p50）"),
    ("Input cost", "输入成本"),
    ("Input", "输入"),
    ("Last 25 &mdash; click row to expand", "最近 25 条 &mdash; 点击行展开"),
    ("Last Active", "最近活跃"),
    ("Latency", "延迟"),
    ("Latest total", "最新累计"),
    ("Lifetime Compression Savings", "累计压缩节省"),
    ("Lifetime Tokens Saved", "累计节省 token"),
    ("Lifetime totals — attributed requests only", "累计统计 — 仅计入可归因请求"),
    ("Lifetime", "累计"),
    ("Live Activity", "实时活动"),
    ("Live Feed", "实时流"),
    ("Lost to Cache Busts", "因缓存失效损失"),
    ("Measured", "实测"),
    ("Message Transformations", "消息转换明细"),
    ("Model Routing", "模型路由"),
    ("Model", "模型"),
    ("Month start", "月初"),
    ("Monthly Reset", "每月重置"),
    ("Monthly Savings", "每月节省"),
    ("Msg&nbsp;Saved", "消息节省"),
    ("Net", "净节省"),
    ("No per-project data yet.", "暂无按项目数据。"),
    ("No persisted savings history yet", "暂无持久化节省历史"),
    ("No requests yet", "暂无请求"),
    ("Observed TTL Buckets", "观测到的 TTL 分布"),
    ("Observed write-token split", "观测到的写入 token 分布"),
    ("OpenAI Codex Rate-Limit Window", "OpenAI Codex 限流窗口"),
    ("Optimization Time", "优化耗时"),
    ("Original Tokens", "原始 token"),
    ("Output Tokens Saved", "输出 token 节省"),
    ("Output Tokens", "输出 token"),
    ("Output", "输出"),
    ("Output shaping is off. Set", "输出整形未开启。设置"),
    ("Overhead Range", "开销区间"),
    ("Overhead", "开销"),
    ("Pay-as-you-go credits balance", "按量付费余额"),
    ("Per-Model Breakdown", "按模型分解"),
    ("Per-Model Token Savings", "按模型 token 节省"),
    ("Per-Project Savings", "按项目节省"),
    ("Per-Provider Breakdown", "按提供商分解"),
    ("Performance", "性能"),
    ("Pipeline Breakdown", "流水线分解"),
    ("Prefix Cache Impact", "前缀缓存影响"),
    ("Prefix Cache saved", "前缀缓存节省"),
    ("Prefix Cache", "前缀缓存"),
    ("Prefix Change", "前缀变更"),
    ("Prefix Freeze Net", "前缀冻结净收益"),
    ("Press", "按"),
    ("Primary", "主模型"),
    ("Project", "项目"),
    ("Provider cache discount", "提供商缓存折扣"),
    ("Provider-reported cache write mix", "提供商报告的缓存写入占比"),
    ("Providers", "提供商"),
    ("Proxy Removed", "代理移除"),
    ("Proxy compression only", "仅代理压缩"),
    ("Rate Limited", "被限流"),
    ("Raw vs Submitted", "原始 vs 上报"),
    ("Read / write", "读 / 写"),
    ("Reads (discounted)", "读取（有折扣）"),
    ("Recent Historical Checkpoints", "最近的历史检查点"),
    ("Recent Requests", "最近请求"),
    ("Reduction", "降幅"),
    ("Relay Tasks", "中继任务"),
    ("Request Health", "请求健康度"),
    ("Requested", "请求模型"),
    ("Requests", "请求数"),
    ("Retention", "保留期限"),
    ("Rolling display session economics", "滚动显示会话成本"),
    ("Saved $", "节省 $"),
    ("Saved by Compression", "压缩带来的节省"),
    ("Saved by Headroom", "Headroom 节省"),
    ("Saved", "已节省"),
    ("Savings %", "节省 %"),
    ("Savings Attribution", "节省归因"),
    ("Savings Over Time", "节省趋势"),
    ("Savings", "节省"),
    ("Secondary", "副模型"),
    ("Selected points", "选中数据点"),
    ("Selected series", "选中序列"),
    ("Sent", "已发送"),
    ("Served", "服务模型"),
    ("Session", "会话"),
    ("Share", "占比"),
    ("Stacks", "客户端栈"),
    ("Status", "状态"),
    ("TTFB Range", "TTFB 区间"),
    ("TTL Expiry", "TTL 过期"),
    ("This session", "本次会话"),
    ("Throughput", "吞吐量"),
    ("Time", "时间"),
    ("Token Savings", "token 节省"),
    ("Token Usage", "token 用量"),
    ("Token flow", "token 流向"),
    ("Tokens Removed", "移除 token"),
    ("Tokens Saved", "节省 token"),
    ("Tokens Sent", "发送 token"),
    ("Tokens saved by compression against cached-prefix tokens its mutations invalidated",
     "压缩节省的 token，需扣除其改动导致缓存前缀失效的部分"),
    ("Tokens saved", "节省 token"),
    ("Tokens", "Token 数"),
    ("Top Models + Other", "主要模型 + 其他"),
    ("Total Misses", "未命中总数"),
    ("Transforms Applied", "应用的转换"),
    ("Trend data will appear after multiple requests.", "多次请求后这里会显示趋势数据。"),
    ("Uncached", "未缓存"),
    ("Unknown", "未知"),
    ("Unlimited", "无限制"),
    ("Updated", "更新于"),
    ("Values cover the active persisted display session.", "数值覆盖当前持久化显示会话。"),
    ("Waste Detected", "检测到的浪费"),
    ("Waste Signals", "浪费信号"),
    ("Weekly Savings", "每周节省"),
    ("What Headroom Removed", "Headroom 移除的内容"),
    ("Why turns that expected a prompt-cache hit missed — TTL lapse (consider a longer TTL) vs the cacheable prefix changing",
     "预期命中提示缓存却未命中的原因 — TTL 过期（可考虑调长 TTL）或可缓存前缀发生变化"),
    ("Writes", "写入"),
    ("at list price", "按原价计"),
    ("basis", "口径"),
    ("expected a cache hit, got none", "预期命中缓存，实际未命中"),
    ("new message", "新消息"),
    ("no activity since restart", "重启后暂无活动"),
    ("provider-observed, rolling display session", "提供商口径，滚动显示会话"),
    ("s avg", "秒 平均"),
    ("saved minus bust losses", "节省减去失效损失"),
    ("stable prefix, within TTL", "稳定前缀，TTL 内"),
    ("to measure it for real.", "以进行真实测量。"),
    ("to refresh", "即可刷新"),
    ("tokens removed before send", "发送前移除的 token"),
    ("with cache data", "含缓存数据"),
    ("⚠ Anomalies Detected", "⚠ 检测到异常"),
    ("Approximate: a benchmark factor, not your traffic. Set", "近似值：基准系数，非你的真实流量。设置"),
    ("Daily rollups will appear after persisted history spans at least one checkpoint.",
     "持久化历史跨过至少一个检查点后，这里会显示按日汇总。"),
    ("Evaluating every turn; cache is warm, so switching would cost more than it saves.",
     "正在评估每一轮；缓存正热，切换的代价大于收益。"),
    ("Monthly rollups will appear after persisted history spans multiple months.",
     "持久化历史跨多月后，这里会显示按月汇总。"),
    ("No requests yet. Start using the proxy to see activity here.",
     "暂无请求。开始使用代理后，这里会显示活动。"),
    ("No waste signals detected yet. Data appears after requests are processed.",
     "尚未检测到浪费信号。请求处理后这里会显示数据。"),
    ("Per-model attribution appears for checkpoints recorded after upgrading.",
     "升级后记录的检查点会显示按模型归因。"),
    ("Survives restarts — kept in routemegood's decision log, not proxy memory.",
     "重启后保留 — 存于 routemegood 的决策日志，而非代理内存。"),
    ("Weekly rollups will appear after persisted history spans multiple days.",
     "持久化历史跨多日后，这里会显示按周汇总。"),
    ("tokens", "token"),
]

# ------------------------------------------------------------ title tooltips
TITLE_MAP_DASH = [
    ("Discount the provider gives on prompt-cache reads. Headroom's CacheAligner and prefix freeze raise the hit rate, but the discount is provider-native, so it is not counted as Headroom savings.",
     "提供商对提示缓存读取给出的折扣。Headroom 的 CacheAligner 与前缀冻结能提升命中率，但折扣由提供商原生提供，因此不计入 Headroom 节省。"),
    ("Dollars Headroom kept off the bill: message compression and tool-schema deferral, priced at what those tokens would actually have been billed given each request's cache mix.",
     "Headroom 为账单省下的金额：消息压缩与工具定义延迟，按各请求缓存组合下的真实计费价折算。"),
    ("Every turn was evaluated. Keeping the model is the correct call when the prefix cache is warm — switching would pay a cold write on the target.",
     "每一轮都经过评估。前缀缓存正热时保留原模型才是正确选择——切换会对目标模型支付一次冷写入。"),
    ("Measured: compression and tool-schema deferral. Projected: extension-attributed estimates such as model routing.",
     "实测：消息压缩与工具定义延迟。预估：模型路由等扩展归因的估算值。"),
    ("Message-compression share of this request only. Tool-schema deferral, cache discounts and routing savings are counted in the headline cards, not per row.",
     "仅本条请求的消息压缩占比。工具定义延迟、缓存折扣与路由节省计入顶部卡片，不按行计。"),
    ("Requests rejected with 429 — by Headroom&#39;s own rate limiter or by the upstream provider. /stats splits them under requests.rate_limited_by_source.",
     "被 429 拒绝的请求 — 来自 Headroom 自身限流器或上游提供商。/stats 在 requests.rate_limited_by_source 下区分二者。"),
    ("Requests that failed upstream — 4xx and 5xx. 429s are counted under Rate Limited instead, and neither is included in Completed.",
     "在上游失败的请求 — 4xx 与 5xx。429 计入“被限流”，两者均不计入“已完成”。"),
    ("Spend is input + output at the provider's billed rates.",
     "支出 = 按提供商计费价计算的输入 + 输出费用。"),
    ("The anonymous telemetry beacon is on: compression stats only, never prompts, code, or file paths. Turn it off with HEADROOM_BEACON=off or DO_NOT_TRACK=1.",
     "匿名遥测已开启：仅上报压缩统计，绝不含提示词、代码或文件路径。设 HEADROOM_BEACON=off 或 DO_NOT_TRACK=1 可关闭。"),
    ("The same tokens at flat list price. This is an upper bound: it assumes every removed token would have been a cache MISS, which is true only for the first request of a cache window.",
     "同一批 token 按统一原价估算。这是上限口径：假定每个被移除的 token 都会缓存未命中，仅缓存窗口的首次请求如此。"),
    ("Toggle light/dark mode", "切换明 / 暗模式"),
    ("Tool-definition tokens deferred out of context", "被延迟移出上下文的工具定义 token"),
    ("Total saved as a fraction of the without-Headroom baseline",
     "节省占“不经 Headroom”基线的比例"),
    ("What the removed tokens would actually have been billed at, given the cache mix of the requests they came out of.",
     "按被移除 token 所属请求的缓存组合，其原本实际会被计费的金额。"),
]

# ------------------------------------------- whitelisted display literals in
# the inline Alpine script (logic keys like 'daily'/'healthy' stay untouched)
LITERAL_MAP_DASH = [
    ("'Current proxy profile: '", "'当前代理配置档：'"),
    ("'Show all models'", "'显示全部模型'"),
    ("'Show only this model'", "'只看此模型'"),
    ("' from compression · '", "' 来自压缩 · '"),
    ("' from deferred tool schemas'", "' 来自工具定义延迟'"),
    ("'Balanced'", "'均衡'"),
    ("'1h leaning'", "'偏向 1h'"),
    ("'5m leaning'", "'偏向 5m'"),
    ("'Checkpoint history'", "'检查点历史'"),
    ("'Checkpoints'", "'检查点'"),
    ("'History'", "'历史'"),
    ("'Daily'", "'每日'"),
    ("'Weekly'", "'每周'"),
    ("'Monthly'", "'每月'"),
    ("'Daily cumulative savings'", "'每日累计节省'"),
    ("'Weekly cumulative savings'", "'每周累计节省'"),
    ("'Monthly cumulative savings'", "'每月累计节省'"),
    ("'Historical savings'", "'历史节省'"),
    ("'Tokens'", "'Token 数'"),
    ("'Cost'", "'成本'"),
    ("'Waiting for saved requests'", "'等待已保存的请求'"),
    ("'No TTL bucket data'", "'暂无 TTL 分布数据'"),
    ("'Persisted locally'", "'本地持久化'"),
    ("'Of total wire input tokens: all forwarded input, cached history included'",
     "'占线上输入 token 总量：含缓存历史的全部转发输入'"),
    ("'provider ratio (model publishes no cache pricing)'", "'按提供商比例（模型未公布缓存价格）'"),
    ("'partly unpriced'", "'部分未定价'"),
    ("'aggregate fallback'", "'聚合回退'"),
    ("'JSON Bloat'", "'JSON 冗余'"),
    ("'HTML Noise'", "'HTML 噪声'"),
    ("'Base64 Blobs'", "'Base64 数据块'"),
    ("'Whitespace'", "'空白字符'"),
    ("'Dynamic Dates'", "'动态日期'"),
    ("'Repetition'", "'重复内容'"),
    ("'Re-read Tool Results'", "'重复读取的工具结果'"),
    ("'today'", "'今天'"),
    ("'tomorrow'", "'明天'"),
    ("'Failed to fetch stats:'", "'获取 stats 失败:'"),
    ("'Failed to fetch lifetime stats:'", "'获取累计统计失败:'"),
    ("'Failed to fetch history stats:'", "'获取历史统计失败:'"),
    ("'Failed to fetch transformations:'", "'获取转换记录失败:'"),
    ("'Failed to export history'", "'导出历史失败'"),
    ("'ms avg / '", "'ms 均 / '"),
    ("'ms max'", "'ms 峰值'"),
    ("'Healthy'", "'正常'"),
    ("'Of new input: '", "'占新输入：'"),
    ("'Measured $'", "'实测 $'"),
    ("' · projected $'", "' · 预估 $'"),
    ("' spent vs $'", "' 已支出 vs $'"),
    ("' baseline'", "' 基线'"),
    ("' provider cache discount'", "' 提供商缓存折扣'"),
    ("' shaped responses · counterfactual'", "' 次整形响应 · 反事实'"),
    ("' calls · '", "' 次调用 · '"),
    ("'realized'", "'实测'"),
    ("'projected'", "'预估'"),
    ("'Proxy '", "'代理 '"),
    ("'Active'", "'活跃'"),
    ("'Idle'", "'空闲'"),
    ("'No Credits'", "'无余额'"),
    ("'Coverage: '", "'覆盖：'"),
    ("'Full metric coverage since '", "'完整指标覆盖自 '"),
    ("'Lifetime data since '", "'累计数据自 '"),
    ("'Mostly TTL lapse'", "'主要为 TTL 过期'"),
    ("'Mostly prefix change'", "'主要为前缀变更'"),
    ("'Net negative'", "'净收益为负'"),
    ("'Net positive'", "'净收益为正'"),
    ("'No overage'", "'无超额'"),
    ("'Overage allowed'", "'允许超额'"),
    ("'Persistence degraded: '", "'持久化异常：'"),
    ("'Persistence healthy'", "'持久化正常'"),
    ("'Provider cache discount, current process: $'", "'提供商缓存折扣（当前进程）：$'"),
    ("'Resets in '", "'重置倒计时 '"),
    ("'Savings · '", "'节省 · '"),
    ("'Showing '", "'已显示 '"),
    ("'TTL 1h '", "'TTL 1h '"),
    ("'% / 5m '", "'% / 5m '"),
    ("'d / '", "' 天 / '"),
    ("'range '", "'区间 '"),
    ("'95% CI '", "'95% 置信区间 '"),
    ("'unknown error'", "'未知错误'"),
    ("' tokens total'", "' tokens 总计'"),
    ("' busts observed'", "' 次缓存失效'"),
    ("' busts avoided, '", "' 次失效避免，'"),
    ("' foregone'", "' 次放弃压缩'"),
    ("' busts'", "' 次失效'"),
    ("' reads ('", "' 读取（'"),
    ("' off)'", "' 折扣）'"),
    ("' writes (+'", "' 写入（+'"),
    ("'% saved'", "'% 已节省'"),
    ("' logged requests'", "' 条已记录请求'"),
    ("'% of attributed — idle past cache TTL'", "'% 可归因 — 缓存 TTL 过期'"),
    ("'% of attributed — cached prefix shifted'", "'% 可归因 — 缓存前缀变化'"),
    ("' saved'", "' 节省'"),
    ("' requests'", "' 次请求'"),
    ("'Error'", "'异常'"),
    ("'s ago'", "' 秒前'"),
    ("'m ago'", "' 分钟前'"),
    ("' · target '", "' · 目标 '"),
    ("' buckets'", "' 个桶'"),
    ("' cumulative'", "' 累计'"),
    ("' decisions · '", "' 条决策 · '"),
    ("' decisions'", "' 条决策'"),
    ("' downgraded · '", "' 降级 · '"),
    ("' kept'", "' 保留'"),
    ("' left'", "' 剩余'"),
    ("' msgs'", "' 条消息'"),
    ("' overage uses'", "' 次超额使用'"),
    ("' plan'", "' 套餐'"),
    ("' points'", "' 个点'"),
    ("' project(s)'", "' 个项目'"),
    ("' recorded checkpoints'", "' 个已记录检查点'"),
    ("' requests observed'", "' 次请求观测'"),
    ("' tok'", "' token'"),
    ("' tokens forwarded'", "' token 转发'"),
    ("' tokens re-written'", "' token 重写'"),
    ("' tokens'", "' token'"),
    ("' unchanged · '", "' 不变 · '"),
    ("' upgraded · '", "' 升级 · '"),
    ("' write premium'", "' 写入加价'"),
    ("' · projected'", "' · 预估'"),
    ("'% of input served from cache'", "'% 的输入由缓存提供'"),
    ("'∞ Unlimited'", "'∞ 无限制'"),
    ("healthy ? 'Healthy' : 'Error'", "healthy ? '正常' : '异常'"),
    # backend-provided display labels → Chinese at render site
    ('x-text="pc.label"',
     'x-text="(pc.label || \'\').replace(\'Explicit breakpoints, 5-min TTL\', \'显式缓存断点（5 分钟 TTL）\').replace(\'Automatic, no TTL control\', \'自动缓存（无 TTL 控制）\')"'),
    ('<span x-text="agent.source"></span>',
     '<span x-text="({provider: \'按提供商\', client: \'按客户端\'})[agent.source] || agent.source"></span>'),
]

# ------------------------------------------------ specific code lines (plain
# substring replaces; keep logic intact, translate display words only)
TARGETED_DASH = [
    ("if (h > 0) return h + 'h ' + m + 'm';", "if (h > 0) return h + '小时' + m + '分';"),
    ("if (m > 0) return m + 'm ' + Math.floor(seconds % 60) + 's';",
     "if (m > 0) return m + '分' + Math.floor(seconds % 60) + '秒';"),
    ("return Math.floor(seconds) + 's';", "return Math.floor(seconds) + '秒';"),
    ("return 'in ' + days + ' days ('", "return days + ' 天后（'"),
    ('<html lang="en"', '<html lang="zh-CN"'),
    ("·\n                                Fwd:", "· 转发:"),
]

TEXT_MAP_SETTINGS = [    ("&larr; Dashboard", "&larr; 返回仪表盘"),
    ("-- edits here have no effect until it's unset.", "—— 在解除覆盖前，此处的编辑不会生效。"),
    ("Advanced", "高级"),
    ("Apply &amp; Restart", "应用并重启"),
    ("Clear stored value", "清除已保存值"),
    ("Configure Headroom runtime knobs. Changes need a restart to apply.",
     "配置 Headroom 运行时参数。更改需重启后生效。"),
    ("Headroom Settings", "Headroom 设置"),
    ("Managed by the install manifest — change via", "由安装清单管理 — 修改途径："),
    ("Overridden by environment variable", "已被环境变量覆盖"),
    ("Run this on the host to apply:", "在主机上运行以下命令以生效："),
    ("Save", "保存"),
    ("Settings", "设置"),
]
TARGETED_SETTINGS = [('<html lang="en"', '<html lang="zh-CN"')]


TEXT_MAPS = {"dashboard.html": TEXT_MAP_DASH, "settings.html": TEXT_MAP_SETTINGS}
TITLE_MAPS = {"dashboard.html": TITLE_MAP_DASH, "settings.html": []}
LITERAL_MAPS = {"dashboard.html": LITERAL_MAP_DASH, "settings.html": []}
TARGETED_MAPS = {"dashboard.html": TARGETED_DASH, "settings.html": TARGETED_SETTINGS}
