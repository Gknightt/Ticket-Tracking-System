import { useState, useEffect, useRef, useCallback } from 'react';

const MESSAGING_API_BASE = import.meta.env.VITE_MESSAGING_API || 'http://localhost:8005/api';
const WEBSOCKET_BASE = import.meta.env.VITE_MESSAGING_WS || 'ws://localhost:8005';

export const useMessaging = (ticketId, userId = 'anonymous') => {
  const [ticket, setTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [typingUsers, setTypingUsers] = useState(new Set());
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // API functions
  const apiCall = async (endpoint, options = {}) => {
    const url = `${MESSAGING_API_BASE}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for authentication
      ...options,
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return response.json();
  };

  // Fetch messages for a ticket using the correct endpoint
  const fetchMessages = async () => {
    if (!ticketId) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await apiCall(`/messages/by_ticket/?ticket_id=${ticketId}`, {
        method: 'GET',
      });

      setTicket({
        ticket_id: result.ticket_id,
        status: result.ticket_status
      });
      setMessages(result.messages || []);
      return result;
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch messages:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!ticketId) return;

    try {
      const wsUrl = `${WEBSOCKET_BASE}/ws/tickets/${ticketId}/`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected to ticket:', ticketId);
        setIsConnected(true);
        setError(null);
        
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        
        // Attempt to reconnect after a delay (unless manual close)
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection failed');
      };

    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
      setError('Failed to establish WebSocket connection');
    }
  }, [ticketId]);

  // Handle incoming WebSocket messages for real-time updates
  const handleWebSocketMessage = useCallback((data) => {
    switch (data.type) {
      case 'connection_established':
        console.log('WebSocket connection confirmed:', data.message);
        break;

      case 'message_sent':
        // Add new message from WebSocket (real-time)
        setMessages(prev => {
          const exists = prev.some(msg => msg.message_id === data.message.message_id);
          if (!exists) {
            return [...prev, data.message].sort((a, b) => 
              new Date(a.created_at) - new Date(b.created_at)
            );
          }
          return prev;
        });
        break;

      case 'message_edited':
        // Update edited message in real-time
        setMessages(prev => prev.map(msg => 
          msg.message_id === data.message.message_id ? data.message : msg
        ));
        break;

      case 'message_deleted':
        // Remove deleted message in real-time
        setMessages(prev => prev.filter(msg => msg.message_id !== data.message_id));
        break;

      case 'reaction_added':
        // Update reactions in real-time
        setMessages(prev => prev.map(msg => {
          if (msg.message_id === data.message_id) {
            const updatedReactions = [...(msg.reactions || [])];
            const existingIndex = updatedReactions.findIndex(
              r => r.user === data.reaction.user && r.reaction === data.reaction.reaction
            );
            if (existingIndex === -1) {
              updatedReactions.push(data.reaction);
            }
            
            // Recalculate reaction counts
            const reactionCounts = {};
            updatedReactions.forEach(r => {
              reactionCounts[r.reaction] = (reactionCounts[r.reaction] || 0) + 1;
            });
            
            return { ...msg, reactions: updatedReactions, reaction_counts: reactionCounts };
          }
          return msg;
        }));
        break;

      case 'reaction_removed':
        // Remove reaction in real-time
        setMessages(prev => prev.map(msg => {
          if (msg.message_id === data.message_id) {
            const updatedReactions = (msg.reactions || []).filter(
              r => !(r.user === data.user && r.reaction === data.reaction)
            );
            
            // Recalculate reaction counts
            const reactionCounts = {};
            updatedReactions.forEach(r => {
              reactionCounts[r.reaction] = (reactionCounts[r.reaction] || 0) + 1;
            });
            
            return { ...msg, reactions: updatedReactions, reaction_counts: reactionCounts };
          }
          return msg;
        }));
        break;

      case 'typing_indicator':
        setTypingUsers(prev => {
          const newSet = new Set(prev);
          if (data.is_typing && data.user !== userId) {
            newSet.add(data.user);
          } else {
            newSet.delete(data.user);
          }
          return newSet;
        });
        break;

      case 'pong':
        // Handle ping/pong for connection keepalive
        break;

      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }, [userId]);

  // Send a message with optional attachments
  const sendMessage = async (messageText, attachments = []) => {
    if (!ticketId || !messageText.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('ticket_id', ticketId);
      formData.append('message', messageText.trim());

      // Add attachments
      attachments.forEach((file) => {
        formData.append('attachments', file);
      });

      const result = await fetch(`${MESSAGING_API_BASE}/messages/`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (!result.ok) {
        const errorData = await result.json().catch(() => ({}));
        throw new Error(errorData.error || errorData.message || `HTTP ${result.status}`);
      }

      const newMessage = await result.json();
      
      // Add the new message to the local state if not already added via WebSocket
      setMessages(prev => {
        const exists = prev.some(msg => msg.message_id === newMessage.message_id);
        if (!exists) {
          return [...prev, newMessage].sort((a, b) => 
            new Date(a.created_at) - new Date(b.created_at)
          );
        }
        return prev;
      });

      return newMessage;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Edit a message
  const editMessage = async (messageId, newContent) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiCall(`/messages/${messageId}/`, {
        method: 'PUT',
        body: JSON.stringify({
          message: newContent,
        }),
      });

      // Update the message in local state
      setMessages(prev => prev.map(msg => 
        msg.message_id === messageId ? result : msg
      ));

      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Delete a message
  const deleteMessage = async (messageId) => {
    setIsLoading(true);
    setError(null);

    try {
      await apiCall(`/messages/${messageId}/`, {
        method: 'DELETE',
      });

      // Remove the message from local state
      setMessages(prev => prev.filter(msg => msg.message_id !== messageId));

      return { success: true };
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Add reaction to a message
  const addReaction = async (messageId, reaction) => {
    console.log('Adding reaction:', { messageId, reaction, userId });
    try {
      const result = await apiCall('/reactions/add/', {
        method: 'POST',
        body: JSON.stringify({
          message_id: messageId,
          reaction: reaction,
        }),
      });

      console.log('Add reaction result:', result);
      return result;
    } catch (err) {
      console.error('Add reaction error:', err);
      setError(err.message);
      throw err;
    }
  };

  // Remove reaction from a message
  const removeReaction = async (messageId, reaction) => {
    console.log('Removing reaction:', { messageId, reaction, userId });
    try {
      const result = await apiCall('/reactions/remove/', {
        method: 'POST',
        body: JSON.stringify({
          message_id: messageId,
          reaction: reaction,
        }),
      });

      console.log('Remove reaction result:', result);
      return result;
    } catch (err) {
      console.error('Remove reaction error:', err);
      setError(err.message);
      throw err;
    }
  };

  // Download attachment
  const downloadAttachment = (attachmentId) => {
    const url = `${MESSAGING_API_BASE}/attachments/${attachmentId}/download/`;
    window.open(url, '_blank');
  };

  // Typing indicators
  const sendTypingIndicator = useCallback((isTyping) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: isTyping ? 'typing_start' : 'typing_stop',
        user: userId,
      }));
    }
  }, [userId]);

  const startTyping = useCallback(() => {
    sendTypingIndicator(true);
    
    // Clear any existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Stop typing indicator after 3 seconds of inactivity
    typingTimeoutRef.current = setTimeout(() => {
      sendTypingIndicator(false);
    }, 3000);
  }, [sendTypingIndicator]);

  const stopTyping = useCallback(() => {
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
    sendTypingIndicator(false);
  }, [sendTypingIndicator]);

  // Initialize: Fetch messages first via HTTP, then connect WebSocket for real-time updates
  useEffect(() => {
    if (ticketId) {
      fetchMessages().then(() => {
        connectWebSocket();
      }).catch((error) => {
        console.error('Failed to fetch messages:', error);
        connectWebSocket();
      });
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [ticketId, connectWebSocket]);

  // Keepalive ping
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
  }, [isConnected]);

  return {
    // State
    ticket,
    messages,
    isConnected,
    isLoading,
    error,
    typingUsers: Array.from(typingUsers),

    // Actions
    fetchMessages,
    sendMessage,
    editMessage,
    deleteMessage,
    addReaction,
    removeReaction,
    downloadAttachment,

    // Typing indicators
    startTyping,
    stopTyping,

    // WebSocket management
    reconnect: connectWebSocket,
  };
};