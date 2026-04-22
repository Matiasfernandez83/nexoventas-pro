document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // 1. LÓGICA DE FILTRADO (Grilla)
    // ==========================================
    const botonesFiltro = document.querySelectorAll('.btn-filtro');
    const tarjetasNormal= document.querySelectorAll('.tarjeta-normal');

    botonesFiltro.forEach(boton => {
        boton.addEventListener('click', () => {
            botonesFiltro.forEach(b => b.classList.remove('active'));
            boton.classList.add('active');

            const categoriaFiltro = boton.getAttribute('data-categoria');

            tarjetasNormal.forEach(tarjeta => {
                tarjeta.style.opacity = '0';
                tarjeta.style.transform = 'scale(0.95)';
                
                setTimeout(() => {
                    const categoriaProducto = tarjeta.getAttribute('data-categoria');
                    
                    if (categoriaFiltro === 'todos' || categoriaFiltro === categoriaProducto) {
                        tarjeta.style.display = 'flex';
                        setTimeout(() => {
                            tarjeta.style.opacity = '1';
                            tarjeta.style.transform = 'scale(1)';
                        }, 50);
                    } else {
                        tarjeta.style.display = 'none';
                    }
                }, 300);
            });
        });
    });

    // ==========================================
    // 2. LÓGICA DEL CARRUSEL PRINCIPAL
    // ==========================================
    const slides = document.querySelectorAll('.slide');
    const dots = document.querySelectorAll('.dot');
    const prevBtn = document.querySelector('.prev');
    const nextBtn = document.querySelector('.next');
    const carouselInner = document.querySelector('.carousel-inner');
    
    let currentSlide = 0;
    const totalSlides = slides.length;
    let autoSlideInterval;

    function moveCarousel(direction) {
        if (direction === 'next') {
            currentSlide = (currentSlide + 1) % totalSlides;
        } else if (direction === 'prev') {
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
        } else {
            currentSlide = direction; // Saltos por Dots
        }
        
        updateCarousel();
    }

    function updateCarousel() {
        if(!carouselInner) return;
        
        // Mover el offset horizontal multiplicando por 100% el offset actual.
        // Dado que usamos flex en carousel-inner, podemos mover con translateX
        carouselInner.style.transform = `translateX(-${currentSlide * 100}%)`;
        
        // Actualizar active classes
        slides.forEach((slide, index) => {
            slide.classList.toggle('active', index === currentSlide);
        });
        
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentSlide);
        });

        // Actualizar contador
        const counter = document.getElementById('slideCounter');
        if (counter) counter.textContent = currentSlide + 1;
    }

    function startAutoSlide() {
        stopAutoSlide(); // Prevenir duplicados
        autoSlideInterval = setInterval(() => {
            moveCarousel('next');
        }, 5000); // 5 segundos
    }

    function stopAutoSlide() {
        clearInterval(autoSlideInterval);
    }

    // Event Listeners Carrusel
    if (prevBtn && nextBtn) {
        prevBtn.addEventListener('click', () => {
            moveCarousel('prev');
            startAutoSlide(); // Reiniciar timer tras click manual
        });

        nextBtn.addEventListener('click', () => {
            moveCarousel('next');
            startAutoSlide();
        });

        dots.forEach(dot => {
            dot.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-slide'));
                moveCarousel(index);
                startAutoSlide();
            });
        });

        // Pausar auto slide si el usuario pasa el mouse
        const carousel = document.querySelector('.carousel');
        if(carousel){
            carousel.addEventListener('mouseenter', stopAutoSlide);
            carousel.addEventListener('mouseleave', startAutoSlide);
        }

        // Iniciar
        startAutoSlide();
    }
});
