"""Anthropic Claude LLM

This module is to run the Anthropic Claude API hosted and maintained by Anthropic.
To read more on Anthropic Claude follow
https://docs.anthropic.com/en/api/getting-started

Example:
    Use below example to call Anthropic Claude Model

    >>> from pandasai.llm.anthropic_claude import AnthropicClaude
"""

from typing import Any, Optional, Dict
import anthropic
from pandasai.llm.base import LLM
from pandasai.exceptions import APIKeyNotFoundError
from pandasai.prompts.base import BasePrompt
from pandasai.pipelines.pipeline_context import PipelineContext


class AnthropicClaude(LLM):
    """Anthropic Claude LLM
    LLM class extended for Anthropic Claude model.
    """

    _supported_models = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
    ]

    _valid_params = [
        "max_tokens",
        "model",
        "temperature",
        "top_p",
    ]

    max_tokens: int = 1024
    model: str = "claude-3-sonnet-20240229"
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    anthropic_client: Any

    def __init__(self, api_key: str, **kwargs):
        """初始化 Anthropic Claude 客户端
        
        Args:
            api_key: Anthropic API 密钥
            **kwargs: 其他参数
        """
        if not api_key:
            raise APIKeyNotFoundError("Anthropic API key is required")
        
        self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        
        for key, val in kwargs.items():
            if key in self._valid_params:
                setattr(self, key, val)

    @property
    def _default_params(self) -> Dict[str, Any]:
        """获取默认参数"""
        params = {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        
        # 只在 top_p 有效值时添加
        if isinstance(self.top_p, (int, float)) and 0 <= self.top_p <= 1:
            params["top_p"] = self.top_p
            
        return params

    def call(self, instruction: BasePrompt, context: PipelineContext = None) -> str:
        """调用 Anthropic API 生成文本
        
        Args:
            instruction: 提示词
            context: 管道上下文
            
        Returns:
            生成的文本响应
        """
        prompt = instruction.to_string()
        memory = context.memory if context else None

        messages = []
        system_prompt = "you are a professional python data analyst, the only job is to generate the code to sovle the user's question to the dataframe, if the code is not working, you should try to fix it."
        
        if memory:
            if memory.agent_info:
                system_prompt = memory.get_system_prompt()

            # 添加历史消息
            for message in memory.all():
                if message["is_user"]:
                    messages.append({
                        "role": "user",
                        "content": message["message"]
                    })
                else:
                    messages.append({
                        "role": "assistant", 
                        "content": message["message"]
                    })

        # 添加当前提示词
        messages.append({
            "role": "user",
            "content": prompt
        })

        # 获取API调用参数
        params = self._default_params.copy()
        
        # 调用 API
        response = self.anthropic_client.messages.create(
            model=self.model,
            messages=messages,
            system=system_prompt,
            **params  # 使用处理过的参数
        )

        self.last_prompt = prompt
        return response.content[0].text

    @property
    def type(self) -> str:
        return "anthropic-claude"
