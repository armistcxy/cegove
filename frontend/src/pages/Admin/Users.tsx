import styles from './Admin.module.css';
import React, { useEffect, useState } from 'react';
import { getAllUsers, deleteUser, setUserRole } from './Utils/ApiFunction';

interface User {
  id: number;
  fullName: string;
  email: string;
  phone?: string | null;
  role: string;
  dob?: string | null;
  gender?: string | null;
  address?: string | null;
  district?: string | null;
  city?: string | null;
  imgFile?: string | null;
  img?: string | null;
  createdAt?: string;
}

const roleOptions = ['USER', 'LOCAL_ADMIN'];

export default function Users() {
  const USERS_PER_PAGE = 5;
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [roleEditId, setRoleEditId] = useState<number | null>(null);
  const [roleValue, setRoleValue] = useState<string>('USER');
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(users.length / USERS_PER_PAGE);
  const paginatedUsers = users.slice((currentPage - 1) * USERS_PER_PAGE, currentPage * USERS_PER_PAGE);

  const token = localStorage.getItem('access-token') || '';

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAllUsers(token);
      setUsers(res.data);
    } catch (err: any) {
      setError('Không thể tải danh sách user.');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line
  }, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Bạn có chắc muốn xóa user này?')) return;
    try {
      await deleteUser(token, id);
      setUsers(users.filter(u => u.id !== id));
    } catch {
      alert('Xóa user thất bại!');
    }
  };

  const handleSetRole = async (id: number) => {
    try {
      await setUserRole(token, id, roleValue);
      setUsers(users.map(u => u.id === id ? { ...u, role: roleValue } : u));
      setRoleEditId(null);
    } catch {
      alert('Cập nhật role thất bại!');
    }
  };

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.pageTitle}>Quản lý User</h1>
      <div className={styles.card}>
        {loading ? (
          <p>Đang tải...</p>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className={styles.table} style={{ minWidth: 800 }}>
              <thead>
                <tr>
                  <th>Id</th>
                  <th>Full Name</th>
                  <th>Email</th>
                  <th>Photo</th>
                  <th>Role</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {paginatedUsers.map(user => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.fullName}</td>
                    <td>{user.email}</td>
                    <td>
                      {user.img ? (
                        <img src={user.img} alt={user.fullName} style={{ width: 40, height: 40, borderRadius: '50%' }} />
                      ) : 'No photo'}
                    </td>
                    <td>
                      {roleEditId === user.id ? (
                        <select value={roleValue} onChange={e => setRoleValue(e.target.value)}>
                          {roleOptions.map(role => (
                            <option key={role} value={role}>{role}</option>
                          ))}
                        </select>
                      ) : (
                        user.role
                      )}
                    </td>
                    <td>
                      <button
                        onClick={() => handleDelete(user.id)}
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
                      >
                        Delete
                      </button>
                      {roleEditId === user.id ? (
                        <>
                          <button
                            onClick={() => handleSetRole(user.id)}
                            style={{
                              marginRight: 4,
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
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setRoleEditId(null)}
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
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => { setRoleEditId(user.id); setRoleValue(user.role); }}
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
                        >
                          Set Role
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {/* Pagination controls */}
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: 16, gap: 8 }}>
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                style={{
                  padding: '6px 14px',
                  borderRadius: 6,
                  border: '1px solid #bbb',
                  background: currentPage === 1 ? '#eee' : '#fff',
                  color: '#222',
                  cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                  fontWeight: 500,
                  transition: 'background 0.2s, color 0.2s',
                }}
              >
                Previous
              </button>
              <span style={{ alignSelf: 'center' }}>Page {currentPage} / {totalPages || 1}</span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages || totalPages === 0}
                style={{
                  padding: '6px 14px',
                  borderRadius: 6,
                  border: '1px solid #bbb',
                  background: (currentPage === totalPages || totalPages === 0) ? '#eee' : '#fff',
                  color: '#222',
                  cursor: (currentPage === totalPages || totalPages === 0) ? 'not-allowed' : 'pointer',
                  fontWeight: 500,
                  transition: 'background 0.2s, color 0.2s',
                }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
