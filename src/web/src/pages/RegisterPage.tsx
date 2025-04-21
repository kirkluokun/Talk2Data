import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthForm from '../components/auth/AuthForm';
import useAuth from '../hooks/useAuth';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register, error: authError, isLoading: authLoading, clearError } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string>();

  // 清除错误
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  const handleSubmit = async (data: { username: string; password: string; email?: string }) => {
    // 验证邮箱
    if (!data.email) {
      setValidationError('邮箱是必填项');
      return;
    }
    
    setValidationError(undefined);
    setIsSubmitting(true);
    
    try {
      await register({
        username: data.username,
        email: data.email,
        password: data.password
      });
      
      // 注册成功后跳转到登录页
      navigate('/login', { 
        replace: true,
        state: { message: '注册成功，请登录' }
      });
    } catch (err) {
      // 错误已经通过useAuth中的状态处理
      console.error('注册失败:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isLoading = authLoading || isSubmitting;
  const error = validationError || authError;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            注册账号
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            注册账号以使用金融数据对话系统
          </p>
        </div>
        
        <AuthForm
          mode="register"
          onSubmit={handleSubmit}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </div>
  );
};

export default RegisterPage; 