import { Link } from 'react-router-dom';
import logo from '../../assets/cgvlogo.png';
import muaVeNgay from '../../assets/mua-ve_ngay.png';

import "./Header.module.css";
import {useUser} from "../../context/UserContext.tsx";

export default function Header() {
    const { isLoggedIn, userProfile, handleLogout } = useUser();

  return (
    <div className="header">
      <div className="header-mini">
          {isLoggedIn ? (
              <ul className="flex items-center gap-6">
                  {/* <li className="flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                      </svg>
                      <Link to="/promotions" className="hover:text-red-600 transition">
                          TIN MỚI & ƯU ĐÃI
                      </Link>
                  </li> */}
                  <li className="flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                      </svg>
                      <Link to="/my-tickets" className="hover:text-red-600 transition">
                          VÉ CỦA TÔI
                      </Link>
                  </li>
                  <li className="flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <div className="relative group">
                          <button className="hover:text-red-600 transition flex items-center gap-1">
                              XIN CHÀO, {userProfile.fullName?.toUpperCase() || 'NGƯỜI DÙNG'}
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                          </button>
                          {/* Dropdown menu */}
                          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                              <Link to="/profile" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-t-lg transition">
                                  Thông tin cá nhân
                              </Link>
                              {/*<Link to="/order-history" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 transition">*/}
                              {/*    Lịch sử đặt vé*/}
                              {/*</Link>*/}
                              <button
                                  onClick={handleLogout}
                                  className="w-full text-left px-4 py-2 text-red-600 hover:bg-gray-100 rounded-b-lg transition"
                              >
                                  Đăng xuất
                              </button>
                          </div>
                      </div>
                  </li>
              </ul>
          ) : (
              <ul>
                  <li><Link to="/login">đăng nhập/đăng ký</Link></li>
              </ul>

          )}
      </div>

      <div className="header-main">
        <div className="menu-header">
          <ul className="parent">
            <li><Link to="/homepage" className="logo"><img src={logo} alt="logo" /></Link></li>
            <li className="hover-effect">
              phim
              <ul className="child-menu">
                <li><Link to="/movie" className="hover-red">Danh sách phim</Link></li>
                <li><Link to="/recent-movie" className="hover-red">Phim đang chiếu</Link></li>
                <li><Link to="/movies-for-you" className="hover-red">Dành cho bạn</Link></li>
              </ul>
            </li>
            <li className="hover-effect">
              rạp cgv
              <ul className="child-menu">
                <li><Link to="/cinema" className="hover-red">Tất cả các rạp</Link></li>
                {/* <li><Link to="/NotAvailable" className="hover-red">Rạp đặc biệt</Link></li>
                <li><Link to="/NotAvailable" className="hover-red">Rạp sắp mở</Link></li> */}
              </ul>
            </li> 
            <li className="hover-effect">
              thành viên
              <ul className="child-menu">
                <li><Link to="/profile" className="hover-red">Tài khoản CGV</Link></li>
                {/* <li><Link to="/NotAvailable" className="hover-red">Quyền lợi</Link></li> */}
              </ul>
            </li>
          </ul>

          <div className="search-buy-infor">
            <Link to="/Movie" className="mua-ve"><img src={muaVeNgay} alt="" /></Link>
          </div>
        </div>
      </div>

    
    </div>
  );
}
