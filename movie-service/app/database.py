from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Fix postgres:// to postgresql://
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables and indexes"""
    from app.models import movie  # Import to register models
    
    Base.metadata.create_all(bind=engine)
    
    # Create full-text search GIN index
    with engine.connect() as conn:
        # Check if index exists
        check_index = text("""
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'ix_movies_fulltext_search'
        """)
        
        result = conn.execute(check_index).fetchone()
        
        if not result:
            # Create GIN index for full-text search
            create_index = text("""
                CREATE INDEX ix_movies_fulltext_search ON movies 
                USING gin(
                    to_tsvector('english', 
                        COALESCE(series_title, '') || ' ' ||
                        COALESCE(overview, '') || ' ' ||
                        COALESCE(director, '') || ' ' ||
                        COALESCE(genre, '')
                    )
                )
            """)
            
            conn.execute(create_index)
            conn.commit()
            print("✅ Created full-text search index")
        else:
            print("✅ Full-text search index already exists")