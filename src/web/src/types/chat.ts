/**
 * 对话数据类型定义文件
 */

// 对话列表项类型
export type Conversation = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
};

// 后端返回的消息类型
export type ApiMessageType = {
  id: number;
  conversation_id: number;
  user_id: number | null;
  content: string;
  content_type: string | null;
  file_path: string | null;
  timestamp: string;
  is_from_user: boolean;
};

// 前端使用的消息类型，与 ChatInterface.tsx 中的定义保持一致
export type MessageType = {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: string;
  contentType?: string;
  filePath?: string;
  error?: string | null;
};

// 进度状态类型，与 ChatInterface.tsx 中的定义保持一致
export type ProgressStatus = {
  isActive: boolean;
  progress: number;
  stage: string;
};

// 将后端消息类型转换为前端显示类型
export const convertApiMessage = (apiMessage: ApiMessageType): MessageType => {
  return {
    id: apiMessage.id.toString(),
    content: apiMessage.content,
    isUser: apiMessage.is_from_user,
    timestamp: new Date(apiMessage.timestamp).toLocaleTimeString(),
    contentType: apiMessage.content_type || undefined,
    filePath: apiMessage.file_path || undefined,
    error: null
  };
};

// 创建新的前端用户消息 (临时添加到UI，未保存到后端时使用)
export const createUserMessage = (content: string): MessageType => {
  return {
    id: Date.now().toString(),
    content,
    isUser: true,
    timestamp: new Date().toLocaleTimeString(),
  };
};

// 创建新的前端错误消息
export const createErrorMessage = (errorText: string): MessageType => {
  return {
    id: (Date.now() + 1).toString(),
    content: '发生错误',
    isUser: false,
    timestamp: new Date().toLocaleTimeString(),
    contentType: 'error',
    error: errorText
  };
}; 