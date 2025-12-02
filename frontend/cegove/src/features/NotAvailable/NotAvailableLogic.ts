// NotAvailableLogic.ts

// Helper function to track feature usage analytics (optional)
export const trackFeatureAttempt = (featureName: string) => {
  console.log(`User attempted to access feature: ${featureName}`);
  // Here you could send analytics to your backend
};

// List of features that are not available yet
export const unavailableFeatures = [
  'user-profile',
  'watchlist',
  'reviews',
  'recommendations',
  'payments',
  'notifications',
  'social-sharing'
];

// Check if a feature is available
export const isFeatureAvailable = (featureName: string): boolean => {
  return !unavailableFeatures.includes(featureName);
};

// Get a friendly message for unavailable features
export const getUnavailableMessage = (featureName?: string): string => {
  const messages = {
    'user-profile': 'Trang cá nhân đang được phát triển',
    'watchlist': 'Danh sách yêu thích sẽ sớm có mặt',
    'reviews': 'Tính năng đánh giá đang hoàn thiện',
    'recommendations': 'Hệ thống gợi ý phim đang được xây dựng',
    'payments': 'Thanh toán trực tuyến sẽ sớm được tích hợp',
    'notifications': 'Thông báo sẽ có trong phiên bản tiếp theo',
    'social-sharing': 'Chia sẻ mạng xã hội đang phát triển'
  };
  
  return featureName && messages[featureName as keyof typeof messages] 
    ? messages[featureName as keyof typeof messages]
    : 'Tính năng này đang được phát triển';
};