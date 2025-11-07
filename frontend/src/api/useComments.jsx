// src/api/useComments.jsx
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import api from './axios';

// Define the API endpoint as an environment variable to avoid hardcoding
const MESSAGING_API = import.meta.env.VITE_MESSAGING_API

export const useComments = (ticketId) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    current_page: 1,
    total_pages: 1
  });
  const { user } = useAuth();

  const refreshComments = useCallback(() => {
    setRefreshKey(prev => prev + 1);
  }, []);

  // Helper function to get the user's role for comments
  const getUserRole = useCallback(() => {
    // Get user role from user object if available
    if (user) {
      // Try to get role from common locations in the user object
      return user.role || user.userRole || 'User';
    }
    // Default to 'User' if no specific role is found
    return 'User';
  }, [user]);

  // Fetch comments for a ticket with pagination
  const fetchComments = useCallback(async (page = 1) => {
    if (!ticketId) return;

    setLoading(true);
    try {
      const response = await api.get(`${MESSAGING_API}/api/comments/?ticket_id=${ticketId}&page=${page}`);
      
      // Handle both paginated and non-paginated responses
      if (response.data.results) {
        // Paginated response
        setComments(response.data.results);
        setPagination({
          count: response.data.count,
          next: response.data.next,
          previous: response.data.previous,
          current_page: page,
          total_pages: Math.ceil(response.data.count / 10) // Assuming page size of 10
        });
      } else {
        // Non-paginated response (fallback)
        setComments(response.data);
        setPagination({
          count: response.data.length,
          next: null,
          previous: null,
          current_page: 1,
          total_pages: 1
        });
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching comments:', err);
      setError('Failed to load comments. Please try again later.');
      setComments([]);
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  // Add a new comment with optional file attachments
  const addComment = useCallback(async (content, files = []) => {
    if (!ticketId || !user?.id) {
      setError('Unable to add comment: Missing ticket ID or user information');
      return null;
    }

    const userRole = getUserRole();
    
    try {
      const formData = new FormData();
      formData.append('ticket_id', ticketId);
      formData.append('user_id', user.id);
      formData.append('firstname', user.first_name || user.firstname || '');
      formData.append('lastname', user.last_name || user.lastname || '');
      formData.append('role', userRole);
      formData.append('content', content);

      // Add files using the 'documents' field that the backend expects
      files.forEach((file) => {
        formData.append('documents', file);
      });

      const response = await api.post(`${MESSAGING_API}/api/comments/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      refreshComments();
      return response.data;
    } catch (err) {
      console.error('Error adding comment:', err);
      setError('Failed to post your comment. Please try again.');
      return null;
    }
  }, [ticketId, user, getUserRole, refreshComments]);

  // Add a reply to a comment with optional file attachments
  const addReply = useCallback(async (parentCommentId, content, files = []) => {
    if (!ticketId || !user?.id) {
      setError('Unable to add reply: Missing ticket ID or user information');
      return null;
    }

    const userRole = getUserRole();
    
    try {
      const formData = new FormData();
      formData.append('user_id', user.id);
      formData.append('firstname', user.first_name || user.firstname || '');
      formData.append('lastname', user.last_name || user.lastname || '');
      formData.append('role', userRole);
      formData.append('content', content);

      // Add files if any
      files.forEach((file, index) => {
        if (index < 5) {
          formData.append('documents', file);
        }
      });

      const response = await api.post(`${MESSAGING_API}/api/comments/${parentCommentId}/reply/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      refreshComments();
      return response.data;
    } catch (err) {
      console.error('Error adding reply:', err);
      setError('Failed to post your reply. Please try again.');
      return null;
    }
  }, [ticketId, user, getUserRole, refreshComments]);

  // Add a reaction to a comment (like/dislike)
  const addReaction = useCallback(async (commentId, reactionType) => {
    if (!user?.id) {
      setError('Unable to react: Missing user information');
      return null;
    }

    const userRole = getUserRole();
    
    try {
      const response = await api.post(`${MESSAGING_API}/api/comments/${commentId}/rate/`, {
        user_id: user.id,
        firstname: user.first_name || user.firstname || '',
        lastname: user.last_name || user.lastname || '',
        role: userRole,
        rating: reactionType === 'like' ? true : false // Convert like/dislike to true/false
      });
      refreshComments();
      return response.data;
    } catch (err) {
      console.error('Error adding reaction:', err);
      setError('Failed to save your reaction. Please try again.');
      return null;
    }
  }, [user, getUserRole, refreshComments]);

  // Remove a reaction
  const removeReaction = useCallback(async (commentId) => {
    if (!user?.id) {
      setError('Unable to remove reaction: Missing user information');
      return false;
    }
    
    const userRole = getUserRole();
    
    try {
      await api.post(`${MESSAGING_API}/api/comments/${commentId}/rate/`, {
        user_id: user.id,
        firstname: user.first_name || user.firstname || '',
        lastname: user.last_name || user.lastname || '',
        role: userRole,
        rating: null // null to remove rating
      });
      refreshComments();
      return true;
    } catch (err) {
      console.error('Error removing reaction:', err);
      setError('Failed to remove your reaction. Please try again.');
      return false;
    }
  }, [refreshComments, user, getUserRole]);

  // Delete a comment
  const deleteComment = useCallback(async (commentId) => {
    if (!commentId) {
      setError('Unable to delete comment: Missing comment id');
      return false;
    }

    try {
      await api.delete(`${MESSAGING_API}/api/comments/${commentId}/`);
      refreshComments();
      return true;
    } catch (err) {
      console.error('Error deleting comment:', err);
      setError('Failed to delete comment. Please try again.');
      return false;
    }
  }, [refreshComments]);

  // Attach document to existing comment
  const attachDocument = useCallback(async (commentId, files) => {
    if (!user?.id || !files?.length) {
      setError('Unable to attach document: Missing user information or files');
      return false;
    }

    const userRole = getUserRole();
    
    try {
      const formData = new FormData();
      formData.append('user_id', user.id);
      formData.append('firstname', user.first_name || user.firstname || '');
      formData.append('lastname', user.last_name || user.lastname || '');
      formData.append('role', userRole);

      // Add files
      files.forEach(file => {
        formData.append('documents', file);
      });

      const response = await api.post(`${MESSAGING_API}/api/comments/${commentId}/attach_document/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      refreshComments();
      return response.data;
    } catch (err) {
      console.error('Error attaching document:', err);
      setError('Failed to attach document. Please try again.');
      return false;
    }
  }, [user, getUserRole, refreshComments]);

  // Download document
  const downloadDocument = useCallback(async (documentId, filename) => {
    try {
      const response = await api.get(`${MESSAGING_API}/api/comments/download-document/${documentId}/`, {
        responseType: 'blob',
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (err) {
      console.error('Error downloading document:', err);
      setError('Failed to download document. Please try again.');
      return false;
    }
  }, []);

  // Effect to fetch comments when ticketId changes or refreshKey is updated
  useEffect(() => {
    fetchComments();
  }, [fetchComments, refreshKey]);

  return {
    comments,
    loading,
    error,
    pagination,
    addComment,
    addReply,
    addReaction,
    removeReaction,
    deleteComment,
    attachDocument,
    downloadDocument,
    refreshComments,
    fetchComments // Expose for pagination
  };
};

export default useComments;