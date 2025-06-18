import importlib
import pandas as pd
import re
import asyncio
from typing import Tuple, Optional, Dict, List, Any
import gradio as gr
from utils.resp_parser import process_responses
from config import get_model_by_key
from llm_client import multi_request
import os
from ui_shared import create_common_inputs, create_model_selector, create_prompt_inputs, price_change_handler
from utils.comparator import COMPARE_FUNCTIONS

# 默认提示词
DEFAULT_SYS_PROMPT = """你是一个客服助理，需要帮助客服从客户的提问中识别出客户的所在位置。请识别对话中的行政区划和地址信息，从文本中分析和识别省、市、区县和详细地址，并输出为JSON格式
遵循规则：
如果说明了房子不在某地，不要识别出来
如果包含多个行政区，只输出一个主要的、可能代表房产位置的地址。例如"我在上海上班，家在武汉"，应视为武汉市
不要回答房型、面积等与位置无关的信息
一定不要回答其他内容，只输出JSON，key是 province / city / district / street
预期输出JSON格式示例：{"province":"","city":"","district":"","street":""}"""
DEFAULT_USER_PROMPT = "客户发送的消息是：$input"

def create_tab_table():
    """创建表格评测标签页的UI界面"""
    with gr.TabItem("表格评测", id="table"):
        with gr.Row():
            with gr.Column():
                sys_prompt_input, user_prompt_input = create_prompt_inputs(
                    sys_prompt=DEFAULT_SYS_PROMPT,
                    user_prompt=DEFAULT_USER_PROMPT
                )
            
            with gr.Column():
                response_format, temperature, parser_selector = create_common_inputs(
                    resp_parser=""
                )
                comparator = gr.Dropdown(
                    choices=[(v, k) for k, v in COMPARE_FUNCTIONS.items()],
                    label="评估方式",
                    value="compare_text"
                )
                file_upload = gr.File(label="上传表格文件 (CSV/XLS/XLSX)", file_types=[".csv", ".xls", ".xlsx"], height=100)
                use_example_btn = gr.Button("使用示例表格")
            
            with gr.Column():
                price_selector, model_selector = create_model_selector()

        submit_btn = gr.Button("提交", variant="primary")
        
        stats_table = gr.Dataframe(
            label="统计信息",
            headers=["模型", "最小响应时间", "最大响应时间", "平均响应时间", "平均输入Token", "平均输出Token", "完成数", "完成率", "正确数", "正确率"]
        )

        output_table = gr.Dataframe(
            label="表格内容"
        )
        
        download_file = gr.DownloadButton(label="下载表格")
        
        # 绑定价格筛选事件
        price_selector.change(
            fn=price_change_handler,
            inputs=price_selector,
            outputs=model_selector
        )
        
        # 使用示例表格按钮事件
        use_example_btn.click(
            fn=lambda: "table_demo.xlsx",
            outputs=file_upload
        )
        
        # 评估按钮事件
        submit_btn.click(
            fn=table_submit_handler,
            inputs=[
                file_upload, 
                sys_prompt_input, 
                user_prompt_input, 
                model_selector, 
                comparator,
                parser_selector,
                response_format,
                temperature
            ],
            outputs=[stats_table, output_table, download_file]
        )

def extract_template_vars(prompt: str):
    """从提示词中提取变量名"""
    return re.findall(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", prompt or "")

def check_table_columns(df: pd.DataFrame, vars_list):
    """检查表格中是否包含所需的列"""
    missing = [v for v in vars_list if f"${v}" not in df.columns]
    return missing

async def table_submit_handler(file, sys_prompt, user_prompt, selected_models, comparator, parser_type, response_format, temperature, progress=gr.Progress()) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[str]]:
    # 输入验证
    if file is None:
        raise gr.Error("请上传表格文件")
    if not selected_models:
        raise gr.Error("请至少选择一个模型")
        
    # 读取表格文件
    file_path = file.name if hasattr(file, 'name') else str(file)
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
    else:
        raise gr.Error("不支持的文件格式，请上传CSV或XLS/XLSX文件")

    # 预处理表格数据
    if "期望答案" in df.columns:
        df["期望答案"] = df["期望答案"].fillna("")

    # 验证提示词变量
    vars_in_prompt = set(extract_template_vars(sys_prompt) + extract_template_vars(user_prompt))
    if not vars_in_prompt:
        raise gr.Error("未在Prompt中检测到变量（如 $input）")
        
    # 验证表格列
    missing = check_table_columns(df, vars_in_prompt)
    if missing:
        raise gr.Error(f"表格中缺少以下列: {', '.join(missing)}")

    # 构建并发任务
    all_tasks = []
    task_mapping = []  # 记录每个任务对应的(模型, 行索引)
    
    for row_idx, row in df.iterrows():
        for model_key in selected_models:
            # 替换提示词中的变量
            row_vars = {v: row.get(f"${v}", "") for v in vars_in_prompt}
            sys_prompt_filled = sys_prompt
            user_prompt_filled = user_prompt
            for k, v in row_vars.items():
                sys_prompt_filled = sys_prompt_filled.replace(f"${k}", str(v) if v is not None else "")
                user_prompt_filled = user_prompt_filled.replace(f"${k}", str(v) if v is not None else "")
            
            # 添加任务
            all_tasks.append({
                "sys_prompt": sys_prompt_filled,
                "user_prompt": user_prompt_filled,
                "model_key": model_key,
                "response_format": response_format,
                "temperature": temperature
            })
            task_mapping.append((model_key, row_idx))
    
    # 并发执行模型请求
    results = await multi_request(all_tasks, progress)
    
    # 并发处理响应结果
    contents = [r["content"] for r in results]
    processed_contents = await process_responses(contents, parser_type)
    
    # 整理处理结果
    model_results = {model_key: [""] * len(df) for model_key in selected_models}
    for (model_key, row_idx), processed in zip(task_mapping, processed_contents):
        model_results[model_key][row_idx] = processed

    # 更新DataFrame并评估结果
    model_cols = []  # 用于存储所有模型相关的列名
    for model_key in selected_models:
        model_info = get_model_by_key(model_key)
        col_name = model_info['showname']
        df[col_name] = model_results[model_key]
        model_cols.append(col_name)
        
        # 评估结果
        if "期望答案" in df.columns:
            judge_col = f"{model_info['showname']}结果"  # 每个模型一个结果列
            module = importlib.import_module("utils.comparator")
            compare_func = getattr(module, comparator, None)
            
            # 计算正确率
            judge_results = []
            for model_ans, expected in zip(df[col_name], df["期望答案"]):
                model_ans = "" if pd.isna(model_ans) else str(model_ans)
                expected = "" if pd.isna(expected) else str(expected)
                is_correct = compare_func(model_ans, expected)
                judge_results.append(1 if is_correct else 0)
            df[judge_col] = judge_results
            model_cols.append(judge_col)

    # 添加平均结果列
    if "期望答案" in df.columns:
        judge_cols = [col for col in df.columns if col.endswith("结果")]
        df["平均结果"] = df[judge_cols].mean(axis=1).round(1)
        # 将平均结果列移动到期望答案后面
        cols = df.columns.tolist()
        expect_idx = cols.index("期望答案")
        cols.remove("平均结果")
        cols.insert(expect_idx + 1, "平均结果")
        df = df[cols]

    # 添加汇总统计
    if "期望答案" in df.columns:
        summary_row = pd.Series(index=df.columns, data="")
        for model_key in selected_models:
            model_info = get_model_by_key(model_key)
            judge_col = f"{model_info['showname']}结果"
            correct_count = sum(1 for x in df[judge_col] if x == 1)
            summary_row[judge_col] = str(correct_count)
        df = pd.concat([df, pd.DataFrame([summary_row])], ignore_index=True)

    # 计算统计数据
    stats_data = []
    for model_key in selected_models:
        model_info = get_model_by_key(model_key)
        model_results = [r for r, (m, _) in zip(results, task_mapping) if m == model_key]
        
        # 计算统计数据
        completed_results = [r for r in model_results if r["time"] is not None]
        completed_count = len(completed_results)
        completion_rate = completed_count / len(model_results) * 100
        
        min_time = min(r["time"] for r in completed_results) if completed_count > 0 else "-"
        max_time = max(r["time"] for r in completed_results) if completed_count > 0 else "-"
        avg_time = sum(r["time"] for r in completed_results) / completed_count if completed_count > 0 else "-"
        avg_input_tokens = sum(r["input_tokens"] for r in completed_results) / completed_count if completed_count > 0 else "-"
        avg_output_tokens = sum(r["output_tokens"] for r in completed_results) / completed_count if completed_count > 0 else "-"
        
        # 计算正确率
        correct_count = 0
        accuracy = 0
        if "期望答案" in df.columns:
            judge_col = f"{model_info['showname']}结果"
            correct_count = sum(1 for x in df[judge_col] if x == 1)
            accuracy = correct_count / (len(df)-1) * 100
            
        stats_data.append([
            model_info['showname'],
            f"{round(min_time)}ms",
            f"{round(max_time)}ms",
            f"{round(avg_time)}ms",
            round(avg_input_tokens),
            round(avg_output_tokens),
            completed_count,
            f"{round(completion_rate, 1)}%",
            correct_count,
            f"{round(accuracy, 1)}%"
        ])
    
    stats_df = pd.DataFrame(
        stats_data,
        columns=["模型", "最小响应时间", "最大响应时间", "平均响应时间", "平均输入Token", "平均输出Token", "完成数", "完成率", "正确数", "正确率"]
    )

    # 保存结果
    os.makedirs("runtime", exist_ok=True)
    result_file = "runtime/result.csv"
    df.to_csv(result_file, index=False)

    # 限制显示的数据量
    display_df = df.head(100)
    total_rows = len(df)
    display_rows = len(display_df)
    
    # 如果数据被缩减，显示提示信息
    label_text = f"表格内容（📊 总数据量：{total_rows} 条，当前显示：{display_rows} 条，更多请下载表格）" if total_rows > display_rows else "表格内容"

    # 设置列宽：结果列120，其他列250
    column_widths = [120 if col.endswith("结果") else 250 for col in display_df.columns]

    return stats_df, gr.update(value=display_df, label=label_text, column_widths=column_widths), result_file