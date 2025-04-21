import sys
import matplotlib.pyplot as plt


def config_matplotlib():
    """
    配置matplotlib的中文字体支持
    使用系统自带的中文字体
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    try:
        # 设置字体
        if sys.platform == 'darwin':  # macOS
            plt.rcParams['font.family'] = ['Arial Unicode MS']
        else:  # Windows 和其他系统
            plt.rcParams['font.family'] = ['SimHei']
        
        # 其他通用设置
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['figure.figsize'] = [10, 6]
        plt.rcParams['figure.dpi'] = 300  # 提高DPI以获得更清晰的显示
        
    except Exception as e:
        print(f"字体配置错误: {str(e)}")

