import React from 'react';

/**
 * 聊天输入框组件属性
 */
type ChatInputProps = {
  // 接收输入值和更新函数
  value: string;
  onValueChange: (value: string) => void;
  // 发送消息的回调函数
  onSendMessage: (content: string) => void;
  // 是否禁用输入框
  disabled?: boolean;
  // 输入框占位文本
  placeholder?: string;
};

/**
 * 聊天输入框组件，包含输入框和发送按钮
 */
const ChatInput: React.FC<ChatInputProps> = ({ 
  value,
  onValueChange,
  onSendMessage, 
  disabled = false, 
  placeholder = "输入您的财务查询..." 
}) => {
  // 处理表单提交
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (value.trim() && !disabled) {
      onSendMessage(value.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex">
      <input
        type="text"
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
      />
      <button
        type="submit"
        disabled={!value.trim() || disabled}
        className={`px-4 py-2 bg-blue-600 text-white rounded-r-md ${
          !value.trim() || disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'
        }`}
      >
        发送
      </button>
    </form>
  );
};

export default ChatInput; 