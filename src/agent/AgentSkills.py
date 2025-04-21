import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import Dict, Any, Union, List, Optional
from pandasai.skills import skill
from datetime import datetime
from matplotlib.dates import AutoDateLocator, DateFormatter, YearLocator, MonthLocator
from pydantic import BaseModel, Field, model_validator  # 确保使用v2的验证器
from pydantic.v1 import BaseModel  # 如果必须使用v1语法
import warnings

def date_format(date: str) -> Optional[str]:
    """
    标准化日期格式。
    
    Args:
        date: 支持多种日期格式输入，如:
            - 标准日期: '2023-12-31', '2023/12/31'
            - 数字格式: '20231231'
            - 中文格式: '2023年12月31日'
            
    Returns:
        str: 'yyyymmdd'格式的日期字符串，如'20231231'
    """
    try:
        # 处理空值
        if pd.isna(date):
            return None
            
        # 如果已经是datetime对象，直接格式化
        if isinstance(date, (pd.Timestamp, datetime)):
            return date.strftime("%Y%m%d")
            
        # 移除空格并处理中文日期
        date = str(date).strip()
        if '年' in date:
            date = date.replace('年', '-').replace('月', '-').replace('日', '')
            
        # 对于 'yyyy-mm-dd' 格式的特殊处理
        if len(date) == 10 and date[4] == '-' and date[7] == '-':
            year = date[:4]
            month = date[5:7]
            day = date[8:]
            return f"{year}{month}{day}"
            
        # 尝试直接转换
        try:
            return pd.to_datetime(date).strftime("%Y%m%d")
        except Exception:
            # 尝试常见格式
            formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%m/%d/%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(date, fmt).strftime("%Y%m%d")
                except Exception:
                    continue
                    
        raise ValueError(f"无法解析的日期格式: {date}")
        
    except Exception as e:
        print(f"日期格式转换错误: {str(e)}")
        return None

class AgentSkills:
    """PandasAI Agent 的技能集合类"""
    
    @staticmethod
    @skill
    def setup_matplotlib_fonts() -> Dict[str, bool]:
        """
        配置 matplotlib 的中文字体支持。
        
        此函数自动检测并配置当前操作系统上可用的中文字体，解决matplotlib图表中的中文显示问题。
        无需任何参数，直接调用即可应用适合当前系统的中文字体设置。
        
        使用方法:
            在生成matplotlib图表之前，调用此函数:
            ```
            setup_matplotlib_fonts()
            plt.figure()
            # ... 绘图代码 ...
            ```
        
        Returns:
            Dict[str, bool]: 包含配置状态的字典
                - success: 配置过程是否成功完成
                - font_found: 是否找到可用的中文字体
        """
        try:
            # 在MacOS上设置非图形后端以避免fork崩溃
            if os.sys.platform.startswith('darwin'):
                # 在主进程中，必须在任何matplotlib操作前设置后端
                mpl.use('Agg')  # 使用非交互式后端
                
                # 设置一个环境变量以防止ObjC运行时的fork问题
                os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
            
            # 忽略字体警告
            warnings.filterwarnings("ignore", category=UserWarning)
            
            # 设置全局字体
            font_found = False
            if os.sys.platform.startswith('win'):
                font_list = ['SimHei', 'Microsoft YaHei']
            elif os.sys.platform.startswith('darwin'):
                font_list = ['PingFang HK', 'Arial Unicode MS']
            else:
                font_list = ['WenQuanYi Zen Hei', 'DejaVu Sans']

            # 配置字体
            for font in font_list:
                try:
                    mpl.font_manager.findfont(font)
                    plt.rcParams['font.family'] = font
                    font_found = True
                    break
                except Exception:
                    continue

            # 设置默认字体大小和其他参数
            plt.rcParams['font.size'] = 12
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['figure.figsize'] = [10, 10]
            plt.rcParams['figure.dpi'] = 100
            
            return {"success": True, "font_found": font_found}
        except Exception as e:
            print(f"设置matplotlib字体时出错: {str(e)}")
            return {"success": False, "error": str(e)}
            
    @skill
    # 写一个提示性函数，不需要有计算功能
    def plot_notice_prompt(self, query: str) -> str:
        """
        你拿到的数据中【报告日】格式是日期格式datetime，在处理的时候注意不要用str()函数。
        在横坐标的坐标轴的报告日标签的显示要转换为使用文本格式，坐标轴日期要用yyyymmdd格式。
        """
        return f"写一个提示性函数，不需要有计算功能，提示性函数内容为：{query}"
    
    @staticmethod
    @skill
    def bar_line_chart_skills(
        data: pd.DataFrame,
        x_col: str,
        y_col_primary: str,
        y_col_secondary: str,
        title: str
    ) -> Dict[str, Any]:
        """
        绘制财务指标的柱状图+增速折线的组合图。
        
        Args:
            data: pd.DataFrame
            x_col: 报告日(yyyymmdd格式)
            y_col_primary: 财务指标(柱状图)
            y_col_secondary: 财务指标增速(折线图)
            title: 图表标题
            
        Returns:
            output_path:图表的相对路径
        """
        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False

            # 转换日期格式：保持原始字符串格式用于显示，转换为datetime用于排序
            data = data.copy()
            data['datetime_col'] = pd.to_datetime(data[x_col], format='%Y%m%d')
            data = data.sort_values('datetime_col')

            # 创建图表
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # 使用数值化的日期坐标（解决自动缩放问题）
            x_dates_num = mpl.dates.date2num(data['datetime_col'])
            bar_width = 60  # 以天为单位的柱宽

            # 绘制柱状图（使用数值化日期）
            ax1.bar(x_dates_num, data[y_col_primary], 
                    color='#4472C4', width=bar_width, align='center')

            # 设置背景网格
            ax1.grid(True, linestyle='--', alpha=0.3, axis='y')
            ax1.set_axisbelow(True)
            ax1.set_ylabel(f'{title}（单位）', fontsize=10)
            ax1.set_ylim(0, ax1.get_ylim()[1])

            # 创建第二个Y轴
            ax2 = ax1.twinx()

            # 绘制折线图（右轴）
            ax2.plot(
                x_dates_num,
                data[y_col_secondary],
                color='#ED7D31',
                linewidth=2, 
                marker='o',
                markersize=6
            )
            ax2.set_ylabel('增速', fontsize=10)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.2f}%'))

            # 修改刻度设置部分
            # 动态计算最大刻度数（根据图表宽度）
            max_ticks = min(15, len(data))  # 最大显示15个刻度
            step = max(1, (len(data)-1) // max_ticks)
            
            # 确保包含最后一个数据点
            selected_ticks = list(range(0, len(data), step)) 
            if (len(data)-1) not in selected_ticks:
                selected_ticks.append(len(data)-1)
            
            ax1.set_xticks(x_dates_num[selected_ticks])
            
            # 必须保留日期格式化函数
            def format_date(x: float, _: Any) -> str:
                dt = mpl.dates.num2date(x)
                return dt.strftime('%Y%m%d')
            
            ax1.xaxis.set_major_formatter(plt.FuncFormatter(format_date))
            
            # 缩小标签字体大小
            plt.xticks(
                rotation=45,
                ha='right',
                rotation_mode='anchor',
                fontsize=7
            )
            
            # 强制设置x轴刻度标签旋转角度
            ax1.tick_params(axis='x', rotation=45)
            
            # 自动调整subplot边距
            plt.subplots_adjust(bottom=0.25)

            # 添加网格线
            ax1.grid(True, which='major', axis='both', linestyle='-', alpha=0.2)
            
            # 调整布局，确保日期标签不被截断
            plt.tight_layout()

            # 移除上边框
            ax1.spines['top'].set_visible(False)
            ax2.spines['top'].set_visible(False)

            # 保存路径
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_bar_line_chart.png"
            output_path = os.path.join("src", "output", "PDA", "charts", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()

            return output_path

        except Exception as e:
            print(f"生成图表时出错: {str(e)}")
            return None

    @staticmethod
    @skill
    def calculate_quarterly_data(
        data: pd.DataFrame, 
        date_col: str, 
        value_cols: Union[str, List[str]],
        stock_code_col: str = "股票代码",
        stock_name_col: str = "股票名称"
    ) -> pd.DataFrame:
        """
        计算单季度数据

        Args:
            data : pd.DataFrame - 包含财务数据的数据框
            date_col : str - 报告日期列名(yyyymmdd格式)
            value_cols : Union[str, List[str]] - 要计算单季度值的财务科目列名，可以是单个字符串或字符串列表
            stock_code_col : str - 股票代码列名，默认为"股票代码"
            stock_name_col : str - 股票名称列名，默认为"股票名称"
            
        Returns:
            pd.DataFrame - 包含计算后的单季度数据的DataFrame，其中：
                - 保留原始财务指标值列
                - 新增"年份"和"季度"列
                - 新增"单季度+原列名"格式的计算列，如"单季度营业收入"
                - 返回空DataFrame则表示计算出错
        """
        try:
            # 将单个字符串转换为列表
            if isinstance(value_cols, str):
                value_cols = [value_cols]
                
            # 复制输入数据
            df = data.copy()
            
            # 找出所有原始信息列（除了将被处理的财务指标列）
            all_cols = list(df.columns)
            info_cols = [col for col in all_cols if col not in value_cols and col != date_col]
            
            # 确保股票代码为6位字符串格式
            df[stock_code_col] = df[stock_code_col].astype(str).str.zfill(6)
            
            # 确保日期列为datetime类型
            df[date_col] = pd.to_datetime(df[date_col])
            
            # 提取年份和季度
            df['年份'] = df[date_col].dt.year
            df['季度'] = df[date_col].dt.quarter.map({1: '1', 2: '2', 3: '3', 4: '4'})
            
            result_dfs = []
            # 按股票分组处理
            for (code, name), group in df.groupby([stock_code_col, stock_name_col]):
                # 按日期排序
                group = group.sort_values(date_col)
                
                # 保留所有原始信息列、处理日期和原始财务指标列
                result_dict = {}
                for col in info_cols:
                    result_dict[col] = group[col].values
                    
                result_dict.update({
                    date_col: group[date_col].values,
                    '年份': group['年份'].values,
                    '季度': group['季度'].values
                })
                
                # 保留原始财务指标列
                for value_col in value_cols:
                    result_dict[value_col] = group[value_col].values
                
                # 处理每个财务科目，计算单季度值
                for value_col in value_cols:
                    quarterly_values = []
                    for idx, row in group.iterrows():
                        quarter = row['季度']
                        if quarter == '1':
                            # 第一季度直接使用当期值
                            quarterly_values.append(row[value_col])
                        else:
                            # 获取同一年度的上一季度数据
                            same_year_prev_data = group[
                                (group['年份'] == row['年份']) & 
                                (group[date_col] < row[date_col])
                            ]
                            
                            if len(same_year_prev_data) > 0:
                                prev_value = same_year_prev_data.iloc[-1][value_col]
                                quarterly_value = row[value_col] - prev_value
                            else:
                                # 如果找不到上一季度数据，使用当期值
                                quarterly_value = row[value_col]
                                
                            quarterly_values.append(quarterly_value)
                    
                    result_dict[f'单季度{value_col}'] = quarterly_values
                
                result_dfs.append(pd.DataFrame(result_dict))
            
            if not result_dfs:
                return pd.DataFrame()
            
            # 合并所有结果
            final_df = pd.concat(result_dfs, ignore_index=True)
            
            # 排序
            final_df = final_df.sort_values([stock_code_col, date_col])
            
            # 获取原始所有列名
            original_cols = data.columns.tolist()
            # 获取新生成的列名
            generated_cols = ['年份', '季度'] + [f'单季度{col}' for col in value_cols]

            # 构建最终列顺序：保留原始列，追加新生成的列（如果存在且不重复）
            final_cols_order = original_cols + [
                gc for gc in generated_cols
                if gc in final_df.columns and gc not in original_cols
            ]

            # 确保返回的列都实际存在于 final_df 中
            existing_final_cols = [c for c in final_cols_order if c in final_df.columns]

            return final_df[existing_final_cols]
            
        except Exception as e:
            print(f"计算单季度数据时出错: {str(e)}")
            # 返回空DataFrame
            return pd.DataFrame()

    @staticmethod
    @skill
    def yoy_or_qoq_growth(
        data: pd.DataFrame,
        date_col: str,
        value_cols: Union[str, List[str]],
        freq: str = "同比增速",
        stock_code_col: str = "股票代码",
        stock_name_col: str = "股票名称"
    ) -> pd.DataFrame:
        """
        计算同比增速或环比增速
        
        Args:
            data : pd.DataFrame - 包含财务数据的数据框
            date_col : str - 报告日期列名(yyyymmdd格式)
            value_cols : Union[str, List[str]] - 要计算增速的财务科目列名，可以是单个字符串或字符串列表
            freq : str - 增速类型，可选值为"同比增速"或"环比增速"，默认为"同比增速"
            stock_code_col : str - 股票代码列名，默认为"股票代码"
            stock_name_col : str - 股票名称列名，默认为"股票名称"
            
        Returns:
            pd.DataFrame - 包含计算后的增速数据的DataFrame，其中：
                - 保留原始财务指标值列
                - 新增"年份"和"季度"列（如果原数据中没有）
                - 新增"{指标}_同比增速"或"{指标}_环比增速"格式的计算列，如"营业收入_同比增速"
        """
        try:
            # 将单个字符串转成列表
            if isinstance(value_cols, str):
                value_cols = [value_cols]

            df = data.copy()
            
            # 找出所有可能的基础信息列
            all_cols = list(df.columns)
            info_cols = [col for col in all_cols if col not in value_cols 
                        and col != date_col and col != '年份' and col != '季度']
            
            # 确保股票代码列是字符串
            df[stock_code_col] = df[stock_code_col].astype(str)
            
            # 将日期列转为 datetime 类型
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col])
            
            # 提取年份和季度(如果还没有)
            if '年份' not in df.columns:
                df["年份"] = df[date_col].dt.year
            if '季度' not in df.columns:
                df["季度"] = df[date_col].dt.quarter
            
            # 按 [股票代码, 日期] 排序
            df = df.sort_values(by=[stock_code_col, date_col]).reset_index(drop=True)
            
            # 根据 freq 选择计算方式
            if freq == "同比增速":
                for col in value_cols:
                    yoy_col = f"{col}_同比增速"
                    df[yoy_col] = (
                        df.groupby([stock_code_col, "季度"])[col]
                        .pct_change(periods=1, fill_method=None) * 100
                    )
            elif freq == "环比增速":
                for col in value_cols:
                    qoq_col = f"{col}_环比增速"
                    df[qoq_col] = (
                        df.groupby(stock_code_col)[col]
                        .pct_change(periods=1, fill_method=None) * 100
                    )
            else:
                raise ValueError("freq 参数只能是 '同比增速' 或 '环比增速'。")

            # 获取原始所有列名
            original_cols = data.columns.tolist()
            # 获取新生成的增速列名
            growth_cols = [f"{col}_{'同比' if freq == '同比增速' else '环比'}增速"
                           for col in value_cols]

            # 构建最终列顺序：保留原始列，追加新生成的增速列（如果存在且不重复）
            final_cols_order = original_cols + [
                gc for gc in growth_cols
                if gc in df.columns and gc not in original_cols
            ]

            # 确保返回的列都实际存在于 df 中
            existing_final_cols = [c for c in final_cols_order if c in df.columns]

            return df[existing_final_cols]

        except Exception as e:
            print(f"计算同比/环比增速时出错: {str(e)}")
            return pd.DataFrame()