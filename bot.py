<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>wait | otklix</title>
    <style>
        /* ===== ОСНОВНЫЕ СТИЛИ ===== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            text-align: center;
            overflow: hidden;
            position: relative;
        }

        /* ============================================
                   ЗАДНИЙ ПЛАН (как на Aqua-Cookies)
                   ============================================ */

        /* 1. Основной фон с затемнением */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background:
                radial-gradient(ellipse at 20% 50%, rgba(88, 166, 255, 0.08) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 50%, rgba(240, 136, 62, 0.06) 0%, transparent 60%),
                radial-gradient(ellipse at 50% 100%, rgba(88, 166, 255, 0.04) 0%, transparent 50%);
            z-index: 0;
            pointer-events: none;
        }

        /* 2. Декоративные градиентные линии (как на Aqua-Cookies) */
        .bg-lines {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
            opacity: 0.4;
        }

        .bg-line {
            position: absolute;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(88, 166, 255, 0.3), rgba(240, 136, 62, 0.3), transparent);
            border-radius: 50%;
            animation: lineFloat 8s ease-in-out infinite alternate;
        }

        .bg-line:nth-child(1) {
            top: 10%;
            left: -10%;
            width: 40%;
            animation-delay: 0s;
        }
        .bg-line:nth-child(2) {
            top: 30%;
            right: -10%;
            width: 35%;
            animation-delay: 2s;
            background: linear-gradient(90deg, transparent, rgba(240, 136, 62, 0.2), rgba(88, 166, 255, 0.2), transparent);
        }
        .bg-line:nth-child(3) {
            top: 55%;
            left: -5%;
            width: 30%;
            animation-delay: 4s;
        }
        .bg-line:nth-child(4) {
            top: 75%;
            right: -5%;
            width: 45%;
            animation-delay: 1s;
            background: linear-gradient(90deg, transparent, rgba(240, 136, 62, 0.15), rgba(88, 166, 255, 0.15), transparent);
        }
        .bg-line:nth-child(5) {
            top: 90%;
            left: 10%;
            width: 25%;
            animation-delay: 3s;
        }

        @keyframes lineFloat {
            0% {
                transform: translateX(0) scaleX(1);
                opacity: 0.3;
            }
            50% {
                transform: translateX(30px) scaleX(1.2);
                opacity: 0.7;
            }
            100% {
                transform: translateX(-20px) scaleX(0.8);
                opacity: 0.3;
            }
        }

        /* 3. Частицы (звёздочки) */
        #particles-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
        }

        /* ============================================
                   КОНТЕНТ
                   ============================================ */

        .container {
            position: relative;
            z-index: 1;
            max-width: 600px;
            width: 100%;
        }

        /* ===== АНИМАЦИЯ ПРИВЕТСТВИЯ ===== */
        .hero {
            margin-bottom: 2rem;
        }

        .welcome-text {
            font-size: 1.2rem;
            font-weight: 300;
            letter-spacing: 4px;
            color: #58a6ff;
            opacity: 0;
            animation: fadeIn 0.8s ease forwards;
            animation-delay: 0.2s;
        }

        .main-title {
            font-size: 4rem;
            font-weight: 800;
            letter-spacing: 2px;
            margin-top: 0.5rem;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.1rem;
        }

        .letter {
            display: inline-block;
            opacity: 0;
            transform: translateY(20px);
            animation: letterAppear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
            color: #ffffff;
        }

        .letter.gradient {
            background: linear-gradient(135deg, #58a6ff, #f0883e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .letter.white {
            color: #ffffff;
        }

        .letter.pipe {
            color: #8b949e;
            font-weight: 300;
        }

        @keyframes letterAppear {
            0% {
                opacity: 0;
                transform: translateY(20px) scale(0.8);
                filter: blur(4px);
            }
            60% {
                opacity: 1;
                transform: translateY(-5px) scale(1.05);
                filter: blur(0);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1);
                filter: blur(0);
            }
        }

        @keyframes fadeIn {
            0% {
                opacity: 0;
                transform: translateY(-10px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* ===== КАРТОЧКА ===== */
        .card {
            background: rgba(22, 27, 34, 0.75);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 2.5rem 2rem;
            border: 1px solid rgba(255, 255, 255, 0.06);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
            opacity: 0;
            animation: fadeIn 1s ease forwards;
            animation-delay: 2.8s;
        }

        /* ===== СТАТУС ===== */
        .status {
            background: rgba(13, 17, 23, 0.7);
            border-radius: 12px;
            padding: 0.8rem 1.2rem;
            margin: 1rem 0;
            border-left: 3px solid #3fb950;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }

        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #3fb950;
            border-radius: 50%;
            animation: pulse-dot 2s infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.8); }
        }

        .status-text {
            color: #7ee787;
            font-weight: 500;
        }

        /* ===== ФИЧИ ===== */
        .features {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin: 1.2rem 0;
            font-size: 0.9rem;
        }

        .features span {
            background: rgba(13, 17, 23, 0.6);
            padding: 8px 14px;
            border-radius: 8px;
            border: 1px solid #21262d;
            transition: all 0.3s ease;
        }

        .features span:hover {
            border-color: #58a6ff;
            background: rgba(88, 166, 255, 0.05);
            transform: translateX(3px);
        }

        /* ===== КНОПКИ ===== */
        .btn-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 1.2rem;
        }

        .btn {
            display: inline-block;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            font-size: 0.95rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, #238636, #2ea043);
            color: #fff;
        }

        .btn-primary:hover {
            transform: scale(1.02);
            box-shadow: 0 0 30px rgba(35, 134, 54, 0.3);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: #8b949e;
            border: 1px solid #30363d;
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: #58a6ff;
            color: #c9d1d9;
        }

        .btn-row {
            display: flex;
            gap: 10px;
        }
        .btn-row .btn {
            flex: 1;
            text-align: center;
        }

        .footer {
            margin-top: 1.5rem;
            font-size: 0.75rem;
            color: #484f58;
        }

        /* ===== АДАПТИВНОСТЬ ===== */
        @media (max-width: 480px) {
            .main-title {
                font-size: 2.5rem;
            }
            .card {
                padding: 1.5rem;
            }
            .features {
                grid-template-columns: 1fr;
            }
            .btn-row {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>

    <!-- ===== ЗАДНИЙ ПЛАН ===== -->

    <!-- Градиентные линии -->
    <div class="bg-lines">
        <div class="bg-line"></div>
        <div class="bg-line"></div>
        <div class="bg-line"></div>
        <div class="bg-line"></div>
        <div class="bg-line"></div>
    </div>

    <!-- Частицы -->
    <canvas id="particles-canvas"></canvas>

    <!-- ===== КОНТЕНТ ===== -->
    <div class="container">

        <!-- Приветствие -->
        <div class="hero">
            <div class="welcome-text">welcome</div>
            <div class="main-title">
                <span class="letter gradient">w</span>
                <span class="letter gradient">a</span>
                <span class="letter gradient">i</span>
                <span class="letter gradient">t</span>
                <span class="letter pipe" style="animation-delay: 0.6s;">&nbsp;|&nbsp;</span>
                <span class="letter white" style="animation-delay: 0.7s;">o</span>
                <span class="letter white" style="animation-delay: 0.8s;">t</span>
                <span class="letter white" style="animation-delay: 0.9s;">k</span>
                <span class="letter white" style="animation-delay: 1.0s;">l</span>
                <span class="letter white" style="animation-delay: 1.1s;">i</span>
                <span class="letter white" style="animation-delay: 1.2s;">x</span>
            </div>
        </div>

        <!-- Карточка -->
        <div class="card">
            <div class="status">
                <span class="status-dot"></span>
                <span class="status-text">Бот активен</span>
                <span style="color:#8b949e; font-size:0.75rem;">(GitHub Actions)</span>
            </div>

            <div class="features">
                <span>🔍 Проверка ников</span>
                <span>🚀 Создание каналов</span>
                <span>👑 Передача прав</span>
                <span>⚡ Fragment.com</span>
            </div>

            <div class="btn-group">
                <a href="#" class="btn btn-primary" id="botLink">🤖 Открыть бота</a>
                <div class="btn-row">
                    <a href="https://github.com/otklix/wait" target="_blank" class="btn btn-secondary">📦 GitHub</a>
                    <a href="https://github.com/otklix/wait/issues" target="_blank" class="btn btn-secondary">🐛 Баги</a>
                </div>
            </div>

            <div class="footer">
                otklix · 2026
            </div>
        </div>
    </div>

    <!-- ===== СКРИПТЫ ===== -->
    <script>
        // ===========================
        // 1. ЧАСТИЦЫ
        // ===========================
        const canvas = document.getElementById('particles-canvas');
        const ctx = canvas.getContext('2d');
        let width, height, particles;

        function resizeCanvas() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        class Particle {
            constructor() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.size = Math.random() * 2.5 + 0.5;
                this.speedX = (Math.random() - 0.5) * 0.3;
                this.speedY = (Math.random() - 0.5) * 0.3;
                this.opacity = Math.random() * 0.3 + 0.1;
            }

            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                if (this.x > width) this.x = 0;
                if (this.x < 0) this.x = width;
                if (this.y > height) this.y = 0;
                if (this.y < 0) this.y = height;
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
                ctx.fill();
            }
        }

        particles = [];
        for (let i = 0; i < 80; i++) {
            particles.push(new Particle());
        }

        function animateParticles() {
            ctx.clearRect(0, 0, width, height);
            particles.forEach(p => {
                p.update();
                p.draw();
            });
            requestAnimationFrame(animateParticles);
        }
        animateParticles();

        // ===========================
        // 2. АНИМАЦИЯ БУКВ
        // ===========================
        document.addEventListener('DOMContentLoaded', () => {
            const letters = document.querySelectorAll('.letter:not(.pipe)');
            letters.forEach((el, i) => {
                el.style.animationDelay = `${i * 0.12 + 0.5}s`;
            });
        });

        // ===========================
        // 3. ССЫЛКА НА БОТА
        // ===========================
        document.getElementById('botLink').href = 'https://t.me/Username1FinderBOT';
    </script>

</body>
</html>