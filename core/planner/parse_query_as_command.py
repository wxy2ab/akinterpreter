from typing import Dict, Any, Generator, Callable, List, Tuple
import re

class ParseQueryAsCommand:
    def __init__(self):
        self.commands = {}
        self.keyword_commands = {}

    def add_command(self, command: str, handler: Callable, help_text: str, use_regex: bool = False):
        if use_regex:
            self.commands[re.compile(command, re.IGNORECASE)] = (handler, help_text)
        else:
            self.commands[command.lower()] = (handler, help_text)

    def add_keyword_command(self, keywords: List[str], handler: Callable, help_text: str):
        for keyword in keywords:
            self.keyword_commands[keyword.lower()] = (handler, help_text)

    def parse(self, query: str, context: Any) -> Generator[Dict[str, Any], bool, None]:
        lower_query = query.lower()

        # 检查关键词命令
        for keyword, (handler, _) in self.keyword_commands.items():
            if lower_query == keyword:
                yield from handler(context)
                return True

        # 检查前缀命令和正则表达式命令
        for cmd, (handler, _) in self.commands.items():
            if isinstance(cmd, re.Pattern):
                match = cmd.match(query)
                if match:
                    yield from handler(context, **match.groupdict())
                    return True
            elif lower_query.startswith(cmd):
                args = query[len(cmd):].strip()
                yield from handler(context, args)
                return True

        return False

    def get_help(self) -> List[Tuple[str, str]]:
        help_list = []
        seen_help_texts = set()

        # 处理正则表达式命令
        for cmd, (_, help_text) in self.commands.items():
            if help_text not in seen_help_texts:
                cmd_str = cmd.pattern if isinstance(cmd, re.Pattern) else cmd
                # 只取正则表达式的第一个单词或短语
                first_word = cmd_str.split('|')[0].strip('^$')
                help_list.append((first_word, help_text))
                seen_help_texts.add(help_text)

        # 处理关键词命令
        for keyword, (_, help_text) in self.keyword_commands.items():
            if help_text not in seen_help_texts:
                help_list.append((keyword, help_text))
                seen_help_texts.add(help_text)

        return sorted(help_list)

def create_command_parser():
    parser = ParseQueryAsCommand()

    # 添加关键词命令
    parser.add_keyword_command(
        ["确认计划", "确认", "开始", "开始执行", "运行", "执行", "没问题", "没问题了", "执行计划","go", "run", "start"],
        lambda ctx: ctx.handle_confirm_plan(),
        "确认并执行当前计划"
    )
    parser.add_keyword_command(
        ["重置", "清除", "再来一次", "重新开始", "重来", "清空", "清空所有", "清空数据", "清空状态", "清空计划", 
         "清空所有数据", "清空所有状态", "清空所有计划", "清空所有数据和状态", "清空所有数据和计划", "reset"],
        lambda ctx: (ctx.reset(), (yield {"type": "message", "content": "已重置所有数据，请重新开始。"})),
        "重置所有数据并重新开始"
    )

    # 添加前缀命令
    parser.add_command("schedule_run", 
        lambda ctx, args: ctx._handle_schedule_run(args),
        "调度运行任务",
        use_regex=False
    )
    parser.add_command("set_max_retry=", 
        lambda ctx, args: handle_set_max_retry(ctx, args),
        "设置最大重试次数",
        use_regex=False
    )
    parser.add_command("set_allow_yfinance=", 
        lambda ctx, args: handle_set_allow_yfinance(ctx, args),
        "设置是否允许使用 yfinance",
        use_regex=False
    )
    parser.add_command("show_config", 
        lambda ctx, args: (yield {"type": "message", "content": f"当前配置：\nmax_retry: {ctx.get_max_retry()}\nallow_yfinance: {ctx.get_allow_yfinance()}\nstop_every_step: {ctx.get_stop_every_step()}"}),
        "显示当前配置",
        use_regex=False
    )
    parser.add_command(r"show_step_code=(?P<step>\d+)", 
        lambda ctx, step: ctx.show_step_code(int(step)-1),
        "显示特定步骤的代码",
        use_regex=True
    )
    parser.add_command(r"modify_step_code=(?P<step>\d+)\s*(?P<query>.*)", 
        lambda ctx, step, query: ctx.modify_step_code(int(step)-1, query),
        "修改特定步骤的代码",
        use_regex=True
    )
    # 添加 help 命令
    parser.add_command("help", 
        lambda ctx, args: handle_help_command(ctx),
        "显示所有可用的命令及其描述",
        use_regex=False
    )
    parser.add_command(
        "set_stop_every_step=",
        lambda ctx, args: handle_set_stop_every_step(ctx, args),
        "设置是否在每个步骤后停止（true/false）",
        use_regex=False
    )

    # Add the new show_plan command
    parser.add_command("show_plan", 
        lambda ctx, args: handle_show_plan(ctx),
        "显示当前计划",
        use_regex=False
    )
    # Add the new clear_history command
    parser.add_command("clear_history", 
        lambda ctx, args: handle_clear_history(ctx),
        "清除聊天历史",
        use_regex=False
    )
    # Add the new clear_all command
    parser.add_command("clear_all", 
        lambda ctx, args: handle_clear_all(ctx),
        "清除所有数据",
        use_regex=False
    )
    return parser

def handle_set_stop_every_step(ctx, args):
    value = args.lower()
    if value in ["true", "false"]:
        new_value = value == "true"
        yield from ctx.set_stop_every_step(new_value)
    else:
        yield {"type": "error", "content": "无效的 stop_every_step 值。请使用 true 或 false。"}

def handle_help_command(ctx):
    commands = ctx.command_parser.get_help()
    help_text = "可用的命令：\n\n"
    for cmd, description in commands:
        help_text += f"{cmd}: {description}\n"
    yield {"type": "message", "content": help_text}
    
def handle_set_max_retry(ctx, args):
    try:
        new_max_retry = int(args)
        for message in ctx.set_max_retry(new_max_retry):
            yield message
    except ValueError:
        yield {"type": "error", "content": "无效的 max_retry 值。请输入一个整数。"}

def handle_set_allow_yfinance(ctx, args):
    value = args.lower()
    if value in ["true", "false"]:
        for message in ctx.set_allow_yfinance(value == "true"):
            yield message
    else:
        yield {"type": "error", "content": "无效的 allow_yfinance 值。请使用 true 或 false。"}

def handle_show_plan(ctx):
    current_plan = ctx.get_current_plan()
    if current_plan:
        yield {"type": "plan", "content": current_plan}
    else:
        yield {"type": "message", "content": "当前没有计划。"}

def handle_clear_history(ctx):
    ctx._notify_command_send("clear_history")
    yield {"type": "message", "content": "聊天历史已清除。"}

# New handler function for clear_all command
def handle_clear_all(ctx):
    ctx._notify_command_send("clear_all")
    yield {"type": "message", "content": "所有数据已清除。"}