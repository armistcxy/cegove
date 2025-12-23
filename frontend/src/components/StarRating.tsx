import React from 'react';

interface StarRatingProps {
  rating: number | null;
  onRate?: (rating: number) => void;
  size?: number;
  readOnly?: boolean;
}

const StarRating: React.FC<StarRatingProps> = ({ rating, onRate, size = 24, readOnly = false }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {[1, 2, 3, 4, 5].map((star) => (
        <span
          key={star}
          style={{
            cursor: readOnly ? 'default' : 'pointer',
            color: (rating ?? 0) >= star ? '#FFD600' : '#E0E0E0',
            fontSize: size,
            transition: 'color 0.2s',
            userSelect: 'none',
          }}
          onClick={() => !readOnly && onRate && onRate(star)}
          title={star + ' sao'}
        >
          ★
        </span>
      ))}
    </div>
  );
};

export default StarRating;
