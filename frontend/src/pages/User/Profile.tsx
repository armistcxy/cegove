import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {useUser} from "../../context/UserContext.tsx";

const Profile = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { isLoggedIn, userProfile, refreshUserProfile } = useUser();

    const [loading, setLoading] = useState<boolean>(false);

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

    if (loading) {
        return <div>Đang tải thông tin người dùng...</div>;
    }

    return (
        <div style={{ padding: 20 }}>
            {isLoggedIn ? (
                <>
                    <h1>Hồ sơ người dùng</h1>
                    <div>
                        <p><strong>Họ tên:</strong> {userProfile.fullName}</p>
                        <p><strong>Email:</strong> {userProfile.email}</p>
                    </div>
                </>

            ) : (
                <>
                    <h1>Bạn chưa đăng nhập</h1>
                    <p>Vui lòng <a href="/login">đăng nhập</a> để xem hồ sơ của bạn.</p>
                </>
            )}
        </div>
    );
};

export default Profile;