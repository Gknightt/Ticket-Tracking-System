import useTriggerAction from "../../../../api/useTriggerAction";
import styles from "./ticket-action.module.css";
import { useState } from "react";

export default function TicketAction({
  closeTicketAction,
  ticket,
  action,
  instance,
}) {
  const [selectedActionId, setSelectedActionId] = useState("");
  const [comment, setComment] = useState("");
  const [triggerNow, setTriggerNow] = useState(false);
  const [errors, setErrors] = useState({});

  const { loading, error, response } = useTriggerAction({
    uuid: instance,
    action_id: selectedActionId,
    method: "post",
    comment,
    trigger: triggerNow,
  });

  const handleClick = () => {
    const newErrors = {};
    if (!selectedActionId) {
      newErrors.action = "Please select an action.";
    }
    if (!comment.trim()) {
      newErrors.comment = "Comment is required.";
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length > 0) return;

    setTriggerNow(true);
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  };

  // Reset the trigger after action completes
  if (triggerNow && !loading && (error || response)) {
    setTimeout(() => setTriggerNow(false), 500);
  }

  return (
    <div className={styles.taOverlayWrapper} onClick={() => closeTicketAction(false)}>
      <div className={styles.ticketActionModal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.taExit} onClick={() => closeTicketAction(false)}>
          <i className="fa-solid fa-xmark"></i>
        </div>

        <div className={styles.taHeader}>
          <h1>Ticket No. {ticket?.ticket_id}</h1>
          <div className={styles.taSubject}>{ticket?.subject}</div>
        </div>

        <div className={styles.tdMetaData}>
          <p className={styles.tdDateOpened}>Opened On: {ticket?.opened_on}</p>
          <p className={styles.tdDateResolution}>Expected Resolution: </p>
        </div>

        <div className={styles.tdValidation}>
          {response && (
            <p style={{ color: "green" }}>Action triggered successfully!</p>
          )}
          {error && error.comment && (
            <p style={{ color: "red" }}>{`Comment: ${error.comment.join(", ")}`}</p>
          )}
        </div>

        <div className={styles.taBody}>
          <div className={styles.taDescriptionCont}>
            <h3>Description</h3>
            <p>{ticket?.description}</p>
          </div>

          <div className={styles.taActionStatusCont}>
            <select
              name="ticket-action-status"
              className={styles.actionStatus}
              value={selectedActionId}
              onChange={(e) => setSelectedActionId(e.target.value)}
            >
              <option value="" disabled>
                Please select an option
              </option>
              {action?.map((a) => (
                <option key={a.action_id} value={a.action_id}>
                  {a.name}
                </option>
              ))}
            </select>
            {errors.action && <p className={styles.errorText}>{errors.action}</p>}
          </div>

          <div className={styles.taCommentCont}>
            <h3>Comment</h3>
            <textarea
              className={styles.actionStatus}
              placeholder="Enter a comment..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            {errors.comment && <p className={styles.errorText}>{errors.comment}</p>}
          </div>

          <button
            className={styles.taActionButton}
            onClick={handleClick}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className={styles.spinner}></span> Sending...
              </>
            ) : (
              "Push Changes"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
