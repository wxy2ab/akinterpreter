import sys
from typing import Union, Dict, Any
from ..talk.talker_factory import TalkerFactory
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

def chat_cli():
    factory = TalkerFactory()
    talker = factory.get_instance("CliTalker")  # 获取默认的 Talker 实例

    print_colored("欢迎使用聊天程序！输入 'quit' 或 'exit' 结束对话。", 'cyan')

    while True:
        try:
            user_input = input("\n您: ")
            if user_input.lower() in ['quit', 'exit']:
                print_colored("谢谢使用，再见！", 'yellow')
                break

            if user_input.strip() == "":
                continue

            print_colored("AI: ", 'green', end='')
            sys.stdout.flush()

            global current_response_type
            current_response_type = None  # 重置响应类型

            for chunk in talker.chat(user_input):
                if isinstance(chunk, str):
                    print(chunk, end='', flush=True)
                elif isinstance(chunk, dict):
                    handle_dict_response(chunk)
                else:
                    print(str(chunk), end='', flush=True)
            print()  # 换行

        except KeyboardInterrupt:
            print_colored("\n程序被中断。再见！", 'yellow')
            break
        except Exception as e:
            print_colored(f"发生错误: {str(e)}", 'red')

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