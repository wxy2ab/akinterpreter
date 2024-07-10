import sys
import asyncio
from typing import Union, Dict, Any
from ..talk.talker_factory import TalkerFactory
from ..scheduler.async_generator import AsyncSingletonReplayGenerator

async_generator = AsyncSingletonReplayGenerator()
current_response_type = None

def print_colored(text: str, color: str = 'white', end: str = '\n', flush: bool = True):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
    }
    end_color = '\033[0m'
    print(f"{colors.get(color, '')}{text}{end_color}", end=end, flush=flush)


async def chat_cli():
    from ..scheduler.replay_message_queue import ReplayMessageQueue
    factory = TalkerFactory()
    talker = factory.get_instance("CliTalker")
    message_queue = ReplayMessageQueue()

    print_colored("欢迎使用聊天程序！输入 'quit' 或 'exit' 结束对话。", 'cyan')

    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "\n您: ")
        if user_input.lower() in ['quit', 'exit']:
            print_colored("谢谢使用，再见！", 'yellow')
            break

        if user_input.strip() == "":
            continue

        print_colored("AI: ", 'green', end='')
        sys.stdout.flush()

        # 启动 talker 和 planner 任务
        talker_task = asyncio.create_task(process_talker_response(talker, user_input))
        planner_task = asyncio.create_task(process_planner_response(message_queue))

        while True:
            # 使用 wait 和超时机制
            done, pending = await asyncio.wait(
                [talker_task, planner_task], 
                timeout=0.1,  # 100ms 超时
                return_when=asyncio.FIRST_COMPLETED
            )

            if talker_task in done:
                # Talker 完成了响应
                break

            if planner_task in done:
                # Planner 完成了一次响应，重新启动它
                planner_task = asyncio.create_task(process_planner_response(message_queue))

            # 处理 planner 的输出
            while not message_queue.empty():
                message = await message_queue.get()
                handle_dict_response(message)

        # 确保所有任务都完成
        for task in [talker_task, planner_task]:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        

async def process_talker_response(talker, user_input):
    for chunk in talker.chat(user_input):
        if isinstance(chunk, str):
            print(chunk, end='', flush=True)
        elif isinstance(chunk, dict):
            handle_dict_response(chunk)
        else:
            print(str(chunk), end='', flush=True)

async def process_planner_response(message_queue):
    message = await message_queue.get()
    return message

def handle_dict_response(response: Dict[str, Any]):
    global current_response_type
    response_type = response.get('type', '')
    content = response.get('content', '')

    if response_type != current_response_type:
        if current_response_type is not None:
            print()  # 添加换行，为新类型做准备
        current_response_type = response_type
        if response_type == 'error':
            print_colored("[错误] ", 'red', end='')
        elif response_type == 'plan':
            print_colored("[计划] ", 'cyan', end='')
        elif response_type == 'code_generation':
            print_colored("[代码生成] ", 'magenta', end='')
        elif response_type == 'finished':
            print_colored("[完成] ", 'green', end='')
        elif response_type == 'report':
            print_colored("[报告] ", 'yellow', end='')

    # 打印内容
    if response_type in ['message', 'error', 'plan', 'code_generation', 'finished', 'report','code_execution']:
        print(content, end='', flush=True)
    else:
        # 处理其他类型作为普通消息
        print(content, end='', flush=True)

if __name__ == "__main__":
    chat_cli()