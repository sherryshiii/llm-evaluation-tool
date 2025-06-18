import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_app()
    
    def start_app(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("\n正在启动应用...")
        self.process = subprocess.Popen([sys.executable, "main.py"])
    
    def on_modified(self, event):
        if event.src_path.endswith('.py') and not event.src_path.endswith('dev.py'):
            print(f"\n检测到文件变化: {event.src_path}")
            self.start_app()

if __name__ == "__main__":
    event_handler = CodeChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if event_handler.process:
            event_handler.process.terminate()
        observer.stop()
    observer.join() 