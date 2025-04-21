from setuptools import setup, find_packages

setup(
    name="financial_data_chat",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "pydantic",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "celery",
        "redis",
        "litellm",
        "pandasai",
        "smolagents",
        "python-multipart",
        "PyYAML",
    ],
) 