import React, { useState, useEffect } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { tagsAPI } from '../../lib/featureUtils';

export default function TagsComponent({ complaintId, token, onTagsUpdate, isAdmin = false }) {
  const [tags, setTags] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchTags();
  }, [complaintId]);

  const fetchTags = async () => {
    try {
      const response = await tagsAPI.getTags(complaintId, token);
      if (response.success) {
        setTags(response.data.tags);
      }
    } catch (err) {
      setError('Failed to fetch tags');
    }
  };

  const addTag = async () => {
    if (!inputValue.trim() || !isAdmin) return;

    setLoading(true);
    try {
      const response = await tagsAPI.addTags(complaintId, [inputValue.trim()], token);
      if (response.success) {
        setTags(response.data.tags);
        setInputValue('');
        if (onTagsUpdate) onTagsUpdate(response.data.tags);
      }
    } catch (err) {
      setError('Failed to add tag');
    } finally {
      setLoading(false);
    }
  };

  const removeTag = async (tag) => {
    if (!isAdmin) return;

    try {
      const response = await tagsAPI.removeTag(complaintId, tag, token);
      if (response.success) {
        setTags(response.data.tags);
        if (onTagsUpdate) onTagsUpdate(response.data.tags);
      }
    } catch (err) {
      setError('Failed to remove tag');
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900 dark:text-white">Tags</h4>
        {isAdmin && tags.length > 0 && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {tags.length} tag{tags.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Tags Display */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <div
              key={tag}
              className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100 rounded-full text-sm"
            >
              <span>#{tag}</span>
              {isAdmin && (
                <button
                  onClick={() => removeTag(tag)}
                  className="hover:text-blue-600 dark:hover:text-blue-300 transition-colors"
                  title="Remove tag"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add Tag Input (Admin Only) */}
      {isAdmin && (
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addTag()}
            placeholder="Add new tag..."
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white bg-white"
          />
          <button
            onClick={addTag}
            disabled={loading || !inputValue.trim()}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            <PlusIcon className="h-5 w-5" />
          </button>
        </div>
      )}

      {error && (
        <div className="text-sm text-red-600 dark:text-red-400">{error}</div>
      )}

      {tags.length === 0 && !isAdmin && (
        <p className="text-sm text-gray-500 dark:text-gray-400">No tags yet</p>
      )}
    </div>
  );
}
