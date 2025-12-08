import sys
import os
import pandas as pd
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import SessionLocal, init_db
from app.models.movie import Movie


def clean_value(value):
    """Clean and convert values"""
    if pd.isna(value) or value == '' or value == 'NaN':
        return None
    return value


def clean_numeric(value):
    """Clean numeric values (remove commas)"""
    if pd.isna(value) or value == '' or value == 'NaN':
        return None
    if isinstance(value, str):
        return value.replace(',', '')
    return str(value)


def import_movies_from_csv(csv_path: str):
    """Import movies from CSV file"""
    
    # Initialize database (create tables if not exist)
    print("🔧 Initializing database...")
    init_db()
    
    # Read CSV
    print(f"📖 Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"📊 Found {len(df)} movies in CSV")
    
    # Create database session
    db: Session = SessionLocal()
    
    try:
        imported_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            try:
                # Check if movie already exists
                existing_movie = db.query(Movie).filter(
                    Movie.series_title == clean_value(row.get('Series_Title'))
                ).first()
                
                if existing_movie:
                    print(f"⏭️  Skipping duplicate: {row.get('Series_Title')}")
                    skipped_count += 1
                    continue
                
                # Create movie object
                movie = Movie(
                    poster_link=clean_value(row.get('Poster_Link')),
                    series_title=clean_value(row.get('Series_Title')),
                    released_year=clean_value(row.get('Released_Year')),
                    certificate=clean_value(row.get('Certificate')),
                    runtime=clean_value(row.get('Runtime')),
                    genre=clean_value(row.get('Genre')),
                    imdb_rating=float(clean_value(row.get('IMDB_Rating'))) if clean_value(row.get('IMDB_Rating')) else None,
                    overview=clean_value(row.get('Overview')),
                    meta_score=int(float(clean_value(row.get('Meta_score')))) if clean_value(row.get('Meta_score')) else None,
                    director=clean_value(row.get('Director')),
                    star1=clean_value(row.get('Star1')),
                    star2=clean_value(row.get('Star2')),
                    star3=clean_value(row.get('Star3')),
                    star4=clean_value(row.get('Star4')),
                    no_of_votes=int(clean_numeric(row.get('No_of_Votes'))) if clean_numeric(row.get('No_of_Votes')) else None,
                    gross=clean_numeric(row.get('Gross'))
                )
                
                db.add(movie)
                imported_count += 1
                
                # Commit every 50 records
                if imported_count % 50 == 0:
                    db.commit()
                    print(f"✅ Imported {imported_count} movies...")
                
            except Exception as e:
                print(f"❌ Error importing row {index}: {str(e)}")
                db.rollback()
                continue
        
        # Final commit
        db.commit()
        
        print("\n" + "="*50)
        print(f"✨ Import completed!")
        print(f"✅ Successfully imported: {imported_count} movies")
        print(f"⏭️  Skipped duplicates: {skipped_count} movies")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error during import: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Path to CSV file
    csv_file_path = "data/movies.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        print(f"📝 Please place your CSV file at: {csv_file_path}")
        sys.exit(1)
    
    import_movies_from_csv(csv_file_path)