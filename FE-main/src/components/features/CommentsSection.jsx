import React, { useState, useEffect } from 'react';
import { commentsAPI, getTimeAgo } from '../../lib/featureUtils';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

export default function CommentsSection({ complaintId, token, currentUserRole }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchComments();
  }, [complaintId]);

  const fetchComments = async () => {
    setLoading(true);
    try {
      const response = await commentsAPI.getComments(complaintId, token);
      if (response.success) {
        setComments(response.data.comments);
      }
    } catch (err) {
      setError('Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;

    setSubmitting(true);
    try {
      const response = await commentsAPI.addComment(complaintId, newComment, token);
      if (response.success) {
        setComments([...comments, response.data.comment]);
        setNewComment('');
        setError('');
      }
    } catch (err) {
      setError('Failed to post comment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-4">
      <h4 className="font-medium text-gray-900 dark:text-white">
        Discussion ({comments.length})
      </h4>

      {/* Comments List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        )}

        {comments.map((comment) => (
          <div
            key={comment.id}
            className={`p-3 rounded-lg ${
              comment.is_admin_response
                ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                : 'bg-gray-50 dark:bg-gray-800/50'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-gray-900 dark:text-white">
                  {comment.author_name}
                </span>
                {comment.is_admin_response && (
                  <span className="text-xs bg-blue-200 dark:bg-blue-700 text-blue-800 dark:text-blue-100 px-2 py-0.5 rounded">
                    Admin
                  </span>
                )}
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {getTimeAgo(comment.created_at)}
              </span>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {comment.comment_text}
            </p>
          </div>
        ))}

        {!loading && comments.length === 0 && (
          <p className="text-center text-gray-500 dark:text-gray-400 py-4">
            No comments yet. Be the first to comment!
          </p>
        )}
      </div>

      {/* Add Comment */}
      {error && (
        <div className="text-sm text-red-600 dark:text-red-400">{error}</div>
      )}

      <div className="flex gap-2">
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
          rows={2}
          className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white resize-none"
        />
        <button
          onClick={submitComment}
          disabled={submitting || !newComment.trim()}
          className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          title="Post comment"
        >
          {submitting ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
          ) : (
            <PaperAirplaneIcon className="h-5 w-5" />
          )}
        </button>
      </div>
    </div>
  );
}
