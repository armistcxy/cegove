
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import CommentList from '../../components/CommentList/CommentList';
import CommentForm from '../../components/CommentList/CommentForm';
import styles from './CinemaDetails.module.css';
import StarRating from '../../components/StarRating';
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

  // State cho insight
  const [insight, setInsight] = useState<any>(null);
  const [insightLoading, setInsightLoading] = useState(false);
  const [insightError, setInsightError] = useState('');

  // Tông màu chủ đạo đỏ đơn giản
  const mainRed = '#b71c1c'; // đỏ đậm
  const lightRed = '#fbe9e7'; // đỏ nhạt
  const borderRed = '#f44336';

  // Fetch insight về rạp
  useEffect(() => {
    if (!id) return;
    setInsightLoading(true);
    setInsightError('');
    fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/sentiment/insights/theater/${id}?force_refresh=false&max_comments=50`)
      .then(res => {
        if (!res.ok) throw new Error('Không thể tải insight.');
        return res.json();
      })
      .then(data => setInsight(data))
      .catch(() => setInsightError('Cần tối thiểu 3 comments để tổng hợp.'))
      .finally(() => setInsightLoading(false));
  }, [id]);
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
    <div
      className={styles.container}
      style={{
        boxSizing: 'border-box',
        maxWidth: 1100, // vừa phải hơn
        margin: '32px auto',
        background: lightRed,
        borderRadius: 16,
        border: `2px solid ${borderRed}`,
        boxShadow: '0 4px 24px 0 rgba(183,28,28,0.08)',
        padding: '32px 48px', // padding vừa phải
        minHeight: 600,
        color: mainRed,
      }}
    >
      {/* Thông tin rạp */}
      {cinemaLoading ? (
        <div className={styles.loading}>Đang tải thông tin rạp...</div>
      ) : cinemaError ? (
        <div className={styles.error}>{cinemaError}</div>
      ) : cinema ? (
        <div style={{ marginBottom: 24, borderBottom: `2px solid ${borderRed}33`, paddingBottom: 16 }}>
          <h2 className={styles.title} style={{ color: mainRed }}>{cinema.name}</h2>
          <div><strong>Địa chỉ:</strong> {cinema.address}, {cinema.district}, {cinema.city}</div>
          {cinema.phone && <div><strong>Điện thoại:</strong> {cinema.phone}</div>}
          {cinema.email && <div><strong>Email:</strong> {cinema.email}</div>}
        </div>
      ) : null}

      {/* Đánh giá trung bình luôn hiển thị */}
      <div style={{ marginBottom: 16 }}>
        {(() => {
          const ratings = comments.map((c: any) => c.rating).filter((r: any) => typeof r === 'number') as number[];
          const avg = ratings.length > 0 ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null;
          return (
            <div style={{marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8}}>
              <b style={{ color: mainRed }}>Đánh giá trung bình:</b>
              {avg !== null ? (
                <>
                  <span style={{fontWeight: 600, fontSize: 18, color: borderRed}}>{avg.toFixed(1)}/5</span>
                  <StarRating rating={avg} size={24} readOnly />
                  <span style={{color: '#888', fontSize: 13}}>({ratings.length} đánh giá)</span>
                </>
              ) : (
                <span style={{color: '#aaa'}}>Chưa có đánh giá</span>
              )}
            </div>
          );
        })()}
      </div>

      {/* Insight về rạp (dạng mới) */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ fontWeight: 600, fontSize: 18, marginBottom: 8, color: mainRed }}>Nhận xét tổng quan về rạp</h3>
        {insightLoading ? (
          <div className={styles.loading}>Đang tải insight...</div>
        ) : insightError ? (
          <div className={styles.error}>{insightError}</div>
        ) : insight ? (
          <div style={{
            background: '#fff',
            borderRadius: 8,
            padding: 16,
            marginBottom: 8,
            border: `1.5px solid ${borderRed}33`, // viền nhẹ hơn
            boxShadow: '0 2px 8px 0 rgba(183,28,28,0.04)', // thêm bóng nhẹ
          }}>
            {insight.summary && (
              <div style={{ marginBottom: 8 }}><strong style={{ color: mainRed }}>Tóm tắt:</strong> {insight.summary}</div>
            )}
            {insight.positive_aspects && insight.positive_aspects.length > 0 && (
              <div style={{ marginBottom: 8 }}>
                <strong style={{ color: mainRed }}>Điểm mạnh nổi bật:</strong>
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {insight.positive_aspects.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {insight.negative_aspects && insight.negative_aspects.length > 0 && (
              <div style={{ marginBottom: 8 }}>
                <strong style={{ color: mainRed }}>Điểm cần cải thiện:</strong>
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {insight.negative_aspects.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {insight.recommendations && (
              <div style={{ marginBottom: 8 }}><strong style={{ color: mainRed }}>Khuyến nghị:</strong> {insight.recommendations}</div>
            )}
            <div style={{ fontSize: 14, color: '#666', marginTop: 8 }}>
              <span><strong>Dựa trên:</strong> {insight.based_on_comments ?? 'N/A'} bình luận</span>
              {insight.is_stale && (
                <span style={{ marginLeft: 16, color: borderRed }}>(Dữ liệu cũ)</span>
              )}
            </div>
          </div>
        ) : null}
      </div>

      <h2 className={styles.title} style={{ color: mainRed }}>Bình luận về rạp</h2>
      <CommentForm onSubmit={handleAddComment} loading={commentFormLoading} />
      {commentError && <div style={{ color: borderRed, marginBottom: 12 }}>{commentError}</div>}
      {loading && <div className={styles.loading}>Đang tải bình luận...</div>}
      {error && <div className={styles.error}>{error}</div>}
      {!loading && !error && (
        <CommentList comments={comments} userAvatars={userAvatars} reloadComments={loadComments} />
      )}
    </div>
  );
}
