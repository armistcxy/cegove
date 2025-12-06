import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUser } from "../../context/UserContext.tsx";
import { updateUserProfile } from "./Utils/ApiFunction.ts";

interface EditableProfileData {
    fullName: string;
    email: string;
    phone: string;
    dob: string;
    address: string;
    district: string;
    city: string;
    gender: 'MALE' | 'FEMALE' | '';
}

const Profile = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { isLoggedIn, userProfile, refreshUserProfile } = useUser();

    const [loading, setLoading] = useState<boolean>(false);
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const [updating, setUpdating] = useState<boolean>(false);
    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const [previewImage, setPreviewImage] = useState<string>('');
    const [error, setError] = useState<string>('');
    const [success, setSuccess] = useState<string>('');

    const [editForm, setEditForm] = useState<EditableProfileData>({
        fullName: '',
        email: '',
        phone: '',
        dob: '',
        address: '',
        district: '',
        city: '',
        gender: ''
    });

    useEffect(() => {
        const checkLoginGoogle = async () => {
            const params = new URLSearchParams(location.search);
            const urlToken = params.get('accessToken');

            if (urlToken) {
                setLoading(true);
                localStorage.setItem('access-token', urlToken);
                await refreshUserProfile();
                window.history.replaceState({}, document.title, "/profile");
                setLoading(false);
            }
        };

        checkLoginGoogle();
    }, [location, navigate]);

    useEffect(() => {
        if (userProfile) {
            setEditForm({
                fullName: userProfile.fullName || '',
                email: userProfile.email || '',
                phone: userProfile.phone || '',
                dob: userProfile.dob || '',
                address: userProfile.address || '',
                district: userProfile.district || '',
                city: userProfile.city || '',
                gender: userProfile.gender || ''
            });
            setPreviewImage(userProfile.img || '');
        }
    }, [userProfile]);

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Clear previous errors
            setError('');
            
            // Check file size (5MB limit)
            if (file.size > 5 * 1024 * 1024) {
                setError('Kích thước ảnh không được vượt quá 5MB');
                e.target.value = ''; // Clear the input
                return;
            }
            
            // Check file type
            const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                setError('Chỉ hỗ trợ định dạng JPG, PNG, WEBP');
                e.target.value = ''; // Clear the input
                return;
            }

            console.log('Selected file:', file.name, 'Size:', Math.round(file.size / 1024), 'KB');
            setSelectedImage(file);
            
            // Create preview
            const reader = new FileReader();
            reader.onload = (event) => {
                setPreviewImage(event.target?.result as string);
            };
            reader.onerror = () => {
                setError('Không thể đọc file ảnh');
                setSelectedImage(null);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setEditForm(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSaveProfile = async () => {
        setUpdating(true);
        setError('');
        setSuccess('');

        try {
            const token = localStorage.getItem('access-token');
            if (!token) {
                setError('Phiên đăng nhập đã hết hạn');
                return;
            }

            // Validate required fields
            if (!editForm.fullName.trim()) {
                setError('Họ và tên không được để trống');
                return;
            }
            
            if (!editForm.email.trim()) {
                setError('Email không được để trống');
                return;
            }

            const formData = new FormData();
            
            // Append profile data (only non-empty values)
            formData.append('fullName', editForm.fullName.trim());
            formData.append('email', editForm.email.trim());
            
            if (editForm.phone.trim()) {
                formData.append('phone', editForm.phone.trim());
            }
            
            if (editForm.dob) {
                formData.append('dob', editForm.dob);
            }
            
            if (editForm.address.trim()) {
                formData.append('address', editForm.address.trim());
            }
            
            if (editForm.district.trim()) {
                formData.append('district', editForm.district.trim());
            }
            
            if (editForm.city.trim()) {
                formData.append('city', editForm.city.trim());
            }
            
            if (editForm.gender) {
                formData.append('gender', editForm.gender);
            }

            // Append image if selected
            if (selectedImage) {
                console.log('Uploading image:', selectedImage.name);
                formData.append('imgFile', selectedImage);
            }

            console.log('Sending profile update...');
            const response = await updateUserProfile(token, formData);
            console.log('Update response:', response.data);
            
            await refreshUserProfile();
            
            setIsEditing(false);
            setSelectedImage(null);
            setSuccess('Cập nhật thông tin thành công!');
            setTimeout(() => setSuccess(''), 3000);
        } catch (error: any) {
            setError(error.response?.data?.message || 'Có lỗi xảy ra khi cập nhật thông tin');
        } finally {
            setUpdating(false);
        }
    };

    const handleCancelEdit = () => {
        setIsEditing(false);
        setSelectedImage(null);
        if (userProfile) {
            setEditForm({
                fullName: userProfile.fullName || '',
                email: userProfile.email || '',
                phone: userProfile.phone || '',
                dob: userProfile.dob || '',
                address: userProfile.address || '',
                district: userProfile.district || '',
                city: userProfile.city || '',
                gender: userProfile.gender || ''
            });
            setPreviewImage(userProfile.img || '');
        }
        setError('');
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Đang tải thông tin người dùng...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            {isLoggedIn ? (
                <div className="max-w-4xl mx-auto px-4">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-lg shadow-lg p-6 mb-8 text-white">
                        <h1 className="text-3xl font-bold">Thông Tin Cá Nhân</h1>
                        <p className="mt-2 opacity-90">Quản lý thông tin tài khoản CGV của bạn</p>
                    </div>

                    {/* Success/Error Messages */}
                    {success && (
                        <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg">
                            <div className="flex items-center">
                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                {success}
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                            <div className="flex items-center">
                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                </svg>
                                {error}
                            </div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Avatar Section */}
                        <div className="lg:col-span-1">
                            <div className="bg-white rounded-lg shadow-md p-6">
                                <div className="text-center">
                                    <div className="relative inline-block">
                                        <img
                                            src={previewImage || userProfile?.img || `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile?.fullName || 'User')}&size=200&background=ef4444&color=fff&bold=true`}
                                            alt="Avatar"
                                            className="w-40 h-40 rounded-full object-cover border-4 border-red-100 shadow-lg mx-auto"
                                            onError={(e) => {
                                                const target = e.target as HTMLImageElement;
                                                target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile?.fullName || 'User')}&size=200&background=ef4444&color=fff&bold=true`;
                                            }}
                                        />
                                        {isEditing && (
                                            <label className="absolute bottom-2 right-2 bg-red-600 text-white p-2 rounded-full cursor-pointer hover:bg-red-700 transition-colors shadow-lg">
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                                                </svg>
                                                <input
                                                    type="file"
                                                    accept="image/jpeg,image/png,image/jpg,image/webp"
                                                    onChange={handleImageChange}
                                                    className="hidden"
                                                    id="avatar-upload"
                                                />
                                            </label>
                                        )}
                                    </div>
                                    <h2 className="mt-4 text-xl font-semibold text-gray-800 truncate">{userProfile?.fullName}</h2>
                                    <p className="text-gray-600 text-sm truncate" title={userProfile?.email}>{userProfile?.email}</p>
                                    {userProfile?.phone && (
                                        <p className="text-gray-600 mt-1 truncate">{userProfile.phone}</p>
                                    )}
                                    {selectedImage && (
                                        <p className="text-green-600 text-xs mt-2">Ảnh mới đã được chọn ✓</p>
                                    )}
                                </div>
                                
                                {/* Upload section when editing */}
                                {isEditing && (
                                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Cập nhật ảnh đại diện
                                        </label>
                                        <div className="flex items-center justify-center w-full">
                                            <label htmlFor="avatar-upload-main" className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
                                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                                    <svg className="w-8 h-8 mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                                    </svg>
                                                    <p className="mb-2 text-sm text-gray-500">
                                                        <span className="font-semibold">Click để chọn ảnh</span> hoặc kéo thả
                                                    </p>
                                                    <p className="text-xs text-gray-500">PNG, JPG, WEBP (MAX. 5MB)</p>
                                                </div>
                                                <input 
                                                    id="avatar-upload-main" 
                                                    type="file" 
                                                    accept="image/jpeg,image/png,image/jpg,image/webp"
                                                    onChange={handleImageChange}
                                                    className="hidden" 
                                                />
                                            </label>
                                        </div>
                                        {selectedImage && (
                                            <div className="mt-3 text-sm text-green-600">
                                                ✓ Đã chọn: {selectedImage.name} ({Math.round(selectedImage.size / 1024)} KB)
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Profile Information */}
                        <div className="lg:col-span-2">
                            <div className="bg-white rounded-lg shadow-md p-6">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-xl font-semibold text-gray-800">Thông Tin Chi Tiết</h3>
                                    {!isEditing ? (
                                        <button
                                            onClick={() => setIsEditing(true)}
                                            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
                                        >
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                            </svg>
                                            Chỉnh sửa
                                        </button>
                                    ) : (
                                        <div className="flex gap-2">
                                            <button
                                                onClick={handleCancelEdit}
                                                disabled={updating}
                                                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
                                            >
                                                Hủy
                                            </button>
                                            <button
                                                onClick={handleSaveProfile}
                                                disabled={updating}
                                                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                                            >
                                                {updating ? (
                                                    <>
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                                        Đang lưu...
                                                    </>
                                                ) : (
                                                    <>
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                        </svg>
                                                        Lưu thay đổi
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    )}
                                </div>

                                {!isEditing ? (
                                    // Display mode
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-600 mb-1">Họ và tên</label>
                                                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg min-h-[3rem] flex items-center truncate" title={userProfile?.fullName}>{userProfile?.fullName || 'Chưa cập nhật'}</p>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-600 mb-1">Email</label>
                                                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg text-sm min-h-[3rem] flex items-center truncate" title={userProfile?.email}>{userProfile?.email || 'Chưa cập nhật'}</p>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-600 mb-1">Số điện thoại</label>
                                                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg min-h-[3rem] flex items-center truncate" title={userProfile?.phone}>{userProfile?.phone || 'Chưa cập nhật'}</p>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-600 mb-1">Giới tính</label>
                                                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg min-h-[3rem] flex items-center">
                                                    {userProfile?.gender === 'MALE' ? 'Nam' : userProfile?.gender === 'FEMALE' ? 'Nữ' : 'Chưa cập nhật'}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-600 mb-1">Ngày sinh</label>
                                                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg min-h-[3rem] flex items-center">
                                                    {userProfile?.dob ? new Date(userProfile.dob).toLocaleDateString('vi-VN') : 'Chưa cập nhật'}
                                                </p>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-600 mb-1">Địa chỉ</label>
                                                <div className="text-gray-900 bg-gray-50 p-3 rounded-lg min-h-[3rem] flex items-start">
                                                    <p className="line-clamp-2 leading-relaxed" title={userProfile?.address}>{userProfile?.address || 'Chưa cập nhật'}</p>
                                                </div>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-600 mb-1">Quận/Huyện</label>
                                                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg min-h-[3rem] flex items-center truncate" title={userProfile?.district}>{userProfile?.district || 'Chưa cập nhật'}</p>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-600 mb-1">Thành phố</label>
                                                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg min-h-[3rem] flex items-center truncate" title={userProfile?.city}>{userProfile?.city || 'Chưa cập nhật'}</p>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    // Edit mode
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Họ và tên *</label>
                                                <input
                                                    type="text"
                                                    name="fullName"
                                                    value={editForm.fullName}
                                                    onChange={handleInputChange}
                                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                                    placeholder="Nhập họ và tên"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
                                                <input
                                                    type="email"
                                                    name="email"
                                                    value={editForm.email}
                                                    onChange={handleInputChange}
                                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent text-sm"
                                                    placeholder="Nhập email"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Số điện thoại</label>
                                                <input
                                                    type="text"
                                                    name="phone"
                                                    value={editForm.phone}
                                                    onChange={handleInputChange}
                                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                                    placeholder="Nhập số điện thoại"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Giới tính</label>
                                                <select
                                                    name="gender"
                                                    value={editForm.gender}
                                                    onChange={handleInputChange}
                                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                                >
                                                    <option value="">Chọn giới tính</option>
                                                    <option value="MALE">Nam</option>
                                                    <option value="FEMALE">Nữ</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Ngày sinh</label>
                                                <input
                                                    type="date"
                                                    name="dob"
                                                    value={editForm.dob}
                                                    onChange={handleInputChange}
                                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Địa chỉ</label>
                                                <textarea
                                                    name="address"
                                                    value={editForm.address}
                                                    onChange={handleInputChange}
                                                    rows={2}
                                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none"
                                                    placeholder="Nhập địa chỉ"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Quận/Huyện</label>
                                                <input
                                                    type="text"
                                                    name="district"
                                                    value={editForm.district}
                                                    onChange={handleInputChange}
                                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                                    placeholder="Nhập quận/huyện"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Thành phố</label>
                                                <input
                                                    type="text"
                                                    name="city"
                                                    value={editForm.city}
                                                    onChange={handleInputChange}
                                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                                    placeholder="Nhập thành phố"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="min-h-screen flex items-center justify-center bg-gray-50">
                    <div className="bg-white p-8 rounded-lg shadow-md text-center max-w-md w-full mx-4">
                        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                        </div>
                        <h1 className="text-2xl font-bold text-gray-800 mb-2">Bạn chưa đăng nhập</h1>
                        <p className="text-gray-600 mb-6">Vui lòng đăng nhập để xem và chỉnh sửa thông tin cá nhân của bạn.</p>
                        <button
                            onClick={() => navigate('/login')}
                            className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors w-full font-medium"
                        >
                            Đăng nhập ngay
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Profile;