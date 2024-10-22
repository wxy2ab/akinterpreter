import asyncio
from core.cli.cli_chat import chat_cli
from core.utils.tsdata import check_proxy_running

if __name__ == "__main__":
    asyncio.run(chat_cli())