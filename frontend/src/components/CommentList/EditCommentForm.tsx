import React, { useState } from 'react';

interface EditCommentFormProps {
  initialContent: string;
  onSave: (content: string) => void;
  onCancel: () => void;
  loading?: boolean;
}

const EditCommentForm: React.FC<EditCommentFormProps> = ({ initialContent, onSave, onCancel, loading }) => {
  const [content, setContent] = useState(initialContent);
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) {
      setError('Nội dung không được để trống.');
      return;
    }
    setError('');
    onSave(content);
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        background: '#fafbfc',
        border: '1.5px solid #e5e7eb',
        borderRadius: 10,
        padding: 14,
        margin: '8px 0',
        boxShadow: '0 2px 8px 0 rgba(0,0,0,0.04)'
      }}
    >
      <textarea
        value={content}
        onChange={e => setContent(e.target.value)}
        rows={3}
        disabled={loading}
        style={{
          resize: 'vertical',
          borderRadius: 8,
          border: '1.5px solid #d1d5db',
          padding: 10,
          fontSize: 15,
          background: '#fff',
          outline: 'none',
          boxShadow: '0 1px 2px 0 rgba(0,0,0,0.02)'
        }}
        placeholder="Chỉnh sửa bình luận..."
      />
      {error && <div style={{ color: '#e11d48', fontSize: 13 }}>{error}</div>}
      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <button
          type="submit"
          disabled={loading}
          style={{
            background: '#ef4444',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            padding: '6px 18px',
            fontWeight: 600,
            fontSize: 15,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1
          }}
        >
          Lưu
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          style={{
            background: '#f3f4f6',
            color: '#374151',
            border: '1.5px solid #d1d5db',
            borderRadius: 6,
            padding: '6px 18px',
            fontWeight: 500,
            fontSize: 15,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1
          }}
        >
          Hủy
        </button>
      </div>
    </form>
  );
};

export default EditCommentForm;
