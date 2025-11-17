import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# Thêm root directory vào Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

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
        print("Đang xóa user behaviors cũ...")
        db.query(UserBehavior).delete()
        db.commit()
        
        behaviors_list = list(BEHAVIOR_SCORES.keys())
        created_count = 0
        
        print(f"Bắt đầu tạo behaviors cho {n_users} users...")
        
        for user_id in range(1, n_users + 1):
            # Mỗi user có random số behaviors
            n_behaviors = random.randint(10, n_behaviors_per_user)
            
            # Random chọn movies (không trùng)
            user_movies = random.sample(movie_ids, min(n_behaviors, len(movie_ids)))
            
            for movie_id in user_movies:
                # Random behavior với xác suất khác nhau
                # view: 50%, book: 30%, rate: 20%
                rand = random.random()
                if rand < 0.5:
                    behavior = 'view'
                elif rand < 0.8:
                    behavior = 'book'
                else:
                    behavior = 'rate'
                
                score = BEHAVIOR_SCORES[behavior]
                
                # Random timestamp trong 30 ngày gần đây
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
                
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
                print(f"✓ Created behaviors for {user_id}/{n_users} users...")
        
        db.commit()
        print(f"\n{'='*60}")
        print(f"✓ Seed completed successfully!")
        print(f"  - Total users: {n_users}")
        print(f"  - Total behaviors: {created_count}")
        print(f"  - Average behaviors per user: {created_count/n_users:.1f}")
        print(f"{'='*60}")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def seed_diverse_behaviors(n_users: int = 100):
    """
    Tạo diverse behaviors với patterns khác nhau
    """
    db = SessionLocal()
    
    try:
        Base.metadata.create_all(bind=engine)
        
        movies = db.query(Movie.id).all()
        if not movies:
            print("Không có movies trong database.")
            return
        
        movie_ids = [m.id for m in movies]
        print(f"Tìm thấy {len(movie_ids)} movies")
        
        # Xóa dữ liệu cũ
        db.query(UserBehavior).delete()
        db.commit()
        
        created_count = 0
        behaviors_list = list(BEHAVIOR_SCORES.keys())
        
        print(f"Tạo diverse behaviors cho {n_users} users...")
        
        for user_id in range(1, n_users + 1):
            # Tạo user patterns khác nhau
            if user_id <= 20:
                # Heavy users: xem nhiều phim
                n_behaviors = random.randint(30, 50)
                preference = behaviors_list  # Tất cả behaviors
            elif user_id <= 50:
                # Medium users: xem vừa phải
                n_behaviors = random.randint(15, 30)
                preference = ['view', 'book']  # Ít rate
            else:
                # Light users: xem ít
                n_behaviors = random.randint(5, 15)
                preference = ['view']  # Chủ yếu view
            
            user_movies = random.sample(movie_ids, min(n_behaviors, len(movie_ids)))
            
            for movie_id in user_movies:
                behavior = random.choice(preference)
                score = BEHAVIOR_SCORES[behavior]
                
                # Có thể có multiple behaviors cho cùng movie
                if random.random() < 0.3 and behavior == 'view':
                    # 30% chance view -> book
                    extra_behavior = UserBehavior(
                        user_id=user_id,
                        movie_id=movie_id,
                        behavior='book',
                        score=BEHAVIOR_SCORES['book'],
                        created_at=datetime.now() - timedelta(days=random.randint(0, 30))
                    )
                    db.add(extra_behavior)
                    created_count += 1
                
                days_ago = random.randint(0, 60)
                created_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
                
                user_behavior = UserBehavior(
                    user_id=user_id,
                    movie_id=movie_id,
                    behavior=behavior,
                    score=score,
                    created_at=created_at
                )
                db.add(user_behavior)
                created_count += 1
            
            if user_id % 20 == 0:
                db.commit()
                print(f"✓ Created behaviors for {user_id}/{n_users} users...")
        
        db.commit()
        print(f"\n{'='*60}")
        print(f"✓ Diverse seed completed!")
        print(f"  - Heavy users (30-50 behaviors): 20")
        print(f"  - Medium users (15-30 behaviors): 30")
        print(f"  - Light users (5-15 behaviors): {n_users - 50}")
        print(f"  - Total behaviors: {created_count}")
        print(f"{'='*60}")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed user behaviors')
    parser.add_argument('--mode', choices=['simple', 'diverse'], default='simple',
                       help='Seed mode: simple or diverse')
    parser.add_argument('--users', type=int, default=50,
                       help='Number of users')
    parser.add_argument('--behaviors', type=int, default=20,
                       help='Max behaviors per user (for simple mode)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("SEED USER BEHAVIORS")
    print("="*60)
    
    if args.mode == 'simple':
        print(f"Mode: Simple (uniform distribution)")
        seed_user_behaviors(n_users=args.users, n_behaviors_per_user=args.behaviors)
    else:
        print(f"Mode: Diverse (varied user patterns)")
        seed_diverse_behaviors(n_users=args.users)