import os
import logging
import subprocess
import asyncio

def create_logger():
    llm_logger = logging.getLogger("req")
    llm_handler = logging.FileHandler('logs/req.log')
    llm_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s\n'))
    llm_logger.addHandler(llm_handler)
    llm_logger.setLevel(logging.INFO)
    return llm_logger

async def read_logs():
    logpath = "logs/req.log"
    os.system(f"touch {logpath}")

    # 使用tail -n 10 读取最后10行日志并输出
    full_path = os.path.abspath(logpath)
    history_log = subprocess.check_output(f"tail -n 10 {full_path}", shell=True, text=True)
    yield history_log + "============接下来是新日志============\n"

    with open(logpath, "r") as f:
        f.seek(0, 2)
        last_position = f.tell()

        silent_time = 0
        while True:
            f.seek(last_position)
            new_content = f.read()
            
            if new_content:
                last_position = f.tell()
                silent_time = 0
                yield new_content
            else:
                silent_time += 1
                if silent_time >= 5: # 5秒没有新日志，yield一次，此时如果连接断开，则退出函数，避免一直循环
                    yield ""
                    silent_time = 0

            await asyncio.sleep(1) 