import React, { useState, useEffect, useCallback, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, Transition } from '@headlessui/react';
import { useAuth } from '../context/AuthContext';
import { format, parseISO } from 'date-fns';
import TrendAnalytics from '../components/features/TrendAnalytics';
import {
  Bars3Icon,
  XMarkIcon,
  ShieldCheckIcon,
  UserIcon,
  EnvelopeIcon,
  PaperClipIcon,
  DocumentTextIcon,
  EyeIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  ArrowRightOnRectangleIcon,
  CalendarIcon,
  ClockIcon,
  CheckCircleIcon,
  ChartBarIcon,
  CogIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  BellIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

function AdminDashboard() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [complaints, setComplaints] = useState([]);
  const [stats, setStats] = useState(null);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [filteredComplaints, setFilteredComplaints] = useState([]);
  const [selectedComplaints, setSelectedComplaints] = useState([]);

  useEffect(() => {
    if (complaints.length > 0) {
      const filtered = complaints.filter(complaint => {
        const complaintDate = parseISO(complaint.created_at);
        return format(complaintDate, 'yyyy-MM-dd') === format(selectedDate, 'yyyy-MM-dd');
      });
      setFilteredComplaints(filtered);
    }
  }, [selectedDate, complaints]);
  const [adminUser, setAdminUser] = useState(null);
  const [previewImage, setPreviewImage] = useState(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [currentAttachments, setCurrentAttachments] = useState([]);
  const [currentAttachmentIndex, setCurrentAttachmentIndex] = useState(0);

  const handleAttachmentClick = (attachments, index) => {
    if (attachments[index].file_type.startsWith('image/')) {
      setCurrentAttachments(attachments.filter(att => att.file_type.startsWith('image/')));
      setCurrentAttachmentIndex(index);
      setPreviewImage(attachments[index].file_url);
      setIsPreviewOpen(true);
    } else {
      window.open(attachments[index].file_url, '_blank');
    }
  };

  const handlePrevImage = useCallback(() => {
    const newIndex = (currentAttachmentIndex - 1 + currentAttachments.length) % currentAttachments.length;
    setCurrentAttachmentIndex(newIndex);
    setPreviewImage(currentAttachments[newIndex].file_url);
  }, [currentAttachmentIndex, currentAttachments]);

  const handleNextImage = useCallback(() => {
    const newIndex = (currentAttachmentIndex + 1) % currentAttachments.length;
    setCurrentAttachmentIndex(newIndex);
    setPreviewImage(currentAttachments[newIndex].file_url);
  }, [currentAttachmentIndex, currentAttachments]);

  const handleKeyPress = useCallback((e) => {
    if (!isPreviewOpen) return;

    switch (e.key) {
      case 'ArrowLeft':
        handlePrevImage();
        break;
      case 'ArrowRight':
        handleNextImage();
        break;
      case 'Escape':
        setIsPreviewOpen(false);
        break;
      default:
        break;
    }
  }, [isPreviewOpen, handlePrevImage, handleNextImage]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/complaints/stats`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setStats(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchComplaints = async (status = null) => {
    setLoadingData(true);
    try {
      let url = `${import.meta.env.VITE_API_URL}/api/complaints/all`;
      if (status) {
        url += `?status=${status}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setComplaints(data.data.complaints);
      }
    } catch (error) {
      setError('Failed to fetch complaints');
    } finally {
      setLoadingData(false);
    }
  };

  // First useEffect - always called
  useEffect(() => {
    // Check for admin authentication
    const adminToken = localStorage.getItem('adminToken');
    const adminUserData = localStorage.getItem('adminUser');

    if (!adminToken || !adminUserData) {
      navigate('/admin-login');
      return;
    }

    try {
      const userData = JSON.parse(adminUserData);
      setAdminUser(userData);
    } catch (error) {
      console.error('Error parsing admin user data:', error);
      navigate('/admin-login');
    }
  }, [navigate]);

  // Second useEffect - always called
  useEffect(() => {
    // Only fetch data if adminUser is set
    if (adminUser) {
      fetchStats();
      if (activeSection === 'all-complaints' || activeSection === 'dashboard') {
        fetchComplaints();
      } else if (activeSection === 'pending') {
        fetchComplaints('pending');
      } else if (activeSection === 'in-progress') {
        fetchComplaints('in_progress');
      } else if (activeSection === 'resolved') {
        fetchComplaints('resolved');
      }
    }
  }, [activeSection, adminUser]);

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminUser');
    navigate('/admin-login');
  };

  const navigation = [
    { name: 'Dashboard', icon: ChartBarIcon, href: 'dashboard', current: activeSection === 'dashboard' },
    { name: 'All Complaints', icon: DocumentTextIcon, href: 'all-complaints', current: activeSection === 'all-complaints' },
    { name: 'Pending', icon: ClockIcon, href: 'pending', current: activeSection === 'pending' },
    { name: 'In Progress', icon: CogIcon, href: 'in-progress', current: activeSection === 'in-progress' },
    { name: 'Resolved', icon: CheckCircleIcon, href: 'resolved', current: activeSection === 'resolved' },    { name: 'Analytics', icon: ChartBarIcon, href: 'analytics', current: activeSection === 'analytics' },  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'in_progress': return 'bg-indigo-100 text-indigo-800 border-indigo-300';
      case 'resolved': return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'closed': return 'bg-gray-100 text-gray-800 border-gray-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const updateComplaintStatus = async (complaintId, newStatus, adminResponse = '') => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/complaints/${complaintId}/update-status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
        },
        body: JSON.stringify({
          status: newStatus,
          admin_response: adminResponse
        })
      });

      const data = await response.json();
      if (data.success) {
        // Refresh complaints list
        fetchComplaints();
        fetchStats();
        return true;
      } else {
        setError(data.message || 'Failed to update status');
        return false;
      }
    } catch (error) {
      setError('Failed to update complaint status');
      return false;
    }
  };

  const handleBulkUpdate = async (newStatus) => {
    const promises = selectedComplaints.map(id => updateComplaintStatus(id, newStatus, 'Bulk update by administrator'));
    await Promise.all(promises);
    setSelectedComplaints([]);
    fetchComplaints();
    fetchStats();
  };

  const toggleSelection = (complaintId) => {
    setSelectedComplaints(prev =>
      prev.includes(complaintId)
        ? prev.filter(id => id !== complaintId)
        : [...prev, complaintId]
    );
  };

  // Show loading state while checking auth
  if (!adminUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return (
          <div className="space-y-8">
            {/* Calendar Section */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-8 mb-8">
              <div className="flex items-center space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-xl flex items-center justify-center">
                  <CalendarIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Complaint Calendar</h2>
                  <p className="text-gray-600">View complaints by date</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="rounded-xl overflow-hidden shadow-sm border border-purple-100">
                  <div className="bg-gradient-to-r from-purple-500 to-indigo-500 px-4 py-3 border-b border-purple-100">
                    <h4 className="text-sm font-medium text-white">Select Date</h4>
                  </div>
                  <input
                    type="date"
                    value={format(selectedDate, 'yyyy-MM-dd')}
                    onChange={(e) => setSelectedDate(parseISO(e.target.value))}
                    className="w-full p-4 border-none focus:ring-2 focus:ring-purple-500 focus:outline-none bg-white/90"
                  />
                </div>

                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl overflow-hidden shadow-sm border border-purple-100">
                  <div className="bg-gradient-to-r from-purple-500 to-indigo-500 px-4 py-3 border-b border-purple-100">
                    <h4 className="text-sm font-medium text-white">{format(selectedDate, 'MMMM d, yyyy')}</h4>
                  </div>
                  {filteredComplaints.length === 0 ? (
                    <div className="flex items-center justify-center h-20 bg-white/90 p-4">
                      <p className="text-gray-500">No complaints for this date</p>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-20 bg-white/90 p-4">
                      <div className="bg-gradient-to-r from-red-50 to-red-100 px-6 py-3 rounded-full border border-red-200">
                        <p className="text-red-600 font-semibold text-lg">{filteredComplaints.length} complaints found</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Welcome Section */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-8">
              <div className="flex items-center space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-xl flex items-center justify-center">
                  <ShieldCheckIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Welcome, {adminUser?.name}!</h2>
                  <p className="text-gray-600">Admin Dashboard - Manage complaints and users</p>
                </div>
              </div>

              {/* Admin Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-xl">
                  <UserIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Name</p>
                    <p className="font-medium text-gray-900">{adminUser?.name}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-xl">
                  <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="font-medium text-gray-900">{adminUser?.email}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-xl">
                  <ShieldCheckIcon className="h-5 w-5 text-purple-600" />
                  <div>
                    <p className="text-sm text-gray-500">Role</p>
                    <p className="font-medium text-gray-900 capitalize">admin</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Statistics */}
            {stats && (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-6 font-display">System Intelligence</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
                  {/* Status Distribution */}
                  <div className="space-y-6">
                    <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Status Distribution</h4>
                    <div className="h-64">
                      <Pie
                        data={{
                          labels: ['Pending', 'In Progress', 'Resolved'],
                          datasets: [
                            {
                              label: 'Complaints',
                              data: [
                                stats.status_stats.pending,
                                stats.status_stats.in_progress,
                                stats.status_stats.resolved
                              ],
                              backgroundColor: [
                                'rgba(255, 196, 0, 0.8)',
                                'rgba(79, 70, 229, 0.8)',
                                'rgba(16, 185, 129, 0.8)',
                              ],
                              borderColor: [
                                'rgba(255, 196, 0, 1)',
                                'rgba(79, 70, 229, 1)',
                                'rgba(16, 185, 129, 1)',
                              ],
                              borderWidth: 1,
                            },
                          ],
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: { position: 'bottom' },
                          }
                        }}
                      />
                    </div>
                  </div>

                  {/* Sentiment Health */}
                  <div className="space-y-6">
                    <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Sentiment Health</h4>
                    <div className="h-64">
                      <Pie
                        data={{
                          labels: ['Positive', 'Neutral', 'Negative'],
                          datasets: [
                            {
                              label: 'Sentiment',
                              data: [
                                stats.sentiment_stats?.positive || 0,
                                stats.sentiment_stats?.neutral || 0,
                                stats.sentiment_stats?.negative || 0
                              ],
                              backgroundColor: [
                                'rgba(34, 197, 94, 0.8)',   // Green
                                'rgba(156, 163, 175, 0.8)', // Gray
                                'rgba(239, 68, 68, 0.8)',   // Red
                              ],
                              borderColor: [
                                'rgba(34, 197, 94, 1)',
                                'rgba(156, 163, 175, 1)',
                                'rgba(239, 68, 68, 1)',
                              ],
                              borderWidth: 1,
                            },
                          ],
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: { position: 'bottom' },
                          }
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Recent Complaints */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-gray-900">Recent Complaints</h3>
                <button
                  onClick={() => setActiveSection('all-complaints')}
                  className="text-purple-600 hover:text-purple-700 text-sm font-medium cursor-pointer"
                >
                  View all
                </button>
              </div>

              {loadingData ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                  <span className="ml-3 text-gray-600">Loading complaints...</span>
                </div>
              ) : complaints.length === 0 ? (
                <div className="text-center py-8">
                  <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-600">No complaints found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {complaints.slice(0, 5).map((complaint) => (
                    <div key={complaint.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-center space-x-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h4 className="font-medium text-gray-900">{complaint.title}</h4>
                            <span className="text-sm font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {complaint.ticket_id}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{complaint.description.substring(0, 100)}...</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(complaint.status)}`}>
                          {complaint.status.replace('_', ' ')}
                        </span>
                        <button
                          onClick={() => setActiveSection('all-complaints')}
                          className="text-purple-600 hover:text-purple-700 cursor-pointer"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      case 'all-complaints':
      case 'pending':
      case 'in-progress':
      case 'resolved':
        return (
          <div className="space-y-8">
            {/* Header - Simplified */}
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-900">
                {activeSection === 'all-complaints' && 'All Complaints'}
                {activeSection === 'pending' && 'Pending Complaints'}
                {activeSection === 'in-progress' && 'In Progress Complaints'}
                {activeSection === 'resolved' && 'Resolved Complaints'}
              </h2>
              <p className="text-gray-600 mt-1">
                {complaints.length} complaints found
              </p>
            </div>

            {/* Complaints List - Horizontal Layout */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-8">
              {loadingData ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                  <span className="ml-3 text-gray-600">Loading complaints...</span>
                </div>
              ) : complaints.length === 0 ? (
                <div className="text-center py-12">
                  <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No complaints found</h3>
                  <p className="text-gray-600">No complaints match the current filter.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {complaints.map((complaint) => (
                    <div key={complaint.id} className="bg-gray-50 rounded-xl p-4 border border-gray-200 flex flex-col h-full">
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={selectedComplaints.includes(complaint.id)}
                              onChange={() => toggleSelection(complaint.id)}
                              className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                            />
                            <h4 className="text-base font-semibold text-gray-900 truncate">{complaint.title}</h4>
                          </div>
                          <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                            {complaint.ticket_id}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{complaint.description}</p>

                        <div className="flex flex-wrap gap-1.5 mb-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(complaint.status)}`}>
                            {complaint.status.replace('_', ' ')}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getPriorityColor(complaint.priority)}`}>
                            {complaint.priority}
                          </span>
                        </div>

                        <div className="text-xs text-gray-500 mb-3">
                          <div>Created: {formatDate(complaint.created_at)}</div>
                          {complaint.resolved_at && (
                            <div>Resolved: {formatDate(complaint.resolved_at)}</div>
                          )}
                        </div>
                      </div>

                      <div className="mt-auto">
                        {complaint.status === 'pending' && (
                          <button
                            onClick={(e) => {
                              // Add loading state to the button
                              const button = e.target;
                              const originalText = button.innerHTML;
                              button.innerHTML = '<div class="flex items-center justify-center"><div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>Processing...</div>';
                              button.disabled = true;

                              // Call the update function
                              updateComplaintStatus(complaint.id, 'in_progress')
                                .finally(() => {
                                  // Reset button state if needed (though the component will likely re-render)
                                  button.innerHTML = originalText;
                                  button.disabled = false;
                                });
                            }}
                            className="w-full px-3 py-2 text-sm text-white rounded-lg transition-colors cursor-pointer hover:opacity-90" style={{ backgroundColor: 'rgb(79, 70, 229)' }}
                          >
                            Start Progress
                          </button>
                        )}
                        {complaint.status === 'in_progress' && (
                          <button
                            onClick={(e) => {
                              // Add loading state to the button
                              const button = e.target;
                              const originalText = button.innerHTML;
                              button.innerHTML = '<div class="flex items-center justify-center"><div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>Processing...</div>';
                              button.disabled = true;

                              // Call the update function
                              updateComplaintStatus(complaint.id, 'resolved')
                                .finally(() => {
                                  // Reset button state if needed (though the component will likely re-render)
                                  button.innerHTML = originalText;
                                  button.disabled = false;
                                });
                            }}
                            className="w-full px-3 py-2 text-sm text-white rounded-lg transition-colors cursor-pointer hover:opacity-90" style={{ backgroundColor: 'rgb(16, 185, 129)' }}
                          >
                            Mark Resolved
                          </button>
                        )}
                      </div>


                      {/* Admin Response - Compact */}
                      {complaint.admin_response && (
                        <div className="mt-2 p-2 bg-blue-50 rounded-lg border border-blue-200 text-xs">
                          <h5 className="font-medium text-blue-900 mb-1">Admin Response:</h5>
                          <p className="text-blue-800 line-clamp-2">{complaint.admin_response}</p>
                        </div>
                      )}

                      {/* Attachments - Compact */}
                      {complaint.attachments && complaint.attachments.length > 0 && (
                        <div className="mt-2">
                          <div className="flex items-center text-xs font-medium text-gray-700 mb-1">
                            <PaperClipIcon className="h-3 w-3 mr-1" />
                            <span>Attachments: {complaint.attachments.length}</span>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {complaint.attachments.map((attachment, index) => (
                              <div
                                key={index}
                                className={`relative w-12 h-12 rounded-lg overflow-hidden border border-gray-200 hover:border-purple-400 transition-colors ${attachment.file_type.startsWith('image/') ? 'cursor-pointer' : ''}`}
                                onClick={() => handleAttachmentClick(complaint.attachments, index)}
                              >
                                {attachment.file_type.startsWith('image/') ? (
                                  <>
                                    <img
                                      src={attachment.file_url}
                                      alt={attachment.original_filename}
                                      className="w-full h-full object-cover"
                                      onError={(e) => {
                                        e.target.style.display = 'none';
                                        e.target.parentElement.innerHTML = `
                                          <div class="w-full h-full flex items-center justify-center bg-gray-100">
                                            <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                            </svg>
                                          </div>
                                        `;
                                      }}
                                    />
                                    <div
                                      className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-20 transition-opacity flex items-center justify-center group"
                                    >
                                      <EyeIcon className="h-5 w-5 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                  </>
                                ) : (
                                  <div className="w-full h-full bg-gray-50 hover:bg-gray-100 transition-colors flex flex-col items-center justify-center p-1 cursor-pointer">
                                    <DocumentTextIcon className="h-5 w-5 text-gray-400 mb-0.5" />
                                    <span className="text-[8px] text-gray-500 text-center truncate w-full">
                                      {attachment.original_filename.split('.').pop().toUpperCase()}
                                    </span>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );



      case 'analytics':
        return (
          <div className="space-y-8">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Analytics & Trends</h2>
              <p className="text-gray-600 mt-1">View complaint trends, statistics, and analytics</p>
            </div>
            <TrendAnalytics token={adminToken} />
          </div>
        );

      default:
        return null;
    }
  };

  // Image Preview Popup
  const ImagePreviewPopup = () => {
    return (
      <Transition appear show={isPreviewOpen} as={Fragment}>
        <Dialog as="div" className="fixed inset-0 z-50 overflow-y-auto" onClose={() => setIsPreviewOpen(false)}>
          <div className="min-h-screen px-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0"
              enterTo="opacity-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Dialog.Overlay className="fixed inset-0 bg-black opacity-75" />
            </Transition.Child>

            <span className="inline-block h-screen align-middle" aria-hidden="true">
              &#8203;
            </span>

            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <div className="inline-block w-full max-w-5xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-2xl">
                <div className="absolute top-0 right-0 pt-4 pr-4">
                  <button
                    type="button"
                    className="bg-white rounded-md p-2 text-gray-400 hover:text-gray-500 focus:outline-none cursor-pointer"
                    onClick={() => setIsPreviewOpen(false)}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {previewImage && (
                  <div className="mt-2">
                    <div className="relative group">
                      {currentAttachments.length > 1 && (
                        <>
                          <button
                            onClick={handlePrevImage}
                            className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-white/80 hover:bg-white p-2 rounded-full shadow-lg z-10 transition-all opacity-0 group-hover:opacity-100"
                          >
                            <ChevronLeftIcon className="h-6 w-6 text-gray-600" />
                          </button>
                          <button
                            onClick={handleNextImage}
                            className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-white/80 hover:bg-white p-2 rounded-full shadow-lg z-10 transition-all opacity-0 group-hover:opacity-100"
                          >
                            <ChevronRightIcon className="h-6 w-6 text-gray-600" />
                          </button>
                        </>
                      )}
                      <img
                        src={previewImage}
                        alt="Preview"
                        className="max-w-full max-h-[80vh] object-contain mx-auto rounded-lg shadow-lg"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = `${import.meta.env.VITE_API_URL}/api/complaints/${complaintId}/attachment/${attachment.id}`;
                          console.log('Image failed to load:', previewImage);
                        }}
                        onLoad={() => console.log('Image loaded successfully:', previewImage)}
                      />
                      <div className="absolute inset-0 bg-black opacity-0 group-hover:opacity-10 transition-opacity rounded-lg"></div>
                    </div>
                    <div className="mt-4 text-center space-y-2">
                      {currentAttachments.length > 1 && (
                        <>
                          <p className="text-sm font-medium text-gray-600">
                            Image {currentAttachmentIndex + 1} of {currentAttachments.length}
                          </p>
                          <div className="flex items-center justify-center space-x-4 text-sm text-gray-500">
                            <span className="flex items-center">
                              <ArrowLeftIcon className="h-4 w-4 mr-1" /> Previous
                            </span>
                            <span className="flex items-center">
                              <ArrowRightIcon className="h-4 w-4 mr-1" /> Next
                            </span>
                          </div>
                        </>
                      )}
                      <p className="text-sm text-gray-500">Click outside or press ESC to close</p>
                    </div>
                  </div>
                )}
              </div>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex flex-col">
      {/* Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]"></div>
        <div className="absolute top-20 left-20 w-72 h-72 bg-gradient-to-br from-purple-400/20 to-indigo-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-gradient-to-br from-indigo-400/20 to-purple-400/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      {/* Header - Fixed at top */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-sm border-b border-white/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500 cursor-default"
              >
                <Bars3Icon className="h-6 w-6" />
              </button>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent ml-4 lg:ml-0">
                Query Pro Admin
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <ShieldCheckIcon className="h-5 w-5 text-purple-600" />
                <span className="text-sm text-gray-700">{adminUser?.name}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 relative">
        {/* Sidebar - Fixed position */}
        <div className={`fixed top-16 bottom-0 left-0 z-30 w-64 bg-white/90 backdrop-blur-sm transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 transition duration-300 ease-in-out shadow-xl overflow-y-auto`}>
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Admin Panel</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 cursor-default"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <nav className="mt-8 px-4 pb-8">
            <ul className="space-y-2">
              {navigation.map((item) => (
                <li key={item.name}>
                  <button
                    onClick={() => setActiveSection(item.href)}
                    className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-colors cursor-pointer ${item.current
                      ? 'bg-purple-50 text-purple-700 border border-purple-200'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </button>
                </li>
              ))}

              {/* Logout Button */}
              <li className="pt-4 border-t border-gray-200">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-50 hover:text-red-700 rounded-xl transition-colors cursor-pointer"
                >
                  <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
                  Logout
                </button>
              </li>
            </ul>
          </nav>
        </div>

        {/* Main Content - Scrollable */}
        <div className="flex-1 lg:ml-64 overflow-y-auto">
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {renderContent()}
          </main>
        </div>

        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Bulk Action Bar */}
        {selectedComplaints.length > 0 && (
          <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50 bg-white/90 backdrop-blur-md rounded-2xl shadow-2xl border border-purple-200 px-6 py-4 flex items-center space-x-6 animate-slide-up">
            <div className="flex items-center space-x-2 border-r border-gray-200 pr-6">
              <span className="bg-purple-600 text-white text-xs font-bold px-2 py-1 rounded-full">
                {selectedComplaints.length}
              </span>
              <span className="text-sm font-medium text-gray-700">Selected</span>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => handleBulkUpdate('in_progress')}
                className="flex items-center px-4 py-2 bg-indigo-50 text-indigo-700 text-sm font-medium rounded-xl border border-indigo-100 hover:bg-indigo-100 transition-colors"
              >
                <CogIcon className="h-4 w-4 mr-2" />
                Start Selected
              </button>
              <button
                onClick={() => handleBulkUpdate('resolved')}
                className="flex items-center px-4 py-2 bg-emerald-50 text-emerald-700 text-sm font-medium rounded-xl border border-emerald-100 hover:bg-emerald-100 transition-colors"
              >
                <CheckCircleIcon className="h-4 w-4 mr-2" />
                Resolve Selected
              </button>
              <button
                onClick={() => setSelectedComplaints([])}
                className="text-sm text-gray-500 hover:text-gray-700 font-medium px-4 cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <ImagePreviewPopup />
      </div>
    </div>
  );
}

export default AdminDashboard;
