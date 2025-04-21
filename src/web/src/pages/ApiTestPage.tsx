import { useState } from 'react';

const ApiTestPage = () => {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<string>('');
  const [error, setError] = useState<string>('');

  // 测试API代理
  const testApiProxy = async () => {
    setLoading(true);
    setError('');

    try {
      // 尝试请求后端健康检查接口
      const response = await fetch('/api/health');
      const data = await response.json();
      
      setResponse(JSON.stringify(data, null, 2));
    } catch (err) {
      setError(`API请求失败: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <h1 className="text-2xl font-bold mb-4">API代理测试</h1>
      
      <button 
        onClick={testApiProxy}
        disabled={loading}
        className="mb-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? '请求中...' : '测试API代理'}
      </button>
      
      {error && (
        <div className="w-full max-w-md p-4 mb-4 bg-red-50 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {response && (
        <div className="w-full max-w-md">
          <h2 className="text-lg font-semibold mb-2">响应结果:</h2>
          <pre className="p-4 bg-gray-100 rounded overflow-auto">
            {response}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ApiTestPage; 