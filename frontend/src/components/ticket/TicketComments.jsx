// src/components/ticket/TicketComments.jsx
import React, { useState } from "react";
import { format } from "date-fns";
import { useAuth } from "../../api/AuthContext";
import useComments from "../../api/useComments";
import styles from "./ticketComments.module.css";

// Document attachment component
const DocumentAttachment = ({ document, onDownload }) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return 'fa-file-pdf';
      case 'doc': case 'docx': return 'fa-file-word';
      case 'xls': case 'xlsx': return 'fa-file-excel';
      case 'ppt': case 'pptx': return 'fa-file-powerpoint';
      case 'jpg': case 'jpeg': case 'png': case 'gif': return 'fa-file-image';
      case 'zip': case 'rar': return 'fa-file-zipper';
      default: return 'fa-file';
    }
  };

  return (
    <div className={styles.documentAttachment}>
      <i className={`fas ${getFileIcon(document.original_filename)} ${styles.documentIcon}`}></i>
      <div className={styles.documentInfo}>
        <span className={styles.documentName}>{document.original_filename}</span>
        <span className={styles.documentSize}>{formatFileSize(document.file_size)}</span>
      </div>
      <button
        className={styles.downloadButton}
        onClick={() => onDownload(document.id, document.original_filename)}
        title="Download file"
      >
        <i className="fas fa-download"></i>
      </button>
    </div>
  );
};

// File upload component
const FileUpload = ({ onFilesSelected, maxFiles = 5, uniqueId = 'file-upload', clearTrigger = 0 }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const fileInputRef = React.useRef();

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const limitedFiles = files.slice(0, maxFiles);
    setSelectedFiles(limitedFiles);
    onFilesSelected(limitedFiles);
  };

  const removeFile = (index) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    onFilesSelected(newFiles);
    
    // Reset input if no files left
    if (newFiles.length === 0 && fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Clear files when clearTrigger changes (after successful submissions)
  React.useEffect(() => {
    if (clearTrigger > 0) {
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [clearTrigger]);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={styles.fileUpload}>
      <div className={styles.fileInputContainer}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className={styles.fileInput}
          id={uniqueId}
          accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.zip,.rar,.txt"
        />
        <label htmlFor={uniqueId} className={styles.fileInputLabel}>
          <i className="fas fa-paperclip"></i>
          Attach Files ({selectedFiles.length}/{maxFiles})
        </label>
      </div>
      
      {selectedFiles.length > 0 && (
        <div className={styles.selectedFiles}>
          <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '8px' }}>
            Selected Files:
          </div>
          {selectedFiles.map((file, index) => (
            <div key={`${file.name}-${index}`} className={styles.selectedFile}>
              <span className={styles.fileName}>
                {file.name} ({formatFileSize(file.size)})
              </span>
              <button
                type="button"
                onClick={() => removeFile(index)}
                className={styles.removeFileButton}
                title="Remove file"
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Pagination component
const Pagination = ({ pagination, onPageChange, loading }) => {
  if (pagination.total_pages <= 1) return null;

  const pages = [];
  const maxPages = 5;
  let startPage = Math.max(1, pagination.current_page - Math.floor(maxPages / 2));
  let endPage = Math.min(pagination.total_pages, startPage + maxPages - 1);

  if (endPage - startPage + 1 < maxPages) {
    startPage = Math.max(1, endPage - maxPages + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  return (
    <div className={styles.pagination}>
      <button
        onClick={() => onPageChange(pagination.current_page - 1)}
        disabled={!pagination.previous || loading}
        className={styles.paginationButton}
      >
        <i className="fas fa-chevron-left"></i> Previous
      </button>

      <div className={styles.pageNumbers}>
        {startPage > 1 && (
          <>
            <button onClick={() => onPageChange(1)} className={styles.pageButton}>1</button>
            {startPage > 2 && <span className={styles.ellipsis}>...</span>}
          </>
        )}

        {pages.map(page => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`${styles.pageButton} ${page === pagination.current_page ? styles.activePage : ''}`}
            disabled={loading}
          >
            {page}
          </button>
        ))}

        {endPage < pagination.total_pages && (
          <>
            {endPage < pagination.total_pages - 1 && <span className={styles.ellipsis}>...</span>}
            <button onClick={() => onPageChange(pagination.total_pages)} className={styles.pageButton}>
              {pagination.total_pages}
            </button>
          </>
        )}
      </div>

      <button
        onClick={() => onPageChange(pagination.current_page + 1)}
        disabled={!pagination.next || loading}
        className={styles.paginationButton}
      >
        Next <i className="fas fa-chevron-right"></i>
      </button>
    </div>
  );
};

// Comment component to render individual comments
const Comment = ({
  comment,
  onReply,
  onReaction,
  onDelete,
  onDownloadDocument,
  canDelete = false,
  currentUserId,
  isReply = false,
}) => {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyContent, setReplyContent] = useState("");
  const [replyFiles, setReplyFiles] = useState([]);
  const [clearReplyFilesTrigger, setClearReplyFilesTrigger] = useState(0);

  console.log("Comment data:", comment);

  // === track if content is expanded
  const [isContentExpanded, setIsContentExpanded] = useState(false); // Track content expansion
  const MAX_CONTENT_LENGTH = 200;

  // Truncate comment content if it's too long
  const truncatedContent =
    comment.content.length > MAX_CONTENT_LENGTH
      ? comment.content.slice(0, MAX_CONTENT_LENGTH) + "..."
      : comment.content;

  const handleToggleContent = () => {
    setIsContentExpanded(!isContentExpanded);
  };
  // ===

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return format(date, "h:mm a | MMM d, yyyy");
    } catch (e) {
      return "Invalid date";
    }
  };

  // Check if the current user has already reacted
  const userReaction = comment.reactions?.find(
    (reaction) => reaction.user_id === currentUserId
  );

  const handleReplySubmit = (e) => {
    e.preventDefault();
    if (replyContent.trim()) {
      onReply(comment.id, replyContent, replyFiles);
      setReplyContent("");
      setReplyFiles([]);
      setShowReplyForm(false);
      setClearReplyFilesTrigger((prev) => prev + 1);
    }
  };

  const handleLikeClick = () => {
    if (userReaction && userReaction.reaction_type === "like") {
      onReaction(comment.id, userReaction.id, null); // Remove reaction
    } else {
      onReaction(comment.id, userReaction?.id, "like"); // Add/change to like
    }
  };

  const handleDislikeClick = () => {
    if (userReaction && userReaction.reaction_type === "dislike") {
      onReaction(comment.id, userReaction.id, null); // Remove reaction
    } else {
      onReaction(comment.id, userReaction?.id, "dislike"); // Add/change to dislike
    }
  };

  const getLikeCount = () => {
    // Use the thumbs_up_count directly from the API response if available
    if (comment.thumbs_up_count !== undefined) {
      return comment.thumbs_up_count;
    }
    // Fallback to the original calculation method
    return (
      comment.reactions?.filter((r) => r.reaction_type === "like").length || 0
    );
  };

  const getDislikeCount = () => {
    // Use the thumbs_down_count directly from the API response if available
    if (comment.thumbs_down_count !== undefined) {
      return comment.thumbs_down_count;
    }
    // Fallback to the original calculation method
    return (
      comment.reactions?.filter((r) => r.reaction_type === "dislike").length ||
      0
    );
  };

  return (
    <div className={styles.commentCard}>
      <div className={styles.commentBody}>
        <div className={styles.commentHeader}>
          <div className={styles.userInfo}>
            <span className={styles.commentAuthor}>
              {comment.firstname || comment.user?.first_name}{" "}
              {comment.lastname || comment.user?.last_name}
            </span>
            {(comment.role || comment.user?.role) && (
              <span className={styles.userRole}>
                {comment.role || comment.user?.role}
              </span>
            )}
          </div>
          <span className={styles.commentTime}>
            {formatDate(comment.created_at)}
          </span>
        </div>
        {/* <div className={styles.commentContent}>{comment.content}</div> */}
        <div className={styles.commentContent}>
          {isContentExpanded || comment.content.length <= MAX_CONTENT_LENGTH
            ? comment.content
            : truncatedContent}
          {comment.content.length > MAX_CONTENT_LENGTH && (
            <button
              className={styles.seeMoreButton}
              onClick={handleToggleContent}
            >
              {isContentExpanded ? "See Less" : "See More"}
            </button>
          )}
        </div>

        {/* Display attached documents */}
        {comment.documents && comment.documents.length > 0 && (
          <div className={styles.documentsContainer}>
            <div className={styles.documentsHeader}>
              <i className="fas fa-paperclip"></i>
              <span>Attachments ({comment.documents.length})</span>
            </div>
            <div className={styles.documentsList}>
              {comment.documents.map((docAttachment) => (
                <DocumentAttachment
                  key={docAttachment.id}
                  document={docAttachment.document}
                  onDownload={onDownloadDocument}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      <div className={styles.commentActions}>
        <button
          className={`${styles.actionButton} ${
            userReaction?.reaction_type === "like"
              ? styles.actionButtonActive
              : ""
          }`}
          onClick={handleLikeClick}
        >
          <i className="fa-solid fa-thumbs-up"></i> {getLikeCount()}
        </button>

        <button
          className={`${styles.actionButton} ${
            userReaction?.reaction_type === "dislike"
              ? styles.actionButtonActive
              : ""
          }`}
          onClick={handleDislikeClick}
        >
          <i className="fa-solid fa-thumbs-down"></i> {getDislikeCount()}
        </button>

        {/* Only show reply button if this is not already a reply */}
        {!isReply && (
          <button
            className={styles.actionButton}
            onClick={() => setShowReplyForm(!showReplyForm)}
          >
            <i className="fa-solid fa-reply"></i> Reply
          </button>
        )}

        {/* Delete button shown only when user can delete */}
        {canDelete && (
          <button
            className={styles.actionButton}
            onClick={() => {
              if (onDelete) {
                const confirmed = window.confirm("Delete this comment?");
                if (confirmed) onDelete(comment.id);
              }
            }}
          >
            <i className="fa-solid fa-trash"></i> Delete
          </button>
        )}
      </div>

      {showReplyForm && (
        <form className={styles.replyForm} onSubmit={handleReplySubmit}>
          <textarea
            className={styles.replyInput}
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            placeholder="Write a reply..."
            rows="3"
          />
          
          <FileUpload
            onFilesSelected={setReplyFiles}
            maxFiles={3}
            uniqueId={`reply-file-upload-${comment.id}`}
            clearTrigger={clearReplyFilesTrigger}
          />
          
          <div className={styles.replyFormActions}>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={() => {
                setShowReplyForm(false);
                setReplyContent("");
                setReplyFiles([]);
              }}
            >
              Cancel
            </button>
            <button type="submit" className={styles.replyButton}>
              Reply
            </button>
          </div>
        </form>
      )}

      {comment.replies && comment.replies.length > 0 && (
        <div className={styles.repliesContainer}>
          {comment.replies.map((reply) => (
            <Comment
              key={reply.id}
              comment={reply}
              onReply={onReply}
              onReaction={onReaction}
              onDownloadDocument={onDownloadDocument}
              currentUserId={currentUserId}
              isReply={true} // Mark this as a reply so it won't show the reply button
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Loading spinner component
const LoadingSpinner = () => (
  <div className={styles.loadingSpinner}>
    <div className={styles.loadingDots}>
      <div className={styles.loadingDot}></div>
      <div className={styles.loadingDot}></div>
      <div className={styles.loadingDot}></div>
    </div>
  </div>
);

// Empty state component
const EmptyState = () => (
  <div className={styles.emptyStateContainer}>
    <i className="fa-regular fa-comments styles.emptyStateIcon"></i>
    <p className={styles.emptyStateText}>
      No comments yet. Be the first to start a conversation!
    </p>
  </div>
);

// Error state component
const ErrorState = ({ message, onRetry }) => (
  <div className={styles.errorMessage}>
    <p>{message}</p>
    {onRetry && (
      <button onClick={onRetry} className={styles.actionButton}>
        <i className="fa-solid fa-rotate"></i> Retry
      </button>
    )}
  </div>
);

const TicketComments = ({ ticketId }) => {
  const { user, isAdmin } = useAuth();
  const [newComment, setNewComment] = useState("");
  const [attachmentFiles, setAttachmentFiles] = useState([]);
  const [clearAttachmentFilesTrigger, setClearAttachmentFilesTrigger] = useState(0);

  const {
    comments,
    loading,
    error,
    pagination,
    addComment,
    addReply,
    addReaction,
    removeReaction,
    deleteComment,
    downloadDocument,
    refreshComments,
    fetchComments,
  } = useComments(ticketId);

  const handleDelete = async (commentId) => {
    if (!commentId) return;
    const confirmed = window.confirm(
      "Are you sure you want to delete this comment? This cannot be undone."
    );
    if (!confirmed) return;

    const success = await deleteComment(commentId);
    if (!success) {
      // Optionally: show a user-facing notification here
      console.error("Failed to delete comment", commentId);
    }
  };

  const handleSendComment = async (e) => {
    e.preventDefault();
    if (newComment.trim()) {
      console.log('Sending comment with files:', attachmentFiles);
      const result = await addComment(newComment, attachmentFiles);
      if (result) {
        setNewComment("");
        setAttachmentFiles([]);
        setClearAttachmentFilesTrigger((prev) => prev + 1);
        console.log('Comment sent successfully');
      } else {
        console.error('Failed to send comment');
      }
    }
  };

  const handleReply = async (parentId, content, files = []) => {
    console.log('Sending reply with files:', files);
    const result = await addReply(parentId, content, files);
    if (result) {
      console.log('Reply sent successfully');
    } else {
      console.error('Failed to send reply');
    }
  };

  const handleReaction = async (
    commentId,
    existingReactionId,
    reactionType
  ) => {
    if (!reactionType && existingReactionId) {
      // Remove reaction
      await removeReaction(existingReactionId);
    } else if (existingReactionId) {
      // Update existing reaction
      // For simplicity, we'll remove and re-add
      await removeReaction(existingReactionId);
      if (reactionType) {
        await addReaction(commentId, reactionType);
      }
    } else if (reactionType) {
      // Add new reaction
      await addReaction(commentId, reactionType);
    }
  };

  const handleDownloadDocument = async (documentId, filename) => {
    await downloadDocument(documentId, filename);
  };

  const handlePageChange = (page) => {
    fetchComments(page);
  };

  // Organize comments into a tree structure (root comments and their replies)
  const organizedComments = React.useMemo(() => {
    if (!comments) return [];

    // console.log("Raw comments data:", comments);

    // Map the comments to include the 'id' field expected by the component
    // Use the already nested 'replies' structure from the API
    const mappedComments = comments.map((comment) => {
      // Process the main comment
      const processedComment = {
        ...comment,
        id: comment.comment_id,
        parent_id: comment.parent,
      };

      // Process any replies that come pre-nested from the API
      if (comment.replies && Array.isArray(comment.replies)) {
        processedComment.replies = comment.replies.map((reply) => ({
          ...reply,
          id: reply.comment_id,
          parent_id: reply.parent || comment.comment_id,
        }));
      }

      return processedComment;
    });

    // Filter to only include root comments (those without a parent)
    const rootComments = mappedComments.filter((comment) => !comment.parent);

    console.log("Organized comments:", rootComments);
    return rootComments;
  }, [comments]);

  if (!ticketId) {
    return (
      <div className={styles.commentsSection}>
        <ErrorState message="No ticket ID provided. Comments cannot be loaded." />
      </div>
    );
  }

  return (
    <div className={styles.commentsSection}>
      <div className={styles.commentsHeader}>
        <h3>Comments</h3>
        {pagination.count > 0 && (
          <span className={styles.commentsCount}>
            {pagination.count} comment{pagination.count !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className={styles.commentsList}>
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorState message={error} onRetry={refreshComments} />
        ) : organizedComments.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {organizedComments.map((comment) => (
              <Comment
                key={comment.id}
                comment={comment}
                onReply={handleReply}
                onReaction={handleReaction}
                onDelete={handleDelete}
                onDownloadDocument={handleDownloadDocument}
                canDelete={
                  (user?.id && String(user.id) === String(comment.user_id)) ||
                  (typeof isAdmin === "function" ? isAdmin() : false)
                }
                currentUserId={user?.id}
              />
            ))}
            
            <Pagination
              pagination={pagination}
              onPageChange={handlePageChange}
              loading={loading}
            />
          </>
        )}
      </div>

      <form onSubmit={handleSendComment} className={styles.commentForm}>
        <textarea
          className={styles.commentInput}
          placeholder="Write a comment..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          disabled={loading}
          rows="4"
        />
        
        <FileUpload
          onFilesSelected={setAttachmentFiles}
          maxFiles={5}
          uniqueId="comment-file-upload"
          clearTrigger={clearAttachmentFilesTrigger}
        />
        
        <div className={styles.commentFormActions}>
          <div className={styles.attachmentInfo}>
            {attachmentFiles.length > 0 && (
              <span className={styles.fileCount}>
                <i className="fas fa-paperclip"></i>
                {attachmentFiles.length} file{attachmentFiles.length !== 1 ? 's' : ''} selected
              </span>
            )}
          </div>
          <button
            className={styles.commentButton}
            type="submit"
            disabled={loading || !newComment.trim()}
          >
            <i className="fa-solid fa-paper-plane"></i> Send
          </button>
        </div>
      </form>
    </div>
  );
};

export default TicketComments;
