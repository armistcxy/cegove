import React, { useState, useRef, useEffect } from "react";
import slide1 from '../../assets/slide1-new.png';
import slide2 from '../../assets/slide2.png';
import slide3 from '../../assets/slide3.jpg';
import slide4 from '../../assets/slide4.jpg';
import slide5 from '../../assets/slide5.jpg';
import h3Event from '../../assets/h3_event.gif';
import h3MovieSelection from '../../assets/h3_movie_selection.gif';
import captainMarvel from '../../assets/captainmarvel_combo_240x201.jpg';
import web13 from '../../assets/web_240x201_13.jpg';
import gudetama2 from '../../assets/gudetama2_240-x-201.jpg';
import sjora from '../../assets/sjora_240x201.jpg';
import waffle from '../../assets/waffle_240-x-201.jpg';
import photoTicket from '../../assets/phototicket---496x247_1.jpg';
import "./HomePage.module.css";
import { movieList as initialMovieList } from "./HomePageLogic";

export default function HomePage() {
  const [movies] = useState(initialMovieList);
  // Slider refs & indices
  const menuNeRef = useRef<HTMLDivElement | null>(null);
  const postersRef = useRef<HTMLDivElement | null>(null);
  const abvRef = useRef<HTMLUListElement | null>(null);

  const [slideIndex, setSlideIndex] = useState(0);
  const [movieIndex, setMovieIndex] = useState(0);
  const [abvIndex, setAbvIndex] = useState(0);

  // constants
  const SLIDE_WIDTH = 980;
  const MOVIE_SPACE = 246;
  const ABV_SPACE = 247;

  useEffect(() => {
    if (menuNeRef.current) {
      menuNeRef.current.style.transition = "transform 0.4s";
      menuNeRef.current.style.transform = `translateX(${ -slideIndex * SLIDE_WIDTH }px)`;
    }
  }, [slideIndex]);

  useEffect(() => {
    if (postersRef.current) {
      postersRef.current.style.transition = "transform 1s";
      postersRef.current.style.transform = `translateX(${ -movieIndex * MOVIE_SPACE }px)`;
    }
  }, [movieIndex]);

  useEffect(() => {
    if (abvRef.current) {
      abvRef.current.style.transition = "transform 1s";
      abvRef.current.style.transform = `translateX(${ -abvIndex * ABV_SPACE }px)`;
    }
  }, [abvIndex]);

  function handleNextSlide() {
    const list = menuNeRef.current?.querySelectorAll('li') ?? [];
    if (slideIndex >= list.length - 1) return;
    setSlideIndex(prev => prev + 1);
  }

  function handlePrevSlide() {
    if (slideIndex <= 0) return;
    setSlideIndex(prev => prev - 1);
  }

  function handleNextMovie() {
    const list = postersRef.current?.querySelectorAll('.poster-movie') ?? [];
    // allow sliding until last visible
    if (movieIndex >= Math.max(0, list.length - 4)) return;
    const nextIndex = movieIndex + 1;
    setMovieIndex(nextIndex);
    
    // Show/hide navigation buttons
    const prevBtn = document.getElementById('prev-movie');
    const nextBtn = document.getElementById('next-movie');
    if (prevBtn) prevBtn.style.display = 'block';
    if (nextBtn && nextIndex >= Math.max(0, list.length - 4)) nextBtn.style.display = 'none';
  }

  function handlePrevMovie() {
    if (movieIndex <= 0) return;
    const prevIndex = movieIndex - 1;
    setMovieIndex(prevIndex);
    
    // Show/hide navigation buttons
    const prevBtn = document.getElementById('prev-movie');
    const nextBtn = document.getElementById('next-movie');
    if (nextBtn) nextBtn.style.display = 'block';
    if (prevBtn && prevIndex <= 0) prevBtn.style.display = 'none';
  }

  function handleNextAbv() {
  const list = abvRef.current?.querySelectorAll('li') ?? [];
  const visibleCount = 4; // số ảnh hiển thị cùng lúc

  if (abvIndex >= list.length - visibleCount) return; // dừng khi ảnh cuối đã hiển thị

  const nextIndex = abvIndex + 1;
  setAbvIndex(nextIndex);

  // Show/hide navigation buttons
  const prevBtn = document.getElementById('prev-adv');
  const nextBtn = document.getElementById('next-adv');

  if (prevBtn) prevBtn.style.display = 'block';
  if (nextBtn && nextIndex >= list.length - visibleCount) nextBtn.style.display = 'none';
}


  function handlePrevAbv() {
    if (abvIndex <= 0) return;
    const prevIndex = abvIndex - 1;
    setAbvIndex(prevIndex);
    
    // Show/hide navigation buttons
    const prevBtn = document.getElementById('prev-adv');
    const nextBtn = document.getElementById('next-adv');
    if (nextBtn) nextBtn.style.display = 'block';
    if (prevBtn && prevIndex <= 0) prevBtn.style.display = 'none';
  }

  return (
    <div className="HomePage">
      {/* SLIDER */}
      <div className="slide">
        <div className="slide-quang-cao parent">
          <div className="menu-ne" ref={menuNeRef}>
            <ul className="slide-container">
              <li><img src={slide5} alt="" /></li>
              <li><img src={slide1} alt="" /></li>
              <li><img src={slide2} alt="" /></li>
              <li><img src={slide3} alt="" /></li>
              <li><img src={slide4} alt="" /></li>
            </ul>
          </div>
          <button className="next child-abs hover-effect" onClick={handleNextSlide}>
            <i className="fas fa-chevron-right" style={{ fontSize: 48, color: "#e6e6e6" }}></i>
          </button>
          <button className="prev child-abs hover-effect" onClick={handlePrevSlide}>
            <i className="fas fa-chevron-left" style={{ fontSize: 48, color: "#e7e7e7" }}></i>
          </button>
        </div>
      </div>

      
      {/* EVENTS */}
      <div className="home-movie-selector">
        <div className="home-title">
          <img src={h3Event} alt="" />
        </div>
      </div>

      <div className="quang-cao">
  <div className="parent">
    <div className="content-quang-cao">
      <ul className="abv-content" ref={abvRef}>
        <li><img src={captainMarvel} alt="" /></li>
        <li><img src={web13} alt="" /></li>
        <li><img src={gudetama2} alt="" /></li>
        <li><img src={sjora} alt="" /></li>
        <li><img src={waffle} alt="" /></li>
      </ul>
      <div id="prev-adv" className="child-abs prev" onClick={handlePrevAbv}>
        {/* <i className="fas fa-chevron-left" style={{ fontSize: 24, color: "white" }}></i> */}
      </div>
      <div id="next-adv" className="child-abs next" onClick={handleNextAbv}>
        {/* <i className="fas fa-chevron-right" style={{ fontSize: 24, color: "white" }}></i> */}
      </div>
    </div>
  </div>
</div>


      {/* TICKET */}
      <div className="ticket-couples">
        <div className="content-ticket">
          <a href="#"><img src={photoTicket} alt="" /></a>
        </div>
      </div>

    {/* MOVIE SELECTION */}
      <div className="home-movie-selector">
        <div className="home-title">
          <img src={h3MovieSelection} alt="" />
        </div>
      </div>

      {/* MOVIES */}
      <div className="container-movie">
        <div className="menu-movie parent">
          <div className="slide-movie" ref={postersRef}>
            {movies.map(movie => (
              <div key={movie.id} className="poster-movie parent hover-effect">
                <div className={`rating-${movie.rating} child-abs`}></div>
                <img src={movie.img} alt={movie.name} className="poster-off-movie" />
                <div className="infor-buyticket child-abs hover-effect movie-banner">
                  <div className="infor-movie">
                    <div className="name-movie">{movie.name}</div>
                    <div className="gr-button">
                      <a href="#" className="xem-chi-tiet">Xem chi tiết</a>
                      <a href="#" className="buy-ticket">
                        <div className="icon-call"></div>
                        Mua vé
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <button id="next-movie" className="child-abs next" onClick={handleNextMovie}>
            <i className="fas fa-chevron-right" style={{ fontSize: 24, color: "white" }}></i>
          </button>
          <button id="prev-movie" className="child-abs prev" onClick={handlePrevMovie} style={{display: 'none'}}>
            <i className="fas fa-chevron-left" style={{ fontSize: 24, color: "white" }}></i>
          </button>
        </div>
      </div>

      {/* FOOTER */}
      <div className="footer-content">
        <div className="footer-brand-slide">
          <ul className="list-brand-film">
            {Array.from({ length: 8 }).map((_, i) => (
              <li key={i}><a id={`brand-${i + 1}`} href="#"></a></li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
