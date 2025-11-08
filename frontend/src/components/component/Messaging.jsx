import React, { useState, useRef } from "react";
import { useMessaging } from "../../hooks/useMessaging";
import styles from "./messaging.module.css";

const Messaging = ({
  ticket_id,
  agentName = "Agent",
  agentStatus = "Active",
  currentUser = null,
}) => {
  const [message, setMessage] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [editingMessage, setEditingMessage] = useState(null);
  const [editText, setEditText] = useState('');
  const [showReactionModal, setShowReactionModal] = useState(null); // messageId for which modal is shown
  const [reactionTooltip, setReactionTooltip] = useState(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);

  // Get current user identifier - improved logic
  const currentIdentifier = currentUser?.full_name || 
    currentUser?.user_id ||
    currentUser?.id ||
    currentUser?.email ||
    `${currentUser?.first_name || ""} ${currentUser?.last_name || ""}`.trim() ||
    "Employee";

  // Debug logging to help identify the issue
  console.log('Current User Debug:', {
    currentUser,
    currentIdentifier,
    fullName: currentUser?.full_name,
    userId: currentUser?.user_id,
    id: currentUser?.id,
    email: currentUser?.email
  });

  const {
    ticket, // Add ticket state
    messages,
    isConnected,
    isLoading,
    error,
    typingUsers,
    sendMessage: sendMessageAPI,
    editMessage,
    deleteMessage,
    addReaction,
    removeReaction,
    downloadAttachment,
    startTyping,
    stopTyping,
  } = useMessaging(ticket_id, currentIdentifier);

  // Add debugging - remove this after fixing
  console.log('Messaging Component Debug:', {
    ticket_id,
    ticket,
    messagesCount: messages?.length || 0,
    isLoading,
    error,
    isConnected
  });

  // Scroll to bottom when messages change
  const scrollToBottom = (behavior = "smooth") => {
    try {
      if (containerRef.current) {
        containerRef.current.scrollTo({
          top: containerRef.current.scrollHeight,
          behavior,
        });
      } else {
        messagesEndRef.current?.scrollIntoView({ behavior });
      }
    } catch (err) {
      if (containerRef.current) {
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
      }
    }
  };

  // Send message with attachments
  const sendMessage = async () => {
    if (!message.trim() && attachments.length === 0) return;
    
    try {
      await sendMessageAPI(message.trim(), attachments);
      setMessage("");
      setAttachments([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      stopTyping();
      setTimeout(() => scrollToBottom(), 100);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // Handle message editing
  const handleEditMessage = async (messageId) => {
    if (!editText.trim()) return;

    try {
      await editMessage(messageId, editText);
      setEditingMessage(null);
      setEditText('');
    } catch (error) {
      console.error('Failed to edit message:', error);
    }
  };

  // Handle message deletion
  const handleDeleteMessage = async (messageId) => {
    if (window.confirm('Are you sure you want to delete this message?')) {
      try {
        await deleteMessage(messageId);
      } catch (error) {
        console.error('Failed to delete message:', error);
      }
    }
  };

  // Handle reactions
  const handleReaction = async (messageId, reaction) => {
    try {
      // Enhanced user identification for reaction detection
      const possibleIdentifiers = [
        currentUser?.full_name,
        currentUser?.user_id,
        currentUser?.id,
        currentUser?.email,
        currentUser?.username,
        `${currentUser?.first_name || ""} ${currentUser?.last_name || ""}`.trim(),
        currentIdentifier
      ].filter(Boolean);

      const message = messages.find(msg => msg.message_id === messageId);
      const existingReaction = message?.reactions?.find(r => {
        const reactionUser = r.user_full_name || r.user;
        return possibleIdentifiers.some(id => 
          (reactionUser === id || String(reactionUser).toLowerCase() === String(id).toLowerCase()) &&
          r.reaction === reaction
        );
      });

      console.log('Handle Reaction Debug:', {
        messageId,
        reaction,
        possibleIdentifiers,
        existingReaction,
        messageReactions: message?.reactions
      });

      if (existingReaction) {
        await removeReaction(messageId, reaction);
      } else {
        await addReaction(messageId, reaction);
      }
    } catch (error) {
      console.error('Failed to handle reaction:', error);
    }
  };

  // Handle file selection
  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    setAttachments(prev => [...prev, ...files]);
  };

  // Remove attachment
  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  // Handle input change with typing indicators
  const handleInputChange = (e) => {
    setMessage(e.target.value);
    if (e.target.value.trim()) {
      startTyping();
    } else {
      stopTyping();
    }
  };

  const formatTimestamp = (iso) => {
    try {
      const d = new Date(iso);
      return (
        d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) +
        " | " +
        d.toLocaleDateString()
      );
    } catch {
      return iso;
    }
  };

  const availableReactions = ['👍', '👎', '❤️', '😂', '😮', '😢', '😡', '👏', '🎉', '🔥'];

  return (
    <div className={styles.messagingPage}>
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <span className={styles.agentName}>{agentName}</span>
          <span className={styles.agentStatus}>{agentStatus}</span>
          <span className={`${styles.connectionStatus} ${isConnected ? styles.connected : styles.disconnected}`}>

            
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
        {error && <div className={styles.error}>Error: {error}</div>}
      </div>

      <div className={styles.messageContainer} ref={containerRef}>
        {isLoading && messages.length === 0 && (
          <div className={styles.loadingText}>Loading messages...</div>
        )}

        {messages.map((m) => {
          const senderValue = m.sender || "Unknown User";
          const senderRole = m.sender_role || null;
          
          // Enhanced user identification - try multiple comparison methods
          const possibleIdentifiers = [
            currentUser?.full_name,
            currentUser?.user_id,
            currentUser?.id,
            currentUser?.email,
            currentUser?.username,
            `${currentUser?.first_name || ""} ${currentUser?.last_name || ""}`.trim(),
            currentIdentifier
          ].filter(Boolean);

          const isOwn = possibleIdentifiers.some(identifier => 
            senderValue === identifier ||
            String(senderValue).toLowerCase() === String(identifier).toLowerCase()
          );

          // Enhanced debugging for sender identification
          console.log(`Message ${m.message_id} Debug:`, {
            sender: senderValue,
            currentIdentifier,
            possibleIdentifiers,
            isOwn,
            reactions: m.reactions,
            userReactions: m.reactions?.filter(r => 
              possibleIdentifiers.some(id => r.user === id || r.user_full_name === id)
            ),
            reactionCounts: m.reaction_counts
          });

          return (
            <div className={styles.messageGroup} key={m.message_id}>
              {editingMessage === m.message_id ? (
                <div className={styles.editForm}>
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows={3}
                    className={styles.editTextarea}
                  />
                  <div className={styles.editActions}>
                    <button onClick={() => handleEditMessage(m.message_id)} className={styles.saveButton}>
                      Save
                    </button>
                    <button onClick={() => setEditingMessage(null)} className={styles.cancelButton}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {isOwn ? (
                    <div className={styles.messageRight}>
                      <div className={styles.messageBubble}>
                        <div className={styles.messageBubbleBlue}>
                          <div className={styles.messageHeader}>
                            <span className={styles.senderName}>You</span>
                            {senderRole && (
                              <span className={styles.senderRole}>({senderRole})</span>
                            )}
                          </div>
                          <div className={styles.messageContent}>
                            {m.message}
                            {m.is_edited && <span className={styles.editedIndicator}> (edited)</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className={styles.messageLeft}>
                      <div className={styles.avatar}></div>
                      <div className={styles.messageBubble}>
                        <div className={styles.messageBubbleGray}>
                          <div className={styles.messageHeader}>
                            <span className={styles.senderName}>{senderValue}</span>
                            {senderRole && (
                              <span className={styles.senderRole}>({senderRole})</span>
                            )}
                          </div>
                          <div className={styles.messageContent}>
                            {m.message}
                            {m.is_edited && <span className={styles.editedIndicator}> (edited)</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Attachments */}
                  {m.attachments && m.attachments.length > 0 && (
                    <div className={styles.attachments}>
                      {m.attachments.map((attachment) => (
                        <div key={attachment.attachment_id} className={styles.attachment}>
                          <button 
                            onClick={() => downloadAttachment(attachment.attachment_id)}
                            className={styles.attachmentButton}
                          >
                            📎 {attachment.filename} ({Math.round(attachment.file_size / 1024)}KB)
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Reactions */}
                  <div className={styles.reactions}>
                    {/* Show existing reactions with counts */}
                    {Object.keys(m.reaction_counts || {}).length > 0 && (
                      <div className={styles.existingReactions}>
                        {Object.entries(m.reaction_counts || {}).map(([emoji, count]) => {
                          // Enhanced user reaction detection - check multiple possible user identifiers
                          const userReacted = m.reactions?.some(r => {
                            const reactionUser = r.user_full_name || r.user;
                            return possibleIdentifiers.some(id => 
                              reactionUser === id || 
                              String(reactionUser).toLowerCase() === String(id).toLowerCase()
                            );
                          });
                          
                          const reactorNames = m.reactions
                            ?.filter(r => r.reaction === emoji)
                            ?.map(r => r.user_full_name || r.user)
                            ?.slice(0, 3) // Show first 3 names
                            ?.join(', ');
                          
                          // Debug logging for reaction detection
                          console.log(`Reaction ${emoji} Debug:`, {
                            userReacted,
                            possibleIdentifiers,
                            messageReactions: m.reactions?.filter(r => r.reaction === emoji),
                            reactorNames
                          });
                          
                          return (
                            <button
                              key={emoji}
                              className={`${styles.reactionCount} ${userReacted ? styles.userReacted : ''}`}
                              onClick={() => handleReaction(m.message_id, emoji)}
                              title={`${reactorNames}${m.reactions?.filter(r => r.reaction === emoji).length > 3 ? ' and others' : ''}`}
                              onMouseEnter={() => setReactionTooltip({ messageId: m.message_id, emoji, names: reactorNames })}
                              onMouseLeave={() => setReactionTooltip(null)}
                            >
                              {emoji} {count}
                            </button>
                          );
                        })}
                      </div>
                    )}
                    
                    {/* Add reaction button */}
                    <div className={styles.addReactionContainer}>
                      <button
                        className={styles.addReactionButton}
                        onClick={() => setShowReactionModal(showReactionModal === m.message_id ? null : m.message_id)}
                        title="Add reaction"
                      >
                        😊
                      </button>
                      
                      {/* Facebook-style reaction modal */}
                      {showReactionModal === m.message_id && (
                        <div className={styles.reactionModal}>
                          <div className={styles.reactionModalContent}>
                            {availableReactions.map((emoji) => (
                              <button
                                key={emoji}
                                className={styles.reactionModalOption}
                                onClick={() => {
                                  handleReaction(m.message_id, emoji);
                                  setShowReactionModal(null);
                                }}
                                title={`React with ${emoji}`}
                              >
                                {emoji}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Message Actions for own messages */}
                  {isOwn && (
                    <div className={styles.messageActions}>
                      <button 
                        onClick={() => {
                          setEditingMessage(m.message_id);
                          setEditText(m.message);
                        }}
                        className={styles.actionButton}
                      >
                        Edit
                      </button>
                      <button 
                        onClick={() => handleDeleteMessage(m.message_id)}
                        className={styles.actionButton}
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </>
              )}

              <div className={styles.messageTimestamp}>
                {formatTimestamp(m.created_at)}
              </div>
            </div>
          );
        })}

        {/* Typing Indicators */}
        {typingUsers.length > 0 && (
          <div className={styles.typingIndicators}>
            {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className={styles.footer}>
        {/* File Attachments Preview */}
        {attachments.length > 0 && (
          <div className={styles.attachmentsPreview}>
            {attachments.map((file, index) => (
              <div key={index} className={styles.attachmentPreview}>
                <span>{file.name}</span>
                <button 
                  type="button" 
                  onClick={() => removeAttachment(index)}
                  className={styles.removeAttachment}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <div className={styles.inputContainer}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            multiple
            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar"
            style={{ display: 'none' }}
          />
          
          <button 
            type="button" 
            onClick={() => fileInputRef.current?.click()}
            className={styles.attachButton}
            disabled={isLoading}
          >
            📎
          </button>

          <input
            type="text"
            className={styles.messageInput}
            placeholder="Type your message here..."
            value={message}
            onChange={handleInputChange}
            onBlur={stopTyping}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            disabled={isLoading}
          />
          
          <button
            className={styles.sendButton}
            onClick={sendMessage}
            disabled={isLoading || (!message.trim() && attachments.length === 0)}
          >
            {isLoading ? "..." : "➤"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Messaging;
