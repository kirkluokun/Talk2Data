import { createContext, useReducer, useEffect, ReactNode, useCallback } from 'react';
import { AuthContextType, AuthState, LoginCredentials, RegisterData, User } from '../types/auth';
import { loginUser, registerUser, getCurrentUser, setAuthToken } from '../lib/api';
import tokenStore from '../utils/tokenStore';
import axios from 'axios';

// 初始状态
const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// 创建上下文
export const AuthContext = createContext<AuthContextType>({
  ...initialState,
  login: async () => { throw new Error('AuthProvider not found'); },
  register: async () => { throw new Error('AuthProvider not found'); },
  logout: () => { throw new Error('AuthProvider not found'); },
  clearError: () => { throw new Error('AuthProvider not found'); },
});

// Action类型
type AuthAction =
  | { type: 'LOGIN_REQUEST' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; token: string } }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'REGISTER_REQUEST' }
  | { type: 'REGISTER_SUCCESS' }
  | { type: 'REGISTER_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'AUTH_LOADED'; payload?: { user: User; token: string } };

// Reducer函数
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'LOGIN_REQUEST':
    case 'REGISTER_REQUEST':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        isLoading: false,
        user: action.payload.user,
        token: action.payload.token,
        error: null,
      };
    case 'LOGIN_FAILURE':
    case 'REGISTER_FAILURE':
      return {
        ...state,
        isLoading: false,
        error: action.payload,
      };
    case 'REGISTER_SUCCESS':
      return {
        ...state,
        isLoading: false,
        error: null,
      };
    case 'LOGOUT':
      return {
        ...initialState,
        isLoading: false,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'AUTH_LOADED':
      return {
        ...state,
        isAuthenticated: !!action.payload,
        user: action.payload?.user || null,
        token: action.payload?.token || null,
        isLoading: false,
      };
    default:
      return state;
  }
};

// Props类型
interface AuthProviderProps {
  children: ReactNode;
}

// AuthProvider组件
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // 初始化时从本地存储加载认证状态
  useEffect(() => {
    let isMounted = true; // 防止在 unmounted 组件上更新状态
    const initAuth = async () => {
      const token = tokenStore.getToken();
      
      if (token) {
        try {
          setAuthToken(token);
          const user = await getCurrentUser();
          if (isMounted) {
            tokenStore.setUser(user); // 确保本地存储也更新
            dispatch({
              type: 'AUTH_LOADED',
              payload: { user, token },
            });
          }
        } catch (err) {
          console.error('初始化认证失败 (获取用户信息失败或令牌无效):', err);
          tokenStore.clearToken();
          setAuthToken(null);
          if (isMounted) {
            dispatch({ type: 'AUTH_LOADED' });
          }
        }
      } else {
        if (isMounted) {
          dispatch({ type: 'AUTH_LOADED' });
        }
      }
    };

    initAuth();
    
    return () => {
      isMounted = false; // 组件卸载时设置标志
    };
  }, []);

  // 登录方法 (使用 useCallback 记忆化)
  const login = useCallback(async (credentials: LoginCredentials) => {
    dispatch({ type: 'LOGIN_REQUEST' });

    try {
      const response = await loginUser(credentials);
      const token = response.access_token;
      setAuthToken(token);
      tokenStore.setToken(token);

      try {
        const user = await getCurrentUser();
        tokenStore.setUser(user);
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: { user, token },
        });
      } catch (userError) {
         console.error('登录成功但获取用户信息失败:', userError);
         // 即使获取用户信息失败，也认为是登录成功，但用户信息可能不完整
         // 可以考虑设置一个默认/部分用户对象，或显示错误提示
         // 这里我们仍然分发 LOGIN_SUCCESS 但可能 user 为 null 或部分信息
         // 或者可以触发一个 LOGIN_FAILURE 并提示用户刷新或联系支持
         const partialUser: User = { 
             id: 0, // 或其他默认值
             username: credentials.username, 
             email: '', 
             is_active: false, 
             is_superuser: false, 
             created_at: '', 
             updated_at: '' 
         };
         tokenStore.setUser(partialUser); // 存储部分信息
         dispatch({
             type: 'LOGIN_SUCCESS',
             payload: { user: partialUser, token }, // 传递部分用户
         });
        // 或者抛出错误让调用者处理
        // throw new Error('登录成功但无法获取用户信息');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '登录失败，请重试';
      dispatch({
        type: 'LOGIN_FAILURE',
        payload: errorMessage,
      });
      throw error; // 重新抛出错误，让调用组件可以捕获
    }
  }, []); // 空依赖数组，因为 login 不依赖外部可变状态

  // 注册方法 (使用 useCallback 记忆化)
  const register = useCallback(async (data: RegisterData) => {
    dispatch({ type: 'REGISTER_REQUEST' });

    try {
      await registerUser(data);
      dispatch({ type: 'REGISTER_SUCCESS' });
      // 注册成功后，通常不需要自动登录，用户会被导航到登录页
    } catch (error) {
      let errorMessage = '注册失败，请重试';
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      dispatch({
        type: 'REGISTER_FAILURE',
        payload: errorMessage,
      });
      throw error; // 重新抛出错误
    }
  }, []); // 空依赖数组

  // 登出方法 (使用 useCallback 记忆化)
  const logout = useCallback(() => {
    tokenStore.clearToken();
    setAuthToken(null);
    dispatch({ type: 'LOGOUT' });
    // 通常在调用 logout 后会进行页面跳转，这在组件层面处理
  }, []); // 空依赖数组

  // 清除错误信息 (使用 useCallback 记忆化)
  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []); // 空依赖数组

  // 提供上下文值 (包含记忆化的函数)
  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};