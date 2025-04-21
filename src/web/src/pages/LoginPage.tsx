import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AuthForm from '../components/auth/AuthForm';
import useAuth from '../hooks/useAuth';

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, isLoading: authLoading, error: authError, clearError } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 如果用户已登录，跳转到首页或之前尝试访问的页面
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);
  
  // 清除错误
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  const handleSubmit = async (data: { username: string; password: string }) => {
    setIsSubmitting(true);
    
    try {
      await login({
        username: data.username,
        password: data.password
      });
      // 登录成功后，会通过上面的useEffect自动跳转
    } catch (err) {
      // 错误已经通过useAuth中的状态处理
      console.error('登录失败:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isLoading = authLoading || isSubmitting;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            登录
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            登录后开始使用金融数据对话系统
          </p>
        </div>
        
        <AuthForm
          mode="login"
          onSubmit={handleSubmit}
          isLoading={isLoading}
          error={authError}
        />
      </div>
    </div>
  );
};

export default LoginPage; 