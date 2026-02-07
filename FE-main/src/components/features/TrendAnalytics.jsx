import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ArrowUpIcon, ArrowDownIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';

function TrendAnalytics({ token }) {
  const [trendData, setTrendData] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [timeRange, setTimeRange] = useState(30);

  const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

  useEffect(() => {
    fetchTrendData();
  }, [timeRange, token]);

  const fetchTrendData = async () => {
    try {
      setLoading(true);
      setError('');

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:6969';

      // Fetch complaint trends, category data, and dashboard stats in parallel
      const [trendsRes, categoriesRes, dashRes] = await Promise.all([
        fetch(`${apiUrl}/api/trends/complaints-over-time?days=${timeRange}`, { headers }),
        fetch(`${apiUrl}/api/trends/category-trends?days=${timeRange}`, { headers }),
        fetch(`${apiUrl}/api/trends/dashboard?days=${timeRange}`, { headers })
      ]);

      if (trendsRes.ok && categoriesRes.ok && dashRes.ok) {
        const trendsData = await trendsRes.json();
        const categoriesData = await categoriesRes.json();
        const dashData = await dashRes.json();

        console.log('✅ Trend data loaded:', { trendsData, categoriesData, dashData });

        setTrendData(trendsData.data);
        setCategoryData(categoriesData.data);
        setDashboardStats(dashData.data);
      } else {
        const errorDetails = {
          trends: trendsRes.ok ? 'OK' : `${trendsRes.status} ${trendsRes.statusText}`,
          categories: categoriesRes.ok ? 'OK' : `${categoriesRes.status} ${categoriesRes.statusText}`,
          dashboard: dashRes.ok ? 'OK' : `${dashRes.status} ${dashRes.statusText}`
        };
        console.error('❌ Failed to fetch trend data:', errorDetails);
        setError(`Failed to fetch trend data. Check console for details.`);
      }
    } catch (err) {
      console.error('❌ Error loading trends:', err);
      setError(`Error loading trends: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-sm text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex gap-2 mb-6">
        {[7, 14, 30, 90, 365].map((days) => (
          <button
            key={days}
            onClick={() => setTimeRange(days)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              timeRange === days
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {days === 7 ? '7d' : days === 14 ? '2w' : days === 30 ? '30d' : days === 90 ? '3m' : '1y'}
          </button>
        ))}
      </div>

      {/* Key Metrics */}
      {dashboardStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <p className="text-sm text-gray-600 mb-2">Total Complaints</p>
            <p className="text-3xl font-bold text-blue-600">{dashboardStats.metrics.total_complaints}</p>
            <p className="text-xs text-gray-500 mt-2">Period: {dashboardStats.period.days} days</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <p className="text-sm text-gray-600 mb-2">Resolution Rate</p>
            <p className="text-3xl font-bold text-green-600">{dashboardStats.metrics.resolution_rate}%</p>
            <p className="text-xs text-gray-500 mt-2">{dashboardStats.metrics.resolved} resolved</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <p className="text-sm text-gray-600 mb-2">Pending</p>
            <p className="text-3xl font-bold text-orange-600">{dashboardStats.metrics.pending}</p>
            <p className="text-xs text-gray-500 mt-2">Awaiting action</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <p className="text-sm text-gray-600 mb-2">Escalation Rate</p>
            <p className="text-3xl font-bold text-red-600">{dashboardStats.metrics.escalation_rate}%</p>
            <p className="text-xs text-gray-500 mt-2">{dashboardStats.metrics.escalated} escalated</p>
          </div>
        </div>
      )}

      {/* Complaints Over Time Chart */}
      {trendData && trendData.trends.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <ArrowTrendingUpIcon className="h-5 w-5 mr-2 text-blue-600" />
            Complaints Over Time
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData.trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#3b82f6" name="Total" />
              <Line type="monotone" dataKey="resolved" stroke="#10b981" name="Resolved" />
              <Line type="monotone" dataKey="pending" stroke="#f59e0b" name="Pending" />
              <Line type="monotone" dataKey="escalated" stroke="#ef4444" name="Escalated" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Category Distribution */}
      {categoryData && categoryData.categories.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bar Chart */}
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Complaints by Category</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryData.categories}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total" fill="#3b82f6" />
                <Bar dataKey="resolved" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Category List */}
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h3>
            <div className="space-y-3">
              {categoryData.categories.slice(0, 5).map((cat, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{cat.category}</p>
                    <p className="text-xs text-gray-500">
                      Resolution: {cat.resolution_rate}%
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-600">{cat.total}</p>
                    <p className="text-xs text-gray-500">{cat.percentage}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Top Categories */}
      {dashboardStats && dashboardStats.top_categories.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Categories</h3>
          <div className="space-y-2">
            {dashboardStats.top_categories.map((cat, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-transparent rounded">
                <span className="font-medium text-gray-900">{cat[0]}</span>
                <span className="bg-blue-100 text-blue-800 text-sm font-semibold px-3 py-1 rounded-full">
                  {cat[1]} complaints
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {trendData && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Total Complaints</p>
              <p className="text-2xl font-bold text-blue-600">{trendData.summary.total_in_period}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Average Daily</p>
              <p className="text-2xl font-bold text-indigo-600">{trendData.summary.average_daily}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Period</p>
              <p className="text-2xl font-bold text-purple-600">{trendData.period_days} days</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TrendAnalytics;
