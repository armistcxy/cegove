import sys
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.user_behavior import UserBehavior
from app.models.movie import Movie

# Định nghĩa behavior scores
BEHAVIOR_SCORES = {
    'view': 1.0,
    'book': 3.0,
    'rate': 5.0,
}

def seed_user_behaviors(n_users: int = 50, n_behaviors_per_user: int = 20):
    """
    Tạo fake data cho user behaviors
    """
    db = SessionLocal()
    
    try:
        # Tạo tables nếu chưa có
        Base.metadata.create_all(bind=engine)
        
        # Lấy danh sách movie_ids
        movies = db.query(Movie.id).all()
        if not movies:
            print("Không có movies trong database. Vui lòng thêm movies trước.")
            return
        
        movie_ids = [m.id for m in movies]
        print(f"Tìm thấy {len(movie_ids)} movies")
        
        # Xóa dữ liệu cũ (optional)
        db.query(UserBehavior).delete()
        db.commit()
        
        behaviors_list = list(BEHAVIOR_SCORES.keys())
        created_count = 0
        
        for user_id in range(1, n_users + 1):
            # Mỗi user có random số behaviors
            n_behaviors = random.randint(10, n_behaviors_per_user)
            
            # Random chọn movies (không trùng)
            user_movies = random.sample(movie_ids, min(n_behaviors, len(movie_ids)))
            
            for movie_id in user_movies:
                # Random behavior
                behavior = random.choice(behaviors_list)
                score = BEHAVIOR_SCORES[behavior]
                
                # Random timestamp trong 30 ngày gần đây
                days_ago = random.randint(0, 30)
                created_at = datetime.now() - timedelta(days=days_ago)
                
                user_behavior = UserBehavior(
                    user_id=user_id,
                    movie_id=movie_id,
                    behavior=behavior,
                    score=score,
                    created_at=created_at
                )
                db.add(user_behavior)
                created_count += 1
            
            if user_id % 10 == 0:
                db.commit()
                print(f"Created behaviors for {user_id} users...")
        
        db.commit()
        print(f"\nSeed completed! Created {created_count} user behaviors for {n_users} users.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting seed user behaviors...")
    seed_user_behaviors(n_users=50, n_behaviors_per_user=20)