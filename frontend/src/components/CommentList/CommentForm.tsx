import React, { useState } from 'react';
import styles from './CommentForm.module.css';

interface CommentFormProps {
  onSubmit: (content: string) => Promise<void>;
  loading?: boolean;
}

const CommentForm: React.FC<CommentFormProps> = ({ onSubmit, loading }) => {
  const [content, setContent] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) {
      setError('Vui lòng nhập nội dung bình luận.');
      return;
    }
    setError('');
    await onSubmit(content);
    setContent('');
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <textarea
        className={styles.textarea}
        value={content}
        onChange={e => setContent(e.target.value)}
        placeholder="Viết bình luận..."
        rows={3}
        disabled={loading}
      />
      {error && <div className={styles.error}>{error}</div>}
      <button className={styles.submit} type="submit" disabled={loading}>
        {loading ? 'Đang gửi...' : 'Gửi bình luận'}
      </button>
    </form>
  );
};

export default CommentForm;
