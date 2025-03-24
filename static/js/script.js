/**
 * Основной JavaScript-файл для лендинга Ассенизатор НН
 * Содержит все необходимые скрипты для функционирования страницы
 * Версия: 2.0 (2025)
 */

// Дождемся полной загрузки документа
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация библиотеки анимаций AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            offset: 100,
            once: true
        });
    }
    
    // Прелоадер
    const preloader = document.querySelector('.preloader');
    if (preloader) {
        window.addEventListener('load', function() {
            setTimeout(function() {
                preloader.classList.add('hidden');
            }, 500);
        });
    }
    
    // Функция для проверки и исправления логотипа
    function checkAndFixLogo() {
        // Найти все логотипы на странице
        const logos = document.querySelectorAll('.logo-img, .footer__logo');
        
        logos.forEach(logo => {
            // Обработчик ошибки загрузки изображения
            logo.onerror = function() {
                console.error('Ошибка загрузки логотипа');
                // Замена на запасной вариант логотипа
                this.src = '/static/images/maz 16m.jpg';
                // Убедимся, что размеры установлены
                this.style.width = this.classList.contains('footer__logo') ? '80px' : '60px';
                this.style.height = this.classList.contains('footer__logo') ? '80px' : '60px';
                this.style.objectFit = 'contain';
            };
            
            // Обработчик успешной загрузки
            logo.onload = function() {
                // Если изображение загрузилось, но его размеры неправильные
                if (this.naturalWidth < 20 || this.naturalHeight < 20) {
                    console.warn('Логотип слишком маленький, применяем стили');
                    this.style.width = this.classList.contains('footer__logo') ? '80px' : '60px';
                    this.style.height = this.classList.contains('footer__logo') ? '80px' : '60px';
                }
            };
            
            // Запустить проверку, если изображение уже загружено
            if (logo.complete) {
                logo.onload();
            }
        });
    }
    
    // Запустить функцию после загрузки страницы
    checkAndFixLogo();
    
    // Добавить favicon динамически, если его нет
    function addFavicon() {
        let favicon = document.querySelector('link[rel="icon"]');
        if (!favicon) {
            favicon = document.createElement('link');
            favicon.rel = 'icon';
            favicon.href = '/static/image/logo.jpg';
            favicon.type = 'image/jpg';
            document.head.appendChild(favicon);
        }
    }
    
    addFavicon();
    
    // Мобильное меню
    const menuToggle = document.getElementById('menuToggle');
    const mainNav = document.getElementById('mainNav');
    
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('active');
            document.body.classList.toggle('menu-open');
            
            // Изменяем иконку меню
            const spans = this.querySelectorAll('span');
            spans.forEach(span => span.classList.toggle('active'));
            
            if (mainNav.classList.contains('active')) {
                // Создаем затемненный фон
                const overlay = document.createElement('div');
                overlay.className = 'menu-overlay';
                document.body.appendChild(overlay);
                
                // Добавляем обработчик клика по затемненному фону
                overlay.addEventListener('click', function() {
                    mainNav.classList.remove('active');
                    document.body.classList.remove('menu-open');
                    spans.forEach(span => span.classList.remove('active'));
                    this.remove();
                });
            } else {
                // Удаляем затемненный фон
                const overlay = document.querySelector('.menu-overlay');
                if (overlay) {
                    overlay.remove();
                }
            }
        });
        
        // Закрытие меню при клике на пункт меню
        const navLinks = mainNav.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                mainNav.classList.remove('active');
                document.body.classList.remove('menu-open');
                const spans = menuToggle.querySelectorAll('span');
                spans.forEach(span => span.classList.remove('active'));
                const overlay = document.querySelector('.menu-overlay');
                if (overlay) {
                    overlay.remove();
                }
            });
        });
    }
    
    // Плавная прокрутка к секциям
    const smoothLinks = document.querySelectorAll('a[href^="#"]');
    smoothLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const id = this.getAttribute('href');
            
            if (id === '#') return;
            
            const targetElement = document.querySelector(id);
            if (targetElement) {
                const headerHeight = document.querySelector('.header') ? document.querySelector('.header').offsetHeight : 0;
                window.scrollTo({
                    top: targetElement.offsetTop - headerHeight - 20, // Отступ для хедера
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Кнопка прокрутки вверх
    const scrollToTopBtn = document.getElementById('scrollToTop');
    if (scrollToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                scrollToTopBtn.classList.add('visible');
            } else {
                scrollToTopBtn.classList.remove('visible');
            }
        });
        
        scrollToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Слайдер отзывов
    const reviewsTrack = document.getElementById('reviewsTrack');
    const reviewsPrev = document.getElementById('reviewsPrev');
    const reviewsNext = document.getElementById('reviewsNext');
    const reviewsDots = document.getElementById('reviewsDots');
    
    if (reviewsTrack && reviewsPrev && reviewsNext && reviewsDots) {
        const reviewCards = reviewsTrack.querySelectorAll('.review-card');
        let currentSlide = 0;
        let autoSlideTimer = null;
        
        // Создаем точки-индикаторы
        reviewCards.forEach((_, index) => {
            const dot = document.createElement('div');
            dot.className = 'reviews__dot';
            dot.setAttribute('aria-label', `Отзыв ${index + 1}`);
            if (index === 0) {
                dot.classList.add('active');
            }
            dot.addEventListener('click', () => {
                goToSlide(index);
                resetAutoSlideTimer();
            });
            reviewsDots.appendChild(dot);
        });
        
        // Функция переключения слайда
        function goToSlide(index) {
            if (index < 0) {
                index = reviewCards.length - 1;
            } else if (index >= reviewCards.length) {
                index = 0;
            }
            
            reviewsTrack.style.transform = `translateX(-${index * 100}%)`;
            currentSlide = index;
            
            // Обновляем активную точку
            const dots = reviewsDots.querySelectorAll('.reviews__dot');
            dots.forEach((dot, i) => {
                if (i === index) {
                    dot.classList.add('active');
                    dot.setAttribute('aria-current', 'true');
                } else {
                    dot.classList.remove('active');
                    dot.removeAttribute('aria-current');
                }
            });
            
            // Устанавливаем подсказки aria
            reviewCards.forEach((card, i) => {
                if (i === index) {
                    card.setAttribute('aria-hidden', 'false');
                } else {
                    card.setAttribute('aria-hidden', 'true');
                }
            });
        }
        
        // Сброс и перезапуск таймера автопрокрутки
        function resetAutoSlideTimer() {
            if (autoSlideTimer) {
                clearInterval(autoSlideTimer);
            }
            
            autoSlideTimer = setInterval(() => {
                goToSlide(currentSlide + 1);
            }, 6000);
        }
        
        // Обработчики кнопок
        reviewsPrev.addEventListener('click', () => {
            goToSlide(currentSlide - 1);
            resetAutoSlideTimer();
        });
        
        reviewsNext.addEventListener('click', () => {
            goToSlide(currentSlide + 1);
            resetAutoSlideTimer();
        });
        
        // Остановка слайдера при наведении
        reviewsTrack.addEventListener('mouseenter', () => {
            if (autoSlideTimer) {
                clearInterval(autoSlideTimer);
                autoSlideTimer = null;
            }
        });
        
        // Возобновление слайдера при уходе мыши
        reviewsTrack.addEventListener('mouseleave', () => {
            resetAutoSlideTimer();
        });
        
        // Запуск автопрокрутки
        resetAutoSlideTimer();
        
        // Инициализация первого слайда для доступности
        reviewCards.forEach((card, i) => {
            card.setAttribute('aria-hidden', i === 0 ? 'false' : 'true');
        });
    }
    
    // FAQ аккордеон
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-item__question');
        const answer = item.querySelector('.faq-item__answer');
        
        // Улучшаем доступность
        if (question && answer) {
            const questionId = question.getAttribute('aria-controls');
            if (!questionId && answer.id) {
                question.setAttribute('aria-controls', answer.id);
            } else if (!questionId) {
                const newId = 'faq-answer-' + Math.random().toString(36).substring(2, 9);
                answer.id = newId;
                question.setAttribute('aria-controls', newId);
            }
            
            question.setAttribute('aria-expanded', 'false');
            question.setAttribute('role', 'button');
            question.setAttribute('tabindex', '0');
            
            // Добавляем обработку клавиатуры
            question.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    question.click();
                }
            });
        }
        
        question.addEventListener('click', () => {
            // Если текущий элемент уже активен, закрываем его
            const isActive = item.classList.contains('active');
            
            // Обновляем состояние aria-expanded
            question.setAttribute('aria-expanded', !isActive);
            
            // Закрываем все элементы
            faqItems.forEach(otherItem => {
                if (otherItem !== item && otherItem.classList.contains('active')) {
                    otherItem.classList.remove('active');
                    const otherQuestion = otherItem.querySelector('.faq-item__question');
                    if (otherQuestion) {
                        otherQuestion.setAttribute('aria-expanded', 'false');
                    }
                    const otherAnswer = otherItem.querySelector('.faq-item__answer');
                    if (otherAnswer) {
                        otherAnswer.style.maxHeight = '0';
                    }
                }
            });
            
            // Если элемент не был активен, открываем его
            if (!isActive) {
                item.classList.add('active');
                answer.style.maxHeight = answer.scrollHeight + 'px';
            } else {
                item.classList.remove('active');
                answer.style.maxHeight = '0';
            }
        });
    });
    
    // Обработка отправки формы с улучшенной защитой от двойной отправки
    const orderForm = document.getElementById('orderForm');
    const formMessage = document.getElementById('formMessage');
    const successOverlay = document.getElementById('success-overlay');
    
    if (orderForm && formMessage) {
        // Создаем скрытое поле для идентификатора формы, если его нет
        let formIdInput = orderForm.querySelector('input[name="form_id"]');
        if (!formIdInput) {
            formIdInput = document.createElement('input');
            formIdInput.type = 'hidden';
            formIdInput.name = 'form_id';
            orderForm.appendChild(formIdInput);
        }
        
        // Генерируем уникальный ID для формы
        formIdInput.value = Date.now().toString() + Math.random().toString(36).substring(2, 9);
        
        // Флаг для отслеживания отправки
        let isSubmitting = false;
        
        // Удаляем предыдущий обработчик и добавляем новый
        const oldForm = orderForm;
        const newForm = oldForm.cloneNode(true);
        oldForm.parentNode.replaceChild(newForm, oldForm);
        
        // Обновляем ссылки после клонирования
        const refreshedForm = document.getElementById('orderForm');
        const submitButton = refreshedForm.querySelector('button[type="submit"]');
        formIdInput = refreshedForm.querySelector('input[name="form_id"]');
        
        refreshedForm.addEventListener('submit', function(e) {
            // Предотвращаем стандартное поведение формы
            e.preventDefault();
            
            // Проверяем, не отправляется ли уже форма
            if (isSubmitting) {
                console.log('Форма уже отправляется, игнорируем повторную отправку');
                return false;
            }
            
            // Валидация формы
            const nameInput = this.querySelector('#name');
            const phoneInput = this.querySelector('#phone');
            
            if (!nameInput || !nameInput.value.trim()) {
                formMessage.innerHTML = 'Пожалуйста, укажите ваше имя';
                formMessage.className = 'form-message error';
                formMessage.style.display = 'block';
                return false;
            }
            
            // Упрощенная проверка телефона
            if (!phoneInput) return false;
            const phoneValue = phoneInput.value.replace(/\D/g, '');
            if (phoneValue.length < 11) {
                formMessage.innerHTML = 'Пожалуйста, укажите корректный номер телефона';
                formMessage.className = 'form-message error';
                formMessage.style.display = 'block';
                return false;
            }
            
            // Устанавливаем флаг отправки
            isSubmitting = true;
            
            // Блокируем кнопку отправки
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = 'Отправка...';
            }
            
            // Показываем индикатор загрузки
            formMessage.innerHTML = 'Отправка заявки...';
            formMessage.className = 'form-message';
            formMessage.style.display = 'block';
            
            // Получаем данные формы
            const formData = new FormData(this);
            
            // Отправляем AJAX-запрос
            fetch('/submit-form', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Снимаем флаг отправки
                isSubmitting = false;
                
                // Разблокируем кнопку
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Отправить заявку';
                }
                
                if (data.success) {
                    // Успешная отправка - показываем анимацию
                    formMessage.style.display = 'none';
                    
                    // Сбрасываем форму
                    refreshedForm.reset();
                    
                    // Генерируем новый ID для следующей отправки
                    formIdInput.value = Date.now().toString() + Math.random().toString(36).substring(2, 9);
                    
                    // Показываем оверлей с галочкой
                    if (successOverlay) {
                        successOverlay.style.display = 'flex';
                        
                        // Прячем анимацию через 3 секунды
                        setTimeout(() => {
                            successOverlay.style.display = 'none';
                        }, 3000);
                    }
                } else {
                    // Ошибка при отправке
                    formMessage.innerHTML = '<strong>Произошла ошибка!</strong><br>' + (data.message || 'Пожалуйста, позвоните нам напрямую.');
                    formMessage.className = 'form-message error';
                }
            })
            .catch(error => {
                // Снимаем флаг отправки
                isSubmitting = false;
                
                // Разблокируем кнопку
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Отправить заявку';
                }
                
                // Техническая ошибка
                console.error('Ошибка:', error);
                formMessage.innerHTML = '<strong>Ошибка соединения!</strong><br>Пожалуйста, позвоните нам: +7 (953) 415-96-96';
                formMessage.className = 'form-message error';
            });
        });
    }
    
    // Маска для телефона
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        // Устанавливаем начальное значение
        if (!phoneInput.value) {
            phoneInput.value = '+7 (';
        }
        
        // Обработчик событий ввода
        phoneInput.addEventListener('input', function(e) {
            let x = e.target.value.replace(/\D/g, '').match(/(\d{0,1})(\d{0,3})(\d{0,3})(\d{0,2})(\d{0,2})/);
            
            // Если первая цифра не 7, то заменяем на 7 (для России)
            if (x[1] && x[1] !== '7') {
                x[1] = '7';
            }
            
            e.target.value = !x[2] ? '+7 (' : '+' + x[1] + ' (' + x[2] + ') ' + (x[3] ? x[3] + '-' + x[4] : (x[3] ? x[3] : '')) + (x[5] ? '-' + x[5] : '');
        });
        
        // При фокусе, если поле пустое, добавляем начало номера
        phoneInput.addEventListener('focus', function(e) {
            if (!e.target.value) {
                e.target.value = '+7 (';
            }
        });
        
        // При потере фокуса, если номер не полный, очищаем поле
        phoneInput.addEventListener('blur', function(e) {
            if (e.target.value === '+7 (') {
                e.target.value = '';
            }
        });
    }
    
    // Анимированные счетчики для преимуществ
    const animateCounter = (el, target, duration) => {
        if (!el) return;
        
        let start = 0;
        const step = timestamp => {
            if (!start) start = timestamp;
            const progress = Math.min((timestamp - start) / duration, 1);
            el.innerText = Math.floor(progress * target);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                el.innerText = target;
            }
        };
        window.requestAnimationFrame(step);
    };
    
    // Запуск анимации при прокрутке до элемента с опытом
    const experienceElement = document.getElementById('years-experience');
    if (experienceElement) {
        // Используем IntersectionObserver, если он поддерживается браузером
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // Получаем число из строки (например, "16 лет опыта")
                        const text = experienceElement.innerText;
                        const match = text.match(/(\d+)/);
                        if (match && match[1]) {
                            const number = parseInt(match[1]);
                            const html = experienceElement.innerHTML;
                            experienceElement.innerHTML = html.replace(number, '<span id="experience-counter">0</span>');
                            const counterEl = document.getElementById('experience-counter');
                            if (counterEl) {
                                animateCounter(counterEl, number, 2000);
                            }
                        }
                        observer.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1
            });
            observer.observe(experienceElement);
        } else {
            // Запасной вариант для старых браузеров
            window.addEventListener('scroll', function checkScroll() {
                const rect = experienceElement.getBoundingClientRect();
                if (rect.top <= window.innerHeight && rect.bottom >= 0) {
                    const text = experienceElement.innerText;
                    const match = text.match(/(\d+)/);
                    if (match && match[1]) {
                        const number = parseInt(match[1]);
                        const html = experienceElement.innerHTML;
                        experienceElement.innerHTML = html.replace(number, '<span id="experience-counter">0</span>');
                        const counterEl = document.getElementById('experience-counter');
                        if (counterEl) {
                            animateCounter(counterEl, number, 2000);
                        }
                    }
                    window.removeEventListener('scroll', checkScroll);
                }
            });
        }
    }
    
    // Добавляем эффект параллакса на главном баннере
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        window.addEventListener('scroll', () => {
            const scrollPosition = window.pageYOffset;
            if (scrollPosition < heroSection.offsetHeight) {
                const yPos = -(scrollPosition * 0.3);
                heroSection.style.backgroundPosition = `center ${yPos}px`;
            }
        });
    }
    
    // Динамическое изменение высоты хедера при прокрутке
    const header = document.querySelector('.header');
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 100) {
                header.classList.add('header--scrolled');
            } else {
                header.classList.remove('header--scrolled');
            }
        });
    }
    
    // Ленивая загрузка изображений для повышения производительности
    function lazyLoadImages() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const src = img.getAttribute('data-src');
                        if (src) {
                            img.src = src;
                            img.removeAttribute('data-src');
                        }
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => {
                imageObserver.observe(img);
            });
        } else {
            // Запасной вариант для старых браузеров
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => {
                img.src = img.getAttribute('data-src');
                img.removeAttribute('data-src');
            });
        }
    }
    
    // Запуск ленивой загрузки изображений
    lazyLoadImages();
});