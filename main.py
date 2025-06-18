import gradio as gr
from ui_single import create_tab_single
from ui_table import create_tab_table
from utils.log import read_logs, create_logger

def main():
    create_logger()
    
    # 创建界面
    with gr.Blocks(title="云雀大模型评测工具", theme=gr.themes.Default(spacing_size="sm")) as demo:
        with gr.Tabs(selected="table"):
            create_tab_single()
            create_tab_table()

        # 日志 使用tmplogbox接收服务端日志后，通过js添加到logbox
        clear_btn = gr.Button("清空日志")
        logbox = gr.Textbox(label="日志", lines=10, interactive=False, elem_id="logbox")
        tmplogbox = gr.Textbox(visible=False, interactive=False, value=read_logs)
        tmplogbox.change(fn=None, inputs=[logbox, tmplogbox], outputs=logbox, js="(a, b) => a + b")
        clear_btn.click(fn=None, inputs=[logbox], outputs=logbox, js="() => ''")
    
    # 启动应用
    print("* 点击打开URL http://127.0.0.1:7860")
    demo.queue().launch(server_name="0.0.0.0")

if __name__ == "__main__":
    main()