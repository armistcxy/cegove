import { useEffect, useState } from 'react';
import { fetchCinemas } from '../Cinemas/CinemaLogic';
import { addCinema, deleteCinema, updateCinema } from './Utils/CinemaApi';
import styles from './Admin.module.css';

interface Cinema {
  id: number;
  name: string;
  address: string;
  city: string;
  district: string;
  phone: string;
  email: string;
}

export default function Cinemas() {
  const [cinemas, setCinemas] = useState<Cinema[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [newCinema, setNewCinema] = useState({
    name: '',
    address: '',
    city: '',
    district: '',
    phone: '',
    images: [],
  });
  const [editCinema, setEditCinema] = useState<null | (Cinema & {id: number})>(null);

  useEffect(() => {
    loadCinemas();
  }, []);

  const loadCinemas = async () => {
    setLoading(true);
    try {
      const data = await fetchCinemas();
      setCinemas(data);
    } catch (error) {
      console.error('Error loading cinemas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Bạn có chắc chắn muốn xóa rạp này?')) {
      try {
        await deleteCinema(id);
        loadCinemas();
      } catch (err) {
        alert('Xóa rạp thất bại!');
      }
    }
  };

  const handleEdit = (id: number) => {
    const cinema = cinemas.find(c => c.id === id);
    if (cinema) setEditCinema(cinema);
  };

  const handleUpdateCinema = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editCinema) return;
    try {
      await updateCinema(editCinema.id, editCinema);
      setEditCinema(null);
      loadCinemas();
    } catch (err) {
      alert('Cập nhật rạp thất bại!');
    }
  };

  const handleAddCinema = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await addCinema(newCinema);
      setShowAdd(false);
      setNewCinema({ name: '', address: '', city: '', district: '', phone: '', images: [] });
      loadCinemas();
    } catch (err) {
      alert('Thêm rạp thất bại!');
    }
  };

  // Get unique cities for filter
  const cities = [...new Set(cinemas.map(c => c.city))].sort();

  // Filter cinemas based on search and city
  const filteredCinemas = cinemas.filter(cinema => {
    const name = cinema.name || '';
    const address = cinema.address || '';
    const matchesSearch = name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCity = !selectedCity || cinema.city === selectedCity;
    return matchesSearch && matchesCity;
  });

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Quản lý Rạp Chiếu Phim</h1>
        <button className={styles.btnPrimary} onClick={() => setShowAdd(true)}>+ Thêm rạp mới</button>
      </div>
      
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
          <div className="modal-anim" style={{ background: '#fff', border: '1px solid #bbb', borderRadius: 14, padding: 32, minWidth: 350, boxShadow: '0 8px 32px #0003', position: 'relative', transition: 'box-shadow 0.2s' }}>
            <button onClick={() => setShowAdd(false)} style={{ position: 'absolute', top: 8, right: 12, background: 'none', border: 'none', fontSize: 22, color: '#888', cursor: 'pointer', transition: 'color 0.2s' }} title="Đóng"
              onMouseOver={e => (e.currentTarget.style.color = '#222')}
              onMouseOut={e => (e.currentTarget.style.color = '#888')}
            >×</button>
            <h2 style={{marginTop:0, marginBottom: 16}}>Thêm rạp mới</h2>
            <form onSubmit={handleAddCinema} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Tên rạp</label>
                <input autoFocus required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Tên rạp" value={newCinema.name} onChange={e => setNewCinema({ ...newCinema, name: e.target.value })} />
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Địa chỉ</label>
                <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Địa chỉ" value={newCinema.address} onChange={e => setNewCinema({ ...newCinema, address: e.target.value })} />
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Thành phố</label>
                <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Thành phố" value={newCinema.city} onChange={e => setNewCinema({ ...newCinema, city: e.target.value })} />
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Quận/Huyện</label>
                <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Quận/Huyện" value={newCinema.district} onChange={e => setNewCinema({ ...newCinema, district: e.target.value })} />
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Số điện thoại</label>
                <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Số điện thoại" value={newCinema.phone} onChange={e => setNewCinema({ ...newCinema, phone: e.target.value })} />
              </div>
              <div style={{display:'flex',gap:8,marginTop:8}}>
                <button type="submit" className="modal-btn" style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#222', color: '#fff', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Lưu</button>
                <button type="button" className="modal-btn modal-btn-cancel" onClick={() => setShowAdd(false)} style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#fff', color: '#222', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Hủy</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editCinema && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
            background: 'rgba(0,0,0,0.25)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'fadeInModal 0.25s',
          }}
          onClick={e => { if (e.target === e.currentTarget) setEditCinema(null); }}
        >
          <style>{`
            @keyframes fadeInModal { from { opacity: 0; } to { opacity: 1; } }
            .modal-anim { animation: fadeInModal 0.25s; }
            .modal-btn:hover { background: #222 !important; color: #fff !important; }
            .modal-btn-cancel:hover { background: #eee !important; color: #222 !important; }
            .modal-input:focus { border-color: #222; outline: none; }
          `}</style>
          <div className="modal-anim" style={{ background: '#fff', border: '1px solid #bbb', borderRadius: 14, padding: 32, minWidth: 350, boxShadow: '0 8px 32px #0003', position: 'relative', transition: 'box-shadow 0.2s' }}>
            <button onClick={() => setEditCinema(null)} style={{ position: 'absolute', top: 8, right: 12, background: 'none', border: 'none', fontSize: 22, color: '#888', cursor: 'pointer', transition: 'color 0.2s' }} title="Đóng"
              onMouseOver={e => (e.currentTarget.style.color = '#222')}
              onMouseOut={e => (e.currentTarget.style.color = '#888')}
            >×</button>
            <h2 style={{marginTop:0, marginBottom: 16}}>Sửa rạp</h2>
            <form onSubmit={handleUpdateCinema} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Tên rạp</label>
                <input autoFocus required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Tên rạp" value={editCinema.name} onChange={e => setEditCinema({ ...editCinema, name: e.target.value })} />
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Địa chỉ</label>
                <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Địa chỉ" value={editCinema.address} onChange={e => setEditCinema({ ...editCinema, address: e.target.value })} />
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Thành phố</label>
                <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Thành phố" value={editCinema.city} onChange={e => setEditCinema({ ...editCinema, city: e.target.value })} />
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Quận/Huyện</label>
                <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Quận/Huyện" value={editCinema.district} onChange={e => setEditCinema({ ...editCinema, district: e.target.value })} />
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <label style={{fontWeight:700, minWidth:100}}>Số điện thoại</label>
                <input required className="modal-input" style={{flex:1,padding:8, borderRadius:6, border:'1px solid #bbb'}} placeholder="Số điện thoại" value={editCinema.phone} onChange={e => setEditCinema({ ...editCinema, phone: e.target.value })} />
              </div>
              <div style={{display:'flex',gap:8,marginTop:8}}>
                <button type="submit" className="modal-btn" style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#222', color: '#fff', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Lưu</button>
                <button type="button" className="modal-btn modal-btn-cancel" onClick={() => setEditCinema(null)} style={{ padding: '6px 18px', borderRadius: 6, border: '1px solid #bbb', background: '#fff', color: '#222', fontWeight: 500, cursor: 'pointer', transition: 'background 0.2s, color 0.2s' }}>Hủy</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Filter Section */}
      <div className={styles.filterSection}>
        <input
          type="text"
          placeholder="Tìm kiếm theo tên rạp hoặc địa chỉ..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className={styles.searchInput}
        />
        <select
          value={selectedCity}
          onChange={(e) => setSelectedCity(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="">Tất cả thành phố</option>
          {cities.map(city => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Đang tải dữ liệu...</p>
        </div>
      ) : (
        <>
          <div className={styles.statsCard}>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Tổng số rạp:</span>
              <span className={styles.statValue}>{cinemas.length}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Kết quả hiển thị:</span>
              <span className={styles.statValue}>{filteredCinemas.length}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Số thành phố:</span>
              <span className={styles.statValue}>{cities.length}</span>
            </div>
          </div>

          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'center' }}>ID</th>
                  <th style={{ textAlign: 'center' }}>Tên rạp</th>
                  <th style={{ textAlign: 'center' }}>Thành phố</th>
                  <th style={{ textAlign: 'center' }}>Quận/Huyện</th>
                  <th style={{ textAlign: 'center' }}>Địa chỉ</th>
                  <th style={{ textAlign: 'center' }}>Số điện thoại</th>
                  <th style={{ textAlign: 'center' }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filteredCinemas.length === 0 ? (
                  <tr>
                    <td colSpan={7} className={styles.noData}>
                      Không tìm thấy rạp chiếu phim nào
                    </td>
                  </tr>
                ) : (
                  filteredCinemas.map((cinema) => (
                    <tr key={cinema.id}>
                      <td style={{ textAlign: 'center' }}>{cinema.id}</td>
                      <td className={styles.cinemaName} style={{ textAlign: 'center' }}>{cinema.name}</td>
                      <td style={{ textAlign: 'center' }}>
                        <span className={styles.cityTag}>{cinema.city}</span>
                      </td>
                      <td style={{ textAlign: 'center' }}>{cinema.district}</td>
                      <td className={styles.addressCell} style={{ textAlign: 'center' }}>{cinema.address}</td>
                      <td style={{ textAlign: 'center' }}>{cinema.phone}</td>
                      <td style={{ textAlign: 'center' }}>
                        <div className={styles.actionButtons}>
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
                            onClick={() => handleEdit(cinema.id)}
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
                            onClick={() => handleDelete(cinema.id)}
                            title="Xóa"
                          >
                            Xóa
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
