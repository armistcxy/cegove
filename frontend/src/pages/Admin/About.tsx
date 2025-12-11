import styles from './Admin.module.css';

export default function About() {
  const teamMembers = [
    { name: 'Ngô Lê Hoàng', email: '22028042@vnu.edu.vn' },
    { name: 'Dương Anh Tú', email: '22028021@vnu.edu.vn' },
    { name: 'Nguyễn Đức Khánh', email: '22028196@vnu.edu.vn' },
    { name: 'Trần Thái Dương', email: '22028061@vnu.edu.vn' },
    { name: 'Nguyễn Mạnh Quân', email: '22028171@vnu.edu.vn' },
  ];

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.pageTitle}>About Our Team</h1>

      <div className={styles.card}>
        <h2 className={styles.sectionTitle}>Giới thiệu dự án</h2>
        <p className={styles.aboutText}>
          Đây là hệ thống quản lý rạp chiếu phim CGV được phát triển bởi nhóm 4 lớp SOA
        </p>
      </div>

      <div className={styles.card}>
        <h2 className={styles.sectionTitle}>Thành viên nhóm</h2>
        <div className={styles.teamGrid}>
          {teamMembers.map((member, index) => (
            <div key={index} className={styles.teamCard}>
              <div className={styles.avatar}>
                {member.name.charAt(0)}
              </div>
              <h3>{member.name}</h3>
              <p className={styles.email}>{member.email}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
