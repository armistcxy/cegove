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
import MovieGrid, { RecentMovieGrid } from "../../components/MovieGrid";

export default function HomePage() {
  // Slider refs & indices (kept only what's needed)
  const menuNeRef = useRef<HTMLDivElement | null>(null);
  const abvRef = useRef<HTMLUListElement | null>(null);
  const autoSlideRef = useRef<NodeJS.Timeout | null>(null);

  const [slideIndex, setSlideIndex] = useState(0);
  const [abvIndex, setAbvIndex] = useState(0);
  const [isAutoSliding, setIsAutoSliding] = useState(true);

  // constants
  const getSlideWidth = () => {
    return window.innerWidth > 1200 ? 980 : window.innerWidth;
  };
  const ABV_SPACE = 247; // 240px width + 7px margin
  const SLIDE_COUNT = 5; // Total number of slides

  // Auto-slide functionality
  const startAutoSlide = () => {
    if (autoSlideRef.current) {
      clearInterval(autoSlideRef.current);
    }
    autoSlideRef.current = setInterval(() => {
      if (isAutoSliding) {
        setSlideIndex(prev => prev + 1);
      }
    }, 4000); // Change slide every 4 seconds
  };

  const stopAutoSlide = () => {
    if (autoSlideRef.current) {
      clearInterval(autoSlideRef.current);
      autoSlideRef.current = null;
    }
  };

  useEffect(() => {
    startAutoSlide();
    return () => stopAutoSlide();
  }, [isAutoSliding]);

  useEffect(() => {
    if (menuNeRef.current) {
      const slideWidth = getSlideWidth();
      
      if (slideIndex === SLIDE_COUNT) {
        menuNeRef.current.style.transition = "none";
        setSlideIndex(0);
        menuNeRef.current.style.transform = `translateX(0px)`;
        
        setTimeout(() => {
          if (menuNeRef.current) {
            menuNeRef.current.style.transition = "transform 0.8s ease-in-out";
          }
        }, 50);
      } else {
        // Normal smooth transition
        menuNeRef.current.style.transition = "transform 0.8s ease-in-out";
        menuNeRef.current.style.transform = `translateX(-${slideIndex * slideWidth}px)`;
      }
    }
  }, [slideIndex]);

  useEffect(() => {
    if (abvRef.current) {
      abvRef.current.style.transition = "transform 1s";
      abvRef.current.style.transform = `translateX(${ -abvIndex * ABV_SPACE }px)`;
    }
  }, [abvIndex]);

  function handleNextSlide() {
    setSlideIndex(prev => prev + 1);
    
    setIsAutoSliding(false);
    setTimeout(() => setIsAutoSliding(true), 5000);
  }

  function handlePrevSlide() {
    setSlideIndex(prev => prev - 1);
    
    setIsAutoSliding(false);
    setTimeout(() => setIsAutoSliding(true), 5000);
  }

  function handleNextAbv() {
  const list = abvRef.current?.querySelectorAll('li') ?? [];
  const visibleCount = 4; 

  if (abvIndex >= list.length - visibleCount) return; 

  const nextIndex = abvIndex + 1;
  setAbvIndex(nextIndex);

  const prevBtn = document.getElementById('prev-adv');
  const nextBtn = document.getElementById('next-adv');

  if (prevBtn) prevBtn.style.display = 'block';
  if (nextBtn && nextIndex >= list.length - visibleCount) nextBtn.style.display = 'none';
}


  function handlePrevAbv() {
    if (abvIndex <= 0) return;
    const prevIndex = abvIndex - 1;
    setAbvIndex(prevIndex);
    
    const prevBtn = document.getElementById('prev-adv');
    const nextBtn = document.getElementById('next-adv');
    if (nextBtn) nextBtn.style.display = 'block';
    if (prevBtn && prevIndex <= 0) prevBtn.style.display = 'none';
  }

  return (
    <div className="HomePage">
      {/* SLIDER */}
      <div className="slide">
        <div 
          className="slide-quang-cao parent"
          onMouseEnter={() => setIsAutoSliding(false)}
          onMouseLeave={() => setIsAutoSliding(true)}
        >
          <div className="menu-ne" ref={menuNeRef}>
            <ul className="slide-container">
              <li><img src={slide5} alt="" /></li>
              <li><img src={slide1} alt="" /></li>
              <li><img src={slide2} alt="" /></li>
              <li><img src={slide3} alt="" /></li>
              <li><img src={slide4} alt="" /></li>
              {/* Duplicate first slide for smooth infinite loop */}
              <li><img src={slide5} alt="" /></li>
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

      {/* MOVIES - New Grid Component (Recent Movies) */}
      <RecentMovieGrid
        title=""
        limit={8}
        showTitle={false}
        gridColumns={4}
      />

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
