import { useNavigate } from "react-router-dom";
import styles from "./NotAvailable.module.css";

export default function NotAvailable() {
  const navigate = useNavigate();

  const goBack = () => {
    navigate(-1);
  };

  const goHome = () => {
    navigate("/homepage");
  };

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <div className={styles.iconSection}>
          <div className={styles.constructionIcon}>🚧</div>
          <div className={styles.toolsIcon}>🔧</div>
        </div>
        
        <h1 className={styles.title}>Tính năng đang được phát triển</h1>
        
        <p className={styles.message}>
          Xin lỗi! Tính năng này hiện tại chưa có sẵn. 
          <br />
          Chúng tôi đang nỗ lực hoàn thiện để mang đến trải nghiệm tốt nhất cho bạn!
        </p>
        
        <div className={styles.illustration}>
          <div className={styles.movieReel}>🎞️</div>
          <div className={styles.clapperboard}>🎬</div>
          <div className={styles.popcorn}>🍿</div>
        </div>
        
        <div className={styles.actions}>
          <button 
            className={styles.backButton}
            onClick={goBack}
          >
            ← Quay lại trang trước
          </button>
          
          <button 
            className={styles.homeButton}
            onClick={goHome}
          >
            Về trang chủ
          </button>
        </div>
        
        <div className={styles.footer}>
          <p>Cảm ơn bạn đã kiên nhẫn!</p>
        </div>
      </div>
    </div>
  );
}