# matplotlib_config.py
# matplotlib配置模块，用于设置matplotlib的中文字体支持和其他参数

import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import warnings

def setup_matplotlib_config():
    """配置 matplotlib 的中文字体支持"""
    # 忽略字体警告
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # 设置全局字体
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
            break
        except Exception:
            continue

    # 设置默认字体大小和其他参数
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['figure.figsize'] = [10, 6]
    plt.rcParams['figure.dpi'] = 100
