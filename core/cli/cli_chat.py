import asyncio
from typing import Union, Dict, Any
from ..talk.talker_factory import TalkerFactory
from core.utils.log import logger
from ..planner.cli_handler import CliUIHandler
from ..planner.replay_event_bus import ReplayEventBus
from traceback import format_exc

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
    factory = TalkerFactory()
    talker = factory.get_instance("CliBpTalker")
    ui_handler = CliUIHandler(print_colored)
    event_bus = ReplayEventBus()
    
    ui_handler.subscribe()

    print_colored("欢迎使用聊天程序！输入 'quit' 或 'exit' 结束对话。", 'cyan')

    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "\n您: ")
        if user_input.lower() in ['quit', 'exit']:
            print_colored("谢谢使用，再见！", 'yellow')
            break

        if user_input.strip() == "":
            continue

        print_colored("AI: ", 'green', end='')

        try:
            for chunk in talker.chat(user_input):
                if isinstance(chunk, str):
                    print(chunk, end='', flush=True)
                elif isinstance(chunk, dict):
                    if chunk['type'] == 'error':
                        await event_bus.publish("error", {"content": chunk['content']})
                    else:
                        await event_bus.publish("message", {"content": chunk['content']})
                else:
                    print(str(chunk), end='', flush=True)
        except Exception as e:
            logger.error(f"Error in chat_cli: {str(e)}")
            await event_bus.publish("error", {"content": f"发生错误: {str(e)} {format_exc()}"} )

    ui_handler.unsubscribe()

if __name__ == "__main__":
    asyncio.run(chat_cli())