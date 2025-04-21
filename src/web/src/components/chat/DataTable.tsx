import React, { useState, useEffect, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
} from '@tanstack/react-table';
import axios from 'axios';
import api from '../../lib/axios';

type DataTableProps = {
  filePath: string;
};

// DataTable组件：用于从CSV文件路径加载数据并以表格形式展示
const DataTable: React.FC<DataTableProps> = ({ filePath }) => {
  // 存储CSV数据
  const [data, setData] = useState<Record<string, any>[]>([]);
  // 存储列定义
  const [columns, setColumns] = useState<any[]>([]);
  // 存储排序状态
  const [sorting, setSorting] = useState<SortingState>([]);
  // 加载状态
  const [loading, setLoading] = useState(true);
  // 错误状态
  const [error, setError] = useState<string | null>(null);
  // 实际请求的URL
  const [requestUrl, setRequestUrl] = useState<string>('');

  // 列助手，帮助创建列定义
  const columnHelper = createColumnHelper<Record<string, any>>();
  
  // 处理路径，移除可能的 ../ 前缀
  const processPath = (path: string): string => {
    // 移除开头的 ../ 或 ./
    let processedPath = path.replace(/^\.\.\/|^\.\//g, '');
    
    // 确保路径不以 output/ 或 /output/ 开头重复
    if (processedPath.startsWith('output/')) {
      return processedPath;
    } else if (processedPath.startsWith('/output/')) {
      return processedPath.substring(1); // 移除开头的斜杠
    }
    
    // 如果路径不包含 output，则添加前缀
    return `output/${processedPath}`;
  };

  // 当文件路径变化时加载数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 处理文件路径
        const processedPath = processPath(filePath);
        const apiUrl = `/file/${processedPath}`;
        setRequestUrl(apiUrl);
        
        // 发起请求获取CSV文件
        const response = await api.get(apiUrl, {
          responseType: 'text',
        });

        // 解析CSV数据
        const rows = parseCSV(response.data);
        
        if (rows.length === 0) {
          setError('检索未成功找到数据');
          setLoading(false);
          return;
        }

        // 获取第一行作为列名
        const headers = Object.keys(rows[0]);
        
        // 创建列定义
        const tableColumns = headers.map(header => 
          columnHelper.accessor(header, {
            header: () => <span className="font-semibold">{header}</span>,
            cell: info => {
              const value = info.getValue();
              // 如果是数字，进行格式化
              if (typeof value === 'number') {
                return new Intl.NumberFormat('zh-CN').format(value);
              }
              return String(value);
            },
          })
        );

        setColumns(tableColumns);
        setData(rows);
        setLoading(false);
      } catch (err) {
        console.error('加载CSV数据失败:', err);
        setError(`无法加载表格数据，请稍后再试`);
        setLoading(false);
      }
    };

    if (filePath) {
      fetchData();
    }
  }, [filePath]);

  // 解析CSV数据的辅助函数
  const parseCSV = (csvText: string): Record<string, any>[] => {
    const lines = csvText.trim().split('\n');
    if (lines.length <= 1) return [];

    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    
    return lines.slice(1).map(line => {
      const rowValues = line.split(',');
      const row: Record<string, any> = {};
      
      headers.forEach((header, index) => {
        const valueString = rowValues[index]?.trim().replace(/^"|"$/g, '') || '';
        
        // 特别处理"股票代码"列，始终视为字符串
        if (header === '股票代码') {
          row[header] = valueString;
        } else {
          // 其他列尝试转换为数字
          const num = Number(valueString);
          row[header] = isNaN(num) || valueString === '' ? valueString : num;
        }
      });
      return row;
    });
  };

  // 使用memo优化表格实例创建
  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  // 加载状态显示
  if (loading) {
    return <div className="p-4 text-center">正在加载表格数据...</div>;
  }

  // 错误状态显示
  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-500 mb-2">{error}</p>
        <p className="text-xs text-gray-500">尝试请求: {requestUrl}</p>
        <p className="text-xs text-gray-500">文件路径: {filePath}</p>
      </div>
    );
  }

  // 空数据状态显示
  if (data.length === 0) {
    return <div className="p-4 text-center">表格数据为空</div>;
  }

  // 处理下载CSV文件
  const handleDownloadCSV = async () => {
    try {
      if (filePath) {
        const filename = filePath.split('/').pop() || 'data.csv';
        const response = await api.get(`/file/${processPath(filePath)}`, {
          responseType: 'blob'
        });
      
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('文件下载失败:', err);
      alert('文件下载失败，请稍后再试');
    }
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow mt-4 mb-4">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th
                  key={header.id}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center space-x-1">
                    <span>
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                    </span>
                    <span>
                      {header.column.getIsSorted() === 'asc' 
                        ? ' ▲' 
                        : header.column.getIsSorted() === 'desc' 
                          ? ' ▼' 
                          : ''}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map(row => (
            <tr key={row.id} className="hover:bg-gray-50">
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* 分页控制 */}
      <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
        <div className="flex flex-1 justify-between sm:hidden">
          <button
            onClick={handleDownloadCSV}
            className="relative inline-flex items-center rounded-md border border-transparent bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            下载
          </button>
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className={`relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 ${!table.getCanPreviousPage() ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}`}
          >
            上一页
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className={`relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 ${!table.getCanNextPage() ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}`}
          >
            下一页
          </button>
        </div>
        <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
          <div className="flex items-center">
            <button
              onClick={handleDownloadCSV}
              className="relative inline-flex items-center mr-4 rounded-md border border-transparent bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              下载表格
            </button>
            <p className="text-sm text-gray-700">
              显示第 <span className="font-medium">{table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}</span> 到{' '}
              <span className="font-medium">
                {Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, table.getPrePaginationRowModel().rows.length)}
              </span>{' '}
              条，共 <span className="font-medium">{table.getPrePaginationRowModel().rows.length}</span> 条
            </p>
          </div>
          <div>
            <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
              <button
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
                className={`relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ${!table.getCanPreviousPage() ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}`}
              >
                <span className="sr-only">上一页</span>
                ← 上一页
              </button>
              <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700">
                第 {table.getState().pagination.pageIndex + 1} 页，共 {table.getPageCount()} 页
              </span>
              <button
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
                className={`relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ${!table.getCanNextPage() ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}`}
              >
                <span className="sr-only">下一页</span>
                下一页 →
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataTable; 