import React from 'react';
import styles from './CommentList.module.css';

import type { Comment } from './CommentList.types';

interface CommentListProps {
  comments: Comment[];
  userAvatars?: {[userId: number]: string};
  reloadComments?: () => void;
}


import { useState, useEffect, useRef } from 'react';
import { useUser } from '../../context/UserContext';
import EditCommentForm from './EditCommentForm';

function HeartIcon({ filled }: { filled: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill={filled ? "#ef4444" : "#fff"} stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: 'middle' }}>
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41 0.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
    </svg>
  );
}

function getToken() {
  return localStorage.getItem('access-token') || '';
}

const likeIcon = (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 10v12"/><path d="M19 7c0-1.1-.9-2-2-2h-5.31a2 2 0 0 0-1.9 1.37l-3.34 9.94A2 2 0 0 0 8.31 20H17a2 2 0 0 0 2-2v-7z"/></svg>
);
const dislikeIcon = (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 14V2"/><path d="M5 17c0 1.1.9 2 2 2h5.31a2 2 0 0 0 1.9-1.37l3.34-9.94A2 2 0 0 0 15.69 4H7a2 2 0 0 0-2 2v7z"/></svg>
);


const CommentList: React.FC<CommentListProps> = ({ comments, userAvatars, reloadComments }) => {
  const [menuOpen, setMenuOpen] = useState<{[id: number]: boolean}>({});
  const { userProfile } = useUser();
  const menuRefs = useRef<{ [id: number]: HTMLDivElement | null }>({});

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      // Nếu có menu nào đang mở và click ra ngoài, sẽ đóng tất cả menu
      const anyOpen = Object.values(menuOpen).some(Boolean);
      if (!anyOpen) return;
      let clickedInside = false;
      Object.entries(menuRefs.current).forEach(([id, ref]) => {
        if (menuOpen[Number(id)] && ref && ref.contains(event.target as Node)) {
          clickedInside = true;
        }
      });
      if (!clickedInside) {
        setMenuOpen({});
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);
  const [pending, setPending] = useState<{[id: number]: boolean}>({});
  const [localLikes, setLocalLikes] = useState<{[id: number]: boolean}>({});
  // Số lượng like/dislike lấy từ comment nếu có
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editLoading, setEditLoading] = useState(false);

  // Sửa comment
  const handleEdit = async (id: number, content: string) => {
    setEditLoading(true);
    try {
      const token = getToken();
      const res = await fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/${id}`, {
        method: 'PUT',
        headers: {
          'accept': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error('Sửa bình luận thất bại');
      if (reloadComments) reloadComments();
      setEditingId(null);
    } catch (err) {
      alert('Sửa bình luận thất bại');
    } finally {
      setEditLoading(false);
    }
  };

  // Xóa comment
  const handleDelete = async (id: number) => {
    setPending(prev => ({ ...prev, [id]: true }));
    try {
      const token = getToken();
      const res = await fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/${id}`, {
        method: 'DELETE',
        headers: {
          'accept': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!res.ok) throw new Error('Xóa bình luận thất bại');
      if (reloadComments) reloadComments();
    } catch (err) {
      alert('Xóa bình luận thất bại');
    } finally {
      setPending(prev => ({ ...prev, [id]: false }));
      setMenuOpen(prev => ({ ...prev, [id]: false }));
    }
  };

  // Like/Unlike comment
  const handleLike = async (id: number) => {
    setPending(prev => ({ ...prev, [id]: true }));
    try {
      const token = getToken();
      // Tìm comment hiện tại
      const comment = comments.find(c => c.id === id);
      let res;
      if (comment && comment.user_has_liked) {
        // Đã like, bấm lần nữa là unlike
        res = await fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/${id}/like`, {
          method: 'DELETE',
          headers: {
            'accept': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        });
        if (!res.ok) throw new Error('Hủy like thất bại');
        setLocalLikes(prev => ({ ...prev, [id]: false }));
      } else {
        // Chưa like, bấm là like
        res = await fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/${id}/like`, {
          method: 'POST',
          headers: {
            'accept': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        });
        if (!res.ok) throw new Error('Like thất bại');
        setLocalLikes(prev => ({ ...prev, [id]: true }));
      }
      if (reloadComments) reloadComments();
    } catch (err) {
      // Ưu tiên báo lỗi đúng trạng thái
      const comment = comments.find(c => c.id === id);
      alert((comment && comment.user_has_liked) ? 'Hủy like thất bại' : 'Like thất bại');
    } finally {
      setPending(prev => ({ ...prev, [id]: false }));
      setMenuOpen(prev => ({ ...prev, [id]: false }));
    }
  };

  // Dislike comment
  // Đã loại bỏ tính năng dislike

  return (
    <div className={styles.commentList}>
      {comments.length === 0 ? (
        <div className={styles.empty}>Chưa có bình luận nào.</div>
      ) : (
        comments.map((comment) => (
          <div key={comment.id} className={styles.commentItem}>
            <div className={styles.avatarWrap}>
              <img
                src={(() => {
                  const img = userAvatars && userAvatars[comment.user_id];
                  if (img && img !== 'null' && img !== '' && !img.includes('default-avatar')) {
                    return img;
                  }
                  return `https://ui-avatars.com/api/?name=${encodeURIComponent(comment.fullName || comment.user_name || comment.user_email || 'User')}&size=96&background=ef4444&color=fff&bold=true`;
                })()}
                alt={comment.fullName || comment.user_name || comment.user_email || 'user'}
                className={styles.avatar}
              />
            </div>
            <div className={styles.contentWrap}>
              <div className={styles.username}>{comment.fullName || comment.user_name || comment.user_email || 'Người dùng'}</div>
              {editingId === comment.id ? (
                <EditCommentForm
                  initialContent={comment.content}
                  onSave={content => handleEdit(comment.id, content)}
                  onCancel={() => setEditingId(null)}
                  loading={editLoading}
                />
              ) : (
                <div className={styles.content}>{comment.content}</div>
              )}
              <div className={styles.date}>{new Date(comment.created_at).toLocaleString()}</div>
              <div className={styles.actionsRow}>
                <button className={styles.iconBtn} onClick={() => handleLike(comment.id)} title={localLikes[comment.id] ? "Hủy like" : "Like"} disabled={pending[comment.id]}>
                  <HeartIcon filled={comment.user_has_liked ?? !!localLikes[comment.id]} /> <span>{comment.likes_count ?? comment.like_count ?? 0}</span>
                </button>
                <div className={styles.menuWrap}>
                  <button
                    className={styles.menuBtn}
                    onClick={() =>
                      setMenuOpen(prev => ({ ...prev, [comment.id]: !prev[comment.id] }))
                    }
                    title="Tùy chọn"
                  >
                    &#8230;
                  </button>
                  {menuOpen[comment.id] && (
                    <div
                      className={styles.menuDropdown}
                      ref={el => (menuRefs.current[comment.id] = el)}
                      onClick={e => e.stopPropagation()}
                    >
                      {comment.user_id === userProfile?.id && (
                        <>
                          <button onClick={() => { setEditingId(comment.id); setMenuOpen(prev => ({ ...prev, [comment.id]: false })); }} disabled={editLoading}>Sửa bình luận</button>
                          <button onClick={() => handleDelete(comment.id)} disabled={pending[comment.id]}>Xóa bình luận</button>
                        </>
                      )}
                      <button onClick={() => handleLike(comment.id)} disabled={pending[comment.id]}>
                        <HeartIcon filled={comment.user_has_liked ?? !!localLikes[comment.id]} /> {comment.user_has_liked ?? localLikes[comment.id] ? "Hủy like" : "Like"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default CommentList;
export type { Comment } from './CommentList.types';
