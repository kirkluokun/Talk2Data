import { useContext, useCallback, useRef } from 'react';
import { ChatContext } from '../contexts/ChatContext';
import { 
  getChatHistory, 
  getConversationMessages, 
  deleteConversation as apiDeleteConversation,
  sendQuery,
  getJobStatus
} from '../lib/api';
import { 
  MessageType, 
  createUserMessage, 
  createErrorMessage,
  convertApiMessage
} from '../types/chat';

/**
 * 自定义Hook: 提供聊天相关的状态和方法
 * @returns 聊天上下文内的所有状态和方法
 */
const useChat = () => {
  const context = useContext(ChatContext);
  
  if (!context) {
    throw new Error('useChat 必须在 ChatProvider 内部使用');
  }

  // 解构所需的状态和 dispatch 函数
  const {
    conversations,
    selectedConversationId,
    messages,
    isLoadingHistory,
    isLoadingMessages,
    isSendingMessage,
    currentJobId,
    currentJobProgress,
    error,
    // 以下函数会被重新实现
    dispatch,
    clearError
  } = context;

  // 保存轮询定时器的引用
  const pollingIntervalRef = useRef<number | null>(null);
  // --- 新增: 保存新对话的 ID ---
  const newConversationIdRef = useRef<number | null>(null);
  // --- 结束新增 ---

  // 清理任何现有的轮询
  const clearPolling = useCallback(() => {
    if (pollingIntervalRef.current !== null) {
      window.clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  /**
   * 加载对话历史列表
   */
  const fetchHistory = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING_HISTORY', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const conversationsData = await getChatHistory();
      dispatch({ type: 'SET_CONVERSATIONS', payload: conversationsData });
    } catch (error) {
      console.error('获取对话历史失败:', error);
      dispatch({ type: 'SET_ERROR', payload: '获取对话历史失败，请稍后再试' });
    } finally {
      dispatch({ type: 'SET_LOADING_HISTORY', payload: false });
    }
  }, [dispatch]);

  /**
   * 选择对话
   * @param id 对话ID，null 表示不选择任何对话
   */
  const selectConversation = useCallback(async (id: number | null) => {
    dispatch({ type: 'SELECT_CONVERSATION', payload: id });
    
    // 如果 id 为 null，表示取消选择（例如创建新对话），清空消息列表
    if (id === null) {
      dispatch({ type: 'SET_MESSAGES', payload: [] });
      return;
    }
    
    try {
      dispatch({ type: 'SET_LOADING_MESSAGES', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const messagesData = await getConversationMessages(id);
      
      // 将API返回的消息格式转换为前端使用的格式
      const formattedMessages = messagesData.map(convertApiMessage);
      
      dispatch({ type: 'SET_MESSAGES', payload: formattedMessages });
    } catch (error) {
      console.error('获取对话消息失败:', error);
      dispatch({ type: 'SET_ERROR', payload: '获取对话消息失败，请稍后再试' });
    } finally {
      dispatch({ type: 'SET_LOADING_MESSAGES', payload: false });
    }
  }, [dispatch]);

  /**
   * 创建新对话
   */
  const createNewConversation = useCallback(() => {
    // 清理任何现有的轮询
    clearPolling();
    
    // 将选中的对话ID设为null，清空消息列表，为新对话做准备
    dispatch({ type: 'SELECT_CONVERSATION', payload: null });
    dispatch({ type: 'SET_MESSAGES', payload: [] });
    dispatch({ type: 'SET_ERROR', payload: null });
  }, [clearPolling, dispatch]);

  /**
   * 删除对话
   * @param id 要删除的对话ID
   */
  const deleteConversation = useCallback(async (id: number) => {
    // 保存当前对话列表的副本，以便在 API 调用失败时可以回滚
    const currentConversations = [...conversations];
    
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      // 立即从前端状态中移除对话，提供更快的用户反馈
      dispatch({
        type: 'SET_CONVERSATIONS',
        payload: conversations.filter(conv => conv.id !== id)
      });
      
      // 调用API删除对话
      await apiDeleteConversation(id);
      
      // 如果删除的是当前选中的对话，清空消息并取消选中
      if (selectedConversationId === id) {
        dispatch({ type: 'SELECT_CONVERSATION', payload: null });
        dispatch({ type: 'SET_MESSAGES', payload: [] });
      }
    } catch (error) {
      console.error('删除对话失败:', error);
      dispatch({ type: 'SET_ERROR', payload: '删除对话失败，请稍后再试' });
      
      // 如果 API 调用失败，恢复之前的对话列表
      dispatch({ type: 'SET_CONVERSATIONS', payload: currentConversations });
    }
  }, [conversations, selectedConversationId, dispatch]);

  /**
   * 开始轮询任务状态
   * @param jobId 任务ID
   */
  const startPolling = useCallback((jobId: string) => {
    // 清理可能存在的旧轮询
    clearPolling();
    
    // 设置新的轮询
    const interval = window.setInterval(async () => {
      try {
        // 获取任务状态
        const statusResponse = await getJobStatus(jobId);
        
        // 更新进度状态
        dispatch({
          type: 'SET_CURRENT_JOB_PROGRESS',
          payload: {
            isActive: true,
            progress: statusResponse.progress,
            stage: statusResponse.stage,
          },
        });
        
        // 如果任务完成或失败，停止轮询并更新UI
        if (statusResponse.status === 'completed' || statusResponse.status === 'failed' || statusResponse.status === 'error') {
          clearPolling();
          
          // 重置发送状态
          dispatch({ type: 'SET_SENDING_MESSAGE', payload: false });
          
          // --- 修改: 处理新旧对话的消息加载 --- 
          const conversationIdToLoad = newConversationIdRef.current ?? selectedConversationId;
          
          if (conversationIdToLoad !== null) {
              // 如果有需要加载的对话 (无论是刚创建的新对话还是之前选中的旧对话)
              await selectConversation(conversationIdToLoad); 
              // 如果是新对话，加载完消息后清除标记
              if (newConversationIdRef.current === conversationIdToLoad) {
                  newConversationIdRef.current = null;
                  // 同时刷新历史列表以显示新标题等信息
                  await fetchHistory(); 
              }
          }
          // --- 结束修改 ---
          
          // 重置进度状态
          dispatch({
            type: 'SET_CURRENT_JOB_PROGRESS',
            payload: {
              isActive: false,
              progress: 0,
              stage: '',
            },
          });
        }
      } catch (error) {
        console.error('轮询状态失败:', error);
        clearPolling();
        
        // 重置发送状态
        dispatch({ type: 'SET_SENDING_MESSAGE', payload: false });
        
        // 添加错误消息
        const errorMsg = '轮询状态失败，请刷新页面再试';
        dispatch({ type: 'SET_ERROR', payload: errorMsg });
        
        // 重置进度状态
        dispatch({
          type: 'SET_CURRENT_JOB_PROGRESS',
          payload: {
            isActive: false,
            progress: 0,
            stage: '',
          },
        });
      }
    }, 1000); // 每秒轮询一次
    
    // 保存轮询定时器的ID
    pollingIntervalRef.current = interval;
  }, [clearPolling, conversations, selectedConversationId, selectConversation, fetchHistory, dispatch]);

  /**
   * 发送消息
   * @param content 消息内容
   */
  const sendMessage = useCallback(async (content: string) => {
    // --- 新增: 清除可能残留的新对话 ID 标记 ---
    newConversationIdRef.current = null;
    // --- 结束新增 ---
    try {
      // 设置发送状态为true
      dispatch({ type: 'SET_SENDING_MESSAGE', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      
      // 临时添加用户消息到UI（即时反馈）
      const userMessage = createUserMessage(content);
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      
      // 调用API发送查询
      const response = await sendQuery(content, selectedConversationId);
      const jobId = response.job_id;
      // --- 新增: 如果是新对话，保存其 ID ---
      if (selectedConversationId === null) {
          newConversationIdRef.current = response.conversation_id;
      }
      // --- 结束新增 ---
      
      // 保存任务ID并开始轮询状态
      dispatch({ type: 'SET_CURRENT_JOB_ID', payload: jobId });
      startPolling(jobId);
    } catch (error) {
      console.error('发送消息失败:', error);
      
      // 重置发送状态
      dispatch({ type: 'SET_SENDING_MESSAGE', payload: false });
      
      // 添加错误消息
      const errorMsg = '发送消息失败，请稍后再试';
      dispatch({ type: 'SET_ERROR', payload: errorMsg });
      
      // 创建错误消息并添加到UI
      const errorMessage = createErrorMessage(errorMsg);
      dispatch({ type: 'ADD_MESSAGE', payload: errorMessage });
    }
  }, [selectedConversationId, startPolling, dispatch]);

  // 返回聊天相关的所有状态和方法
  return {
    // 状态
    conversations,
    selectedConversationId,
    messages,
    isLoadingHistory,
    isLoadingMessages,
    isSendingMessage,
    currentJobId,
    currentJobProgress,
    error,
    
    // 方法
    fetchHistory,
    selectConversation,
    createNewConversation,
    deleteConversation,
    sendMessage,
    clearError,
  };
};

export default useChat; 