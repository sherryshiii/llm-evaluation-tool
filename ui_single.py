import gradio as gr
from llm_client import multi_request
from config import get_model_by_key
from utils.resp_parser import process_responses
from ui_shared import create_common_inputs, create_model_selector, create_prompt_inputs, price_change_handler

# 默认提示词
DEFAULT_SYS_PROMPT = """你是一个客服助理，需要帮助客服从客户的提问中识别出客户的所在位置。请识别对话中的行政区划和地址信息，从文本中分析和识别省、市、区县和详细地址，并输出为JSON格式
遵循规则：
如果说明了房子不在某地，不要识别出来
如果包含多个行政区，只输出一个主要的、可能代表房产位置的地址。例如"我在上海上班，家在武汉"，应视为武汉市
不要回答房型、面积等与位置无关的信息
一定不要回答其他内容，只输出JSON，key是 province / city / district / street
预期输出JSON格式示例：{"province":"","city":"","district":"","street":""}"""

DEFAULT_USER_PROMPT = "客户发送的消息是：宝山"

def create_tab_single():
    with gr.TabItem("单句评测", id="single"):
        # 左侧输入区域
        with gr.Row():
            with gr.Column():
                sys_prompt_input, user_prompt_input = create_prompt_inputs(
                    sys_prompt=DEFAULT_SYS_PROMPT,
                    user_prompt=DEFAULT_USER_PROMPT
                )
            with gr.Column():
                response_format, temperature, parser_selector = create_common_inputs()
            
            with gr.Column():
                price_selector, model_selector = create_model_selector()

        # 提交按钮
        submit_btn = gr.Button("提交", variant="primary")

        # 输出表格
        with gr.Row():
            output_table = gr.Dataframe(
                headers=["模型", "响应时间", "输入Token", "输出Token", "最终响应", "原始响应"],
                datatype=["str", "str", "str", "str", "str", "str"],
                col_count=(6, "fixed"),
                label="模型响应",
                show_fullscreen_button=True
            )
        
        # 绑定价格筛选事件
        price_selector.change(
            fn=price_change_handler,
            inputs=price_selector,
            outputs=model_selector
        )

        # 绑定提交事件
        submit_btn.click(
            fn=single_submit_handler,
            inputs=[sys_prompt_input, user_prompt_input, parser_selector, response_format, temperature, model_selector],
            outputs=output_table
        )

async def single_submit_handler(sys_prompt, user_prompt, parser_type, response_format, temperature, selected_models, progress=gr.Progress()):
    # 构建任务列表
    tasks = []
    for model_key in selected_models:
        tasks.append({
            "sys_prompt": sys_prompt,
            "user_prompt": user_prompt,
            "model_key": model_key,
            "response_format": response_format,
            "temperature": temperature
        })
    
    # 并发请求，然后并发处理结果
    results = await multi_request(tasks, progress)
    contents = [r["content"] for r in results]
    processed_contents = await process_responses(contents, parser_type)
    
    # 构建最终结果
    processed_results = []
    for result, processed in zip(results, processed_contents):
        # 获取模型的显示名称
        model_info = get_model_by_key(result["model_key"])
        processed_results.append([
            model_info['showname'],
            f"{result['time']}ms" if result['time'] else "",
            result['input_tokens'],
            result['output_tokens'],
            processed,
            result["content"]
        ])
    
    return processed_results
