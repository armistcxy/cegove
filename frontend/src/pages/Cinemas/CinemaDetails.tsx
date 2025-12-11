
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import CommentList from '../../components/CommentList/CommentList';
import CommentForm from '../../components/CommentList/CommentForm';
import styles from './CinemaDetails.module.css';
import { fetchCinemaById } from './CinemaLogic';
import type { Cinema } from './CinemaLogic';

interface Comment {
  id: number;
  user_id: number;
  content: string;
  created_at: string;
  like_count?: number;
  user_has_liked?: boolean;
  fullName?: string;
}


export default function CinemaDetails() {
  const { id } = useParams<{ id: string }>();
  const [cinema, setCinema] = useState<Cinema | null>(null);
  const [cinemaLoading, setCinemaLoading] = useState(true);
  const [cinemaError, setCinemaError] = useState('');
  const [comments, setComments] = useState<Comment[]>([]);
  const [userAvatars, setUserAvatars] = useState<{ [userId: number]: string }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [commentFormLoading, setCommentFormLoading] = useState(false);
  const [commentError, setCommentError] = useState<string | null>(null);
  // Load cinema info
  useEffect(() => {
    if (!id) return;
    setCinemaLoading(true);
    setCinemaError('');
    fetchCinemaById(Number(id))
      .then(data => setCinema(data))
      .catch(() => setCinemaError('Không thể tải thông tin rạp.'))
      .finally(() => setCinemaLoading(false));
  }, [id]);

  // Load comments
  const loadComments = () => {
    if (!id) return;
    setLoading(true);
    setError('');
    const token = localStorage.getItem('access-token');
    fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/target/theater/${id}?page=1&page_size=20&sort_by=recent`, {
      headers: token ? {
        'Authorization': `Bearer ${token}`,
        'accept': 'application/json'
      } : {
        'accept': 'application/json'
      }
    })
      .then(res => res.json())
      .then(async data => {
        const avatarMap: { [userId: number]: { img: string, fullName: string } } = {};
        const uniqueUserIds = Array.from(new Set((data?.items || []).map((c: any) => c.user_id)));
        await Promise.all(uniqueUserIds.map(async (userId) => {
          if (!userId) return;
          try {
            const res = await fetch(`https://user.cegove.cloud/users/${userId}/profile`);
            if (res.ok) {
              const profile = await res.json();
              avatarMap[userId] = {
                img: profile.img || '',
                fullName: profile.fullName || ''
              };
            } else {
              avatarMap[userId] = { img: '', fullName: '' };
            }
          } catch {
            avatarMap[userId] = { img: '', fullName: '' };
          }
        }));
        const commentsWithFullName = (data?.items || []).map((c: any) => ({
          ...c,
          fullName: avatarMap[c.user_id]?.fullName || c.user_name || c.user_email || 'Người dùng'
        }));
        setComments(commentsWithFullName);
        setUserAvatars(Object.fromEntries(Object.entries(avatarMap).map(([k, v]) => [k, v.img])));
      })
      .catch(() => setError('Không thể tải bình luận.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadComments();
    // eslint-disable-next-line
  }, [id]);

  // Gửi bình luận mới
  const handleAddComment = async (content: string) => {
    if (!id) return;
    setCommentFormLoading(true);
    setCommentError(null);
    try {
      const token = localStorage.getItem('access-token');
      if (!token) {
        setCommentError('Bạn cần đăng nhập để bình luận.');
        setCommentFormLoading(false);
        return;
      }
      const res = await fetch('https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_type: 'theater',
          target_id: Number(id),
          content,
        })
      });
      if (!res.ok) {
        throw new Error('Gửi bình luận thất bại');
      }
      loadComments();
    } catch (err) {
      setCommentError('Gửi bình luận thất bại');
    } finally {
      setCommentFormLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* Thông tin rạp */}
      {cinemaLoading ? (
        <div className={styles.loading}>Đang tải thông tin rạp...</div>
      ) : cinemaError ? (
        <div className={styles.error}>{cinemaError}</div>
      ) : cinema ? (
        <div style={{ marginBottom: 24, borderBottom: '1px solid #eee', paddingBottom: 16 }}>
          <h2 className={styles.title}>{cinema.name}</h2>
          <div><strong>Địa chỉ:</strong> {cinema.address}, {cinema.district}, {cinema.city}</div>
          {cinema.phone && <div><strong>Điện thoại:</strong> {cinema.phone}</div>}
          {cinema.email && <div><strong>Email:</strong> {cinema.email}</div>}
        </div>
      ) : null}

      <h2 className={styles.title}>Bình luận về rạp</h2>
      <CommentForm onSubmit={handleAddComment} loading={commentFormLoading} />
      {commentError && <div style={{ color: '#d32f2f', marginBottom: 12 }}>{commentError}</div>}
      {loading && <div className={styles.loading}>Đang tải bình luận...</div>}
      {error && <div className={styles.error}>{error}</div>}
      {!loading && !error && (
        <CommentList comments={comments} userAvatars={userAvatars} reloadComments={loadComments} />
      )}
    </div>
  );
}
