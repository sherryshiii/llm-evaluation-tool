import gradio as gr
from utils.resp_parser import PARSER_FUNCTIONS
from config import get_all_models

def price_change_handler(selected_prices):
    if not selected_prices:
        return []
    
    models = get_all_models()

    if "all" in selected_prices:
        return [model['value'] for model in models]
        
    selected_models = []
    for price in selected_prices:
        selected_models.extend([model['value'] for model in models if model['price'] == price])
    
    return selected_models

def create_prompt_inputs(sys_prompt, user_prompt):
    # 添加 JavaScript 代码来处理 localStorage
    js = """
    function() {
        // 从 localStorage 获取保存的值
        const savedSysPrompt = localStorage.getItem('sys_prompt');
        const savedUserPrompt = localStorage.getItem('user_prompt');
        
        // 如果有保存的值，则设置到输入框中
        if (savedSysPrompt) {
            document.querySelector('textarea[data-testid="textbox"]').value = savedSysPrompt;
        }
        if (savedUserPrompt) {
            document.querySelectorAll('textarea[data-testid="textbox"]')[1].value = savedUserPrompt;
        }
        
        // 监听输入变化并保存到 localStorage
        const textareas = document.querySelectorAll('textarea[data-testid="textbox"]');
        textareas[0].addEventListener('input', (e) => {
            localStorage.setItem('sys_prompt', e.target.value);
        });
        textareas[1].addEventListener('input', (e) => {
            localStorage.setItem('user_prompt', e.target.value);
        });
    }
    """
    
    sys_prompt_input = gr.Textbox(label="System Prompt", lines=12, value=sys_prompt)
    user_prompt_input = gr.Textbox(label="User Prompt", lines=2, value=user_prompt)
    
    # 添加 JavaScript 代码到页面
    gr.HTML(f"<script>{js}</script>")
    
    return sys_prompt_input, user_prompt_input

def create_common_inputs(resp_parser=""):
    with gr.Row():
        response_format = gr.Radio(choices=["Text", "JSON"], value="Text", label="响应格式")
        temperature = gr.Slider(minimum=0, maximum=1, value=0, step=0.1, label="Temperature")
    parser_selector = gr.Radio(
        choices=[("不处理", "")] + [(v, k) for k, v in PARSER_FUNCTIONS.items()],
        value=resp_parser,
        label="结果处理方式"
    )
    return response_format, temperature, parser_selector

def create_model_selector():
    """创建模型选择区域"""
    # 价格筛选
    with gr.Row():
        price_selector = gr.CheckboxGroup(
            choices=[("全选", "all"), ("免费", "free"), ("低", "low"), ("中", "medium"), ("高", "high")],
            label="价格",
            interactive=True,
            value=["free"]  # 默认选中免费
        )
    
    # 获取所有模型
    models = get_all_models()
    
    # 获取所有免费模型
    free_model_values = [model['value'] for model in models if model['price'] == 'free']
    
    # 创建单个模型选择器
    model_selector = gr.CheckboxGroup(
        choices=[(model['showname'], model['value']) for model in models],
        label="模型选择",
        interactive=True,
        value=free_model_values
    )
    
    return price_selector, model_selector