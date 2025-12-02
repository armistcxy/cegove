import React from "react";
import { Link } from 'react-router-dom';
import logo from '../../assets/cgvlogo.png';
import muaVeNgay from '../../assets/mua-ve_ngay.png';

import "./Header.css";

export default function Header() {
  return (
    <div className="header">
      <div className="header-mini">
        <ul>
          <li><a href="#">đăng nhập/đăng ký</a></li>
        </ul>
      </div>

      <div className="header-main">
        <div className="menu-header">
          <ul className="parent">
            <li><Link to="/homepage" className="logo"><img src={logo} alt="logo" /></Link></li>
            <li className="hover-effect">
              phim
              <ul className="child-menu">
                <li><Link to="/movie" className="hover-red">Phim đang chiếu</Link></li>
                <li><a href="#" className="hover-red">Phim sắp chiếu</a></li>
              </ul>
            </li>
            <li className="hover-effect">
              rạp cgv
              <ul className="child-menu">
                <li><a href="#" className="hover-red">Tất cả các rạp</a></li>
                <li><a href="#" className="hover-red">Rạp đặc biệt</a></li>
                <li><a href="#" className="hover-red">Rạp sắp mở</a></li>
              </ul>
            </li>
            <li className="hover-effect">
              thành viên
              <ul className="child-menu">
                <li><a href="#" className="hover-red">Tài khoản CGV</a></li>
                <li><a href="#" className="hover-red">Quyền lợi</a></li>
              </ul>
            </li>
          </ul>

          <div className="search-buy-infor">
            <a href="#" className="mua-ve"><img src={muaVeNgay} alt="" /></a>
          </div>
        </div>
      </div>

    
    </div>
  );
}
