/**
 * 令牌存储工具类
 * 负责在localStorage中管理JWT令牌和基本用户信息
 */

import { User } from '../types/auth';

// 存储键名
const TOKEN_KEY = 'finance_chat_token';
const USER_KEY = 'finance_chat_user';

// 令牌有效期判断（默认30分钟）
const isTokenExpired = (token: string): boolean => {
  try {
    // JWT格式: header.payload.signature
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload));
    
    // 检查exp字段（过期时间戳）
    if (decoded.exp) {
      // 将exp转换为毫秒并与当前时间比较
      return decoded.exp * 1000 < Date.now();
    }
    return false; // 如果没有exp字段，假设不过期
  } catch (error) {
    console.error('令牌解析错误:', error);
    return true; // 解析错误视为过期
  }
};

const tokenStore = {
  /**
   * 存储令牌到localStorage
   */
  setToken: (token: string): void => {
    localStorage.setItem(TOKEN_KEY, token);
  },

  /**
   * 从localStorage获取令牌
   * 如果令牌过期，自动清除并返回null
   */
  getToken: (): string | null => {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (token && isTokenExpired(token)) {
      tokenStore.clearToken();
      return null;
    }
    
    return token;
  },

  /**
   * 从localStorage清除令牌
   */
  clearToken: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  /**
   * 存储用户信息到localStorage
   */
  setUser: (user: User): void => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  /**
   * 从localStorage获取用户信息
   */
  getUser: (): User | null => {
    const userJson = localStorage.getItem(USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
  }
};

export default tokenStore;