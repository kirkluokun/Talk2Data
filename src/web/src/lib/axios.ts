import axios from 'axios';
import tokenStore from '../utils/tokenStore';

/**
 * 创建并配置共享的Axios实例
 * - 自动处理API请求的基本URL
 * - 添加请求和响应拦截器
 * - 自动附加认证令牌
 * - 处理401响应
 */
const api = axios.create({
  baseURL: '/api', // 使用相对路径，利用Vite的代理配置
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 请求拦截器：自动在请求头中添加Authorization
 */
api.interceptors.request.use(
  (config) => {
    const token = tokenStore.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      // 调试用
      console.log('添加认证令牌到请求:', config.url);
    } else {
      console.warn('请求没有认证令牌:', config.url);
    }
    console.log('发送请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

/**
 * 响应拦截器：处理401错误（令牌无效）
 */
api.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url);
    return response;
  },
  (error) => {
    // 输出详细的错误信息
    if (error.response) {
      console.error('响应错误:', error.response.status, error.config?.url, error.response.data);
    } else {
      console.error('请求错误:', error.message);
    }
    
    // 检查是否是认证失败错误
    if (error.response && error.response.status === 401) {
      console.warn('认证失败，清除令牌并重定向到登录页');
      // 清除失效的令牌
      tokenStore.clearToken();
      // 重定向到登录页
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * 设置全局认证令牌
 * 可在登录时调用，为后续所有请求添加令牌
 */
export const setAuthToken = (token: string | null): void => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
};

// 导出共享的API实例
export default api; 