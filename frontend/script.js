const searchResults = document.querySelector('.search-results');
const inputBox = document.querySelector('.search-input');
const API_KEY = 'this_is_a_secret_key_for_getting_movie_recommendations';

async function callMovieSearchAPI(query) {
    const moviesapi = `http://127.0.0.1:8000/search?q=${query}`;
    const apiResponse = await fetch(moviesapi, {
        headers: { 'x-api-key': API_KEY }
    }); 
    moviesData = await apiResponse.json();
    console.log("Movies data:", moviesData);
    if (!moviesData || moviesData.length === 0){
        return [];
    }
    return moviesData;
}

function debounce(func, delay) {
    let timeoutId;
    return function(...args){
        if(timeoutId) {
            clearTimeout(timeoutId);
        }
        timeoutId = setTimeout(() => {
            func(...args);
        }, delay);
    }
}

const debouncedSearch = debounce(async (query) => {
    const movies = await callMovieSearchAPI(query);
    let resultMovies = [];
    resultMovies = Array.from(movies).map(function(movie) {
            return '<li onclick=selectInput(this)>' + movie + '</li>';
        });
        
    if(resultMovies.length !== 0) {
        searchResults.innerHTML = '<ul>' + resultMovies.join('') + '</ul>';
    }else{
        searchResults.innerHTML = '';
    }
}, 500);

inputBox.addEventListener('keyup', function() {
    let query = inputBox.value;
    console.log("Input query:", query);
    if (query.length > 0) {
        debouncedSearch(query);
    }
    else {
        searchResults.innerHTML = '';
    }
});

function selectInput(element) {
    let selectMovie = element.textContent;
    inputBox.value = selectMovie;
    searchResults.innerHTML = '';
}

function showSkeletonCards(count = 6) {
    const recommendationsSection = document.querySelector('.recommendations');
    recommendationsSection.style.display = 'block';
    const grid = document.querySelector('.recommendations-grid');
    grid.innerHTML = '';
    grid.style.transform = 'translateX(0)';
    clearMessage();

    for (let i = 0; i < count; i++) {
        const skeleton = document.createElement('div');
        skeleton.classList.add('movie-card', 'skeleton-card');
        skeleton.innerHTML = `
            <div class="poster-wrapper skeleton-poster"></div>
            <div class="movie-info">
                <div class="skeleton-line short"></div>
                <div class="skeleton-line"></div>
            </div>`;
        grid.appendChild(skeleton);
    }
}

function showMessage(text, type = 'error') {
    clearMessage();
    const hero = document.querySelector('.hero');
    const msg = document.createElement('div');
    msg.classList.add('status-message', type);
    msg.textContent = text;
    hero.appendChild(msg);
}

function clearMessage() {
    const existing = document.querySelector('.status-message');
    if (existing) existing.remove();
}

async function getRecommendations() {
    const movieTitle = inputBox.value;
    if (!movieTitle.trim()) return;

    showSkeletonCards();

    try {
        const recommendationsAPI = `http://127.0.0.1:8000/recommend?title=${encodeURIComponent(movieTitle)}`;

        const recommendations = await fetch(recommendationsAPI, {
            headers: { 'x-api-key': API_KEY }
        });
        const recommendedMovies = await recommendations.json();
        console.log("Recommended Movies:", recommendedMovies);

        if (recommendedMovies.detail) {
            document.querySelector('.recommendations').style.display = 'none';
            showMessage(recommendedMovies.detail, 'error');
            return;
        }

        if (!recommendedMovies.recommendations || recommendedMovies.recommendations.length === 0) {
            document.querySelector('.recommendations').style.display = 'none';
            showMessage(`No recommendations found for "${movieTitle}". Try a different movie.`, 'error');
            return;
        }

        clearMessage();
        const grid = document.querySelector('.recommendations-grid');
        grid.innerHTML = '';

        recommendedMovies.recommendations.forEach(movie => {
            const movieCard = document.createElement('div');
            movieCard.classList.add('movie-card');

            movieCard.innerHTML = `
                <div class="poster-wrapper">
                    <img src="${movie.poster_url}" alt="${movie.title}" class="poster">
                </div>
                <div class="movie-info">
                    <div class="rating">
                        <span class="star">⭐</span> ${parseFloat(movie.rating).toFixed(2)}
                    </div>
                    <h4 class="movie-title">${movie.title}</h4>
                </div>`;

            movieCard.addEventListener('click', () => openPopup(movie));
            grid.appendChild(movieCard);
        });

        initializeCarousel();
    } catch (error) {
        console.error("Error fetching recommendations:", error);
        document.querySelector('.recommendations').style.display = 'none';
        showMessage('Something went wrong while fetching recommendations. Please try again later.', 'error');
    }
}

function initializeCarousel() {
    const carousel = document.querySelector('.recommendations-carousel');
    const grid = document.querySelector('.recommendations-grid');
    const prevArrow = document.querySelector('.prev-arrow');
    const nextArrow = document.querySelector('.next-arrow');
    const movieCards = document.querySelectorAll('.movie-card');
    
    const totalCards = movieCards.length;
    const visibleCards = 6; // Number of cards visible at a time
    let currentIndex = 0; // Tracks the current position of the carousel

    // Function to update the carousel's position
    function updateCarousel() {
        const cardWidth = movieCards[0].offsetWidth; // Get the width of a single card
        const gap = parseInt(window.getComputedStyle(grid).gap); // Get the gap between cards
        const moveDistance = cardWidth + gap; // Calculate the total distance to move
        grid.style.transform = `translateX(-${currentIndex * moveDistance}px)`; // Apply the transformation
    }

    // Event listener for the next arrow
    nextArrow.addEventListener('click', () => {
        if (currentIndex < totalCards - visibleCards) {
            currentIndex++; // Move to the next set of cards
            updateCarousel();
        }
    });

    // Event listener for the previous arrow
    prevArrow.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--; // Move to the previous set of cards
            updateCarousel();
        }
    });

    // Optional: Recalculate on window resize to maintain responsiveness
    window.addEventListener('resize', updateCarousel);
}

function openPopup(movie) {
    const popup = document.getElementById('movie-popup');
    document.querySelector('.popup-poster img').src = movie.poster_url;
    document.querySelector('.popup-title').textContent = movie.title;
    document.querySelector('.popup-year').textContent = `(${movie.year})`;
    document.querySelector('.popup-rating').textContent = `⭐ ${parseFloat(movie.rating).toFixed(2)}`;
    document.querySelector('.popup-runtime').textContent = `${movie.runtime} min`;
    document.querySelector('.popup-summary').textContent = movie.summary;
    document.querySelector('.popup-director').innerHTML = `<strong>Director:</strong> ${movie.director}`;
    document.querySelector('.popup-actors').innerHTML = `<strong>Actors:</strong> ${movie.actors}`;

    // Render tags as badges
    const tagsContainer = document.querySelector('.popup-tags');
    tagsContainer.innerHTML = '';
    if (movie.tags) {
        const tagList = movie.tags.split(',').map(t => t.trim()).filter(Boolean);
        tagList.forEach(tag => {
            const badge = document.createElement('span');
            badge.classList.add('popup-tag');
            badge.textContent = tag;
            tagsContainer.appendChild(badge);
        });
    }

    // Trailer link
    const trailerLink = document.querySelector('.popup-trailer');
    if (movie.trailer_url) {
        trailerLink.href = movie.trailer_url;
        trailerLink.style.display = 'inline-flex';
    } else {
        const searchQuery = encodeURIComponent(`${movie.title} ${movie.year} official trailer`);
        trailerLink.href = `https://www.youtube.com/results?search_query=${searchQuery}`;
        trailerLink.style.display = 'inline-flex';
    }

    popup.style.display = 'flex';
}

function closePopup() {
    const popup = document.getElementById('movie-popup');
    popup.style.display = 'none';
}

document.querySelector('.close-button').addEventListener('click', closePopup);

window.addEventListener('click', (event) => {
    const popup = document.getElementById('movie-popup');
    if (event.target == popup) {
        closePopup();
    }
});

// AI Mode toast
document.getElementById('themeToggle').addEventListener('click', () => {
    showToast('🚧 AI Mode is coming soon — we\'re working on it!');
});

function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.classList.add('toast');
    toast.textContent = message;
    document.body.appendChild(toast);

    // trigger reflow for animation
    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
