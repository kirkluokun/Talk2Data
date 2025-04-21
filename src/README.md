# 金融数据分析系统

一个基于自然语言处理的金融数据分析系统，支持通过自然语言查询和分析A股上市公司的财务数据。

## 功能特点

- 自然语言查询接口
- 多维度财务数据分析
- 智能数据可视化
- 实时数据更新
- 支持多种数据导出格式

## 系统要求

- Python 3.8+
- SQLite 3.x
- 足够的磁盘空间用于数据存储

## 安装步骤

### 方法一：使用 Miniconda

1. 安装 Miniconda:
   - Windows: 从[Miniconda官网](https://docs.conda.io/en/latest/miniconda.html)下载安装包
   - Linux/Mac:
   ```bash
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   bash Miniconda3-latest-Linux-x86_64.sh
   ```

2. 创建并激活环境:
```bash
# 创建Python 3.8环境
conda create -n finance python=3.8
# 激活环境
conda activate pandasai_env
```

3. 安装依赖:
```bash
# 安装基础依赖
conda install pip
# 安装项目依赖
pip install -e .
```

### 必要配置

1. 配置环境变量:
根目录创建 `.env` 文件并设置以下变量:
```
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

2. 准备数据:
将数据库文件 `Astock_financial_data.db` 放置在 `data/` 目录下。

## 项目依赖说明

主要依赖包括：

```toml
# 核心依赖
pandas>=1.5.0
numpy>=1.21.0
sqlalchemy>=1.4.0

# LLM & AI 相关
openai>=1.0.0
litellm>=0.1.0
pandasai>=0.1.0

# Web 界面
streamlit>=1.15.0

# 数据可视化
matplotlib>=3.5.0
plotly>=5.5.0
seaborn>=0.11.0
```

完整依赖列表请参考 `pyproject.toml`。

## 目录结构

```
financial-analysis-system/
├── data/                   # 数据文件
├── src/                    # 源代码
│   ├── agent/             # AI代理模块
│   ├── web/               # Web界面
│   └── output/            # 输出文件
├── tests/                 # 测试文件
└── docs/                  # 文档
```

## 启动应用

1. 启动Web界面:
```bash
streamlit run src/web/web.py
```

2. 在浏览器中访问:
```
http://localhost:8501
```

## 使用示例

1. 基础查询:
```
查询贵州茅台2023年的营业收入和净利润
```

2. 行业分析:
```
分析电子行业2023年营收前10名公司的毛利率变化
```

3. 财务指标分析:
```
计算2023年所有A股上市公司的ROE中位数
```

## 开发规范

- 代码风格遵循PEP 8
- 所有Python文件使用小写字母和下划线命名
- 配置文件统一放在config/目录
- 每个目录必须包含__init__.py

## 常见问题

1. 数据库连接错误
   - 检查数据库文件是否存在
   - 确认数据库路径配置正确

2. API密钥问题
   - 确保.env文件包含有效的API密钥
   - 检查API密钥权限设置

3. 依赖安装问题
   - 如果pip安装失败，尝试使用conda安装
   - 确保Python版本兼容(3.8+)
   - Windows用户可能需要安装对应的C++构建工具

4. 环境激活问题
   - Windows: 如果无法激活环境，请以管理员身份运行PowerShell
   - Linux/Mac: 确保有执行权限 `chmod +x venv/bin/activate`

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证
