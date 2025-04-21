import axios from 'axios';
import api from './axios';
import { LoginCredentials, RegisterData, LoginResponse, User } from '../types/auth';

// TODO: 从 ../types/chat 定义或导入这些类型
type Conversation = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
};

type MessageType = {
  id: number;
  conversation_id: number;
  user_id: number | null;
  content: string;
  content_type: string | null;
  file_path: string | null;
  timestamp: string;
  is_from_user: boolean;
};

// 辅助函数，将FastAPI验证错误详情格式化为字符串
const formatValidationError = (detail: any): string => {
  if (Array.isArray(detail)) {
    return detail.map(err => {
      const field = err.loc && err.loc.length > 1 ? err.loc[1] : 'field';
      let msg = err.msg;
      // 检查是否是 Pydantic v2 的标准邮箱错误消息
      if (field === 'email' && msg.startsWith('value is not a valid email address')) {
            // 可以进一步细化，比如区分 @ 之前还是之后的部分
            if (msg.includes("The part after the @-sign is not valid")) {
            msg = '邮箱 @ 符号后面的部分无效，需要包含一个点 (.)';
            } else if (msg.includes("The part before the @-sign is not valid")) {
                msg = '邮箱 @ 符号前面的部分无效';
            } else {
                msg = '请输入有效的邮箱地址'; // 通用中文提示
            }
      }
      return `${field}: ${msg}`;
    }).join(', ');
  } else if (typeof detail === 'string') {
    // 如果 detail 本身是字符串，直接返回
    return detail;
  } else if (typeof detail === 'object' && detail !== null) {
    // 尝试处理嵌套的 detail 或其他对象格式
    return JSON.stringify(detail);
  }
  return '验证失败';
};

/**
 * 用户注册
 * @param data 注册数据（邮箱、用户名、密码）
 */
export const registerUser = async (data: RegisterData): Promise<User> => {
  try {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      // 格式化验证错误
      const errorMessage = formatValidationError(error.response.data.detail);
      throw new Error(errorMessage);
    }
    // 保留对其他错误的通用处理
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail)); // 尝试转为字符串
    }
    // 如果没有 detail，抛出通用错误或状态码
    if (axios.isAxiosError(error) && error.response) {
        throw new Error(`请求失败，状态码：${error.response.status}`);
    }
    throw error; // 重新抛出未处理的错误
  }
};

/**
 * 用户登录
 * @param credentials 登录凭证（用户名/邮箱、密码）
 */
export const loginUser = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  try {
    // 登录API需要使用表单格式 (form-urlencoded)
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await api.post<LoginResponse>('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
        // 登录错误通常是字符串
        throw new Error(String(error.response.data.detail));
    } else if (axios.isAxiosError(error) && error.response) {
        // 处理其他HTTP错误
        throw new Error(`登录失败，状态码：${error.response.status}`);
    }
    throw error;
  }
};

/**
 * 获取当前用户信息
 * 需要认证令牌
 */
export const getCurrentUser = async (): Promise<User> => {
  try {
    const response = await api.get<User>('/users/me');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail));
    } else if (axios.isAxiosError(error) && error.response) {
        throw new Error(`获取用户信息失败，状态码：${error.response.status}`);
    }
    throw error;
  }
};

/**
 * 发送查询请求
 * @param query 用户查询文本
 * @param conversationId 可选，关联的对话ID
 * @returns Promise 包含 job_id 和 conversation_id 的对象
 */
export const sendQuery = async (
  query: string, 
  conversationId?: number | null // 允许 null
): Promise<{ job_id: string; conversation_id: number }> => {
  try {
    // 在请求体中包含 query 和可选的 conversation_id
    const payload: { query: string; conversation_id?: number | null } = { query };
    if (conversationId !== undefined && conversationId !== null) {
      payload.conversation_id = conversationId;
    } else {
      payload.conversation_id = null; // 显式发送 null 以创建新对话
    }
    // --- 修改: 更新期望的响应类型 ---
    const response = await api.post<{ job_id: string; conversation_id: number }>(
      '/query', 
      payload
    );
    // --- 结束修改 ---
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail));
    } else if (axios.isAxiosError(error) && error.response) {
        throw new Error(`发送查询失败，状态码：${error.response.status}`);
    }
    throw error;
  }
};

/**
 * 获取任务状态
 * @param jobId 任务ID
 */
export const getJobStatus = async (jobId: string): Promise<any> => {
  try {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail));
    } else if (axios.isAxiosError(error) && error.response) {
        throw new Error(`获取任务状态失败，状态码：${error.response.status}`);
    }
    throw error;
  }
};

// --- 新增 Chat API 函数 ---

/**
 * 获取当前用户的对话历史列表
 */
export const getChatHistory = async (): Promise<Conversation[]> => {
  try {
    const response = await api.get<Conversation[]>('/chat/history');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail));
    } else if (axios.isAxiosError(error) && error.response) {
        throw new Error(`获取对话历史失败，状态码：${error.response.status}`);
    }
    throw error;
  }
};

/**
 * 获取指定对话的所有消息
 * @param conversationId 对话ID
 */
export const getConversationMessages = async (conversationId: number): Promise<MessageType[]> => {
  try {
    const response = await api.get<MessageType[]>(`/chat/conversation/${conversationId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail));
    } else if (axios.isAxiosError(error) && error.response) {
        throw new Error(`获取对话消息失败，状态码：${error.response.status}`);
    }
    throw error;
  }
};

/**
 * 删除指定对话及其所有消息
 * @param conversationId 对话ID
 */
export const deleteConversation = async (conversationId: number): Promise<void> => {
  try {
    await api.delete(`/chat/conversation/${conversationId}`);
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail));
    } else if (axios.isAxiosError(error) && error.response) {
        throw new Error(`删除对话失败，状态码：${error.response.status}`);
    }
    throw error;
  }
};

// ------------------------

// 从axios.ts导出设置认证令牌的函数
export { setAuthToken } from './axios';

// 获取所有任务
export const getAllJobs = async (limit = 10, status?: string) => {
  try {
    const params = { limit, ...(status && { status }) };
    const response = await api.get('/jobs', { params });
    return response.data;
  } catch (error) {
    console.error('获取所有任务失败:', error);
    throw error;
  }
};

// 获取文件内容的 URL
export const getFileContentUrl = (filePath: string) => {
  // 确保 api.defaults.baseURL 存在且是字符串
  const baseURL = typeof api.defaults.baseURL === 'string' ? api.defaults.baseURL : '';
  // 移除 baseURL 末尾的斜杠 (如果存在)
  const cleanedBaseURL = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
  // 移除 filePath 开头的斜杠 (如果存在)
  const cleanedFilePath = filePath.startsWith('/') ? filePath.slice(1) : filePath;
  return `${cleanedBaseURL}/file/${cleanedFilePath}`;
}; 