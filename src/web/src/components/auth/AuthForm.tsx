import { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';

interface AuthFormProps {
  mode: 'login' | 'register';
  onSubmit: (data: { username: string; password: string; email?: string }) => void;
  isLoading?: boolean;
  error?: string;
}

const AuthForm = ({ mode, onSubmit, isLoading = false, error }: AuthFormProps) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const submitData = {
      username: formData.username,
      password: formData.password,
      ...(mode === 'register' ? { email: formData.email } : {}),
    };
    onSubmit(submitData);
  };

  return (
    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}

      <div className="rounded-md shadow-sm -space-y-px">
        {mode === 'register' && (
          <div>
            <label htmlFor="email" className="sr-only">
              邮箱地址
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              className={[
                'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900',
                'rounded-t-md',
                'focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm'
              ].join(' ')}
              placeholder="邮箱地址"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
        )}

        <div>
          <label htmlFor="username" className="sr-only">
            用户名
          </label>
          <input
            id="username"
            name="username"
            type="text"
            required
            className={[
              'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900',
              mode === 'register' ? '' : 'rounded-t-md',
              'focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm'
            ].join(' ')}
            placeholder="用户名"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          />
        </div>

        <div>
          <label htmlFor="password" className="sr-only">
            密码
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
            placeholder="密码"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          />
        </div>
      </div>

      <div>
        <button
          type="submit"
          disabled={isLoading}
          className={[
            'group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          ].join(' ')}
        >
          {isLoading ? (
            <span className="absolute left-0 inset-y-0 flex items-center pl-3">
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </span>
          ) : null}
          {mode === 'login' ? '登录' : '注册'}
        </button>
      </div>

      <div className="text-sm text-center">
        {mode === 'login' ? (
          <p>
            还没有账号？{' '}
            <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500">
              立即注册
            </Link>
          </p>
        ) : (
          <p>
            已有账号？{' '}
            <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
              立即登录
            </Link>
          </p>
        )}
      </div>
    </form>
  );
};

export default AuthForm; 