import { useState } from 'react';
import { useMessagingAPI } from './useMessagingAPI';
import { useWebSocketMessaging } from './useWebSocketMessaging';

export const useMessaging = (ticketId, userId = 'anonymous') => {
  const [messages, setMessages] = useState([]);

  const {
    ticket,
    isLoading,
    error: apiError,
    fetchMessages,
    sendMessage,
    editMessage,
    deleteMessage,
    addReaction,
    removeReaction,
    downloadAttachment,
  } = useMessagingAPI(ticketId, setMessages);

  const {
    isConnected,
    error: wsError,
    typingUsers,
    startTyping,
    stopTyping,
    reconnect,
  } = useWebSocketMessaging(ticketId, userId, setMessages);

  return {
    ticket,
    messages,
    isConnected,
    isLoading,
    error: apiError || wsError,
    typingUsers,
    fetchMessages,
    sendMessage,
    editMessage,
    deleteMessage,
    addReaction,
    removeReaction,
    downloadAttachment,
    startTyping,
    stopTyping,
    reconnect,
  };
};