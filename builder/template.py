# HTML template components for the Go Textbook

HTML_HEAD = """<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Go Backend Engineering: 01. Пакеты и модули (91/91)</title>
    
    <!-- Google Fonts: Roboto & Roboto Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,300;0,400;0,500;0,700;1,400&family=Roboto+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
    <!-- Cascadia Code CDN Font -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fontsource/cascadia-code@5.0.1/index.min.css">
    
    <!-- Prism Syntax Highlighting Dark Theme -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">

    <style>
        :root {
            --bg-body: #090d16;
            --bg-surface: #0f172a;
            --bg-card: #131d33;
            --bg-card-hover: #182440;
            --border-color: #1e293b;
            --border-active: #38bdf8;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --go-cyan: #00ADD8;
            --go-blue: #007d9c;
            --accent-emerald: #10b981;
            --accent-purple: #a855f7;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --sidebar-width: 320px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        html {
            scroll-behavior: smooth;
            background-color: var(--bg-body);
            color: var(--text-primary);
        }

        body {
            font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.65;
            background-color: var(--bg-body);
            color: var(--text-primary);
            overflow-x: hidden;
        }

        code, pre, .mono {
            font-family: 'Cascadia Code', 'Roboto Mono', Consolas, 'Fira Code', monospace;
        }

        /* Progress Bar */
        #progress-bar {
            position: fixed;
            top: 0;
            left: 0;
            height: 3px;
            background: linear-gradient(90deg, #00ADD8, #38bdf8, #818cf8, #c084fc);
            z-index: 1000;
            width: 0%;
            transition: width 0.1s ease-out;
        }

        /* App Layout */
        .app-container {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar Navigation */
        .sidebar {
            width: var(--sidebar-width);
            background-color: var(--bg-surface);
            border-right: 1px solid var(--border-color);
            position: fixed;
            top: 0;
            bottom: 0;
            left: 0;
            display: flex;
            flex-direction: column;
            z-index: 100;
            transition: transform 0.3s ease;
        }

        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
        }

        .logo-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-primary);
            text-decoration: none;
        }

        .go-logo-icon {
            background: #00ADD8;
            color: #000;
            font-weight: 900;
            font-size: 0.8rem;
            padding: 2px 6px;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }

        .sidebar-search {
            margin-top: 14px;
            position: relative;
        }

        .sidebar-search input {
            width: 100%;
            padding: 9px 12px 9px 34px;
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            color: #f1f5f9;
            font-size: 0.88rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .sidebar-search input:focus {
            border-color: var(--go-cyan);
            box-shadow: 0 0 0 2px rgba(0, 173, 216, 0.2);
        }

        .search-icon {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 0.9rem;
            pointer-events: none;
        }

        .sidebar-nav {
            flex: 1;
            overflow-y: auto;
            padding: 16px 12px;
            scroll-behavior: smooth;
        }

        .sidebar-nav::-webkit-scrollbar {
            width: 6px;
        }
        .sidebar-nav::-webkit-scrollbar-thumb {
            background-color: #334155;
            border-radius: 3px;
        }

        .nav-group-title {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            padding: 8px 10px;
            margin-top: 10px;
        }

        .chapter-link {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 10px;
            margin-bottom: 2px;
            border-radius: 6px;
            color: #e2e8f0;
            text-decoration: none;
            font-size: 0.88rem;
            transition: all 0.15s ease;
        }

        .chapter-link:hover {
            background-color: rgba(56, 189, 248, 0.08);
            color: #ffffff;
        }

        .chapter-link.active {
            background-color: rgba(0, 173, 216, 0.15);
            color: #38bdf8;
            font-weight: 500;
            border-left: 3px solid var(--go-cyan);
            cursor: pointer;
            user-select: none;
        }

        .status-badge {
            font-size: 0.68rem;
            padding: 2px 6px;
            border-radius: 10px;
            font-weight: 500;
        }

        .status-badge.done {
            background-color: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-badge.soon {
            background-color: rgba(100, 116, 139, 0.15);
            color: #94a3b8;
            border: 1px solid rgba(100, 116, 139, 0.2);
        }

        .sub-exercises-list {
            padding-left: 14px;
            margin: 4px 0 10px 8px;
            border-left: 1px solid #1e293b;
            transition: all 0.2s ease;
        }

        .sub-exercises-list.collapsed {
            display: none;
        }

        .sub-exercise-link {
            display: block;
            padding: 4px 8px;
            font-size: 0.8rem;
            color: #cbd5e1;
            text-decoration: none;
            border-radius: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: color 0.15s;
        }

        .sub-exercise-link:hover {
            color: #38bdf8;
            background-color: rgba(56, 189, 248, 0.08);
        }

        /* Main Content */
        .main-content {
            margin-left: var(--sidebar-width);
            flex: 1;
            max-width: calc(100vw - var(--sidebar-width));
            padding: 40px 60px 100px;
        }

        @media (max-width: 1024px) {
            .sidebar {
                transform: translateX(-100%);
            }
            .sidebar.open {
                transform: translateX(0);
            }
            .main-content {
                margin-left: 0;
                max-width: 100vw;
                padding: 20px 20px 80px;
            }
            .mobile-menu-btn {
                display: block !important;
            }
        }

        .mobile-menu-btn {
            display: none;
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--go-cyan);
            color: #000;
            border: none;
            font-size: 1.3rem;
            cursor: pointer;
            z-index: 1001;
            box-shadow: 0 4px 12px rgba(0, 173, 216, 0.4);
        }

        /* Hero Header */
        .hero-section {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(19, 29, 51, 0.95) 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 36px 32px;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
        }

        .hero-section::before {
            content: '';
            position: absolute;
            top: -50px;
            right: -50px;
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(0, 173, 216, 0.15) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }

        .hero-tag {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(0, 173, 216, 0.12);
            color: #38bdf8;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            border: 1px solid rgba(0, 173, 216, 0.25);
            margin-bottom: 16px;
        }

        .hero-title {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            line-height: 1.25;
            color: #ffffff;
            margin-bottom: 14px;
        }

        .hero-desc {
            font-size: 1.05rem;
            color: var(--text-secondary);
            max-width: 100%;
            width: 100%;
            line-height: 1.7;
        }

        .hero-stats {
            display: flex;
            gap: 24px;
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            flex-wrap: wrap;
        }

        .stat-item {
            display: flex;
            flex-direction: column;
        }

        .stat-val {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--go-cyan);
        }

        .stat-lbl {
            font-size: 0.78rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Exercise Card Container */
        .exercise-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 28px;
            margin-bottom: 36px;
            scroll-margin-top: 20px;
            transition: border-color 0.2s, box-shadow 0.2s;
            position: relative;
        }

        .exercise-card:hover {
            border-color: #334155;
        }

        .exercise-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 18px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }

        .exercise-num-badge {
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: #fff;
            font-weight: 700;
            font-size: 0.85rem;
            padding: 4px 10px;
            border-radius: 6px;
            white-space: nowrap;
        }

        .exercise-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: #f8fafc;
            line-height: 1.3;
        }

        /* Callout Blocks */
        .callout {
            border-radius: 8px;
            padding: 16px 18px;
            margin: 18px 0;
            font-size: 0.95rem;
            line-height: 1.65;
            position: relative;
        }

        .callout-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 0.92rem;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* 1. Task Statement */
        .callout-task {
            background-color: rgba(15, 23, 42, 0.7);
            border: 1px solid #293548;
            border-left: 4px solid #38bdf8;
        }
        .callout-task .callout-title { color: #38bdf8; }

        /* 2. Theory */
        .callout-theory {
            background-color: rgba(30, 41, 59, 0.5);
            border: 1px solid #334155;
            border-left: 4px solid #818cf8;
        }
        .callout-theory .callout-title { color: #a5b4fc; }

        /* 3. Under the Hood */
        .callout-hood {
            background-color: rgba(88, 28, 135, 0.12);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-left: 4px solid #c084fc;
        }
        .callout-hood .callout-title { color: #e9d5ff; }

        /* 4. Pitfalls */
        .callout-pitfalls {
            background-color: rgba(159, 18, 57, 0.12);
            border: 1px solid rgba(244, 63, 94, 0.3);
            border-left: 4px solid #fb7185;
        }
        .callout-pitfalls .callout-title { color: #fda4af; }

        /* 5. BigTech & Interviews */
        .callout-bigtech {
            background-color: rgba(6, 78, 59, 0.18);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-left: 4px solid #34d399;
        }
        .callout-bigtech .callout-title { color: #6ee7b7; }

        /* Code Container */
        .code-container {
            margin: 14px 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #293548;
            background-color: #0b1120;
        }

        .code-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 14px;
            background-color: #111a2e;
            border-bottom: 1px solid #1e293b;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .code-filename {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
            color: #cbd5e1;
        }

        .copy-btn {
            background: rgba(51, 65, 85, 0.6);
            border: 1px solid #475569;
            color: #cbd5e1;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            cursor: pointer;
            transition: all 0.15s;
        }

        .copy-btn:hover {
            background: var(--go-cyan);
            color: #000;
            border-color: var(--go-cyan);
        }

        pre[class*="language-"] {
            margin: 0 !important;
            padding: 14px 16px !important;
            background: transparent !important;
            font-size: 0.88rem !important;
            line-height: 1.5 !important;
        }

        .code-note {
            padding: 6px 14px;
            background-color: rgba(15, 23, 42, 0.9);
            font-size: 0.78rem;
            color: var(--text-muted);
            border-top: 1px solid #1e293b;
            font-style: italic;
        }

        /* Quick Floating Back-to-Top */
        .back-to-top {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: rgba(30, 41, 59, 0.85);
            border: 1px solid #475569;
            color: #fff;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s, background 0.2s;
            z-index: 99;
            font-size: 1.1rem;
            text-decoration: none;
        }

        .back-to-top.visible {
            opacity: 1;
            pointer-events: auto;
        }

        .back-to-top:hover {
            background: var(--go-cyan);
            color: #000;
        }

        /* Section Separator */
        .section-separator {
            display: flex;
            align-items: center;
            gap: 14px;
            margin: 60px 0 30px;
            padding-bottom: 12px;
            border-bottom: 2px solid #1e293b;
        }

        .section-separator h2 {
            font-size: 1.6rem;
            font-weight: 700;
            color: #f8fafc;
        }

        .section-separator .tag {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 12px;
        }
    </style>
</head>
<body>
    <div id="progress-bar"></div>
    <div class="app-container">
"""

HTML_FOOTER = """
    </div>
    
    <a href="#top" class="back-to-top" id="back-to-top" title="Наверх">↑</a>
    <button class="mobile-menu-btn" id="mobile-menu-btn" title="Оглавление">☰</button>

    <!-- Prism Syntax Highlighting -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-go.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-makefile.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>

    <script>
        // Reading Progress Bar
        window.addEventListener('scroll', () => {
            const winScroll = document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            document.getElementById('progress-bar').style.width = scrolled + '%';

            // Back to top button visibility
            const backToTop = document.getElementById('back-to-top');
            if (winScroll > 400) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });

        // Copy Code Button
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const code = btn.closest('.code-container').querySelector('code').innerText;
                navigator.clipboard.writeText(code).then(() => {
                    const orig = btn.innerText;
                    btn.innerText = 'Скопировано!';
                    btn.style.background = '#10b981';
                    btn.style.color = '#fff';
                    setTimeout(() => {
                        btn.innerText = orig;
                        btn.style.background = '';
                        btn.style.color = '';
                    }, 1800);
                });
            });
        });

        // Auto-center active chapter header in sidebar
        function centerActiveChapterInSidebar(smooth = true) {
            const sidebarNav = document.querySelector('.sidebar-nav');
            const activeChapter = document.querySelector('.chapter-link.active');
            if (!sidebarNav || !activeChapter) return;

            const navRect = sidebarNav.getBoundingClientRect();
            const activeRect = activeChapter.getBoundingClientRect();
            const currentScroll = sidebarNav.scrollTop;
            const targetScroll = currentScroll + (activeRect.top - navRect.top) - (navRect.height / 2) + (activeRect.height / 2);

            sidebarNav.scrollTo({
                top: Math.max(0, targetScroll),
                behavior: smooth ? 'smooth' : 'auto'
            });
        }

        // Auto-center active chapter on initial page load and after transition
        window.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                centerActiveChapterInSidebar(true);
            }, 80);
        });

        window.addEventListener('load', () => {
            setTimeout(() => {
                centerActiveChapterInSidebar(true);
            }, 60);
        });

        // Active Chapter Accordion Toggle (Collapse/Expand in sidebar)
        const activeToggle = document.getElementById('active-chapter-toggle');
        const subList = document.getElementById('active-sub-exercises');
        if (activeToggle && subList) {
            activeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                activeToggle.classList.toggle('collapsed');
                subList.classList.toggle('collapsed');
                setTimeout(() => {
                    centerActiveChapterInSidebar(true);
                }, 120);
            });
        }

        // Search Filter for exercises and chapters
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase().trim();
                
                // If search query exists, ensure subList is expanded so filtered exercises are visible
                if (query && subList && subList.classList.contains('collapsed')) {
                    subList.classList.remove('collapsed');
                    if (activeToggle) activeToggle.classList.remove('collapsed');
                }

                // Filter sidebar exercise links
                document.querySelectorAll('.sub-exercise-link').forEach(link => {
                    const text = link.innerText.toLowerCase();
                    if (!query || text.includes(query)) {
                        link.style.display = 'block';
                    } else {
                        link.style.display = 'none';
                    }
                });

                // Filter exercise cards in main content
                document.querySelectorAll('.exercise-card').forEach(card => {
                    const text = card.innerText.toLowerCase();
                    if (!query || text.includes(query)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        }

        // Mobile Menu Drawer Toggle
        const menuBtn = document.getElementById('mobile-menu-btn');
        const sidebar = document.querySelector('.sidebar');
        if (menuBtn && sidebar) {
            menuBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
                // Center active chapter when opening mobile menu drawer
                if (sidebar.classList.contains('open')) {
                    setTimeout(() => {
                        centerActiveChapterInSidebar(true);
                    }, 100);
                }
            });
            document.addEventListener('click', (e) => {
                if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            });
        }
    </script>
</body>
</html>
"""
