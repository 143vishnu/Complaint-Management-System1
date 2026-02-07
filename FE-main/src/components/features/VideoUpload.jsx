import React, { useState, useRef } from 'react';
import {
  VideoCameraIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  PlayIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';

function VideoUpload({ complaintId, onVideoUpload, token }) {
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [videoTitle, setVideoTitle] = useState('');
  const [videoDescription, setVideoDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [videoPreview, setVideoPreview] = useState('');
  const fileInputRef = useRef(null);

  const ALLOWED_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', '3gp'];
  const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB

  const handleVideoSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError('');
    setSuccess('');

    // Validate file format
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_FORMATS.includes(extension)) {
      setError(`Invalid format. Allowed: ${ALLOWED_FORMATS.join(', ')}`);
      return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setError(`File size exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit`);
      return;
    }

    setSelectedVideo(file);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setVideoPreview(e.target?.result);
    };
    reader.readAsDataURL(file);
  };

  const uploadVideo = async () => {
    if (!selectedVideo || !complaintId) {
      setError('Please select a video file and ensure you have a valid complaint ID');
      return;
    }

    if (!videoTitle.trim()) {
      setError('Please provide a title for the video');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('video', selectedVideo);
      formData.append('title', videoTitle.trim());
      formData.append('description', videoDescription.trim());

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/videos/upload/${complaintId}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );

      const data = await response.json();

      if (data.success) {
        setSuccess(`Video uploaded successfully! Total videos: ${data.data.total_videos}`);
        setSelectedVideo(null);
        setVideoTitle('');
        setVideoDescription('');
        setVideoPreview('');
        if (fileInputRef.current) fileInputRef.current.value = '';

        if (onVideoUpload) {
          onVideoUpload({
            url: data.data.video.url,
            title: videoTitle,
            description: videoDescription
          });
        }

        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(data.message || 'Failed to upload video');
      }
    } catch (err) {
      setError('Error uploading video. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const clearVideo = () => {
    setSelectedVideo(null);
    setVideoTitle('');
    setVideoDescription('');
    setVideoPreview('');
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes, k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h3 className="font-semibold text-purple-900 mb-2 flex items-center">
          <VideoCameraIcon className="h-5 w-5 mr-2" />
          Video Evidence Upload
        </h3>
        <p className="text-sm text-purple-700">
          Upload video evidence to better explain your complaint. Supports MP4, AVI, MOV, MKV, WebM, FLV, 3GP (max 100MB).
        </p>
      </div>

      {/* File Input */}
      <div className="border-2 border-dashed border-purple-300 rounded-lg p-8 hover:border-purple-500 transition-colors bg-purple-50/50">
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleVideoSelect}
          className="hidden"
          accept={ALLOWED_FORMATS.map(f => `.${f}`).join(',')}
        />
        <label onClick={() => fileInputRef.current?.click()} className="cursor-pointer block">
          <div className="text-center">
            <VideoCameraIcon className="mx-auto h-12 w-12 text-purple-400 mb-2" />
            <p className="text-sm font-medium text-purple-900">
              Click to select video or drag and drop
            </p>
            <p className="text-xs text-purple-700 mt-1">
              {ALLOWED_FORMATS.join(', ')} • max 100MB
            </p>
          </div>
        </label>
      </div>

      {/* Selected Video Info */}
      {selectedVideo && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-gray-900">
                {selectedVideo.name}
              </h4>
              <span className="text-xs text-gray-500">
                {formatFileSize(selectedVideo.size)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>

          {/* Video Preview */}
          {videoPreview && (
            <div className="relative rounded-lg overflow-hidden bg-black max-h-48">
              <video
                src={videoPreview}
                className="w-full h-full"
                controls
              />
              <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 bg-black/50 transition-opacity">
                <PlayIcon className="h-12 w-12 text-white" />
              </div>
            </div>
          )}

          {/* Video Details */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Video Title *
            </label>
            <input
              type="text"
              value={videoTitle}
              onChange={(e) => setVideoTitle(e.target.value)}
              placeholder="Give your video a title"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Video Description (Optional)
            </label>
            <textarea
              value={videoDescription}
              onChange={(e) => setVideoDescription(e.target.value)}
              placeholder="Describe what's in the video"
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none"
            />
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
          <ExclamationCircleIcon className="h-5 w-5 text-red-500 flex-shrink-0" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="flex items-center space-x-2 p-4 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircleIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
          <span className="text-sm text-green-700">{success}</span>
        </div>
      )}

      {/* Action Buttons */}
      {selectedVideo && (
        <div className="flex gap-3">
          <button
            onClick={clearVideo}
            type="button"
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition flex items-center justify-center"
          >
            <TrashIcon className="h-4 w-4 mr-2" />
            Clear
          </button>
          <button
            onClick={uploadVideo}
            disabled={uploading || !videoTitle.trim()}
            type="button"
            className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center font-medium"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Uploading...
              </>
            ) : (
              <>
                <CloudArrowUpIcon className="h-4 w-4 mr-2" />
                Upload Video
              </>
            )}
          </button>
        </div>
      )}

      {/* Help Text */}
      {!selectedVideo && (
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-800">
            <strong>Tip:</strong> Videos help us understand your complaint better. 
            You can upload videos after creating your ticket or add them here before submission.
          </p>
        </div>
      )}
    </div>
  );
}

export default VideoUpload;
