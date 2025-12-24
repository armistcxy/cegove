import { useEffect, useState } from 'react';
import { fetchCinemas } from '../Cinemas/CinemaLogic';
import styles from './Admin.module.css';

interface Movie {
  id: number;
  series_title: string;
  poster_link: string;
  released_year: string;
  genre: string;
}

export default function Movies() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [editMovie, setEditMovie] = useState<any | null>(null);
  const [showEdit, setShowEdit] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [newMovie, setNewMovie] = useState({
    poster_link: '',
    series_title: '',
    released_year: '',
    certificate: '',
    runtime: '',
    genre: '',
    imdb_rating: '',
    overview: '',
    meta_score: '',
    director: '',
    star1: '',
    star2: '',
    star3: '',
    star4: '',
    no_of_votes: '',
    gross: '',
  });
  const [showShowtimeModal, setShowShowtimeModal] = useState(false);
  const [showtimeMovieId, setShowtimeMovieId] = useState<number | null>(null);
  const [cities, setCities] = useState<string[]>([]);
  const [selectedCity, setSelectedCity] = useState('');
  const [cinemas, setCinemas] = useState<any[]>([]);
  const [selectedCinemaId, setSelectedCinemaId] = useState<string>('');
  const [auditoriums, setAuditoriums] = useState<any[]>([]);
  const [selectedAuditoriumId, setSelectedAuditoriumId] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [basePrice, setBasePrice] = useState('');
  const [loadingAuditoriums, setLoadingAuditoriums] = useState(false);
  const [isCreatingShowtime, setIsCreatingShowtime] = useState(false);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchMovies();
    }, 500); // Debounce 500ms

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, currentPage]);


  const fetchMovies = async () => {
    setLoading(true);
    try {
      let url = '';
      let data;
      if (searchTerm.trim()) {
        url = `https://movies.cegove.cloud/api/v1/movies/search?limit=10&q=${encodeURIComponent(searchTerm)}`;
        const response = await fetch(url, {
          headers: {
            'accept': 'application/json',
          },
        });
        data = await response.json();
        // API search trả về mảng trực tiếp
        setMovies(Array.isArray(data) ? data : []);
        setTotalPages(1);
      } else {
        url = `https://movies.cegove.cloud/api/v1/movies/?page=${currentPage}&page_size=20&sort_order=desc`;
        const response = await fetch(url);
        data = await response.json();
        setMovies(data.items || []);
        setTotalPages(data.total_pages || 1);
      }
    } catch (error) {
      console.error('Error fetching movies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Bạn có chắc chắn muốn xóa phim này?')) {
      setLoading(true);
      try {
          const token = localStorage.getItem('access-token') ? `Bearer ${localStorage.getItem('access-token')}` : '';
        const response = await fetch(
          `https://movies.cegove.cloud/api/v1/movies/${id}`,
          {
            method: 'DELETE',
            headers: {
              'accept': '*/*',
              'Authorization': token,
            },
          }
        );
        if (response.ok) {
          // Remove movie from state
          setMovies(prev => prev.filter(m => m.id !== id));
          alert('Xóa phim thành công!');
        } else {
          const errorText = await response.text();
          alert('Xóa phim thất bại: ' + errorText);
        }
      } catch (error) {
        alert('Lỗi khi xóa phim: ' + error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleEdit = (id: number) => {
    const movie = movies.find(m => m.id === id);
    if (movie) {
      setEditMovie({ ...movie });
      setShowEdit(true);
    }
  };

  const handleEditMovieChange = (field: string, value: any) => {
    setEditMovie((prev: any) => ({ ...prev, [field]: value }));
  };

  const handleUpdateMovie = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editMovie) return;
    setLoading(true);
    try {
        const token = localStorage.getItem('access-token') ? `Bearer ${localStorage.getItem('access-token')}` : '';
      const response = await fetch(
        `https://movies.cegove.cloud/api/v1/movies/${editMovie.id}`,
        {
          method: 'PUT',
          headers: {
            'accept': 'application/json',
            'Authorization': token,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(editMovie),
        }
      );
      if (response.ok) {
        alert('Cập nhật phim thành công!');
        setShowEdit(false);
        setEditMovie(null);
        fetchMovies();
      } else {
        const errorText = await response.text();
        alert('Cập nhật phim thất bại: ' + errorText);
      }
    } catch (error) {
      alert('Lỗi khi cập nhật phim: ' + error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMovieChange = (field: string, value: any) => {
    setNewMovie((prev: any) => ({ ...prev, [field]: value }));
  };

  const handleAddMovie = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
        const token = localStorage.getItem('access-token') ? `Bearer ${localStorage.getItem('access-token')}` : '';
      const response = await fetch(
        'https://movies.cegove.cloud/api/v1/movies/',
        {
          method: 'POST',
          headers: {
            'accept': 'application/json',
            'Authorization': token,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            ...newMovie,
            imdb_rating: newMovie.imdb_rating ? Number(newMovie.imdb_rating) : 0,
            meta_score: newMovie.meta_score ? Number(newMovie.meta_score) : 0,
            no_of_votes: newMovie.no_of_votes ? Number(newMovie.no_of_votes) : 0,
          }),
        }
      );
      if (response.ok) {
        alert('Thêm phim thành công!');
        setShowAdd(false);
        setNewMovie({
          poster_link: '', series_title: '', released_year: '', certificate: '', runtime: '', genre: '', imdb_rating: '', overview: '', meta_score: '', director: '', star1: '', star2: '', star3: '', star4: '', no_of_votes: '', gross: '',
        });
        fetchMovies();
      } else {
        const errorText = await response.text();
        alert('Thêm phim thất bại: ' + errorText);
      }
    } catch (error) {
      alert('Lỗi khi thêm phim: ' + error);
    } finally {
      setLoading(false);
    }
  };

  // Get unique genres and years for filters (client-side only)
  // Bỏ filter thể loại và năm
  const filteredMovies = movies;

  useEffect(() => {
    async function loadCinemas() {
      try {
        const cinemaList = await fetchCinemas();
        setCinemas(cinemaList);
        const cityList = Array.from(new Set(cinemaList.map((c: any) => c.city).filter(Boolean)));
        setCities(cityList);
      } catch {
        setCinemas([]);
        setCities([]);
      }
    }
    loadCinemas();
  }, []);

  useEffect(() => {
    if (!selectedCinemaId) {
      setAuditoriums([]);
      return;
    }
    setLoadingAuditoriums(true);
    const token = localStorage.getItem('access-token') ? `Bearer ${localStorage.getItem('access-token')}` : '';
    fetch(`https://cinema.cegove.cloud/cinemas/${selectedCinemaId}/auditoriums`, {
      headers: {
        'accept': 'application/json',
        ...(token ? { 'Authorization': token } : {})
      }
    })
      .then(async res => {
        if (!res.ok) {
          const err = await res.text();
          console.error('Lỗi lấy phòng chiếu:', err);
          setAuditoriums([]);
          return [];
        }
        return res.json();
      })
      .then(data => {
        if (Array.isArray(data)) {
          setAuditoriums(data);
        } else if (data && typeof data === 'object') {
          setAuditoriums([data]);
        } else {
          setAuditoriums([]);
        }
      })
      .catch((e) => {
        console.error('Lỗi fetch auditoriums:', e);
        setAuditoriums([]);
      })
      .finally(() => setLoadingAuditoriums(false));
  }, [selectedCinemaId]);

  const handleOpenShowtimeModal = (movieId: number) => {
    setShowtimeMovieId(movieId);
    setShowShowtimeModal(true);
    setSelectedCity('');
    setSelectedCinemaId('');
    setAuditoriums([]);
    setSelectedAuditoriumId('');
    setStartTime('');
    setEndTime('');
    setBasePrice('');
  };

  const handleCreateShowtime = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showtimeMovieId || !selectedCinemaId || !selectedAuditoriumId || !startTime || !endTime || !basePrice) {
      alert('Vui lòng nhập đầy đủ thông tin!');
      return;
    }
    setIsCreatingShowtime(true);
    try {
      const token = localStorage.getItem('access-token') ? `Bearer ${localStorage.getItem('access-token')}` : '';
      const body = {
        showtimes: [
          {
            movie_id: showtimeMovieId.toString(),
            cinema_id: selectedCinemaId,
            auditorium_id: selectedAuditoriumId,
            start_time: new Date(startTime).toISOString(),
            end_time: new Date(endTime).toISOString(),
            base_price: Number(basePrice)
          }
        ]
      };
      const res = await fetch('https://booking.cegove.cloud/api/v1/showtimes', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Authorization': token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      });
      if (res.ok) {
        alert('Tạo lịch chiếu thành công!');
        setShowShowtimeModal(false);
      } else {
        const err = await res.text();
        alert('Tạo lịch chiếu thất bại: ' + err);
      }
    } catch (error) {
      alert('Lỗi khi tạo lịch chiếu: ' + error);
    } finally {
      setIsCreatingShowtime(false);
    }
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Quản lý Phim</h1>
        <button className={styles.btnPrimary} onClick={() => setShowAdd(true)}>+ Thêm phim mới</button>
      </div>

      {/* Edit Movie Modal */}
      {showEdit && editMovie && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
            background: 'rgba(0,0,0,0.25)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'fadeInModal 0.25s',
          }}
          onClick={e => { if (e.target === e.currentTarget) setShowEdit(false); }}
        >
          <style>{`
            @keyframes fadeInModal { from { opacity: 0; } to { opacity: 1; } }
            .modal-anim { animation: fadeInModal 0.25s; }
            .modal-btn:hover { background: #222 !important; color: #fff !important; }
            .modal-btn-cancel:hover { background: #eee !important; color: #222 !important; }
            .modal-input:focus { border-color: #222; outline: none; }
          `}</style>
          <div className="modal-anim" style={{ background: '#fff', border: '1px solid #bbb', borderRadius: 14, padding: 32, minWidth: 700, maxWidth: 900, boxShadow: '0 8px 32px #0003', position: 'relative', transition: 'box-shadow 0.2s' }}>
            <button onClick={() => setShowEdit(false)} style={{ position: 'absolute', top: 8, right: 12, background: 'none', border: 'none', fontSize: 22, color: '#888', cursor: 'pointer', transition: 'color 0.2s' }} title="Đóng"
              onMouseOver={e => (e.currentTarget.style.color = '#222')}
              onMouseOut={e => (e.currentTarget.style.color = '#888')}
            >×</button>
            <h2 style={{marginTop:0, marginBottom: 16}}>Sửa phim</h2>
            <form onSubmit={handleUpdateMovie} style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              <div style={{ display: 'flex', flexDirection: 'row', gap: 32 }}>
                {/* Column 1 */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Tên phim</label>
                    <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Tên phim" value={editMovie.series_title} onChange={e => handleEditMovieChange('series_title', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Poster Link</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Poster Link" value={editMovie.poster_link} onChange={e => handleEditMovieChange('poster_link', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Năm phát hành</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Năm phát hành" value={editMovie.released_year} onChange={e => handleEditMovieChange('released_year', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Thể loại</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Thể loại" value={editMovie.genre} onChange={e => handleEditMovieChange('genre', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Chứng nhận</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Chứng nhận" value={editMovie.certificate || ''} onChange={e => handleEditMovieChange('certificate', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Thời lượng</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Thời lượng" value={editMovie.runtime || ''} onChange={e => handleEditMovieChange('runtime', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>IMDB Rating</label>
                    <input type="number" step="0.1" min="0" max="10" className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="IMDB Rating" value={editMovie.imdb_rating || ''} onChange={e => handleEditMovieChange('imdb_rating', e.target.value)} />
                  </div>
                </div>
                {/* Column 2 */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Meta Score</label>
                    <input type="number" min="0" max="100" className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Meta Score" value={editMovie.meta_score || ''} onChange={e => handleEditMovieChange('meta_score', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Đạo diễn</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Đạo diễn" value={editMovie.director || ''} onChange={e => handleEditMovieChange('director', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Star 1</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Star 1" value={editMovie.star1 || ''} onChange={e => handleEditMovieChange('star1', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Star 2</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Star 2" value={editMovie.star2 || ''} onChange={e => handleEditMovieChange('star2', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Star 3</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Star 3" value={editMovie.star3 || ''} onChange={e => handleEditMovieChange('star3', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Star 4</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Star 4" value={editMovie.star4 || ''} onChange={e => handleEditMovieChange('star4', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Số lượt vote</label>
                    <input type="number" min="0" className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Số lượt vote" value={editMovie.no_of_votes || ''} onChange={e => handleEditMovieChange('no_of_votes', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Gross</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Gross" value={editMovie.gross || ''} onChange={e => handleEditMovieChange('gross', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Overview</label>
                    <textarea className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb', minHeight:60}} placeholder="Overview" value={editMovie.overview || ''} onChange={e => handleEditMovieChange('overview', e.target.value)} />
                  </div>
                </div>
              </div>
              {/* Actions below all fields, right aligned */}
              <div style={{display:'flex',gap:8,marginTop:24,justifyContent:'flex-end'}}>
                <button type="submit" className="modal-btn" style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#222', color: '#fff', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Lưu</button>
                <button type="button" className="modal-btn modal-btn-cancel" onClick={() => setShowEdit(false)} style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#fff', color: '#222', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Hủy</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Movie Modal */}
      {showAdd && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
            background: 'rgba(0,0,0,0.25)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'fadeInModal 0.25s',
          }}
          onClick={e => { if (e.target === e.currentTarget) setShowAdd(false); }}
        >
          <style>{`
            @keyframes fadeInModal { from { opacity: 0; } to { opacity: 1; } }
            .modal-anim { animation: fadeInModal 0.25s; }
            .modal-btn:hover { background: #222 !important; color: #fff !important; }
            .modal-btn-cancel:hover { background: #eee !important; color: #222 !important; }
            .modal-input:focus { border-color: #222; outline: none; }
          `}</style>
          <div className="modal-anim" style={{ background: '#fff', border: '1px solid #bbb', borderRadius: 14, padding: 32, minWidth: 700, maxWidth: 900, boxShadow: '0 8px 32px #0003', position: 'relative', transition: 'box-shadow 0.2s' }}>
            <button onClick={() => setShowAdd(false)} style={{ position: 'absolute', top: 8, right: 12, background: 'none', border: 'none', fontSize: 22, color: '#888', cursor: 'pointer', transition: 'color 0.2s' }} title="Đóng"
              onMouseOver={e => (e.currentTarget.style.color = '#222')}
              onMouseOut={e => (e.currentTarget.style.color = '#888')}
            >×</button>
            <h2 style={{marginTop:0, marginBottom: 16}}>Thêm phim mới</h2>
            <form onSubmit={handleAddMovie} style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              <div style={{ display: 'flex', flexDirection: 'row', gap: 32 }}>
                {/* Column 1 */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Tên phim</label>
                    <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Tên phim" value={newMovie.series_title} onChange={e => handleAddMovieChange('series_title', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Poster Link</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Poster Link" value={newMovie.poster_link} onChange={e => handleAddMovieChange('poster_link', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Năm phát hành</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Năm phát hành" value={newMovie.released_year} onChange={e => handleAddMovieChange('released_year', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Thể loại</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Thể loại" value={newMovie.genre} onChange={e => handleAddMovieChange('genre', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Chứng nhận</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Chứng nhận" value={newMovie.certificate} onChange={e => handleAddMovieChange('certificate', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Thời lượng</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Thời lượng" value={newMovie.runtime} onChange={e => handleAddMovieChange('runtime', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>IMDB Rating</label>
                    <input type="number" step="0.1" min="0" max="10" className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="IMDB Rating" value={newMovie.imdb_rating} onChange={e => handleAddMovieChange('imdb_rating', e.target.value)} />
                  </div>
                </div>
                {/* Column 2 */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Meta Score</label>
                    <input type="number" min="0" max="100" className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Meta Score" value={newMovie.meta_score} onChange={e => handleAddMovieChange('meta_score', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Đạo diễn</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Đạo diễn" value={newMovie.director} onChange={e => handleAddMovieChange('director', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Star 1</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Star 1" value={newMovie.star1} onChange={e => handleAddMovieChange('star1', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Star 2</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Star 2" value={newMovie.star2} onChange={e => handleAddMovieChange('star2', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Star 3</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Star 3" value={newMovie.star3} onChange={e => handleAddMovieChange('star3', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Star 4</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Star 4" value={newMovie.star4} onChange={e => handleAddMovieChange('star4', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Số lượt vote</label>
                    <input type="number" min="0" className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Số lượt vote" value={newMovie.no_of_votes} onChange={e => handleAddMovieChange('no_of_votes', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Gross</label>
                    <input className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Gross" value={newMovie.gross} onChange={e => handleAddMovieChange('gross', e.target.value)} />
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:10}}>
                    <label style={{fontWeight:700, minWidth:120}}>Overview</label>
                    <textarea className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb', minHeight:60}} placeholder="Overview" value={newMovie.overview} onChange={e => handleAddMovieChange('overview', e.target.value)} />
                  </div>
                </div>
              </div>
              {/* Actions below all fields, right aligned */}
              <div style={{display:'flex',gap:8,marginTop:24,justifyContent:'flex-end'}}>
                <button type="submit" className="modal-btn" style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#222', color: '#fff', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Lưu</button>
                <button type="button" className="modal-btn modal-btn-cancel" onClick={() => setShowAdd(false)} style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#fff', color: '#222', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Hủy</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Showtime Modal */}
      {showShowtimeModal && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
            background: 'rgba(0,0,0,0.25)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'fadeInModal 0.25s',
          }}
          onClick={e => { if (e.target === e.currentTarget) setShowShowtimeModal(false); }}
        >
          <style>{`
            @keyframes fadeInModal { from { opacity: 0; } to { opacity: 1; } }
            .modal-anim { animation: fadeInModal 0.25s; }
            .modal-btn:hover { background: #222 !important; color: #fff !important; }
            .modal-btn-cancel:hover { background: #eee !important; color: #222 !important; }
            .modal-input:focus { border-color: #222; outline: none; }
          `}</style>
          <div className="modal-anim" style={{ background: '#fff', border: '1px solid #bbb', borderRadius: 14, padding: 32, minWidth: 500, maxWidth: 600, boxShadow: '0 8px 32px #0003', position: 'relative', transition: 'box-shadow 0.2s' }}>
            <button onClick={() => setShowShowtimeModal(false)} style={{ position: 'absolute', top: 8, right: 12, background: 'none', border: 'none', fontSize: 22, color: '#888', cursor: 'pointer', transition: 'color 0.2s' }} title="Đóng"
              onMouseOver={e => (e.currentTarget.style.color = '#222')}
              onMouseOut={e => (e.currentTarget.style.color = '#888')}
            >×</button>
            <h2 style={{marginTop:0, marginBottom: 16}}>Tạo lịch chiếu mới</h2>
            <form onSubmit={handleCreateShowtime} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <div style={{display:'flex',gap:12}}>
                <div style={{flex:1}}>
                  <label style={{fontWeight:700}}>Chọn thành phố</label>
                  <select required value={selectedCity} onChange={e => {setSelectedCity(e.target.value); setSelectedCinemaId('');}} style={{width:'100%',padding:8,borderRadius:6,border:'1px solid #bbb'}}>
                    <option value="">-- Chọn thành phố --</option>
                    {cities.map(city => <option key={city} value={city}>{city}</option>)}
                  </select>
                </div>
                <div style={{flex:1}}>
                  <label style={{fontWeight:700}}>Chọn rạp</label>
                  <select required value={selectedCinemaId} onChange={e => {setSelectedCinemaId(e.target.value); setSelectedAuditoriumId('');}} style={{width:'100%',padding:8,borderRadius:6,border:'1px solid #bbb'}}>
                    <option value="">-- Chọn rạp --</option>
                    {cinemas.filter(c => !selectedCity || c.city === selectedCity).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </div>
              {selectedCinemaId && (
                <div>
                  <label style={{fontWeight:700}}>Chọn phòng chiếu (Auditorium)</label>
                  {loadingAuditoriums ? (
                    <div>Đang tải phòng chiếu...</div>
                  ) : auditoriums.length === 0 ? (
                    <div style={{color:'#c00',fontWeight:500}}>Không có phòng chiếu nào cho rạp này.</div>
                  ) : (
                    <select required value={selectedAuditoriumId} onChange={e => setSelectedAuditoriumId(e.target.value)} style={{width:'100%',padding:8,borderRadius:6,border:'1px solid #bbb'}}>
                      <option value="">-- Chọn phòng chiếu --</option>
                      {auditoriums.map((a: any) => (
                        <option key={a.id} value={a.id}>{a.name} (ID: {a.id})</option>
                      ))}
                    </select>
                  )}
                </div>
              )}
              <div style={{display:'flex',gap:12}}>
                <div style={{flex:1}}>
                  <label style={{fontWeight:700}}>Thời gian bắt đầu</label>
                  <input required type="datetime-local" value={startTime} onChange={e => setStartTime(e.target.value)} style={{width:'100%',padding:8,borderRadius:6,border:'1px solid #bbb'}} />
                </div>
                <div style={{flex:1}}>
                  <label style={{fontWeight:700}}>Thời gian kết thúc</label>
                  <input required type="datetime-local" value={endTime} onChange={e => setEndTime(e.target.value)} style={{width:'100%',padding:8,borderRadius:6,border:'1px solid #bbb'}} />
                </div>
              </div>
              <div>
                <label style={{fontWeight:700}}>Giá vé (VNĐ)</label>
                <input required type="number" min={0} value={basePrice} onChange={e => setBasePrice(e.target.value)} style={{width:'100%',padding:8,borderRadius:6,border:'1px solid #bbb'}} />
              </div>
              <div style={{display:'flex',gap:8,justifyContent:'flex-end'}}>
                <button
                  type="submit"
                  className="modal-btn"
                  style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: isCreatingShowtime ? '#888' : '#222', color: '#fff', fontWeight: 500, cursor: isCreatingShowtime ? 'not-allowed' : 'pointer', transition: 'background 0.2s, color 0.2s' }}
                  disabled={isCreatingShowtime}
                >
                  {isCreatingShowtime ? 'Đang tạo...' : 'Tạo lịch chiếu'}
                </button>
                <button type="button" className="modal-btn modal-btn-cancel" onClick={() => setShowShowtimeModal(false)} style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#fff', color: '#222', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Hủy</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Filter Section chỉ còn search */}
      <div className={styles.filterSection}>
        <input
          type="text"
          placeholder="Tìm kiếm theo tên phim (search toàn bộ database)..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1); // Reset to first page on new search
          }}
          className={styles.searchInput}
        />
      </div>

      {loading ? (
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Đang tải dữ liệu...</p>
        </div>
      ) : (
        <>
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'center' }}>ID</th>
                  <th style={{ textAlign: 'center' }}>Poster</th>
                  <th style={{ textAlign: 'center' }}>Tiêu đề</th>
                  <th style={{ textAlign: 'center' }}>Phát hành</th>
                  <th style={{ textAlign: 'center' }}>Thể loại</th>
                  <th style={{ textAlign: 'center' }}>Trạng thái</th>
                  <th style={{ textAlign: 'center' }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filteredMovies.length === 0 ? (
                  <tr>
                    <td colSpan={7} className={styles.noData} style={{ textAlign: 'center' }}>
                      Không tìm thấy phim nào
                    </td>
                  </tr>
                ) : (
                  filteredMovies.map((movie) => (
                    <tr key={movie.id}>
                      <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>{movie.id}</td>
                      <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>
                        <img 
                          src={movie.poster_link} 
                          alt={movie.series_title}
                          className={styles.posterThumb}
                        />
                      </td>
                      <td className={styles.movieTitle} style={{ textAlign: 'center', verticalAlign: 'middle' }}>{movie.series_title}</td>
                      <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>{movie.released_year}</td>
                      <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>
                        <span className={styles.genreTag}>{movie.genre}</span>
                      </td>
                      <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>
                        <span className={styles.statusActive}>Active</span>
                      </td>
                      <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>
                        <div className={styles.actionButtons} style={{ justifyContent: 'center' }}>
                          <button
                            style={{
                              marginRight: 8,
                              padding: '6px 14px',
                              borderRadius: 6,
                              border: '1px solid #bbb',
                              background: '#fff',
                              color: '#222',
                              cursor: 'pointer',
                              fontWeight: 500,
                              transition: 'background 0.2s, color 0.2s',
                            }}
                            onMouseOver={e => {
                              e.currentTarget.style.background = '#222';
                              e.currentTarget.style.color = '#fff';
                            }}
                            onMouseOut={e => {
                              e.currentTarget.style.background = '#fff';
                              e.currentTarget.style.color = '#222';
                            }}
                            onClick={() => handleEdit(movie.id)}
                            title="Chỉnh sửa"
                          >
                            Sửa
                          </button>
                          <button
                            style={{
                              padding: '6px 14px',
                              borderRadius: 6,
                              border: '1px solid #bbb',
                              background: '#fff',
                              color: '#222',
                              cursor: 'pointer',
                              fontWeight: 500,
                              transition: 'background 0.2s, color 0.2s',
                            }}
                            onMouseOver={e => {
                              e.currentTarget.style.background = '#222';
                              e.currentTarget.style.color = '#fff';
                            }}
                            onMouseOut={e => {
                              e.currentTarget.style.background = '#fff';
                              e.currentTarget.style.color = '#222';
                            }}
                            onClick={() => handleDelete(movie.id)}
                            title="Xóa"
                          >
                            Xóa
                          </button>
                          <button
                            style={{
                              marginRight: 8,
                              padding: '6px 14px',
                              borderRadius: 6,
                              border: '1px solid #bbb',
                              background: '#fff',
                              color: '#222',
                              cursor: 'pointer',
                              fontWeight: 500,
                              transition: 'background 0.2s, color 0.2s',
                            }}
                            onMouseOver={e => {
                              e.currentTarget.style.background = '#222';
                              e.currentTarget.style.color = '#fff';
                            }}
                            onMouseOut={e => {
                              e.currentTarget.style.background = '#fff';
                              e.currentTarget.style.color = '#222';
                            }}
                            onClick={() => handleOpenShowtimeModal(movie.id)}
                            title="Tạo lịch chiếu"
                          >
                            Tạo Showtime
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className={styles.pagination}>
            <button 
              className={styles.paginationBtn}
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
            >
              ← Previous
            </button>
            <span className={styles.pageInfo}>
              Page {currentPage} of {totalPages}
            </span>
            <button 
              className={styles.paginationBtn}
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(prev => prev + 1)}
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
