# 构建一个query_parser_agent函数，负责解析用户的自然语言查询并转换为结构化数据。
# 函数的输入参数是：用户的query，返回值是：结构化数据结论
# 函数的逻辑
# 1、llm初始化
# 2、加载财务术语对照表
# 3、加载prompt模板
# 4、解析用户查询，提取基本信息
# 5、标准化财务指标
# 6、生成计算步骤
# 7、返回结构化数据结论

import json
import os
import yaml  # 添加yaml库导入
import re
from typing import Dict, List, Tuple, Optional
from litellm import completion

def query_parser_agent(
    user_query: str, model: str = "deepseek-chat", progress_callback=None
) -> Dict:
    """解析用户查询并返回结构化数据和保存结果的路径
    
    Args:
        user_query: 用户输入的自然语言查询字符串
        model: 使用的模型，可选 "deepseek-chat"、"gpt-4" 或 "gpt-4-0613"
        progress_callback: 可选的进度回调函数，用于报告进度
        
    Returns:
        Dict: 包含用户问题和解析结果的字典
    """
    # 初始化QueryParserAgent和QueryJudgeAgent
    parser_agent = QueryParserAgent(model=model)
    
    # 报告开始解析
    if progress_callback:
        progress_callback(5.0, "开始解析查询")
    
    # 解析用户查询
    parse_result = parser_agent.parse_query(
        user_query, progress_callback=progress_callback
    )
    
    # 更新进度
    if progress_callback:
        progress_callback(33.0, "查询解析完成")
    
    # 判断查询难度
    # difficulty_level = judge_agent.judge_query_difficulty(user_query)
    
    # 合并结果
    result = parse_result.copy()
    # result["难度等级"] = difficulty_level
    
    return result

class QueryParserAgent:
    """查询解析代理，负责解析用户的自然语言查询并转换为结构化数据"""

    # 最大重试次数
    MAX_RETRIES = 3

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def __init__(self, 
                 model: str = "deepseek-chat"):
        """初始化查询解析代理
        
        Args:
            model: 使用的模型，可选 "deepseek-chat"、"gpt-4" 或 "gpt-4-0613"
        """
        # 常用财务指标的手动映射表
        self.manual_mappings = {
            "归母净利润": "归属于母公司的净利润",
            "归属于母公司所有者的净利润": "归属于母公司的净利润",
            "归属于母公司股东的净利润": "归属于母公司的净利润",
            "归母净利": "归属于母公司的净利润",
            "归属于母公司净利": "归属于母公司的净利润"
        }
        
        self.model = model
        self.temperature = 0
        self.max_tokens = 2000
        
        # 设置环境变量
        os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")
        
        # 根据模型选择配置
        self.model_name = "deepseek/deepseek-chat"
        os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com/v1"
            
        self._load_financial_terms()
        self._load_table_columns()
        self._load_prompts()
        
    def _load_financial_terms(self):
        """加载金融术语和列名解释"""
        self.standard_terms = set()
        self.aliases = {}
        
        try:
            # 使用相对于当前文件的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_columns_path = os.path.join(
                current_dir, "db_columns_explained.json"
            )
            # print(f"Attempting to load financial terms from: {db_columns_path}") # 移除调试打印
            
            with open(db_columns_path, "r", encoding="utf-8") as f:
                self.db_columns = json.load(f) # 保持加载原始数据
                # print(f"Raw data loaded from db_columns_explained.json (first 500 chars): {str(self.db_columns)[:500]}") # 移除调试打印
                
                # 正确逻辑: 检查顶层结构并访问 'aliases' 键下的嵌套字典
                if isinstance(self.db_columns, dict) and 'aliases' in self.db_columns:
                    alias_mapping = self.db_columns['aliases']
                    if isinstance(alias_mapping, dict):
                        for alias, standard_name in alias_mapping.items():
                            if isinstance(standard_name, str): # 确保值是字符串
                                self.standard_terms.add(standard_name)
                                self.aliases[alias] = standard_name
                    else:
                         print(f"Warning: Expected 'aliases' key in {db_columns_path} to contain a dictionary, but found {type(alias_mapping)}.")
                else:
                    print(f"Warning: Expected {db_columns_path} to be a JSON object with an 'aliases' key.")


                # 确保标准名自身也能被识别（来自 db_columns_names.json）
                # 这一步很重要，因为它能把 db_columns_names.json 中定义的列名也加入 standard_terms
                if hasattr(self, 'table_columns') and isinstance(self.table_columns, dict):
                   for table_info in self.table_columns.values():
                       if isinstance(table_info, dict):
                           for col_name in table_info.get("columns", []):
                               self.standard_terms.add(col_name)


        except FileNotFoundError:
             print(f"Error: Financial terms file not found at {db_columns_path}")
             self.db_columns = {}
             self.standard_terms = set()
             self.aliases = {}
        except json.JSONDecodeError:
             print(f"Error: Failed to decode JSON from {db_columns_path}")
             self.db_columns = {}
             self.standard_terms = set()
             self.aliases = {}
        except Exception as e:
            print(f"加载金融术语时发生意外错误: {str(e)}")
            import traceback
            print(traceback.format_exc())
            # 使用默认空字典/集合，避免完全失败
            self.db_columns = {}
            self.standard_terms = set()
            self.aliases = {}
        
    def _load_table_columns(self):
        """加载数据库表结构信息"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            table_columns_path = os.path.join(
                current_dir, "db_columns_names.json"
            )
            
            with open(table_columns_path, "r", encoding="utf-8") as f:
                self.table_columns = json.load(f)
        except Exception as e:
            print(f"加载数据库表结构信息失败: {str(e)}")
            self.table_columns = {}
            
    def _get_table_for_column(self, column_name: str) -> Optional[str]:
        """确定财务科目属于哪个表
        
        Args:
            column_name: 标准化后的财务科目名称
            
        Returns:
            str: 表名 (income_table/balance_table/cashflow_table/ratio_table) 
                 或 None
        """
        for table_name, table_info in self.table_columns.items():
            if column_name in table_info["columns"]:
                return table_name
        return None
        
    def _load_prompts(self):
        """加载prompt模板"""
        try:
            # 使用相对于当前文件的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_path = os.path.join(
                current_dir, "prompt/QPA_extract_prompt.yaml"
            )
            
            # 加载提取信息的prompt
            # 使用with语句打开文件，确保文件在使用完毕后被关闭
            with open(prompt_path, "r", encoding="utf-8") as f:
                # 读取yaml文件内容
                yaml_content = yaml.safe_load(f)
                # 构建完整的prompt
                self.QPA_extract_prompt = (
                    f"{yaml_content['system_prompt']}\n\n"
                    f"请返回结果，严格遵守返回格式如下：\n"
                    f"{yaml_content['return_format']}"
                )
        except Exception as e:
            print(f"加载prompt模板失败: {str(e)}")
            # 使用默认提示模板
            self.QPA_extract_prompt = (
                "请解析用户查询，提取关键信息，并返回JSON格式。"
            )
            
    def _match_financial_term(
        self, term: str
    ) -> Tuple[Optional[str], List[str]]:
        """匹配财务术语的标准名称
        
        Args:
            term: 用户输入的财务指标名称
            
        Returns:
            Tuple[str, List[str]]: (匹配到的标准名称, 候选列表)
        """
        # 1. 首先检查手动映射表
        if term in self.manual_mappings:
            return self.manual_mappings[term], []
            
        # 2. 检查是否直接是标准名称
        if term in self.standard_terms:
            return term, []
        
        # 3. 检查是否是别名
        if term in self.aliases:
            return self.aliases[term], []
            
        # 4. 如果都没找到匹配，返回原始术语
        return term, []
        
    def _clean_string(self, text: str) -> str:
        """清理字符串中的转义字符和多余的引号
        
        Args:
            text: 需要清理的字符串
            
        Returns:
            str: 清理后的字符串
        """
        if not isinstance(text, str):
            return text
        
        # 移除所有转义字符和引号
        text = text.replace('\\', '').replace('"', '').replace("'", '')
        # 移除末尾的逗号
        text = text.rstrip(',')
        # 清理空白字符
        text = text.strip()
        
        # 如果是逗号分隔的列表，清理每个项
        if ',' in text:
            items = [
                item.strip().replace('"', '').replace("'", '') 
                for item in text.split(',')
            ]
            text = ', '.join(filter(None, items))
        
        # 移除中文标点符号
        text = re.sub(r'[，。；：""【】《》？！]', '', text)
        
        return text
    
    def _format_validation_and_cleaning(self, extracted_info: Dict) -> Dict:
        """验证并清理解析结果的格式
        
        Args:
            extracted_info: 从LLM解析出的原始信息
            
        Returns:
            Dict: 清理和格式化后的信息
        """
        cleaned_info = {}
        
        # 确保必要的字段存在
        required_fields = [
            "报告日区间", "筛选的股票名称", "行业名称", "需要从sql抽取的财务指标"
        ]
        for field in required_fields:
            if field not in extracted_info:
                extracted_info[field] = (
                    "" if field != "需要从sql抽取的财务指标" else []
                )
        
        # 清理和格式化报告日区间
        if "报告日区间" in extracted_info:
            date_range = extracted_info["报告日区间"]
            # 确保日期格式为YYYYMMDD-YYYYMMDD
            date_pattern = r'\d{8}-\d{8}'
            if not re.match(date_pattern, date_range):
                # 尝试提取数字并格式化
                dates = re.findall(r'\d{8}', date_range)
                if len(dates) >= 2:
                    date_range = f"{dates[0]}-{dates[1]}"
                elif len(dates) == 1:
                    date_range = f"{dates[0]}-{dates[0]}"
                else:
                    date_range = ""
            cleaned_info["报告日区间"] = date_range
        
        # 清理股票名称和行业名称
        cleaned_info["筛选的股票名称"] = self._clean_string(
            extracted_info.get("筛选的股票名称", "")
        )
        cleaned_info["行业名称"] = self._clean_string(
            extracted_info.get("行业名称", "")
        )
        
        # 处理财务指标
        if "需要从sql抽取的财务指标" in extracted_info:
            indicators = extracted_info["需要从sql抽取的财务指标"]
            if isinstance(indicators, str):
                # 如果是字符串，尝试解析为列表
                indicators = [
                    ind.strip() for ind in indicators.split(',') if ind.strip()
                ]
            
            # 确保每个指标格式正确: "指标名称来自:表名"
            formatted_indicators = []
            valid_tables = {
                "income_table", "balance_table", "cashflow_table", "ratio_table"
            }
            for indicator in indicators:
                if isinstance(indicator, str):
                    # 清理指标字符串
                    indicator = self._clean_string(indicator)
                    # 检查格式是否正确
                    if "来自:" in indicator:
                        ind_parts = indicator.split("来自:")
                        if len(ind_parts) == 2 and ind_parts[1] in valid_tables:
                            formatted_indicators.append(indicator)
                        else:
                            # 尝试修复格式
                            ind_name = ind_parts[0].strip()
                            table_name = self._get_table_for_column(ind_name)
                            if table_name:
                                formatted_indicators.append(
                                    f"{ind_name}来自:{table_name}"
                                )
                    else:
                        # 没有表名信息，尝试确定表名
                        ind_name = indicator.strip()
                        table_name = self._get_table_for_column(ind_name)
                        if table_name:
                            formatted_indicators.append(
                                f"{ind_name}来自:{table_name}"
                            )
            
            cleaned_info["需要从sql抽取的财务指标"] = formatted_indicators
        
        return cleaned_info

    def _extract_basic_info(
        self, user_query: str, progress_callback=None
    ) -> Dict:
        """从用户的自然语言查询中提取结构化的财务查询信息，失败时自动重试
        
        该方法使用LiteLLM API解析用户的自然语言查询,提取关键信息并进行标准化处理。
        
        Args:
            user_query: 用户输入的自然语言查询字符串
            progress_callback: 可选的进度回调函数，用于报告进度
            
        Returns:
            Dict: 包含以下字段的字典:
                - 报告日区间: 查询的时间范围
                - 股票名称: 查询的股票名称
                - 行业名称: 查询的行业分类
                - 财务指标: 标准化后的财务指标列表
                - 需要计算的指标: 需要计算的指标列表
                - usage: token使用统计
                
        Raises:
            Exception: 所有重试都失败时抛出
        """
        errors = []
        retry_count = 0
        
        # 重试循环
        while retry_count < self.MAX_RETRIES:
            try:
                # 报告进度 - 提取查询关键信息
                if progress_callback:
                    progress_callback(15.0, "提取查询关键信息")
                
                # 调用LiteLLM API进行自然语言解析
                response = completion(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.QPA_extract_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                # 解析API返回的结果
                result = response.choices[0].message.content
                print(f"原始API响应内容: {result}")
                
                # 使用正则表达式分割字符串，处理各种可能的换行符形式
                # 包括实际的\n换行符和文本中的\\n字符串
                lines = re.split(r'\\n|\n', result.strip())
                print(f"分割后的行数: {len(lines)}")
                extracted_info = {}
                
                # 逐行处理API返回的结果
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = self._clean_string(value.strip())  # 清理字符串
                        
                        if key == "需要从sql抽取的财务指标":
                            # 报告进度 - 标准化财务指标
                            if progress_callback:
                                progress_callback(25.0, "标准化财务指标")
                            
                            # 对财务科目进行标准化处理
                            raw_indicators = [
                                x.strip() 
                                for x in value.split(',') 
                                if x.strip()
                            ]
                            # 存储标准化后的指标和其所属表
                            formatted_indicators = []
                            
                            for indicator in raw_indicators:
                                # 使用_match_financial_term方法将财务指标转换为标准名称
                                std_name, _ = self._match_financial_term(
                                    indicator
                                )
                                # 确定该指标属于哪个表
                                table_name = self._get_table_for_column(
                                    std_name
                                )
                                if table_name:
                                    formatted_indicators.append(
                                        f"{std_name}来自:{table_name}"
                                    )
                                    
                            extracted_info[key] = formatted_indicators
                        else:
                            # 其他字段保持原样
                            extracted_info[key] = value    
              
                # 验证和清理结果格式
                cleaned_info = self._format_validation_and_cleaning(
                    extracted_info
                )
                
                # 检查结果是否有效
                if "需要从sql抽取的财务指标" in cleaned_info and cleaned_info[
                    "需要从sql抽取的财务指标"
                ]:
                    return cleaned_info
                else:
                    # 如果没有提取到财务指标，记录错误并重试
                    error_msg = "未能提取有效的财务指标信息"
                    errors.append(error_msg)
                    retry_count += 1
                    print(f"重试 {retry_count}/{self.MAX_RETRIES}: {error_msg}")
                    
            except Exception as e:
                # 捕获异常，记录错误并重试
                error_msg = str(e)
                errors.append(error_msg)
                retry_count += 1
                print(f"重试 {retry_count}/{self.MAX_RETRIES}: {error_msg}")
                import traceback
                print(traceback.format_exc())
        
        # 所有重试都失败，返回默认值
        print(f"达到最大重试次数 ({self.MAX_RETRIES})，所有尝试均失败")
        if errors:
            print(f"最后一次错误: {errors[-1]}")
            
        return {
            "报告日区间": "",
            "筛选的股票名称": "",
            "行业名称": "",
            "需要从sql抽取的财务指标": [],
        }

    def parse_query(self, user_query: str, progress_callback=None) -> Dict:
        """解析用户查询并返回结构化数据
        
        Args:
            user_query: 用户的查询字符串
            progress_callback: 可选的进度回调函数，用于报告进度
            
        Returns:
            Dict: 解析结果
        """
        import time
        start_time = time.time()
        
        try:
            # 提取并标准化基本信息
            parsed_info = self._extract_basic_info(
                user_query, progress_callback
            )
            
            # 计算耗时
            # end_time = time.time()
            # processing_time = end_time - start_time
            
            # 更新进度为30%，即将完成查询解析
            if progress_callback:
                progress_callback(30.0, "生成解析结果")
            
            # 构建结果
            result = {
                "解析结果": parsed_info
            }
            
            return result
            
        except Exception as e:
            print(f"解析过程中出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                "error": str(e),
                "traceback": traceback.format_exc()
            }


class QueryJudgeAgent:
    """查询判断代理，负责判断用户的查询是否符合要求"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化查询判断代理
        
        Args:
            model: 使用的模型，默认为 "gpt-4o-mini"
        """
        self.model = model
        self.model_name = f"openai/{model}"
        self.temperature = 0
        self.max_tokens = 500
        
        # 设置环境变量
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
        os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"
        
        # 加载判断难度的 prompt
        self._load_prompts()
        
    def _load_prompts(self):
        """加载判断难度的 prompt"""
        self.difficulty_prompt = """\
你是一个专业的金融数据查询分析助手。你的任务是判断用户金融数据查询的复杂度。

请根据以下标准判断查询难度:
- 难度等级2：如果查询包含计算需求，如增速、同比增速、环比增速、单季度数据、历史分位数计算、排名百分比%
- 难度等级1：如果查询只包含简单的数据筛选、排序等基本操作，要谨慎的判断是否属于简单问题

请分析以下查询，并仅返回难度等级（1或2），不要有任何其他输出。"""
    
    def judge_query_difficulty(self, user_query: str) -> int:
        """判断用户查询的难度等级
        
        Args:
            user_query: 用户输入的自然语言查询
            
        Returns:
            int: 难度等级，1或2
        """
        try:
            # 调用API进行难度判断
            response = completion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.difficulty_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result = response.choices[0].message.content.strip()
            
            # 提取难度等级，确保返回1或2
            try:
                if "2" in result:
                    return 2
                elif "1" in result:
                    return 1
                else:
                    # 如果结果中没有明确的1或2，默认返回1
                    return 1
            except Exception: # 捕获特定异常类型，避免bare except
                print("提取难度等级时出错，默认为1")
                return 1
                
        except Exception as e:
            print(f"判断查询难度时出错: {str(e)}")
            # 出错时默认返回难度等级1
            return 1


# 写一个测试代码
if __name__ == "__main__":
    # --- 自动化别名识别测试 --- 
    import random
    
    print("开始执行别名识别自动化测试...")
    agent = QueryParserAgent()
    
    # 检查 aliases 是否成功加载
    if not agent.aliases or not agent.table_columns:
        print("错误：未能成功加载别名或表结构信息，无法进行测试。请检查 _load_financial_terms 和 _load_table_columns 函数。")
    else:
        all_aliases = list(agent.aliases.keys())
        num_test_cases = 10
        aliases_per_case = 20
        total_passed = 0
        total_failed = 0

        if len(all_aliases) < aliases_per_case:
             print(f"错误：可用别名数量 ({len(all_aliases)}) 少于每次测试所需的数量 ({aliases_per_case})。")
        else:
            for i in range(num_test_cases):
                print(f"\n--- 测试案例 {i+1}/{num_test_cases} ---")
                selected_aliases = random.sample(all_aliases, aliases_per_case)
                print(f"随机选择的别名: {selected_aliases}")
                
                case_passed_count = 0
                case_failed_details = []
                
                for alias in selected_aliases:
                    std_name, _ = agent._match_financial_term(alias)
                    expected_std_name = agent.aliases.get(alias)
                    table_name = agent._get_table_for_column(std_name)
                    
                    # 验证逻辑
                    is_match_correct = (std_name == expected_std_name)
                    is_table_found = (table_name is not None)
                    
                    if is_match_correct and is_table_found:
                        case_passed_count += 1
                    else:
                        case_failed_details.append({
                            "别名": alias,
                            "期望标准名": expected_std_name,
                            "实际匹配名": std_name,
                            "找到的表名": table_name,
                            "匹配是否正确": is_match_correct,
                            "是否找到表": is_table_found
                        })
                
                total_passed += case_passed_count
                total_failed += len(case_failed_details)
                
                print(f"测试结果: 成功 {case_passed_count}/{aliases_per_case}")
                if case_failed_details:
                    print("失败详情:")
                    for detail in case_failed_details:
                         print(f"  - {detail}")
            
            print("\n--- 测试总结 ---")
            print(f"总测试别名数: {num_test_cases * aliases_per_case}")
            print(f"总成功数: {total_passed}")
            print(f"总失败数: {total_failed}")
            success_rate = (total_passed / (num_test_cases * aliases_per_case)) * 100 if (num_test_cases * aliases_per_case) > 0 else 0
            print(f"成功率: {success_rate:.2f}%")

    print("\n别名识别自动化测试结束.")
    
    # --- 原有的测试调用 (可以选择性注释掉) ---
    # test_query = \'\'\'
    # 20240331-20240930的数据中，找到存货周转天数、ROE、净利率、毛利率、营收、资产周转率、存货周转率都提升的公司
    # \'\'\'
    # result = query_parser_agent(test_query)
    # print("\n--- 原有查询测试结果 ---")
    # print(json.dumps(result, ensure_ascii=False, indent=2))
