import React from "react";
import { Link } from 'react-router-dom';
import logo from '../../assets/cgvlogo.png';
import muaVeNgay from '../../assets/mua-ve_ngay.png';

import "./Header.module.css";

export default function Header() {
  return (
    <div className="header">
      <div className="header-mini">
        <ul>
          <li><Link to="/NotAvailable">đăng nhập/đăng ký</Link></li>
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
                <li><Link to="/NotAvailable" className="hover-red">Phim sắp chiếu</Link></li>
              </ul> 
            </li>
            <li className="hover-effect">
              rạp cgv
              <ul className="child-menu">
                <li><Link to="/NotAvailable" className="hover-red">Tất cả các rạp</Link></li>
                <li><Link to="/NotAvailable" className="hover-red">Rạp đặc biệt</Link></li>
                <li><Link to="/NotAvailable" className="hover-red">Rạp sắp mở</Link></li>
              </ul>
            </li> 
            <li className="hover-effect">
              thành viên
              <ul className="child-menu">
                <li><Link to="/NotAvailable" className="hover-red">Tài khoản CGV</Link></li>
                <li><Link to="/NotAvailable" className="hover-red">Quyền lợi</Link></li>
              </ul>
            </li>
          </ul>

          <div className="search-buy-infor">
            <Link to="/NotAvailable" className="mua-ve"><img src={muaVeNgay} alt="" /></Link>
          </div>
        </div>
      </div>

    
    </div>
  );
}
