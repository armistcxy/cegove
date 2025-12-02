        // HomePageLogic.ts
import movie1 from '../../assets/240_10_27.jpg';
import movie2 from '../../assets/240_10_47.jpg';
import movie3 from '../../assets/240_12_3.jpg';
import movie4 from '../../assets/240_14_19.jpg';
import movie5 from '../../assets/240_12_6.jpg';

// TypeScript interfaces
export interface Movie {
  id: number;
  name: string;
  img: string;
  rating: string;
}

// Slider configuration constants
export const SLIDE_CONFIG = {
  SLIDE_WIDTH: 980,
  MOVIE_SPACE: 246,
  ABV_SPACE: 247,
  TRANSITION_DURATION: '0.4s',
  MOVIE_TRANSITION_DURATION: '1s'
} as const;

// Movie data with imported images
export const movieList: Movie[] = [
  { id: 1, name: "Captain Marvel", img: movie1, rating: "P" },
  { id: 2, name: "Chị trợ lý của anh", img: movie2, rating: "13" },
  { id: 3, name: "Hai Phượng", img: movie3, rating: "18" },
  { id: 4, name: "Mật vụ thanh trừng", img: movie4, rating: "18" },
  { id: 5, name: "Công viên kỳ diệu", img: movie5, rating: "P" },
  { id: 6, name: "Yêu nhầm bạn thân", img: movie1, rating: "16" },
  { id: 7, name: "Hạnh phúc của mẹ", img: movie1, rating: "13" },
];

// Slider state management class
export class SliderController {
  private slideIndex: number = 0;
  private movieIndex: number = 0;
  private abvIndex: number = 0;

  // TODO: Hiệu ứng trượt slide quảng cáo trên đầu : slide vòng
  public nextSlide(slideContainer: HTMLElement | null, slideCount: number): number {
    if (!slideContainer || this.slideIndex >= slideCount - 1) return this.slideIndex;
    
    this.slideIndex++;
    slideContainer.style.transition = SLIDE_CONFIG.TRANSITION_DURATION;
    slideContainer.style.transform = `translateX(${-this.slideIndex * SLIDE_CONFIG.SLIDE_WIDTH}px)`;
    
    return this.slideIndex;
  }

  public prevSlide(slideContainer: HTMLElement | null): number {
    if (!slideContainer || this.slideIndex <= 0) return this.slideIndex;
    
    this.slideIndex--;
    slideContainer.style.transition = SLIDE_CONFIG.TRANSITION_DURATION;
    slideContainer.style.transform = `translateX(${-this.slideIndex * SLIDE_CONFIG.SLIDE_WIDTH}px)`;
    
    return this.slideIndex;
  }

  // TODO: Hiệu ứng trượt slide chọn phim
  public nextMovie(movieContainer: HTMLElement | null, movieCount: number): { index: number; shouldHideNext: boolean; shouldShowPrev: boolean } {
    if (!movieContainer || this.movieIndex >= movieCount - 3) {
      return { index: this.movieIndex, shouldHideNext: false, shouldShowPrev: false };
    }
    
    movieContainer.style.transition = SLIDE_CONFIG.MOVIE_TRANSITION_DURATION;
    this.movieIndex++;
    movieContainer.style.transform = `translateX(${-this.movieIndex * SLIDE_CONFIG.MOVIE_SPACE}px)`;
    
    console.log(`Movie index: ${this.movieIndex}`);
    
    return {
      index: this.movieIndex,
      shouldHideNext: this.movieIndex >= 3,
      shouldShowPrev: true
    };
  }

  public prevMovie(movieContainer: HTMLElement | null): { index: number; shouldHidePrev: boolean; shouldShowNext: boolean } {
    if (!movieContainer || this.movieIndex <= 0) {
      return { index: this.movieIndex, shouldHidePrev: false, shouldShowNext: false };
    }
    
    movieContainer.style.transition = SLIDE_CONFIG.MOVIE_TRANSITION_DURATION;
    this.movieIndex--;
    movieContainer.style.transform = `translateX(${-this.movieIndex * SLIDE_CONFIG.MOVIE_SPACE}px)`;
    
    return {
      index: this.movieIndex,
      shouldHidePrev: this.movieIndex <= 0,
      shouldShowNext: true
    };
  }

  // TODO: Hiệu ứng trượt slide quảng cáo : kế thừa từ hiệu ứng trên
  public nextAbv(abvContainer: HTMLElement | null, abvCount: number): { index: number; shouldHideNext: boolean; shouldShowPrev: boolean } {
    if (!abvContainer || this.abvIndex >= abvCount - 1) {
      return { index: this.abvIndex, shouldHideNext: false, shouldShowPrev: false };
    }
    
    abvContainer.style.transition = SLIDE_CONFIG.MOVIE_TRANSITION_DURATION;
    this.abvIndex++;
    abvContainer.style.transform = `translateX(${-this.abvIndex * SLIDE_CONFIG.ABV_SPACE}px)`;
    
    console.log(`ABV index: ${this.abvIndex}`);
    
    return {
      index: this.abvIndex,
      shouldHideNext: this.abvIndex >= 1,
      shouldShowPrev: true
    };
  }

  public prevAbv(abvContainer: HTMLElement | null): { index: number; shouldHidePrev: boolean; shouldShowNext: boolean } {
    if (!abvContainer || this.abvIndex <= 0) {
      return { index: this.abvIndex, shouldHidePrev: false, shouldShowNext: false };
    }
    
    abvContainer.style.transition = SLIDE_CONFIG.MOVIE_TRANSITION_DURATION;
    this.abvIndex--;
    abvContainer.style.transform = `translateX(${-this.abvIndex * SLIDE_CONFIG.ABV_SPACE}px)`;
    
    return {
      index: this.abvIndex,
      shouldHidePrev: this.abvIndex <= 0,
      shouldShowNext: true
    };
  }

  // Handle infinite slide loop (converted from transitionend logic)
  public handleSlideTransitionEnd(
    slideContainer: HTMLElement,
    currentSlide: HTMLElement,
    slideCount: number
  ): void {
    if (currentSlide.id === 'lastClone') {
      console.log(`${this.slideIndex} last`);
      slideContainer.style.transition = 'transform 0s';
      this.slideIndex = slideCount - 2;
      slideContainer.style.transform = `translateX(${-this.slideIndex * SLIDE_CONFIG.SLIDE_WIDTH}px)`;
    }
    
    if (currentSlide.id === 'firstClone') {
      console.log(`${this.slideIndex} first`);
      slideContainer.style.transition = 'transform 0s';
      this.slideIndex = slideCount - this.slideIndex;
      slideContainer.style.transform = `translateX(${-this.slideIndex * SLIDE_CONFIG.SLIDE_WIDTH}px)`;
    }
  }

  // Getters for current indices
  public getCurrentSlideIndex(): number {
    return this.slideIndex;
  }

  public getCurrentMovieIndex(): number {
    return this.movieIndex;
  }

  public getCurrentAbvIndex(): number {
    return this.abvIndex;
  }

  // Reset methods
  public resetSlideIndex(): void {
    this.slideIndex = 0;
  }

  public resetMovieIndex(): void {
    this.movieIndex = 0;
  }

  public resetAbvIndex(): void {
    this.abvIndex = 0;
  }
}

// Export singleton instance for use in React components
export const sliderController = new SliderController();