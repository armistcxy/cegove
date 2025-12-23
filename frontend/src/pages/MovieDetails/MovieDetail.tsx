import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { Movie } from "../Movies/MovieLogic.ts";
import { fetchMovieDetail, fetchSimilarMovies } from "./MovieDetailLogic.ts";

interface MovieInsight {
  summary: string;
  positive_aspects: string[];
  negative_aspects: string[];
  recommendations: string;
  based_on_comments: number;
}
import BookingPopup from "../../components/BookingPopup/BookingPopup.tsx";
import RelatedMoviesSlider from "../../components/RelatedMoviesSlider/RelatedMoviesSlider.tsx";
import CommentList from "../../components/CommentList/CommentList";
import StarRating from "../../components/StarRating";
import type { Comment } from "../../components/CommentList/CommentList.types";
import CommentForm from "../../components/CommentList/CommentForm";
import styles from "./MovieDetail.module.css";

export default function MovieDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [similarMovies, setSimilarMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isBookingPopupOpen, setIsBookingPopupOpen] = useState(false);
  const [selectedMovieTitle, setSelectedMovieTitle] = useState<string>("");
  const [selectedMovieId, setSelectedMovieId] = useState<number | undefined>(undefined);
  // Comment state
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentLoading, setCommentLoading] = useState(false);
  // Insight state
  const [insight, setInsight] = useState<MovieInsight | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);
  const [insightError, setInsightError] = useState<string | null>(null);
  const [commentError, setCommentError] = useState<string | null>(null);
  const [commentFormLoading, setCommentFormLoading] = useState(false);
  const [userAvatars, setUserAvatars] = useState<{[userId: number]: string}>({});
  const [commentPage, setCommentPage] = useState(1);
  const [commentTotalPages, setCommentTotalPages] = useState(1);

  useEffect(() => {
    if (!id) {
      setError("Movie ID not found");
      setLoading(false);
      return;
    }

    const loadData = async () => {
      try {
        const [movieData, similarData] = await Promise.all([
          fetchMovieDetail(id),
          fetchSimilarMovies(id, 20)
        ]);

        if (movieData) {
          setMovie(movieData);
        } else {
          setError("Movie not found");
        }

        setSimilarMovies(similarData);
      } catch (err) {
        setError("Failed to load movie details");
      } finally {
        setLoading(false);
      }
    };

    loadData();
    // Load insight
    if (id) {
      setInsightLoading(true);
      setInsightError(null);
      fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/sentiment/insights/movie/${id}?force_refresh=false&max_comments=50`, {
        headers: { 'accept': 'application/json' }
      })
        .then(async res => {
          if (!res.ok) {
            // Nếu lỗi 404 hoặc không đủ comment
            let msg = 'Không thể tải insight.';
            try {
              const err = await res.json();
              if (err && err.detail && err.detail.includes('Not enough comments')) {
                msg = 'Chưa đủ bình luận để phân tích đánh giá.';
              }
            } catch {}
            throw new Error(msg);
          }
          return res.json();
        })
        .then(data => {
          setInsight({
            summary: data.summary,
            positive_aspects: data.positive_aspects,
            negative_aspects: data.negative_aspects,
            recommendations: data.recommendations,
            based_on_comments: data.based_on_comments
          });
        })
        .catch((e) => setInsightError(e.message || 'Không thể tải insight.'))
        .finally(() => setInsightLoading(false));
    }
  }, [id]);

  // Load comments
  useEffect(() => {
    if (!id) return;
    setCommentLoading(true);
    setCommentError(null);
    const commentToken = localStorage.getItem('access-token');
    fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/target/movie/${id}?page=${commentPage}&page_size=10&sort_by=recent`, {
      headers: commentToken ? {
        'Authorization': `Bearer ${commentToken}`,
        'accept': 'application/json'
      } : {
        'accept': 'application/json'
      }
    })
      .then(res => res.json())
      .then(async data => {
        setCommentTotalPages(data?.total_pages || 1);
        setComments(data?.items || []);
        // Tích hợp lấy avatar và fullName cho từng user
        const avatarMap: {[userId: number]: {img: string, fullName: string}} = {};
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
              avatarMap[userId] = {
                img: '',
                fullName: ''
              };
            }
          } catch {
            avatarMap[userId] = {
              img: '',
              fullName: ''
            };
          }
        }));
        // Gán fullName vào từng comment
        const commentsWithFullName = (data?.items || []).map((c: any) => ({
          ...c,
          like_count: c.like_count ?? 0,
          dislike_count: c.dislike_count ?? 0,
          fullName: avatarMap[c.user_id]?.fullName || c.user_name || c.user_email || 'Người dùng'
        }));
        setComments(commentsWithFullName);
        setUserAvatars(Object.fromEntries(Object.entries(avatarMap).map(([k, v]) => [k, v.img])));
      })
      .catch(() => setCommentError("Không thể tải bình luận."))
      .finally(() => setCommentLoading(false));
  }, [id, commentPage]);

  // Hàm gửi bình luận mới
  const handleAddComment = async (content: string) => {
    if (!id) return;
    setCommentFormLoading(true);
    setCommentError(null);
    try {
      // Lấy token từ localStorage hoặc context
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
          target_type: 'movie',
          target_id: Number(id),
          content,
        })
      });
      if (!res.ok) {
        throw new Error('Gửi bình luận thất bại');
      }
      // Reload comments và gán lại fullName như khi load ban đầu
      const reloadToken = localStorage.getItem('access-token');
      fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/target/movie/${id}?page=1&page_size=20&sort_by=recent`, {
        headers: reloadToken ? {
          'Authorization': `Bearer ${reloadToken}`,
          'accept': 'application/json'
        } : {
          'accept': 'application/json'
        }
      })
        .then(res => res.json())
        .then(async data => {
          const avatarMap: Record<number, { img: string; fullName: string }> = {};
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
                avatarMap[userId] = {
                  img: '',
                  fullName: ''
                };
              }
            } catch {
              avatarMap[userId] = {
                img: '',
                fullName: ''
              };
            }
          }));
          const commentsWithFullName = (data?.items || []).map((c: any) => ({
            ...c,
            fullName: avatarMap[c.user_id]?.fullName || c.user_name || c.user_email || 'Người dùng'
          }));
          setComments(commentsWithFullName);
          setUserAvatars(Object.fromEntries(Object.entries(avatarMap).map(([k, v]) => [k, v.img])));
        });
    } catch (err) {
      setCommentError('Gửi bình luận thất bại');
    } finally {
      setCommentFormLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Đang tải thông tin phim...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>Lỗi</h2>
          <p>{error}</p>
          <button 
            className={styles.backButton}
            onClick={() => navigate('/movie')}
          >
            ← Quay lại danh sách phim
          </button>
        </div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>Không tìm thấy phim</h2>
          <button 
            className={styles.backButton}
            onClick={() => navigate('/movie')}
          >
            ← Quay lại danh sách phim
          </button>
        </div>
      </div>
    );
  }


  return (
    <div className={styles.container}>
      <button 
        className={styles.backButton}
        onClick={() => navigate('/movie')}
      >
        ← Quay lại danh sách phim
      </button>

      <div className={styles.movieDetail}>
        <div className={styles.posterSection}>
          <img
            src={movie.poster_link}
            alt={movie.series_title}
            className={styles.poster}
            onError={e => {
              (e.currentTarget as HTMLImageElement).src = '/assets/default-movie.png';
            }}
          />
        </div>

        <div className={styles.infoSection}>
          <h1 className={styles.title}>{movie.series_title}</h1>

          <div className={styles.metadata}>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Năm</span>
              <span className={styles.metaValue}>{movie.released_year}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Thời lượng</span>
              <span className={styles.metaValue}>{movie.runtime}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Phân loại</span>
              <span className={styles.metaValue}>{movie.certificate}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Đánh giá IMDb</span>
              <span className={styles.metaValue}>⭐ {movie.imdb_rating}/10</span>
            </div>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Thể loại</h3>
            <p className={styles.genre}>{movie.genre}</p>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Tóm tắt</h3>
            <p className={styles.overview}>{movie.overview}</p>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Đạo diễn</h3>
            <p className={styles.director}>{movie.director}</p>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Diễn viên</h3>
            <div className={styles.cast}>
              {[movie.star1, movie.star2, movie.star3, movie.star4]
                .filter(star => star && star.trim() !== '')
                .map((star, index) => (
                  <span key={index} className={styles.castMember}>
                    {star}
                  </span>
                ))
              }
            </div>
          </div>

          <div className={styles.actions}>
            <button 
              className={styles.buyButton}
              onClick={() => setIsBookingPopupOpen(true)}
            >
              Mua vé
            </button>
            <button className={styles.watchlistButton}>
              Thêm vào danh sách
            </button>
          </div>
        </div>
      </div>

      {/* INSIGHT */}
      <div style={{margin: '32px 0 16px 0', padding: 24, background: '#f8f8fa', borderRadius: 12, boxShadow: '0 2px 8px #0001'}}>
        <h2 style={{fontSize: '1.2rem', fontWeight: 700, marginBottom: 10, color: '#e50914'}}>Phân tích dựa trên đánh giá</h2>
        {/* Luôn hiển thị đánh giá trung bình */}
        {(() => {
          const ratings = comments.map(c => c.rating).filter(r => typeof r === 'number') as number[];
          const avg = ratings.length > 0 ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null;
          return (
            <div style={{marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8}}>
              <b>Đánh giá trung bình:</b>
              {avg !== null ? (
                <>
                  <span style={{fontWeight: 600, fontSize: 18}}>{avg.toFixed(1)}/5</span>
                  <StarRating rating={avg} size={28} readOnly />
                  <span style={{color: '#888', fontSize: 13}}>({ratings.length} đánh giá)</span>
                </>
              ) : (
                <span style={{color: '#aaa'}}>Chưa có đánh giá</span>
              )}
            </div>
          );
        })()}
        {/* Hiển thị insight nếu có, nếu không thì báo chưa đủ bình luận */}
        {insightLoading ? (
          <div>Đang tải insight...</div>
        ) : insight ? (
          <>
            <div style={{marginBottom: 10}}><b>Tóm tắt:</b> {insight.summary}</div>
            <div style={{marginBottom: 10}}>
              <b>Điểm mạnh nổi bật:</b>
              <ul style={{margin: '6px 0 0 18px'}}>
                {insight.positive_aspects.map((item, idx) => <li key={idx}>{item}</li>)}
              </ul>
            </div>
            {insight.negative_aspects && insight.negative_aspects.length > 0 && (
              <div style={{marginBottom: 10}}>
                <b>Điểm hạn chế:</b>
                <ul style={{margin: '6px 0 0 18px'}}>
                  {insight.negative_aspects.map((item, idx) => <li key={idx}>{item}</li>)}
                </ul>
              </div>
            )}
            <div style={{marginBottom: 10}}><b>Khuyến nghị:</b> {insight.recommendations}</div>
            <div style={{fontSize: '0.95em', color: '#888'}}>Phân tích dựa trên {insight.based_on_comments} bình luận gần nhất.</div>
          </>
        ) : (
          insightError && (
            <div style={{color: '#d32f2f'}}>{insightError}</div>
          )
        )}
      </div>

      {/* Booking Popup */}
      <BookingPopup 
        isOpen={isBookingPopupOpen}
        onClose={() => setIsBookingPopupOpen(false)}
        movieTitle={selectedMovieTitle}
        movieId={selectedMovieId}
      />

      {/* Related Movies Slider */}
      <RelatedMoviesSlider 
        movies={similarMovies}
        onBuyClick={(title, movieId) => {
          setSelectedMovieTitle(title);
          setSelectedMovieId(movieId);
          setIsBookingPopupOpen(true);
        }}
      />

      {/* Comment Section */}
      <div style={{ marginTop: 32 }}>
        <h3 style={{ fontSize: '1.3rem', fontWeight: 600, marginBottom: 12 }}>Bình luận</h3>
        <CommentForm onSubmit={handleAddComment} loading={commentFormLoading} />
        {commentError && <div style={{ color: '#d32f2f', marginBottom: 12 }}>{commentError}</div>}
        <CommentList comments={comments} userAvatars={userAvatars} reloadComments={() => {
          setCommentLoading(true);
          setCommentError(null);
          const commentToken = localStorage.getItem('access-token');
          fetch(`https://comment-service-pf4q4c6zkq-pd.a.run.app/api/v1/comments/target/movie/${id}?page=${commentPage}&page_size=10&sort_by=recent`, {
            headers: commentToken ? {
              'Authorization': `Bearer ${commentToken}`,
              'accept': 'application/json'
            } : {
              'accept': 'application/json'
            }
          })
            .then(res => res.json())
            .then(async data => {
              setCommentTotalPages(data?.total_pages || 1);
              const avatarMap: Record<number, { img: string; fullName: string }> = {};
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
                    avatarMap[userId] = {
                      img: '',
                      fullName: ''
                    };
                  }
                } catch {
                  avatarMap[userId] = {
                    img: '',
                    fullName: ''
                  };
                }
              }));
              const commentsWithFullName = (data?.items || []).map((c: any) => ({
                ...c,
                fullName: avatarMap[c.user_id]?.fullName || c.user_name || c.user_email || 'Người dùng'
              }));
              setComments(commentsWithFullName);
              setUserAvatars(Object.fromEntries(Object.entries(avatarMap).map(([k, v]) => [k, v.img])));
            })
            .catch(() => setCommentError("Không thể tải bình luận."))
            .finally(() => setCommentLoading(false));
        }} />
        {/* Pagination for comments */}
        {commentTotalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 18, gap: 6 }}>
            <button
              style={{
                background: '#fff', color: '#e50914', border: '2px solid #e50914', borderRadius: 20, minWidth: 44, height: 36, fontWeight: 700, margin: '0 2px', cursor: commentPage === 1 ? 'not-allowed' : 'pointer', opacity: commentPage === 1 ? 0.5 : 1
              }}
              onClick={() => setCommentPage(p => Math.max(1, p - 1))}
              disabled={commentPage === 1}
            >
              &lt;
            </button>
            {(() => {
              const pageButtons = [];
              const pageWindow = 1;
              let left = Math.max(commentPage - pageWindow, 2);
              let right = Math.min(commentPage + pageWindow, commentTotalPages - 1);
              // Always show first page
              pageButtons.push(
                <button
                  key={1}
                  style={{
                    background: commentPage === 1 ? 'linear-gradient(135deg, #e50914 0%, #b20710 100%)' : '#fff',
                    color: commentPage === 1 ? '#fff' : '#e50914',
                    border: '2px solid #e50914',
                    borderRadius: 20,
                    minWidth: 44,
                    height: 36,
                    fontWeight: 700,
                    margin: '0 2px',
                    cursor: commentPage === 1 ? 'not-allowed' : 'pointer',
                    opacity: commentPage === 1 ? 1 : 1
                  }}
                  onClick={() => setCommentPage(1)}
                  disabled={commentPage === 1}
                >
                  1
                </button>
              );
              if (left > 2) {
                pageButtons.push(<span key="start-ellipsis" style={{ color: '#e50914', fontWeight: 700, padding: '0 6px' }}>...</span>);
              }
              for (let i = left; i <= right; i++) {
                pageButtons.push(
                  <button
                    key={i}
                    style={{
                      background: commentPage === i ? 'linear-gradient(135deg, #e50914 0%, #b20710 100%)' : '#fff',
                      color: commentPage === i ? '#fff' : '#e50914',
                      border: '2px solid #e50914',
                      borderRadius: 20,
                      minWidth: 44,
                      height: 36,
                      fontWeight: 700,
                      margin: '0 2px',
                      cursor: commentPage === i ? 'not-allowed' : 'pointer',
                      opacity: commentPage === i ? 1 : 1
                    }}
                    onClick={() => setCommentPage(i)}
                    disabled={commentPage === i}
                  >
                    {i}
                  </button>
                );
              }
              if (right < commentTotalPages - 1) {
                pageButtons.push(<span key="end-ellipsis" style={{ color: '#e50914', fontWeight: 700, padding: '0 6px' }}>...</span>);
              }
              if (commentTotalPages > 1) {
                pageButtons.push(
                  <button
                    key={commentTotalPages}
                    style={{
                      background: commentPage === commentTotalPages ? 'linear-gradient(135deg, #e50914 0%, #b20710 100%)' : '#fff',
                      color: commentPage === commentTotalPages ? '#fff' : '#e50914',
                      border: '2px solid #e50914',
                      borderRadius: 20,
                      minWidth: 44,
                      height: 36,
                      fontWeight: 700,
                      margin: '0 2px',
                      cursor: commentPage === commentTotalPages ? 'not-allowed' : 'pointer',
                      opacity: commentPage === commentTotalPages ? 1 : 1
                    }}
                    onClick={() => setCommentPage(commentTotalPages)}
                    disabled={commentPage === commentTotalPages}
                  >
                    {commentTotalPages}
                  </button>
                );
              }
              return pageButtons;
            })()}
            <button
              style={{
                background: '#fff', color: '#e50914', border: '2px solid #e50914', borderRadius: 20, minWidth: 44, height: 36, fontWeight: 700, margin: '0 2px', cursor: commentPage === commentTotalPages ? 'not-allowed' : 'pointer', opacity: commentPage === commentTotalPages ? 0.5 : 1
              }}
              onClick={() => setCommentPage(p => Math.min(commentTotalPages, p + 1))}
              disabled={commentPage === commentTotalPages}
            >
              &gt;
            </button>
          </div>
        )}
      </div>
    </div>
  );
}