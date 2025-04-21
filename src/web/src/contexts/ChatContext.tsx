import React, { createContext, useReducer, ReactNode, useEffect, useCallback } from 'react';
import { 
  Conversation, 
  MessageType, 
  ProgressStatus, 
  createUserMessage, 
  createErrorMessage 
} from '../types/chat';

// 聊天上下文状态接口
interface ChatState {
  // 对话列表
  conversations: Conversation[];
  // 当前选中的对话ID
  selectedConversationId: number | null;
  // 当前对话的消息列表
  messages: MessageType[];
  // 是否正在加载对话历史
  isLoadingHistory: boolean;
  // 是否正在加载对话消息
  isLoadingMessages: boolean;
  // 是否正在发送消息
  isSendingMessage: boolean;
  // 当前任务ID
  currentJobId: string | null;
  // 当前任务进度
  currentJobProgress: ProgressStatus;
  // 错误信息
  error: string | null;
}

// 聊天上下文动作类型
type ChatAction =
  | { type: 'SET_CONVERSATIONS'; payload: Conversation[] }
  | { type: 'SELECT_CONVERSATION'; payload: number | null }
  | { type: 'SET_MESSAGES'; payload: MessageType[] }
  | { type: 'ADD_MESSAGE'; payload: MessageType }
  | { type: 'SET_LOADING_HISTORY'; payload: boolean }
  | { type: 'SET_LOADING_MESSAGES'; payload: boolean }
  | { type: 'SET_SENDING_MESSAGE'; payload: boolean }
  | { type: 'SET_CURRENT_JOB_ID'; payload: string | null }
  | { type: 'SET_CURRENT_JOB_PROGRESS'; payload: ProgressStatus }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' };

// 聊天上下文接口
interface ChatContextType extends ChatState {
  // 加载对话历史
  fetchHistory: () => Promise<void>;
  // 选择对话
  selectConversation: (id: number | null) => Promise<void>;
  // 创建新对话
  createNewConversation: () => void;
  // 删除对话
  deleteConversation: (id: number) => Promise<void>;
  // 发送消息
  sendMessage: (content: string) => Promise<void>;
  // 清除错误
  clearError: () => void;
  // 内部调度函数(供 useChat 使用)
  dispatch: React.Dispatch<ChatAction>;
}

// 初始状态
const initialState: ChatState = {
  conversations: [],
  selectedConversationId: null,
  messages: [],
  isLoadingHistory: false,
  isLoadingMessages: false,
  isSendingMessage: false,
  currentJobId: null,
  currentJobProgress: {
    isActive: false,
    progress: 0,
    stage: '',
  },
  error: null,
};

// 创建聊天上下文
export const ChatContext = createContext<ChatContextType | undefined>(undefined);

// 聊天状态 reducer
const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  switch (action.type) {
    case 'SET_CONVERSATIONS':
      return { ...state, conversations: action.payload };
    case 'SELECT_CONVERSATION':
      return { ...state, selectedConversationId: action.payload };
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'SET_LOADING_HISTORY':
      return { ...state, isLoadingHistory: action.payload };
    case 'SET_LOADING_MESSAGES':
      return { ...state, isLoadingMessages: action.payload };
    case 'SET_SENDING_MESSAGE':
      return { ...state, isSendingMessage: action.payload };
    case 'SET_CURRENT_JOB_ID':
      return { ...state, currentJobId: action.payload };
    case 'SET_CURRENT_JOB_PROGRESS':
      return { ...state, currentJobProgress: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
};

// Props 类型定义
interface ChatProviderProps {
  children: ReactNode;
}

// 聊天上下文提供者组件
export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  // 加载对话历史列表 (实际实现在 useChat 中)
  const fetchHistory = useCallback(async () => {
    return Promise.resolve();
  }, []);

  // 选择对话 (实际实现在 useChat 中)
  const selectConversation = useCallback(async (id: number | null) => {
    return Promise.resolve();
  }, []);

  // 创建新对话 (实际实现在 useChat 中)
  const createNewConversation = useCallback(() => {
    // Empty implementation
  }, []);

  // 删除对话 (实际实现在 useChat 中)
  const deleteConversation = useCallback(async (id: number) => {
    return Promise.resolve();
  }, []);

  // 发送消息 (实际实现在 useChat 中)
  const sendMessage = useCallback(async (content: string) => {
    return Promise.resolve();
  }, []);

  // 清除错误
  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  // 提供上下文
  const value = {
    ...state,
    fetchHistory,
    selectConversation,
    createNewConversation,
    deleteConversation,
    sendMessage,
    clearError,
    dispatch,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}; 