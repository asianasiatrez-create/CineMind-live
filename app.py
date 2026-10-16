<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>CineMind | Neural Galaxy Cinema & Series Intelligence</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=Playfair+Display:ital,wght@1,600&display=swap');

:root {
    --bg-deep: #0d0628;
    --sidebar-bg: rgba(16, 9, 44, 0.86);
    --panel-bg: rgba(22, 13, 56, 0.72);
    --card-bg: rgba(24, 14, 60, 0.90);
    --primary-glow: #d946ef;
    --secondary-glow: #00f2fe;
    --tertiary-glow: #7c3aed;
    --accent-pink: #f43f5e;
    --glass-border: rgba(0, 242, 254, 0.28);
    --glass-border-hover: rgba(217, 70, 239, 0.75);
    --text-main: #ffffff;
    --text-muted: #a5b4fc;
    --input-bg: rgba(12, 6, 34, 0.92);
    --modal-bg: linear-gradient(135deg, #190d48, #0c0524);
    --shadow-heavy: 0 25px 65px rgba(5, 2, 18, 0.88);
    --chat-history-bg: linear-gradient(160deg, rgba(16, 9, 44, 0.92), rgba(28, 14, 68, 0.88));
    --ai-bubble-bg: rgba(34, 19, 82, 0.95);
    --ai-bubble-text: #ffffff;
}

html[data-theme="light"] {
    --bg-deep: #e6e0ff;
    --sidebar-bg: rgba(235, 230, 255, 0.90);
    --panel-bg: rgba(230, 224, 255, 0.82);
    --card-bg: rgba(245, 242, 255, 0.96);
    --primary-glow: #9333ea;
    --secondary-glow: #0284c7;
    --tertiary-glow: #6366f1;
    --accent-pink: #e11d48;
    --glass-border: rgba(147, 51, 234, 0.26);
    --glass-border-hover: rgba(2, 132, 199, 0.65);
    --text-main: #1e1b4b;
    --text-muted: #4c1d95;
    --input-bg: rgba(255, 255, 255, 0.92);
    --modal-bg: linear-gradient(135deg, #ede9fe, #e0f2fe);
    --shadow-heavy: 0 20px 50px rgba(99, 102, 241, 0.2);
    --chat-history-bg: linear-gradient(160deg, rgba(228, 222, 255, 0.95), rgba(218, 236, 255, 0.92));
    --ai-bubble-bg: rgba(243, 240, 255, 0.96);
    --ai-bubble-text: #1e1b4b;
}

* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; color: var(--text-main); -webkit-font-smoothing: antialiased; }
html, body { width: 100%; min-height: 100vh; background-color: var(--bg-deep); overflow-x: hidden; -webkit-tap-highlight-color: transparent; transition: background-color 0.35s ease; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: rgba(13, 6, 40, 0.4); }
::-webkit-scrollbar-thumb { background: linear-gradient(var(--secondary-glow), var(--primary-glow)); border-radius: 4px; }

.cosmic-bg {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background:
        radial-gradient(circle at 14% 18%, rgba(0, 242, 254, 0.28) 0%, transparent 42%),
        radial-gradient(circle at 86% 22%, rgba(217, 70, 239, 0.30) 0%, transparent 45%),
        radial-gradient(circle at 50% 80%, rgba(124, 58, 237, 0.32) 0%, transparent 52%),
        radial-gradient(circle at 30% 60%, rgba(244, 63, 94, 0.14) 0%, transparent 42%),
        linear-gradient(160deg, #0d0628 0%, #190a42 50%, #0f072e 100%);
    z-index: -2; pointer-events: none; overflow: hidden;
}
html[data-theme="light"] .cosmic-bg {
    background:
        radial-gradient(circle at 15% 20%, rgba(56, 189, 248, 0.35) 0%, transparent 45%),
        radial-gradient(circle at 85% 25%, rgba(192, 132, 252, 0.38) 0%, transparent 48%),
        radial-gradient(circle at 50% 85%, rgba(129, 140, 248, 0.30) 0%, transparent 52%),
        linear-gradient(160deg, #e6e0ff 0%, #ddd6fe 45%, #bae6fd 100%);
}
.cosmic-stars {
    position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background-image:
        radial-gradient(1.5px 1.5px at 25px 35px, #fff, transparent),
        radial-gradient(1px 1px at 90px 140px, #00f2fe, transparent),
        radial-gradient(2px 2px at 210px 80px, #d946ef, transparent),
        radial-gradient(1.5px 1.5px at 310px 240px, #fff, transparent),
        radial-gradient(1px 1px at 420px 150px, #a855f7, transparent);
    background-size: 480px 320px;
    opacity: 0.55;
    animation: driftStars 90s linear infinite;
}
html[data-theme="light"] .cosmic-stars { opacity: 0.22; }
@keyframes driftStars {
    from { transform: translateY(0); }
    to { transform: translateY(-320px); }
}

.app-layout { display: flex; width: 100%; max-width: 1780px; margin: 0 auto; min-height: 100vh; padding: 24px; gap: 24px; }

/* ---- Sidebar & Pure Unboxed Logo (NO CIRCLE) ---- */
.sidebar { width: 280px; background: var(--sidebar-bg); border: 1px solid var(--glass-border); border-radius: 28px; padding: 24px 20px; display: flex; flex-direction: column; z-index: 20; gap: 18px; flex-shrink: 0; box-shadow: var(--shadow-heavy); backdrop-filter: blur(28px); position: sticky; top: 24px; height: fit-content; max-height: calc(100vh - 48px); overflow-y: auto; }
.sidebar-top-bar { display: flex; flex-direction: column; gap: 16px; width: 100%; }
.logo-free-wrapper { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 6px; width: 100%; cursor: pointer; background: transparent; border: none; }
.logo-unboxed {
    width: 124px;
    height: auto;
    max-height: 124px;
    border-radius: 0 !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    object-fit: contain;
    background: transparent !important;
    filter: drop-shadow(0 0 16px rgba(0, 242, 254, 0.55)) drop-shadow(0 0 28px rgba(217, 70, 239, 0.35));
    transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.35s ease;
    display: block;
}
.logo-free-wrapper:hover .logo-unboxed,
.logo-unboxed.tilting {
    transform: scale(1.12) rotate(-10deg) skewX(-3deg);
    filter: drop-shadow(0 0 25px rgba(217, 70, 239, 0.9)) drop-shadow(0 0 45px rgba(0, 242, 254, 0.8));
}
.logo-brand-title {
    font-size: 1.4rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    background: linear-gradient(90deg, var(--secondary-glow), var(--primary-glow));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
}

.top-controls-row { display: flex; gap: 10px; align-items: center; width: 100%; }
.account-top-btn { flex: 1; background: linear-gradient(135deg, rgba(217, 70, 239, 0.2), rgba(0, 242, 254, 0.2)); border: 1px solid var(--secondary-glow); padding: 11px 14px; border-radius: 16px; display: flex; align-items: center; gap: 10px; cursor: pointer; transition: 0.25s; min-width: 0; }
.account-top-btn:hover { border-color: var(--primary-glow); transform: translateY(-2px); }
.account-info { display: flex; flex-direction: column; gap: 2px; overflow: hidden; }
.account-name { font-weight: 700; font-size: 0.88rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.account-sub { font-size: 0.7rem; color: var(--secondary-glow); font-weight: 600; }

.theme-toggle-btn { width: 44px; height: 44px; border-radius: 14px; background: var(--panel-bg); border: 1px solid var(--glass-border); display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 1.1rem; transition: 0.25s; flex-shrink: 0; }
.theme-toggle-btn:hover { border-color: var(--primary-glow); transform: scale(1.06); }

.nav-links { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.nav-item { padding: 13px 16px; border-radius: 16px; cursor: pointer; color: var(--text-muted); font-weight: 600; font-size: 0.92rem; display: flex; align-items: center; gap: 12px; transition: 0.22s; border: 1px solid transparent; }
.nav-item:hover { color: var(--text-main); background: rgba(124, 58, 237, 0.12); border-color: var(--glass-border); transform: translateX(4px); }
.nav-item.active { background: linear-gradient(90deg, rgba(217, 70, 239, 0.28), rgba(0, 242, 254, 0.18)); border-left: 4px solid var(--secondary-glow); color: var(--text-main); font-weight: 700; }

/* ---- Main Content & Slanted Hero Banner ---- */
.main-content { flex: 1; display: flex; flex-direction: column; gap: 24px; padding-bottom: 100px; min-width: 0; }
.hero-banner {
    position: relative;
    overflow: hidden;
    min-height: 290px;
    justify-content: center;
    background: #070314;
    border: 1.5px solid var(--glass-border);
    border-radius: 28px;
    padding: 40px 42px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    box-shadow: var(--shadow-heavy);
}
.hero-slideshow {
    position: absolute;
    inset: -28%;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
    transform: rotate(-10deg) skewX(-6deg) scale(1.18);
    transform-origin: center center;
}
.hero-slide {
    position: absolute;
    inset: 0;
    opacity: 0;
    transition: opacity 1.1s ease-in-out, transform 6.5s ease-out;
}
.hero-slide.backdrop-slide {
    background-size: cover;
    background-position: center 25%;
    transform: scale(1.12);
    filter: brightness(1.04) contrast(1.12) saturate(1.25);
}
.hero-slide.backdrop-slide.active {
    opacity: 0.88;
    transform: scale(1.02) translateX(-14px);
}
.hero-slide.poster-wall-slide {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    grid-template-rows: repeat(2, 1fr);
    gap: 10px;
    padding: 12px;
    background: #05020e;
    transform: scale(1.04);
}
.hero-slide.poster-wall-slide.active {
    opacity: 0.92;
    transform: scale(1) translateX(12px);
}
.poster-wall-tile {
    width: 100%;
    height: 100%;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(0, 242, 254, 0.28);
    background: #120c30;
    box-shadow: 0 8px 20px rgba(0,0,0,0.65);
}
.poster-wall-tile img { width: 100%; height: 100%; object-fit: cover; display: block; }
.hero-slideshow-overlay {
    position: absolute; inset: 0; z-index: 1; pointer-events: none;
    background:
        linear-gradient(90deg, rgba(4, 2, 14, 0.96) 0%, rgba(7, 4, 22, 0.82) 45%, rgba(10, 6, 28, 0.32) 78%, rgba(6, 3, 18, 0.18) 100%),
        linear-gradient(to top, rgba(4, 2, 14, 0.90) 0%, transparent 50%);
}
html[data-theme="light"] .hero-slideshow-overlay {
    background:
        linear-gradient(90deg, rgba(230, 224, 255, 0.96) 0%, rgba(221, 214, 254, 0.85) 45%, rgba(221, 214, 254, 0.28) 78%, rgba(230, 224, 255, 0.15) 100%),
        linear-gradient(to top, rgba(230, 224, 255, 0.90) 0%, transparent 50%);
}
.hero-banner > *:not(.hero-slideshow):not(.hero-slideshow-overlay) { position: relative; z-index: 2; }
.welcome-title { font-size: clamp(1.6rem, 3vw, 2.5rem); font-weight: 800; line-height: 1.3; }
.text-gradient { font-family: 'Playfair Display', serif; background: linear-gradient(to right, #f43f5e, var(--primary-glow), var(--secondary-glow)); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; font-style: italic; font-weight: 600; }

.hero-search-box { position: relative; width: 100%; max-width: 780px; display: flex; gap: 10px; }
.search-input-wrap { position: relative; flex: 1; min-width: 0; display: flex; }
.search-input-wrap input { width: 100%; background: var(--input-bg); border: 1.5px solid var(--glass-border); border-radius: 40px; padding: 16px 22px 16px 54px; outline: none; color: var(--text-main); font-size: 0.98rem; }
.search-input-wrap input:focus { border-color: var(--secondary-glow); box-shadow: 0 0 25px rgba(0, 242, 254, 0.45); }
.search-input-wrap i.fa-brain { position: absolute; left: 22px; top: 50%; transform: translateY(-50%); color: var(--secondary-glow); font-size: 1.15rem; pointer-events: none; }
.search-btn-submit { background: linear-gradient(135deg, var(--primary-glow), var(--secondary-glow)); border: none; padding: 0 26px; border-radius: 30px; color: #fff; font-weight: 700; cursor: pointer; transition: 0.25s; white-space: nowrap; display: flex; align-items: center; justify-content: center; gap: 8px; }
.search-btn-submit:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0, 242, 254, 0.55); }

/* ---- Filter Panel & Netflix-Style Multi-Column Genre Dropdown ---- */
.filter-panel { display: flex; flex-direction: column; gap: 16px; background: var(--panel-bg); padding: 22px 26px; border-radius: 24px; border: 1px solid var(--glass-border); backdrop-filter: blur(22px); box-shadow: var(--shadow-heavy); position: relative; z-index: 15; }
.filter-dropdown-container { display: flex; gap: 14px; flex-wrap: wrap; align-items: center; padding-bottom: 12px; border-bottom: 1px solid rgba(0, 242, 254, 0.14); }
.filter-select-wrapper { display: flex; align-items: center; gap: 8px; flex: 1 1 200px; min-width: 180px; position: relative; }
.filter-select-wrapper label { font-size: 0.84rem; font-weight: 700; color: var(--secondary-glow); display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.custom-select {
    width: 100%;
    background: var(--input-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 10px 36px 10px 16px;
    color: var(--text-main);
    font-size: 0.86rem;
    font-weight: 600;
    outline: none;
    cursor: pointer;
    transition: 0.22s;
    appearance: none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2300f2fe' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 14px center;
    background-size: 14px;
}
.custom-select:focus, .custom-select:hover { border-color: var(--secondary-glow); box-shadow: 0 0 16px rgba(0, 242, 254, 0.35); }
.custom-select option { background: #120935; color: #fff; }
html[data-theme="light"] .custom-select option { background: #ede9fe; color: #1e1b4b; }

/* Netflix Multi-Column Genre Dropdown Box */
.netflix-dropdown-wrap { position: relative; flex: 1 1 220px; min-width: 200px; }
.netflix-genre-trigger {
    width: 100%;
    background: rgba(8, 4, 24, 0.92);
    border: 1.5px solid var(--secondary-glow);
    border-radius: 16px;
    padding: 10px 16px;
    color: #fff;
    font-size: 0.86rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    cursor: pointer;
    transition: 0.22s;
    box-shadow: 0 4px 16px rgba(0, 242, 254, 0.2);
}
html[data-theme="light"] .netflix-genre-trigger { background: #ffffff; color: #1e1b4b; }
.netflix-genre-trigger:hover { border-color: var(--primary-glow); box-shadow: 0 0 20px rgba(217, 70, 239, 0.45); }
.netflix-genre-menu {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    width: 520px;
    max-width: 92vw;
    background: rgba(8, 4, 24, 0.97);
    border: 1px solid var(--secondary-glow);
    border-radius: 18px;
    padding: 18px 20px;
    display: none;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px 16px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.92);
    backdrop-filter: blur(24px);
    z-index: 120;
}
html[data-theme="light"] .netflix-genre-menu { background: rgba(245, 242, 255, 0.98); }
.netflix-genre-menu.open { display: grid; }
.netflix-genre-item {
    font-size: 0.83rem;
    font-weight: 600;
    color: var(--text-muted);
    padding: 7px 10px;
    border-radius: 10px;
    cursor: pointer;
    transition: 0.18s;
    display: flex;
    align-items: center;
    gap: 7px;
    white-space: nowrap;
}
.netflix-genre-item:hover, .netflix-genre-item.active {
    color: #fff;
    background: linear-gradient(90deg, rgba(217, 70, 239, 0.45), rgba(0, 242, 254, 0.35));
    font-weight: 700;
}

.filter-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; width: 100%; }
.filter-row-middle { justify-content: space-between; text-align: left; padding: 4px 0 12px 0; border-bottom: 1px solid rgba(0, 242, 254, 0.14); }
.filter-label { font-size: 0.85rem; font-weight: 700; color: var(--secondary-glow); min-width: 110px; display: flex; align-items: center; gap: 6px; }
.filter-pill { background: rgba(124, 58, 237, 0.08); border: 1px solid var(--glass-border); padding: 7px 15px; border-radius: 20px; font-size: 0.81rem; font-weight: 600; cursor: pointer; color: var(--text-muted); transition: 0.2s; display: inline-flex; align-items: center; gap: 6px; user-select: none; }
.filter-pill:hover, .filter-pill.active { background: linear-gradient(135deg, var(--primary-glow), var(--secondary-glow)); color: #fff; border-color: transparent; box-shadow: 0 0 18px rgba(0, 242, 254, 0.5); }
.filter-pill.active i, .filter-pill:hover i { color: #fff !important; }

/* ---- Rows & Equal-Sized Cards ---- */
.row-title { font-size: 1.35rem; font-weight: 800; display: flex; align-items: center; gap: 10px; }
.catalog-container { display: flex; flex-direction: column; gap: 34px; min-width: 0; }
.row-section { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.movie-row {
    display: flex;
    flex-wrap: nowrap;
    gap: 20px;
    width: 100%;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 12px 8px 24px 8px;
    -webkit-overflow-scrolling: touch;
    touch-action: pan-x pan-y;
    scroll-snap-type: x proximity;
    scrollbar-width: thin;
    scrollbar-color: var(--secondary-glow) transparent;
}

.movie-card {
    min-width: 215px;
    width: 215px;
    height: 438px;
    background: var(--card-bg);
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid var(--glass-border);
    transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    box-shadow: 0 12px 28px rgba(0,0,0,0.45);
    position: relative;
    scroll-snap-align: start;
    user-select: none;
}
@media (hover: hover) and (pointer: fine) {
    .movie-card:hover { border-color: var(--secondary-glow); transform: translateY(-8px); box-shadow: 0 22px 45px rgba(0, 242, 254, 0.38); }
}
.card-poster-wrap {
    width: 100%;
    height: 285px;
    flex-shrink: 0;
    position: relative;
    overflow: hidden;
    background: #160f38;
}
.card-poster-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    pointer-events: none;
}

/* Quick "Not Interested" Button on Card Top-Left */
.card-not-interested-btn {
    position: absolute;
    top: 10px;
    left: 10px;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: rgba(8, 4, 24, 0.85);
    border: 1px solid rgba(244, 63, 94, 0.65);
    color: #fda4af;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    z-index: 6;
    cursor: pointer;
    transition: 0.2s;
    backdrop-filter: blur(6px);
}
.card-not-interested-btn:hover {
    background: #e11d48;
    color: #fff;
    transform: scale(1.12);
    box-shadow: 0 0 14px rgba(225, 29, 72, 0.8);
}

.badges-container {
    position: absolute;
    top: 10px;
    right: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
    z-index: 4;
    pointer-events: none;
}
.media-badge {
    background: rgba(6, 3, 20, 0.88);
    border: 1px solid var(--secondary-glow);
    color: #fff;
    font-size: 0.68rem;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: 10px;
    backdrop-filter: blur(8px);
    white-space: nowrap;
}
.r18-badge {
    background: linear-gradient(135deg, #dc2626, #991b1b);
    border: 1px solid #fca5a5;
    color: #fff;
    font-size: 0.7rem;
    font-weight: 900;
    padding: 3px 9px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(220, 38, 38, 0.75);
    letter-spacing: 0.5px;
    white-space: nowrap;
}

.origin-country-badge {
    position: absolute;
    bottom: 8px;
    left: 8px;
    background: rgba(8, 4, 26, 0.88);
    border: 1px solid rgba(192, 132, 252, 0.55);
    color: #f8fafc;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 9px;
    backdrop-filter: blur(8px);
    z-index: 4;
    pointer-events: none;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.6);
}

/* Exact Genre Tags on Movie Card */
.card-genres-tags {
    font-size: 0.7rem;
    font-weight: 700;
    color: #e879f9;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ---- Netflix-Style Top 10 Ranked Cards ---- */
.top10-card {
    min-width: 275px;
    width: 275px;
    height: 438px;
    padding-left: 68px;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    overflow: visible !important;
    position: relative;
}
.top10-rank-num {
    position: absolute;
    left: 0px;
    bottom: 24px;
    font-size: 9.5rem;
    font-weight: 900;
    line-height: 0.78;
    letter-spacing: -8px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: rgba(15, 8, 40, 0.92);
    -webkit-text-stroke: 4px var(--secondary-glow);
    text-shadow: 0 0 28px rgba(217, 70, 239, 0.65), 4px 8px 20px rgba(0, 0, 0, 0.9);
    z-index: 1;
    pointer-events: none;
    user-select: none;
}
html[data-theme="light"] .top10-rank-num {
    color: rgba(230, 224, 255, 0.92);
    -webkit-text-stroke: 4px var(--primary-glow);
}
.top10-inner {
    width: 100%;
    height: 100%;
    background: var(--card-bg);
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid var(--glass-border);
    box-shadow: -10px 14px 32px rgba(0,0,0,0.75);
    display: flex;
    flex-direction: column;
    position: relative;
    z-index: 2;
}

.movie-info { padding: 11px 14px; display: flex; flex-direction: column; gap: 4px; flex: 1; justify-content: space-between; overflow: hidden; }
.movie-title { font-weight: 700; font-size: 0.93rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-meta-row { display: flex; justify-content: space-between; align-items: center; gap: 6px; font-size: 0.78rem; font-weight: 700; }
.match-score { color: var(--secondary-glow); display: flex; align-items: center; gap: 4px; }
.rating-badge { color: #fbbf24; display: flex; align-items: center; gap: 4px; }
.card-rationale-preview { font-size: 0.71rem; color: var(--text-muted); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.3; }

.movie-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 22px;
    align-items: stretch;
    width: 100%;
}
.movie-grid .movie-card {
    width: 100%;
    min-width: 0;
    height: 432px;
}
.movie-grid .card-poster-wrap {
    height: 280px;
}
.infinite-loader { text-align: center; padding: 28px; color: var(--secondary-glow); font-weight: 700; font-size: 0.95rem; display: flex; justify-content: center; align-items: center; gap: 10px; }

/* ---- Nova Tilting Animation (Matches Logo Tilt Motion!) ---- */
@keyframes novaFloat {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-7px) rotate(3deg); }
}
@keyframes novaTiltBurst {
    0% { transform: scale(1) rotate(0deg); }
    30% { transform: scale(1.18) rotate(-14deg) skewX(-5deg); }
    65% { transform: scale(1.14) rotate(12deg) skewX(4deg); }
    85% { transform: scale(1.06) rotate(-5deg); }
    100% { transform: scale(1) rotate(0deg); }
}
@keyframes tooltipFloat {
    0%, 100% { transform: translateY(0px); box-shadow: 0 6px 25px rgba(0, 242, 254, 0.35); border-color: var(--secondary-glow); }
    50% { transform: translateY(-6px); box-shadow: 0 12px 28px rgba(217, 70, 239, 0.6); border-color: var(--primary-glow); }
}

.nova-avatar-animated {
    animation: novaFloat 3.4s ease-in-out infinite;
    filter: drop-shadow(0 0 16px rgba(0, 242, 254, 0.75)) drop-shadow(0 0 28px rgba(217, 70, 239, 0.45));
    cursor: pointer;
    border-radius: 0 !important;
    background: transparent !important;
    transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.35s ease;
}
.nova-avatar-animated:hover,
.nova-avatar-animated.tilting {
    animation: novaTiltBurst 0.65s cubic-bezier(0.34, 1.56, 0.64, 1);
    transform: scale(1.12) rotate(-10deg);
    filter: drop-shadow(0 0 25px rgba(217, 70, 239, 0.95)) drop-shadow(0 0 42px rgba(0, 242, 254, 0.85));
}

.nova-chathead {
    width: 78px;
    height: 78px;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    filter: drop-shadow(0 0 22px rgba(0, 242, 254, 0.75)) drop-shadow(0 0 38px rgba(217, 70, 239, 0.55));
    animation: novaFloat 3.6s ease-in-out infinite;
    padding: 0;
    user-select: none;
    touch-action: none;
    transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.35s ease;
}
.nova-chathead:hover,
.nova-chathead.tilting {
    animation: novaTiltBurst 0.65s cubic-bezier(0.34, 1.56, 0.64, 1);
    transform: scale(1.12) rotate(-10deg);
    filter: drop-shadow(0 0 28px rgba(217, 70, 239, 0.95)) drop-shadow(0 0 45px rgba(0, 242, 254, 0.9));
}
.nova-chathead img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 0 !important;
    background: transparent !important;
    pointer-events: none;
}

.chat-tooltip {
    background: linear-gradient(135deg, rgba(25, 12, 64, 0.95), rgba(8, 4, 24, 0.95));
    padding: 10px 18px; border-radius: 20px; font-size: 0.86rem; font-weight: 700; color: #ffffff;
    border: 1.5px solid var(--secondary-glow); cursor: pointer; position: relative;
    animation: tooltipFloat 2.8s ease-in-out infinite; backdrop-filter: blur(12px); user-select: none; white-space: nowrap;
}
html[data-theme="light"] .chat-tooltip { background: linear-gradient(135deg, #ffffff, #f3e8ff); color: #0f172a; }
.chat-tooltip::after {
    content: ""; position: absolute; bottom: -7px; right: 26px; width: 11px; height: 11px;
    background: inherit; border-right: 1.5px solid var(--secondary-glow); border-bottom: 1.5px solid var(--secondary-glow); transform: rotate(45deg);
}

/* ---- Analytics & Accordions ---- */
.cascade-accordion { display: flex; flex-direction: column; gap: 16px; }
.cascade-item { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; overflow: hidden; backdrop-filter: blur(20px); }
.cascade-header { padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; font-weight: 700; font-size: 1.05rem; color: var(--secondary-glow); }
.cascade-body { max-height: 0; overflow: hidden; transition: max-height 0.4s ease, padding 0.4s ease; padding: 0 24px; }
.cascade-item.active .cascade-body { max-height: 1500px; padding: 22px 24px; border-top: 1px solid var(--glass-border); }
.analytics-grid-packed { display: grid; grid-template-columns: repeat(auto-fit, minmax(185px, 1fr)); gap: 14px; margin-bottom: 22px; }
.analytics-stat-card { background: rgba(124, 58, 237, 0.08); border: 1px solid var(--glass-border); padding: 18px; border-radius: 16px; display: flex; flex-direction: column; gap: 6px; }
.analytics-stat-card h4 { font-size: 0.86rem; color: var(--primary-glow); display: flex; align-items: center; gap: 8px; }
.analytics-stat-card p { font-size: 1.25rem; font-weight: 800; }
.chart-box-wrapper { position: relative; width: 100%; height: 270px; background: rgba(124, 58, 237, 0.04); border: 1px solid var(--glass-border); border-radius: 16px; padding: 16px; }

.nova-banner-clean { background: linear-gradient(135deg, rgba(217, 70, 239, 0.22), rgba(0, 242, 254, 0.22)); border: 1px solid var(--secondary-glow); border-radius: 24px; padding: 24px 28px; display: flex; align-items: center; justify-content: space-between; gap: 18px; backdrop-filter: blur(20px); flex-wrap: wrap; }
.nova-banner-clean img { width: 66px; height: 66px; object-fit: contain; }

/* ---- Modals, Exact Genres & Cast/Crew Box ---- */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(8, 3, 24, 0.88); z-index: 200; display: flex; justify-content: center; align-items: center; opacity: 0; pointer-events: none; transition: 0.3s; backdrop-filter: blur(22px); padding: 16px; }
.modal-overlay.active { opacity: 1; pointer-events: auto; }
.modal-content { display: flex; gap: 24px; width: 960px; max-width: 100%; max-height: 92vh; background: var(--modal-bg); padding: 28px; border-radius: 26px; position: relative; border: 1px solid var(--glass-border-hover); box-shadow: var(--shadow-heavy); overflow-y: auto; }
.modal-poster-wrap { position: relative; width: 235px; height: 355px; flex-shrink: 0; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.6); background: #160f38; }
.modal-poster-wrap img { width: 100%; height: 100%; object-fit: cover; }
.modal-info { display: flex; flex-direction: column; gap: 12px; flex: 1; min-width: 0; overflow-y: auto; padding-right: 4px; }
.close-modal { position: absolute; top: 18px; right: 22px; font-size: 1.5rem; cursor: pointer; color: var(--text-muted); z-index: 10; }
.modal-meta { display: flex; flex-wrap: wrap; gap: 10px; font-size: 0.88rem; color: var(--text-muted); font-weight: 600; align-items: center; }
.modal-overview { font-size: 0.92rem; line-height: 1.6; }

.modal-exact-genres { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.exact-genre-pill {
    background: linear-gradient(135deg, rgba(217, 70, 239, 0.22), rgba(0, 242, 254, 0.18));
    border: 1px solid var(--secondary-glow);
    color: var(--text-main);
    font-size: 0.76rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 14px;
}

.credits-box {
    background: rgba(124, 58, 237, 0.10);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.credits-crew-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px 14px;
    font-size: 0.82rem;
    border-bottom: 1px solid rgba(0, 242, 254, 0.16);
    padding-bottom: 10px;
}
.credits-crew-item strong { color: var(--secondary-glow); display: block; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.5px; }
.credits-cast-list {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 4px;
    -webkit-overflow-scrolling: touch;
}
.cast-chip {
    background: rgba(12, 6, 34, 0.78);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 8px 12px;
    min-width: 155px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
html[data-theme="light"] .cast-chip { background: rgba(255, 255, 255, 0.85); }
.cast-actor { font-size: 0.82rem; font-weight: 800; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cast-character { font-size: 0.73rem; color: var(--secondary-glow); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.ai-rationale-box { background: rgba(0, 242, 254, 0.08); border: 1px solid rgba(0, 242, 254, 0.4); padding: 12px 16px; border-radius: 14px; display: flex; flex-direction: column; gap: 4px; }
.ai-rationale-title { font-size: 0.82rem; font-weight: 700; color: var(--secondary-glow); display: flex; align-items: center; gap: 8px; }
.ai-rationale-text { font-size: 0.86rem; color: var(--text-muted); line-height: 1.45; }
.streaming-providers { font-size: 0.82rem; color: var(--secondary-glow); font-weight: 600; display: flex; align-items: center; gap: 8px; background: rgba(0, 242, 254, 0.1); padding: 8px 14px; border-radius: 12px; border: 1px solid rgba(0, 242, 254, 0.3); }

.modal-actions { display: flex; gap: 10px; flex-wrap: wrap; padding-top: 6px; }
.btn-action { background: linear-gradient(135deg, var(--primary-glow), var(--secondary-glow)); border: none; padding: 10px 18px; border-radius: 22px; color: #fff; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 7px; transition: 0.22s; font-size: 0.84rem; text-decoration: none; }
.btn-action:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6); }
.btn-trailer { background: linear-gradient(135deg, #f43f5e, #e11d48); }
.btn-fav { background: rgba(124, 58, 237, 0.14); border: 1px solid var(--glass-border); color: var(--text-main); }
.btn-not-interested { background: rgba(225, 29, 72, 0.18); border: 1px solid #f43f5e; color: #fda4af; }
.btn-not-interested:hover { background: #e11d48; color: #fff; }

.user-info-card { background: rgba(124, 58, 237, 0.12); border: 1px solid var(--glass-border); border-radius: 18px; padding: 18px; display: flex; flex-direction: column; gap: 14px; }
.user-stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; text-align: center; }
.user-stat-pill { background: rgba(0, 242, 254, 0.08); border: 1px solid var(--glass-border); border-radius: 12px; padding: 10px 6px; display: flex; flex-direction: column; gap: 2px; }
.user-stat-pill strong { font-size: 1.15rem; color: var(--secondary-glow); }
.user-stat-pill span { font-size: 0.72rem; color: var(--text-muted); font-weight: 600; }

.modal-similar-strip { display: flex; gap: 12px; overflow-x: auto; padding: 8px 2px; -webkit-overflow-scrolling: touch; }
.modal-sim-card { min-width: 105px; width: 105px; cursor: pointer; display: flex; flex-direction: column; gap: 4px; flex-shrink: 0; }
.modal-sim-card img { width: 100%; height: 150px; object-fit: cover; border-radius: 10px; border: 1px solid var(--glass-border); }
.modal-sim-card span { font-size: 0.72rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ---- Floating Chat ---- */
.chat-wrapper { position: fixed; bottom: 20px; right: 20px; z-index: 150; display: flex; align-items: flex-end; flex-direction: column; gap: 12px; touch-action: none; }
.chat-modal { width: 400px; max-width: calc(100vw - 24px); background: var(--modal-bg); border-radius: 26px; border: 1px solid var(--glass-border-hover); box-shadow: var(--shadow-heavy); display: flex; flex-direction: column; position: absolute; bottom: 86px; right: 0; opacity: 0; pointer-events: none; transition: opacity 0.25s ease; }
.chat-modal.active { opacity: 1; pointer-events: auto; }
.chat-header { padding: 14px 18px; border-bottom: 1px solid var(--glass-border); display: flex; justify-content: space-between; align-items: center; font-weight: 700; }
.chat-body, .nova-history-large { padding: 16px; height: 280px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; background: var(--chat-history-bg); }
.chat-bubble { padding: 11px 15px; border-radius: 16px; font-size: 0.9rem; line-height: 1.5; max-width: 88%; word-break: break-word; }
.ai-bubble { background: var(--ai-bubble-bg); border: 1px solid rgba(0, 242, 254, 0.45); color: var(--ai-bubble-text); align-self: flex-start; }
.user-bubble { background: linear-gradient(135deg, var(--primary-glow), var(--secondary-glow)); color: #fff; align-self: flex-end; }
.quick-chips { display: flex; gap: 8px; padding: 10px 14px; overflow-x: auto; border-top: 1px solid var(--glass-border); scrollbar-width: none; -webkit-overflow-scrolling: touch; }
.chip { background: rgba(124, 58, 237, 0.15); border: 1px solid var(--glass-border); padding: 6px 12px; border-radius: 14px; font-size: 0.76rem; font-weight: 600; cursor: pointer; color: var(--text-muted); white-space: nowrap; }
.chip:hover { background: var(--primary-glow); color: #fff; }
.chat-footer { padding: 12px 14px; border-top: 1px solid var(--glass-border); display: flex; gap: 8px; align-items: center; }
.chat-footer input { flex: 1; background: var(--input-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 11px 16px; outline: none; font-size: 0.9rem; color: var(--text-main); min-width: 0; }
.send-btn { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, var(--primary-glow), var(--secondary-glow)); border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

/* ---- Mobile & Tablet Responsive Layout Fixes ---- */
@media (max-width: 1100px) {
    .app-layout { flex-direction: column; padding: 12px; gap: 16px; }
    .sidebar {
        width: 100%; height: auto; max-height: none; position: static;
        flex-direction: column; padding: 14px 16px; border-radius: 22px; gap: 12px;
    }
    .sidebar-top-bar { display: flex; flex-direction: row; width: 100%; align-items: center; justify-content: space-between; gap: 12px; }
    .logo-free-wrapper { width: auto; flex-direction: row; gap: 10px; }
    .logo-unboxed { width: 52px; max-height: 52px; }
    .logo-brand-title { font-size: 1.15rem; }
    .top-controls-row { width: auto; flex: 0 1 auto; justify-content: flex-end; }
    .account-top-btn { flex: 0 1 auto; padding: 8px 12px; }
    .nav-links {
        flex-direction: row; gap: 8px; overflow-x: auto; width: 100%;
        padding: 4px 2px 6px 2px; -webkit-overflow-scrolling: touch; scrollbar-width: none;
    }
    .nav-item { padding: 9px 14px; font-size: 0.82rem; gap: 7px; white-space: nowrap; flex-shrink: 0; }
    .hero-banner { padding: 24px 18px; min-height: 220px; border-radius: 22px; gap: 16px; }
    .hero-slide.poster-wall-slide { grid-template-columns: repeat(5, 1fr); }
    .filter-panel { padding: 14px 16px; border-radius: 20px; gap: 12px; }
    .filter-dropdown-container { gap: 10px; }
    .filter-select-wrapper, .netflix-dropdown-wrap { flex: 1 1 100%; }
    .netflix-genre-menu { grid-template-columns: repeat(2, 1fr); width: 100%; }
    .filter-row { flex-wrap: nowrap; overflow-x: auto; padding-bottom: 4px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .filter-label { min-width: auto; font-size: 0.8rem; margin-right: 4px; flex-shrink: 0; }
    .filter-pill { flex-shrink: 0; padding: 6px 13px; font-size: 0.78rem; }
}

@media (max-width: 640px) {
    .app-layout { padding: 8px; gap: 12px; }
    .account-info { display: none; }
    .welcome-title { font-size: 1.35rem; }
    .hero-search-box { flex-direction: column; gap: 8px; }
    .search-input-wrap input { padding: 14px 18px 14px 46px; font-size: 0.9rem; }
    .search-btn-submit { padding: 13px; border-radius: 24px; width: 100%; }
    .filter-dropdown-container { flex-direction: column; align-items: stretch; gap: 10px; }
    .filter-select-wrapper, .netflix-dropdown-wrap { width: 100%; min-width: 0; }
    .row-title { font-size: 1.12rem; }
    .movie-row { gap: 12px; padding: 8px 4px 18px 4px; }
    .movie-card { min-width: 160px; width: 160px; height: 350px; border-radius: 16px; }
    .card-poster-wrap { height: 215px; }
    .top10-card { min-width: 195px; width: 195px; height: 350px; padding-left: 46px; }
    .top10-rank-num { font-size: 6.4rem; letter-spacing: -5px; bottom: 18px; }
    .movie-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
    }
    .movie-grid .movie-card { height: 355px; }
    .movie-grid .card-poster-wrap { height: 215px; }
    .modal-content { flex-direction: column; padding: 18px; max-height: 92vh; gap: 14px; }
    .modal-poster-wrap { width: 140px; height: 210px; margin: 0 auto; }
    .chat-wrapper { bottom: 14px; right: 14px; }
    .nova-chathead { width: 64px; height: 64px; }
    .chat-modal { width: calc(100vw - 24px); bottom: 76px; }
    .media-badge, .r18-badge, .origin-country-badge { font-size: 0.58rem; padding: 2px 6px; }
}
</style>
</head>
<body>
<div class="cosmic-bg"></div>
<div class="cosmic-stars"></div>

<div class="app-layout">
<aside class="sidebar">
    <div class="sidebar-top-bar">
        <div class="logo-free-wrapper" id="homeLogoBtn" title="Return to Galaxy Home">
            <img src="CineMind-Logo.jpg" alt="CineMind Logo" class="logo-unboxed" id="mainBrandLogo">
            <h2 class="logo-brand-title">CineMind</h2>
        </div>

        <div class="top-controls-row">
            <div class="account-top-btn" id="openProfile" title="Click to view account or log in">
                <i class="fa-solid fa-user-astronaut" style="color: var(--secondary-glow); font-size: 1.15rem;"></i>
                <div class="account-info">
                    <span class="account-name" id="profileDisplayName">Guest User</span>
                    <span class="account-sub" id="profileSubText">Tap to Login</span>
                </div>
            </div>
            <button class="theme-toggle-btn" id="themeToggleBtn" type="button" title="Switch Light / Dark Galaxy Mode">
                <i class="fa-solid fa-sun" id="themeIcon" style="color: #fbbf24;"></i>
            </button>
        </div>
    </div>

    <ul class="nav-links">
        <li class="nav-item active" data-view="discover"><i class="fa-solid fa-compass" style="color: var(--secondary-glow);"></i> <span>Galaxy Home</span></li>
        <li class="nav-item" data-view="nova"><i class="fa-solid fa-wand-magic-sparkles" style="color: #00f2fe;"></i> <span>Nova AI</span></li>
        <li class="nav-item" data-view="dataviz"><i class="fa-solid fa-chart-line" style="color: #d946ef;"></i> <span>Analytics</span></li>
        <li class="nav-item" data-view="watchlist"><i class="fa-solid fa-bookmark" style="color: #38bdf8;"></i> <span>Watchlist</span></li>
        <li class="nav-item" data-view="favorites"><i class="fa-solid fa-heart" style="color: #f43f5e;"></i> <span>Favorites</span></li>
        <li class="nav-item" data-view="watched"><i class="fa-solid fa-circle-check" style="color: #10b981;"></i> <span>Watched + AI</span></li>
    </ul>
</aside>

<main class="main-content" id="scrollContainer">
    <div class="hero-banner" id="heroBanner">
        <div class="hero-slideshow" id="heroSlideshow"></div>
        <div class="hero-slideshow-overlay"></div>
        <div class="welcome-header">
            <h1 class="welcome-title">Hello <span class="text-gradient" id="welcomeName">Guest</span>,<br>Explore the Neural Cinema Galaxy.</h1>
        </div>
        <div class="hero-search-box">
            <div class="search-input-wrap">
                <i class="fa-solid fa-brain"></i>
                <input type="text" id="searchInput" placeholder="Search movies, BL/GL, real sports, true-crime docs, anime, or ask Nova...">
            </div>
            <button class="search-btn-submit" id="searchSubmitBtn" type="button"><i class="fa-solid fa-search"></i> Search</button>
        </div>
    </div>

    <div class="filter-panel" id="filterPanel">
        <!-- 1. TOP: NETFLIX-STYLE GENRE DROPDOWN + STREAMING APP, ORIGIN COUNTRY & REGION -->
        <div class="filter-dropdown-container">
            <div class="netflix-dropdown-wrap" id="netflixGenreDropdownWrap">
                <button type="button" class="netflix-genre-trigger" id="netflixGenreBtn">
                    <span><i class="fa-solid fa-table-cells-large" style="color:var(--primary-glow); margin-right:6px;"></i> <span id="netflixGenreLabel">Browse Genres (Netflix Menu)</span></span>
                    <i class="fa-solid fa-caret-down" style="color:var(--secondary-glow);"></i>
                </button>
                <div class="netflix-genre-menu" id="netflixGenreMenu"></div>
            </div>

            <div class="filter-select-wrapper">
                <label for="providerDropdown"><i class="fa-solid fa-circle-play"></i> Streaming App:</label>
                <select id="providerDropdown" class="custom-select">
                    <option value="">All Streaming Apps</option>
                    <option value="8">Netflix</option>
                    <option value="337">Disney+</option>
                    <option value="119">Prime Video</option>
                    <option value="1899">Max / HBO</option>
                    <option value="350">Apple TV+</option>
                    <option value="158">Viu</option>
                </select>
            </div>

            <div class="filter-select-wrapper">
                <label for="countryDropdown"><i class="fa-solid fa-earth-asia"></i> Origin Country:</label>
                <select id="countryDropdown" class="custom-select">
                    <option value="">🌍 All Countries</option>
                    <option value="PH">🇵🇭 Philippines</option>
                    <option value="KR">🇰🇷 South Korea</option>
                    <option value="TH">🇹🇭 Thailand</option>
                    <option value="US">🇺🇸 USA</option>
                    <option value="JP">🇯🇵 Japan</option>
                    <option value="CN">🇨🇳 China</option>
                    <option value="TW">🇹🇼 Taiwan</option>
                    <option value="GB">🇬🇧 UK</option>
                    <option value="ES">🇪🇸 Spain</option>
                    <option value="FR">🇫🇷 France</option>
                    <option value="IN">🇮🇳 India</option>
                </select>
            </div>

            <div class="filter-select-wrapper">
                <label for="regionDropdown"><i class="fa-solid fa-location-dot"></i> Streaming Region:</label>
                <select id="regionDropdown" class="custom-select">
                    <option value="PH">🇵🇭 Philippines</option>
                    <option value="US">🇺🇸 USA</option>
                    <option value="KR">🇰🇷 South Korea</option>
                    <option value="JP">🇯🇵 Japan</option>
                    <option value="GB">🇬🇧 UK</option>
                    <option value="TH">🇹🇭 Thailand</option>
                </select>
            </div>
        </div>

        <!-- 2. MIDDLE: FORMAT SELECTION & NOT-INTERESTED RESET -->
        <div class="filter-row filter-row-middle" id="mediaFilterRow">
            <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                <span class="filter-label"><i class="fa-solid fa-layer-group"></i> Format:</span>
                <button type="button" class="filter-pill active" data-media="all">🌌 All Formats</button>
                <button type="button" class="filter-pill" data-media="movie">🎬 Movies Only</button>
                <button type="button" class="filter-pill" data-media="tv">📺 TV Series, Shows & Dramas</button>
            </div>
            <button type="button" class="filter-pill" id="resetDislikedBtn" style="display:none; border-color:#f43f5e; color:#fda4af;" title="Reset hidden 'Not Interested' concepts">
                <i class="fa-solid fa-eye-slash"></i> <span id="dislikedCountText">0 Hidden</span> (Reset)
            </button>
        </div>

        <!-- 3. BOTTOM: MULTI-GENRE & SPECIAL CATEGORY FILTER ROW -->
        <div class="filter-row" id="genreFilterRow">
            <span class="filter-label"><i class="fa-solid fa-film"></i> Genres:</span>
            <button type="button" class="filter-pill active" data-genre="">All</button>
            <button type="button" class="filter-pill" data-genre="BL">💙 Boys' Love (BL)</button>
            <button type="button" class="filter-pill" data-genre="GL">💖 Girls' Love (GL)</button>
            <button type="button" class="filter-pill" data-genre="ANIME">⛩️ Anime</button>
            <button type="button" class="filter-pill" data-genre="KIDS">🧸 Kids & Family (Animated)</button>
            <button type="button" class="filter-pill" data-genre="SPORTS">🏆 Sports (Real-Life)</button>
            <button type="button" class="filter-pill" data-genre="99">🕵️ Documentaries</button>
            <button type="button" class="filter-pill" data-genre="28">Action</button>
            <button type="button" class="filter-pill" data-genre="12">Adventure</button>
            <button type="button" class="filter-pill" data-genre="35">Comedy</button>
            <button type="button" class="filter-pill" data-genre="80">Crime</button>
            <button type="button" class="filter-pill" data-genre="18">Drama</button>
            <button type="button" class="filter-pill" data-genre="14">Fantasy</button>
            <button type="button" class="filter-pill" data-genre="27">Horror</button>
            <button type="button" class="filter-pill" data-genre="9648">Mystery</button>
            <button type="button" class="filter-pill" data-genre="10749">Romance</button>
            <button type="button" class="filter-pill" data-genre="878">Sci-Fi</button>
            <button type="button" class="filter-pill" data-genre="53">Thriller</button>
        </div>
    </div>

    <div id="mainContainer" class="catalog-container"></div>
    <div id="infiniteSentinel" class="infinite-loader" style="display:none;">
        <i class="fa-solid fa-spinner fa-spin"></i> Warping more unique galaxy streams...
    </div>
</main>
</div>

<!-- MOVIE / SERIES DETAILS MODAL (WITH FULL CAST, CHARACTERS, DIRECTOR, WRITERS & CREW + EXACT GENRES) -->
<div class="modal-overlay" id="movieModal">
<div class="modal-content">
    <i class="fa-solid fa-xmark close-modal" id="closeModal"></i>
    <div class="modal-poster-wrap">
        <div class="badges-container" id="modalPosterBadges"></div>
        <img id="modalPoster" src="" alt="Poster" onerror="this.onerror=null;this.src=NO_POSTER">
    </div>
    <div class="modal-info">
        <h2 class="modal-title" id="modalTitle">Loading...</h2>
        <div class="modal-meta" id="modalMeta"></div>

        <!-- Exact Genres Row -->
        <div class="modal-exact-genres" id="modalExactGenres"></div>

        <div class="streaming-providers" id="modalProviders">
            <i class="fa-solid fa-tv"></i> <span>Checking streaming availability...</span>
        </div>

        <div class="ai-rationale-box">
            <span class="ai-rationale-title"><i class="fa-solid fa-brain"></i> CineMind Explainable AI Rationale (XAI)</span>
            <span class="ai-rationale-text" id="modalRationale">Analyzing vector confidence...</span>
        </div>

        <p class="modal-overview" id="modalOverview"></p>

        <!-- Starring Cast, Characters, Director, Writers & Crew Box -->
        <div class="credits-box" id="modalCreditsBox">
            <div class="credits-crew-grid" id="modalCrewGrid">
                <div class="credits-crew-item"><strong>Director / Creator</strong><span>Loading...</span></div>
                <div class="credits-crew-item"><strong>Writers</strong><span>Loading...</span></div>
                <div class="credits-crew-item"><strong>Key Crew & Producers</strong><span>Loading...</span></div>
            </div>
            <div style="font-size:0.78rem; font-weight:700; color:var(--secondary-glow);">
                <i class="fa-solid fa-users"></i> Starring Cast & Characters:
            </div>
            <div class="credits-cast-list" id="modalCastList"></div>
        </div>

        <div class="modal-actions">
            <button type="button" class="btn-action btn-trailer" id="trailerBtn"><i class="fa-solid fa-play"></i> Watch Trailer</button>
            <button type="button" class="btn-action" id="watchlistBtn"><i class="fa-solid fa-plus"></i> Watchlist</button>
            <button type="button" class="btn-action btn-fav" id="favoriteBtn"><i class="fa-solid fa-heart"></i> Favorite</button>
            <button type="button" class="btn-action btn-fav" id="watchedBtn"><i class="fa-solid fa-eye"></i> Mark Watched</button>
            <button type="button" class="btn-action btn-not-interested" id="notInterestedModalBtn" title="Hide this title and eliminate movies with the same concept">
                <i class="fa-solid fa-ban"></i> Not Interested
            </button>
        </div>

        <div id="modalSimilarBox" style="display:none; flex-direction:column; gap:8px; margin-top:8px; padding-top:10px; border-top:1px solid var(--glass-border);">
            <span style="font-size:0.84rem; font-weight:700; color:var(--secondary-glow);"><i class="fa-solid fa-wand-magic-sparkles"></i> AI Recommended Similar Titles:</span>
            <div class="modal-similar-strip" id="modalSimilarStrip"></div>
        </div>
    </div>
</div>
</div>

<!-- YOUTUBE TRAILER MODAL -->
<div class="modal-overlay" id="videoModal">
<div class="video-box" style="width: 820px; max-width: 100%; background: #0f0a28; border-radius: 24px; border: 1px solid var(--glass-border); overflow: hidden; display: flex; flex-direction: column;">
    <div style="padding: 16px 22px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--glass-border); gap: 12px; flex-wrap: wrap;">
        <h3 id="videoModalTitle" style="font-size: 1.05rem; font-weight:700; color:#fff;">Official Trailer</h3>
        <div style="display:flex; align-items:center; gap: 14px;">
            <a id="youtubeExternalBtn" href="#" target="_blank" rel="noopener noreferrer" class="btn-action btn-trailer" style="padding: 7px 14px; font-size: 0.8rem;">
                <i class="fa-brands fa-youtube"></i> Open on YouTube ↗
            </a>
            <i class="fa-solid fa-xmark close-modal" id="closeVideoModal" style="position:static; font-size:1.4rem; color:#fff;"></i>
        </div>
    </div>
    <div class="video-wrapper" style="position: relative; width: 100%; padding-bottom: 56.25%; background: #000;">
        <iframe id="youtubeIframe" src="" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;" allowfullscreen></iframe>
    </div>
</div>
</div>

<!-- SMART PROFILE / AUTH MODAL -->
<div class="modal-overlay" id="profileModal">
<div class="profile-box" style="width: 480px; max-width: 100%; max-height: 92vh; overflow-y: auto; background: var(--modal-bg); padding: 30px; border-radius: 26px; border: 1px solid var(--glass-border-hover); box-shadow: var(--shadow-heavy); display: flex; flex-direction: column; gap: 16px; position: relative;">
    <i class="fa-solid fa-xmark close-modal" id="closeProfileModal" style="top:20px; right:22px;"></i>
    <div style="display:flex; align-items:center; gap:12px;">
        <i class="fa-solid fa-shuttle-space" style="color: var(--secondary-glow); font-size: 1.5rem;"></i>
        <div>
            <h2 style="font-size: 1.3rem;" id="profileModalHeading">Welcome to CineMind Galaxy</h2>
            <p style="font-size: 0.8rem; color: var(--text-muted);" id="authMsg">Sign up or log in to sync your library, or calibrate your tastes below:</p>
        </div>
    </div>

    <div id="loggedInAccountView" class="user-info-card" style="display:none;">
        <div style="display:flex; align-items:center; gap:14px;">
            <div style="width:54px; height:54px; border-radius:50%; background:linear-gradient(135deg, var(--primary-glow), var(--secondary-glow)); display:flex; align-items:center; justify-content:center; font-size:1.4rem; font-weight:800; color:#fff; flex-shrink:0;" id="accountAvatarInitial">U</div>
            <div style="display:flex; flex-direction:column; gap:3px;">
                <span style="font-size:1.1rem; font-weight:800;" id="loggedInUsernameDisplay">@username</span>
                <span style="font-size:0.76rem; color:#10b981; font-weight:700;"><i class="fa-solid fa-cloud-arrow-up"></i> Cloud Profile Active & Synced</span>
            </div>
        </div>
        <div class="user-stat-row">
            <div class="user-stat-pill">
                <strong id="accWatchlistCount">0</strong>
                <span>Watchlist</span>
            </div>
            <div class="user-stat-pill">
                <strong id="accFavoritesCount">0</strong>
                <span>Favorites</span>
            </div>
            <div class="user-stat-pill">
                <strong id="accWatchedCount">0</strong>
                <span>Watched</span>
            </div>
        </div>
        <div style="font-size:0.8rem; color:var(--text-muted); line-height:1.4;">
            <strong style="color:var(--secondary-glow);">Calibrated Genres:</strong> <span id="accGenresList">None selected</span>
        </div>
    </div>

    <div class="pref-group" id="guestAuthInputs" style="display:flex; flex-direction:column; gap:10px;">
        <input type="text" id="authUsername" placeholder="Username..." style="width: 100%; background: var(--input-bg); border: 1px solid var(--glass-border); border-radius: 14px; padding: 12px 16px; color: var(--text-main); outline: none; font-size: 0.92rem;">
        <input type="password" id="authPassword" placeholder="Password (6+ chars)..." style="width: 100%; background: var(--input-bg); border: 1px solid var(--glass-border); border-radius: 14px; padding: 12px 16px; color: var(--text-main); outline: none; font-size: 0.92rem;">
    </div>

    <div id="signupGenres" style="display:flex; flex-direction:column; gap:10px; background: rgba(124,58,237,0.08); padding: 14px; border-radius: 16px; border: 1px solid var(--glass-border);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.84rem; font-weight:700; color:var(--secondary-glow);"><i class="fa-solid fa-sparkles"></i> Pick at least 3 Genres You Love:</span>
            <span id="genreCountBadge" style="font-size:0.76rem; font-weight:700; color:var(--primary-glow);">0 / 3+ selected</span>
        </div>
        <div id="genrePicker" style="display:flex; flex-wrap:wrap; gap:8px;"></div>
    </div>

    <div id="guestAuthButtons" style="display: flex; flex-direction: column; gap: 12px;">
        <div style="display: flex; gap: 10px;">
            <button type="button" class="btn-action" id="loginBtn" style="flex:1; justify-content:center;"><i class="fa-solid fa-right-to-bracket"></i> Log In</button>
            <button type="button" class="btn-action btn-fav" id="signupBtn" style="flex:1; justify-content:center; border-color: var(--primary-glow);"><i class="fa-solid fa-user-plus"></i> Sign Up</button>
        </div>
        <div style="display:flex; align-items:center; gap:10px; margin: 2px 0;">
            <div style="flex:1; height:1px; background:var(--glass-border);"></div>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:600;">OR</span>
            <div style="flex:1; height:1px; background:var(--glass-border);"></div>
        </div>
        <button type="button" class="btn-action btn-fav" id="continueGuestBtn" style="width:100%; justify-content:center; background: rgba(0, 242, 254, 0.12); border-color: rgba(0, 242, 254, 0.4);">
            <i class="fa-solid fa-user-astronaut"></i> Continue as Guest (Apply Selected Genres)
        </button>
    </div>

    <div id="loggedInActionButtons" style="display:none; flex-direction:column; gap:10px;">
        <button type="button" class="btn-action" id="saveUserGenresBtn" style="width:100%; justify-content:center;">
            <i class="fa-solid fa-floppy-disk"></i> Save Updated Genre Preferences
        </button>
        <button type="button" class="btn-action btn-trailer" id="logoutBtn" style="width:100%; justify-content:center;">
            <i class="fa-solid fa-right-from-bracket"></i> Log Out of Account
        </button>
    </div>
</div>
</div>

<!-- FLOATING NOVA AI ASSISTANT -->
<div class="chat-wrapper" id="chatWrapper">
    <div class="chat-tooltip" id="chatTooltip">Ask Nova AI ✨</div>
    <div class="chat-modal" id="chatModal">
        <div class="chat-header">
            <div style="display:flex; align-items:center; gap:8px;">
                <img src="nova.png" alt="Nova" class="nova-avatar-animated" onclick="triggerTiltAnimation(this)" style="width:32px; height:32px; object-fit:contain;" onerror="this.src='CineMind-Logo.jpg'">
                <span>Nova AI</span>
                <span style="font-size:0.68rem; background:rgba(16,185,129,0.2); color:#10b981; padding:2px 8px; border-radius:10px; border:1px solid rgba(16,185,129,0.4);">Online</span>
            </div>
            <div style="display:flex; align-items:center; gap:12px;">
                <i class="fa-solid fa-broom" title="Clear Nova Memory" onclick="clearNovaMemory()" style="cursor:pointer; color:var(--text-muted); font-size:0.9rem;"></i>
                <i class="fa-solid fa-xmark close-chat" id="closeChat" style="cursor: pointer;"></i>
            </div>
        </div>
        <div class="chat-body" id="chatHistory"></div>
        <div class="quick-chips">
            <span class="chip" onclick="sendQuickPrompt('Thai Boys Love series recommendations')">💙 Thai BL Hits</span>
            <span class="chip" onclick="sendQuickPrompt('Girls Love GL series and movies')">💖 Best GL Picks</span>
            <span class="chip" onclick="sendQuickPrompt('True crime documentaries like Jeffrey Dahmer')">🕵️ True Crime Docs</span>
            <span class="chip" onclick="sendQuickPrompt('Real life sports documentaries like FIFA and Formula 1')">🏆 Real Sports</span>
        </div>
        <div class="chat-footer">
            <input type="text" id="chatInput" placeholder="Ask a movie question, country, plot, or mood..." autocomplete="off">
            <button type="button" class="send-btn" id="sendBtn" title="Send to Nova"><i class="fa-solid fa-paper-plane" style="color: white; font-size: 0.85rem;"></i></button>
        </div>
    </div>
    <div class="nova-chathead" id="chatToggle" title="Tap to open Nova AI!">
        <img src="nova.png" alt="Nova" onerror="this.src='CineMind-Logo.jpg'">
    </div>
</div>

<script>
const TMDB_API_KEY = "7c7e21b0fe58e5868e262c9bd6b8e7e9";
const BACKEND_URL = "https://cinemind-live.onrender.com";

const NO_POSTER = `data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='500' height='750'><rect width='100%' height='100%' fill='%23160f38'/><text x='50%' y='50%' fill='%2394a3b8' font-size='28' text-anchor='middle' font-family='sans-serif'>CineMind Poster</text></svg>`;

// Unboxed Transparent Fallback Logo (NO CIRCLE)
const FALLBACK_LOGO_SVG = `data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120'><text x='50%' y='56%' font-size='78' text-anchor='middle' dominant-baseline='middle'>🧠</text></svg>`;
const LOGO_CANDIDATES = ['CineMind-Logo.jpg', 'CineMind-Logo.png', 'logo.png', 'logo.jpg', 'assets/CineMind-Logo.jpg', 'assets/logo.png', FALLBACK_LOGO_SVG];
let logoTryIdx = 0;
const mainBrandLogo = document.getElementById('mainBrandLogo');
mainBrandLogo.onerror = function() {
    logoTryIdx++;
    if (logoTryIdx < LOGO_CANDIDATES.length) {
        this.src = LOGO_CANDIDATES[logoTryIdx];
    } else {
        this.onerror = null;
    }
};

function triggerTiltAnimation(el) {
    if (!el) return;
    el.classList.remove('tilting');
    void el.offsetWidth;
    el.classList.add('tilting');
    setTimeout(() => el.classList.remove('tilting'), 700);
}

let currentMovieData = null;
let currentUser = localStorage.getItem('cinemind_auth_user') || null;
let watchlist = [];
let favorites = [];
let watchedMovies = JSON.parse(localStorage.getItem(`cinemind_watched_${currentUser || 'guest'}`) || '[]');
let selectedRegion = localStorage.getItem('cinemind_region') || "PH";

// "Not Interested" Concept Elimination State
let notInterestedState = JSON.parse(localStorage.getItem(`cinemind_not_interested_${currentUser || 'guest'}`) || '{"ids":[],"keywords":[],"genrePairs":[],"titles":[]}');

function saveNotInterestedState() {
    localStorage.setItem(`cinemind_not_interested_${currentUser || 'guest'}`, JSON.stringify(notInterestedState));
    updateDislikedBadgeUI();
}

function updateDislikedBadgeUI() {
    const btn = document.getElementById('resetDislikedBtn');
    const txt = document.getElementById('dislikedCountText');
    if (!btn || !txt) return;
    const count = (notInterestedState.ids || []).length;
    if (count > 0) {
        btn.style.display = 'inline-flex';
        txt.textContent = `${count} Not Interested Hidden`;
    } else {
        btn.style.display = 'none';
    }
}

document.getElementById('resetDislikedBtn').onclick = () => {
    if (confirm("Reset your 'Not Interested' list and restore hidden movie concepts?")) {
        notInterestedState = { ids: [], keywords: [], genrePairs: [], titles: [] };
        saveNotInterestedState();
        initEndlessNetflixHome();
    }
};

let conversationHistory = JSON.parse(sessionStorage.getItem('cinemind_nova_history') || '[]');
let lastNovaMovies = JSON.parse(sessionStorage.getItem('cinemind_nova_movies') || '[]');
let lastNovaQuery = sessionStorage.getItem('cinemind_nova_query') || '';

let currentView = "discover";
let selectedMedia = "all";
let selectedProvider = "";
let selectedGenres = new Set();
let selectedCountry = "";
let activeSearchQuery = "";
let analyticsChartInstance = null;

let displayedMovieIds = new Set();
let r18Cache = new Map();
let originCountryCache = new Map();
let movieKeywordCache = new Map();

let infiniteMode = "rows";
let nextRowIndex = 0;
let emptyBatchStreak = 0;
let streamExhausted = false;
let searchPage = 1;
let searchTotalPages = 1;
let isFetchingMore = false;

const PROVIDER_NAMES = {
    "8": "Netflix", "337": "Disney+", "119": "Prime Video",
    "1899": "Max / HBO", "350": "Apple TV+", "158": "Viu"
};

const COUNTRY_NAMES = {
    KR: "South Korea 🇰🇷", PH: "Philippines 🇵🇭", US: "USA 🇺🇸",
    JP: "Japan 🇯🇵", GB: "UK 🇬🇧", IN: "India 🇮🇳",
    FR: "France 🇫🇷", ES: "Spain 🇪🇸", TH: "Thailand 🇹🇭",
    CN: "China 🇨🇳", HK: "Hong Kong 🇭🇰", TW: "Taiwan 🇹🇼",
    ID: "Indonesia 🇮🇩", DE: "Germany 🇩🇪", IT: "Italy 🇮🇹",
    MX: "Mexico 🇲🇽", CA: "Canada 🇨🇦", AU: "Australia 🇦🇺", BR: "Brazil 🇧🇷"
};

const LANG_TO_COUNTRY = {
    tl: "PH", fil: "PH", ko: "KR", th: "TH", ja: "JP",
    hi: "IN", ta: "IN", te: "IN", fr: "FR", es: "ES",
    zh: "CN", cn: "HK", id: "ID", de: "DE", it: "IT",
    pt: "BR", en: "US"
};

// Complete Genre Lookup Map (Movies + TV + Custom Categories)
const ALL_GENRE_LABELS = {
    "28": "Action", "12": "Adventure", "16": "Animation", "35": "Comedy",
    "80": "Crime", "99": "Documentary", "18": "Drama", "10751": "Kids & Family",
    "14": "Fantasy", "36": "History", "27": "Horror", "10402": "Music",
    "9648": "Mystery", "10749": "Romance", "878": "Sci-Fi", "53": "Thriller",
    "10752": "War", "37": "Western", "10759": "Action & Adventure",
    "10762": "Kids", "10765": "Sci-Fi & Fantasy", "10768": "War & Politics",
    "BL": "Boys' Love (BL)", "GL": "Girls' Love (GL)", "ANIME": "Anime",
    "KIDS": "Kids & Family", "SPORTS": "Sports"
};

const GENRE_OPTIONS = {
    "BL": "💙 Boys' Love (BL)",
    "GL": "💖 Girls' Love (GL)",
    "ANIME": "⛩️ Anime",
    "KIDS": "🧸 Kids & Family",
    "SPORTS": "🏆 Sports (Real-Life)",
    "99": "🕵️ Documentaries",
    "28": "Action",
    "12": "Adventure",
    "35": "Comedy",
    "80": "Crime",
    "18": "Drama",
    "14": "Fantasy",
    "27": "Horror",
    "9648": "Mystery",
    "10749": "Romance",
    "878": "Sci-Fi",
    "53": "Thriller"
};

// Curated High-Precision Lists for BL, GL, Real-Life Sports & True-Crime Documentaries
const CURATED_SPECIAL_TITLES = {
    BL: [
        { title: "KinnPorsche", media_type: "tv", year: 2022, why: "Hit Thai Boys' Love action-romance drama." },
        { title: "2gether: The Series", media_type: "tv", year: 2020, why: "Iconic Thai Boys' Love campus romance series." },
        { title: "Bad Buddy", media_type: "tv", year: 2021, why: "Beloved Thai Boys' Love enemies-to-lovers series." },
        { title: "Semantic Error", media_type: "tv", year: 2022, why: "Acclaimed Korean Boys' Love campus romance." },
        { title: "Cherry Magic! Thirty Years of Virginity Can Make You a Wizard?!", media_type: "tv", year: 2020, why: "Heartwarming Japanese Boys' Love romantic comedy." },
        { title: "The Eighth Sense", media_type: "tv", year: 2023, why: "Emotional Korean Boys' Love drama." },
        { title: "I Told Sunset About You", media_type: "tv", year: 2020, why: "Critically acclaimed coming-of-age Thai BL drama." },
        { title: "Moonlight Chicken", media_type: "tv", year: 2023, why: "Award-winning Thai Boys' Love series." },
        { title: "Last Twilight", media_type: "tv", year: 2023, why: "Deeply moving Thai BL romance series." },
        { title: "Young Royals", media_type: "tv", year: 2021, why: "Hit Boys' Love royal boarding school drama." },
        { title: "Heartstopper", media_type: "tv", year: 2022, why: "Sweet Boys' Love teen romance series." },
        { title: "Red, White & Royal Blue", media_type: "movie", year: 2023, why: "Popular Boys' Love romantic comedy film." },
        { title: "Your Name Engraved Herein", media_type: "movie", year: 2020, why: "Landmark Taiwanese Boys' Love romantic drama." }
    ],
    GL: [
        { title: "GAP The Series", media_type: "tv", year: 2022, why: "Phenomenal Thai Girls' Love office romance series." },
        { title: "The Secret of Us", media_type: "tv", year: 2024, why: "Hit Thai Girls' Love romantic drama starring LingOrm." },
        { title: "23.5", media_type: "tv", year: 2024, why: "Sweet Thai Girls' Love high school rom-com." },
        { title: "Pluto", media_type: "tv", year: 2024, why: "Emotional Thai Girls' Love mystery-romance series." },
        { title: "Blank The Series", media_type: "tv", year: 2024, why: "Popular Thai Girls' Love romance series." },
        { title: "Affair", media_type: "tv", year: 2024, why: "Trending Thai Girls' Love drama series." },
        { title: "The Loyal Pin", media_type: "tv", year: 2024, why: "Period Thai Girls' Love romance starring FreenBecky." },
        { title: "Uranus 2324", media_type: "movie", year: 2024, why: "Sci-Fi Thai Girls' Love movie starring Freen & Becky." },
        { title: "The Handmaiden", media_type: "movie", year: 2016, why: "Acclaimed Korean Girls' Love psychological thriller." },
        { title: "Portrait of a Lady on Fire", media_type: "movie", year: 2019, why: "Masterpiece Girls' Love historical romance." },
        { title: "Carol", media_type: "movie", year: 2015, why: "Classic Girls' Love romantic drama." },
        { title: "Bottoms", media_type: "movie", year: 2023, why: "Hilarious queer Girls' Love comedy." }
    ],
    SPORTS: [
        { title: "FIFA Uncovered", media_type: "tv", year: 2022, why: "Real-life FIFA world football documentary series." },
        { title: "Formula 1: Drive to Survive", media_type: "tv", year: 2019, why: "Real-life Formula 1 racing series." },
        { title: "The Last Dance", media_type: "tv", year: 2020, why: "Iconic NBA basketball championship series." },
        { title: "Beckham", media_type: "tv", year: 2023, why: "Real-life football legend David Beckham series." },
        { title: "WWE Raw", media_type: "tv", year: 1993, why: "Live-action professional wrestling flagship show." },
        { title: "Vince McMahon: Mr. McMahon", media_type: "tv", year: 2024, why: "Real-life WWE wrestling history series." },
        { title: "Sprint", media_type: "tv", year: 2024, why: "Real-life track & field world championship series." },
        { title: "Quarterback", media_type: "tv", year: 2023, why: "Real-life NFL football series." },
        { title: "Rush", media_type: "movie", year: 2013, why: "Live-action Formula 1 racing biographical drama." },
        { title: "Ford v Ferrari", media_type: "movie", year: 2019, why: "Live-action Le Mans championship racing drama." },
        { title: "Creed", media_type: "movie", year: 2015, why: "Hard-hitting live-action championship boxing film." },
        { title: "King Richard", media_type: "movie", year: 2021, why: "True story of tennis legends Venus and Serena Williams." },
        { title: "Moneyball", media_type: "movie", year: 2011, why: "True-story Major League Baseball drama." },
        { title: "The Iron Claw", media_type: "movie", year: 2023, why: "True-story professional wrestling drama." }
    ],
    DOC: [
        { title: "Conversations with a Killer: The Jeffrey Dahmer Tapes", media_type: "tv", year: 2022, why: "True-crime documentary series examining Jeffrey Dahmer." },
        { title: "Monster: The Jeffrey Dahmer Story", media_type: "tv", year: 2022, why: "Biographical true-crime series on Jeffrey Dahmer." },
        { title: "Night Stalker: The Hunt for a Serial Killer", media_type: "tv", year: 2021, why: "Gripping true-crime documentary series." },
        { title: "Don't F**k with Cats: Hunting an Internet Killer", media_type: "tv", year: 2019, why: "Investigative true-crime documentary series." },
        { title: "Making a Murderer", media_type: "tv", year: 2015, why: "Landmark true-crime documentary series." },
        { title: "American Nightmare", media_type: "tv", year: 2024, why: "True-crime investigative documentary series." },
        { title: "The Tinder Swindler", media_type: "movie", year: 2022, why: "Hit true-crime investigative documentary." },
        { title: "American Murder: The Family Next Door", media_type: "movie", year: 2020, why: "True-crime documentary film." },
        { title: "Girl in the Picture", media_type: "movie", year: 2022, why: "Acclaimed true-crime mystery documentary." },
        { title: "Our Planet", media_type: "tv", year: 2019, why: "Landmark nature documentary series." },
        { title: "13th", media_type: "movie", year: 2016, why: "Oscar-nominated historical documentary." }
    ]
};

// Build Netflix Multi-Column Genre Menu
const netflixGenreBtn = document.getElementById('netflixGenreBtn');
const netflixGenreMenu = document.getElementById('netflixGenreMenu');
const netflixGenreLabel = document.getElementById('netflixGenreLabel');

function renderNetflixGenreDropdown() {
    if (!netflixGenreMenu) return;
    netflixGenreMenu.innerHTML = '';
    const allItem = document.createElement('div');
    allItem.className = 'netflix-genre-item' + (selectedGenres.size === 0 ? ' active' : '');
    allItem.innerHTML = `<i class="fa-solid fa-globe"></i> All Genres`;
    allItem.onclick = () => {
        selectedGenres.clear();
        syncGenrePillsUI();
        netflixGenreMenu.classList.remove('open');
        initEndlessNetflixHome();
    };
    netflixGenreMenu.appendChild(allItem);

    Object.entries(GENRE_OPTIONS).forEach(([code, label]) => {
        const item = document.createElement('div');
        item.className = 'netflix-genre-item' + (selectedGenres.has(code) ? ' active' : '');
        item.textContent = label;
        item.onclick = () => {
            selectedGenres.clear();
            selectedGenres.add(code);
            syncGenrePillsUI();
            netflixGenreMenu.classList.remove('open');
            initEndlessNetflixHome();
        };
        netflixGenreMenu.appendChild(item);
    });
}

function syncGenrePillsUI() {
    const row = document.getElementById('genreFilterRow');
    if (row) {
        row.querySelectorAll('.filter-pill').forEach(btn => {
            const g = btn.getAttribute('data-genre');
            if (!g) {
                btn.classList.toggle('active', selectedGenres.size === 0);
            } else {
                btn.classList.toggle('active', selectedGenres.has(g));
            }
        });
    }
    if (netflixGenreLabel) {
        if (selectedGenres.size === 0) {
            netflixGenreLabel.textContent = "Browse Genres (Netflix Menu)";
        } else {
            const names = [...selectedGenres].map(k => GENRE_OPTIONS[k] || ALL_GENRE_LABELS[k] || k);
            netflixGenreLabel.textContent = names.join(' + ');
        }
    }
    renderNetflixGenreDropdown();
}

netflixGenreBtn.onclick = (e) => {
    e.stopPropagation();
    netflixGenreMenu.classList.toggle('open');
};
document.addEventListener('click', (e) => {
    if (!document.getElementById('netflixGenreDropdownWrap').contains(e.target)) {
        netflixGenreMenu.classList.remove('open');
    }
});

function resolveMovieOriginCountry(movie) {
    if (!movie) return "USA 🇺🇸";
    const key = `${movie.media_type || 'movie'}_${movie.id}`;
    if (originCountryCache.has(key)) return originCountryCache.get(key);

    if (Array.isArray(movie.origin_country) && movie.origin_country.length > 0) {
        const code = String(movie.origin_country[0]).toUpperCase();
        const label = COUNTRY_NAMES[code] || code;
        originCountryCache.set(key, label);
        return label;
    }
    if (typeof movie.origin_country === "string" && movie.origin_country.trim()) {
        const code = movie.origin_country.trim().toUpperCase();
        const label = COUNTRY_NAMES[code] || code;
        originCountryCache.set(key, label);
        return label;
    }
    if (Array.isArray(movie.production_countries) && movie.production_countries.length > 0) {
        const cObj = movie.production_countries[0];
        const code = (cObj.iso_3166_1 || "").toUpperCase();
        const label = COUNTRY_NAMES[code] || cObj.name || code;
        if (label) {
            originCountryCache.set(key, label);
            return label;
        }
    }
    if (selectedCountry && COUNTRY_NAMES[selectedCountry]) {
        return COUNTRY_NAMES[selectedCountry];
    }
    const lang = (movie.original_language || "").toLowerCase();
    if (LANG_TO_COUNTRY[lang]) {
        const code = LANG_TO_COUNTRY[lang];
        return COUNTRY_NAMES[code] || code;
    }
    return "Global 🌍";
}

function getExactGenreNames(movie) {
    if (!movie) return "Cinema";
    const names = [];
    if (movie._customGenreBadge) names.push(movie._customGenreBadge);
    if (Array.isArray(movie.genres) && movie.genres.length) {
        movie.genres.forEach(g => {
            if (g && g.name && !names.includes(g.name)) names.push(g.name);
        });
    }
    if (Array.isArray(movie.genre_ids) && movie.genre_ids.length) {
        movie.genre_ids.forEach(gid => {
            const label = ALL_GENRE_LABELS[String(gid)];
            if (label && !names.includes(label)) names.push(label);
        });
    }
    const lang = (movie.original_language || "").toLowerCase();
    const gids = (movie.genre_ids || (movie.genres || []).map(g => g.id)).map(Number);
    if (gids.includes(16) && ["ja", "ko", "zh"].includes(lang)) {
        const idx = names.indexOf("Animation");
        if (idx >= 0) names[idx] = "Anime";
        else if (!names.includes("Anime")) names.unshift("Anime");
    }
    return names.length ? names.slice(0, 3).join(" • ") : "Drama • Cinema";
}

// Check if movie is Animated / Cartoon (Used to keep Sports & Documentaries strictly live-action)
function isAnimatedOrCartoon(item) {
    if (!item) return false;
    const gids = (item.genre_ids || (item.genres || []).map(g => g.id)).map(Number);
    if (gids.includes(16)) return true;
    const text = `${item.title || item.name || ''} ${item.overview || ''}`.toLowerCase();
    return /\b(anime|animated|cartoon|pixar|dreamworks|studio ghibli|looney tunes|spongebob)\b/i.test(text);
}

// Check if movie is eliminated by "Not Interested" Concept Filter
function isEliminatedByNotInterested(movie) {
    if (!movie) return false;
    const mid = Number(movie.id);
    if ((notInterestedState.ids || []).includes(mid)) return true;

    const gids = (movie.genre_ids || (movie.genres || []).map(g => g.id)).map(Number).sort((a, b) => a - b);
    if (gids.length >= 2) {
        const pairKey = `${gids[0]}_${gids[1]}`;
        if ((notInterestedState.genrePairs || []).includes(pairKey)) {
            const titleWords = (movie.title || movie.name || "").toLowerCase().split(/\W+/).filter(w => w.length > 3);
            const overviewLower = (movie.overview || "").toLowerCase();
            if ((notInterestedState.keywords || []).some(kw => overviewLower.includes(kw) || titleWords.includes(kw))) {
                return true;
            }
        }
    }

    const combinedText = `${movie.title || movie.name || ''} ${movie.overview || ''}`.toLowerCase();
    let kwHits = 0;
    for (const kw of (notInterestedState.keywords || [])) {
        if (kw.length > 3 && combinedText.includes(kw)) {
            kwHits++;
            if (kwHits >= 2) return true;
        }
    }
    return false;
}

// Mark a Movie as "Not Interested" & Eliminate Same-Concept Movies
async function markMovieNotInterested(movie, cardEl = null) {
    if (!movie || !movie.id) return;
    const mid = Number(movie.id);
    const mType = movie.media_type === 'tv' ? 'tv' : 'movie';
    if (!notInterestedState.ids.includes(mid)) notInterestedState.ids.push(mid);

    const title = (movie.title || movie.name || "").toLowerCase();
    if (title && !notInterestedState.titles.includes(title)) notInterestedState.titles.push(title);

    const gids = (movie.genre_ids || (movie.genres || []).map(g => g.id)).map(Number).sort((a, b) => a - b);
    if (gids.length >= 2) {
        const pairKey = `${gids[0]}_${gids[1]}`;
        if (!notInterestedState.genrePairs.includes(pairKey)) notInterestedState.genrePairs.push(pairKey);
    }

    // Extract keywords from overview & TMDB keywords API
    const stopWords = new Set(["with", "from", "that", "this", "their", "they", "have", "were", "when", "where", "what", "into", "after", "before", "about", "movie", "series", "film", "life", "world", "young", "find", "finds", "must"]);
    const overviewWords = (movie.overview || "").toLowerCase().match(/\b[a-z]{5,14}\b/g) || [];
    overviewWords.filter(w => !stopWords.has(w)).slice(0, 5).forEach(w => {
        if (!notInterestedState.keywords.includes(w)) notInterestedState.keywords.push(w);
    });

    try {
        const kwRes = await fetch(`https://api.themoviedb.org/3/${mType}/${mid}/keywords?api_key=${TMDB_API_KEY}`).then(r => r.json());
        const kwArr = (kwRes.keywords || kwRes.results || []).map(k => (k.name || "").toLowerCase().trim()).filter(Boolean);
        kwArr.slice(0, 8).forEach(kw => {
            if (!notInterestedState.keywords.includes(kw)) notInterestedState.keywords.push(kw);
        });
    } catch (e) {}

    saveNotInterestedState();

    // Close modal if open and remove matching concept cards from DOM
    document.getElementById('movieModal').classList.remove('active');
    if (cardEl) cardEl.remove();

    document.querySelectorAll('.movie-card').forEach(el => {
        const cid = Number(el.getAttribute('data-movie-id'));
        const cConcept = (el.getAttribute('data-concept-text') || '').toLowerCase();
        if (cid === mid) {
            el.remove();
            return;
        }
        let matchCount = 0;
        for (const kw of (notInterestedState.keywords || [])) {
            if (kw.length > 3 && cConcept.includes(kw)) {
                matchCount++;
                if (matchCount >= 2) {
                    el.remove();
                    break;
                }
            }
        }
    });
}

const COUNTRY_QUERY_KEYWORDS = {
    "philippines": { code: "PH", lang: "tl", label: "Philippines 🇵🇭", preferredGenres: [18, 10749, 35, 27, 53] },
    "philippine":  { code: "PH", lang: "tl", label: "Philippines 🇵🇭", preferredGenres: [18, 10749, 35, 27, 53] },
    "filipino":    { code: "PH", lang: "tl", label: "Philippines 🇵🇭", preferredGenres: [18, 10749, 35, 27, 53] },
    "pinoy":       { code: "PH", lang: "tl", label: "Philippines 🇵🇭", preferredGenres: [18, 10749, 35] },
    "tagalog":     { code: "PH", lang: "tl", label: "Philippines 🇵🇭", preferredGenres: [18, 10749, 35] },
    "korea":       { code: "KR", lang: "ko", label: "South Korea 🇰🇷", preferredGenres: [18, 10749, 53, 35, 28] },
    "korean":      { code: "KR", lang: "ko", label: "South Korea 🇰🇷", preferredGenres: [18, 10749, 53, 35, 28] },
    "kdrama":      { code: "KR", lang: "ko", label: "South Korea 🇰🇷", preferredGenres: [18, 10749, 35] },
    "k-drama":     { code: "KR", lang: "ko", label: "South Korea 🇰🇷", preferredGenres: [18, 10749, 35] },
    "japan":       { code: "JP", lang: "ja", label: "Japan 🇯🇵", preferredGenres: [16, 14, 27, 878, 18] },
    "japanese":    { code: "JP", lang: "ja", label: "Japan 🇯🇵", preferredGenres: [16, 14, 27, 878, 18] },
    "thailand":    { code: "TH", lang: "th", label: "Thailand 🇹🇭", preferredGenres: [27, 10749, 35, 28, 18] },
    "thai":        { code: "TH", lang: "th", label: "Thailand 🇹🇭", preferredGenres: [27, 10749, 35, 28, 18] },
    "spain":       { code: "ES", lang: "es", label: "Spain 🇪🇸", preferredGenres: [53, 80, 18] },
    "spanish":     { code: "ES", lang: "es", label: "Spain 🇪🇸", preferredGenres: [53, 80, 18] },
    "france":      { code: "FR", lang: "fr", label: "France 🇫🇷", preferredGenres: [18, 10749, 35] },
    "french":      { code: "FR", lang: "fr", label: "France 🇫🇷", preferredGenres: [18, 10749, 35] },
    "india":       { code: "IN", lang: "hi", label: "India 🇮🇳", preferredGenres: [28, 18, 10749, 35] },
    "indian":      { code: "IN", lang: "hi", label: "India 🇮🇳", preferredGenres: [28, 18, 10749, 35] },
    "bollywood":   { code: "IN", lang: "hi", label: "India 🇮🇳", preferredGenres: [28, 18, 10749] },
    "uk":          { code: "GB", lang: "en", label: "UK 🇬🇧", preferredGenres: [18, 80, 9648] },
    "british":     { code: "GB", lang: "en", label: "UK 🇬🇧", preferredGenres: [18, 80, 9648] },
    "usa":         { code: "US", lang: "en", label: "USA 🇺🇸", preferredGenres: [28, 878, 35, 18] },
    "american":    { code: "US", lang: "en", label: "USA 🇺🇸", preferredGenres: [28, 878, 35, 18] }
};

function detectCountryInQuery(text = "") {
    const clean = text.toLowerCase();
    for (const [kw, info] of Object.entries(COUNTRY_QUERY_KEYWORDS)) {
        if (new RegExp(`\\b${kw}\\b`, 'i').test(clean)) return info;
    }
    return null;
}

function detectGenresInQuery(text = "") {
    const lower = text.toLowerCase();
    const matched = [];
    const map = {
        28: ["action", "martial arts", "fight", "explosive"],
        12: ["adventure", "quest", "journey"],
        16: ["animation", "animated", "anime", "cartoon"],
        35: ["comedy", "funny", "hilarious", "romcom", "rom-com"],
        80: ["crime", "heist", "detective", "mafia", "gangster"],
        99: ["documentary", "documentaries", "docuseries", "true crime", "dahmer"],
        10751: ["kids", "family", "children"],
        18: ["drama", "emotional", "sad", "tearjerker"],
        14: ["fantasy", "magic", "dragon"],
        27: ["horror", "scary", "ghost", "creepy", "haunted", "slasher", "zombie"],
        9648: ["mystery", "whodunit", "suspense"],
        10749: ["romance", "romantic", "love", "sweet", "romcom", "rom-com"],
        878: ["sci-fi", "scifi", "science fiction", "space", "time travel", "alien"],
        53: ["thriller", "psychological", "twist", "dark"]
    };
    for (const [gid, words] of Object.entries(map)) {
        if (words.some(w => lower.includes(w))) matched.push(Number(gid));
    }
    return matched;
}

const MOVIE_TO_TV_GENRE = {
    "28": "10759", "12": "10759", "16": "16", "35": "35", "80": "80",
    "99": "99", "10751": "10762,10751", "18": "18", "14": "10765",
    "27": "9648", "9648": "9648", "10749": "18", "878": "10765", "53": "9648"
};

// ---------------- STRICT PORNOGRAPHIC & EROTIC FILM BLOCKER ----------------
const PORN_BLOCK_WORDS = [
    "porn", "porno", "pornographic", "xxx", "erotic", "erotica", "hentai", "jav",
    "av idol", "sex tape", "playboy", "penthouse", "nude", "nudity", "stripper",
    "prostitute", "prostitution", "brothel", "kama sutra", "bdsm", "fetish",
    "orgasm", "milf", "stepmom", "stepsister", "softcore", "pink film", "vivamax",
    "brazzers", "onlyfans", "emmanuelle", "nymphomaniac", "caligula",
    "365 days", "fifty shades", "scorpio nights", "silip", "uhaw", "laman",
    "boso", "sikretong malupit", "macho dancer", "tubero", "pamasahe",
    "selina's gold", "us x her", "bela luna", "kiskisan", "salitan",
    "lampas langit", "virgin forest", "kaliwaan", "purgatoryo", "doblado",
    "paupahan", "ang babaeng nawawala sa sarili", "kinsenas, katapusan",
    "boy bastos", "palitan", "tag-init", "balinsasayaw", "sugar baby",
    "tayuan", "haslers", "dilig", "kaluskos", "unli life", "totnak", "kantot",
    "libog", "malibog", "pokpok", "parausan", "halinghing", "pagnanasa",
    "angeli khang", "azi acosta", "aj raval", "robb guinto", "christine bermas",
    "ayanna misola", "cara gonzales", "yen durano", "apple dy", "denise esteban"
];

const PORN_BLOCK_REGEX = /\b(porn|porno|xxx|erotic|erotica|hentai|jav|sex tape|playboy|penthouse|nudity|stripper|prostitute|brothel|bdsm|fetish|orgasm|milf|softcore|pink film|vivamax|brazzers|onlyfans|nymphomaniac|threesome|foreplay|voyeur|voyeurism|adultery|mistress|seductress|lustful|kinky|sexploitation|bomba film|bold star)\b/i;

function isSafeNonPorn(item) {
    if (!item) return false;
    if (item.adult === true) return false;
    if (isEliminatedByNotInterested(item)) return false;

    const title = (item.title || item.name || "").toLowerCase().trim();
    const origTitle = (item.original_title || item.original_name || "").toLowerCase().trim();
    const overview = (item.overview || "").toLowerCase();
    const combined = `${title} ${origTitle} ${overview}`;

    if (PORN_BLOCK_REGEX.test(combined)) return false;
    for (const bad of PORN_BLOCK_WORDS) {
        if (title === bad || origTitle === bad || combined.includes(bad)) return false;
    }
    if ((item.vote_count || 0) < 35 && /\b(sex|sexual|nude|naked|seduce|seduction|lust|affair|steamy|intimate|passion|forbidden desire|bed|pleasure)\b/i.test(combined)) {
        return false;
    }
    return true;
}

const KNOWN_R18_TITLES = new Set([
    "deadpool", "deadpool 2", "deadpool & wolverine", "logan", "joker", "parasite",
    "oldboy", "oppenheimer", "john wick", "john wick: chapter 2", "john wick: chapter 3 - parabellum", "john wick: chapter 4",
    "saw", "hereditary", "midsommar", "the wolf of wall street", "pulp fiction",
    "fight club", "gone girl", "shutter island", "se7en", "american psycho",
    "saltburn", "the handmaiden", "squid game", "the boys", "euphoria",
    "game of thrones", "house of the dragon", "breaking bad", "dexter",
    "it", "the conjuring", "evil dead rise", "terrifier", "smile", "don't breathe",
    "the substance", "i saw the devil", "the chaser", "monster: the jeffrey dahmer story"
]);

function isGenuineR18(item) {
    if (!item || !isSafeNonPorn(item)) return false;
    const key = `${item.media_type || 'movie'}_${item.id}`;
    if (r18Cache.has(key)) return r18Cache.get(key) === true;
    if (item._isR18 === true || item.r18 === true) {
        r18Cache.set(key, true);
        return true;
    }

    const cert = (item.certification || "").toUpperCase().trim();
    if (["R-18", "R18", "TV-MA"].includes(cert)) {
        r18Cache.set(key, true);
        return true;
    }

    const titleLower = (item.title || item.name || "").toLowerCase().trim();
    const origTitleLower = (item.original_title || item.original_name || "").toLowerCase().trim();
    if (KNOWN_R18_TITLES.has(titleLower) || KNOWN_R18_TITLES.has(origTitleLower)) {
        r18Cache.set(key, true);
        return true;
    }

    const gids = (item.genre_ids || (item.genres || []).map(g => g.id)).map(Number);
    const overview = (item.overview || "").toLowerCase();
    const combinedText = `${titleLower} ${origTitleLower} ${overview}`;

    const disturbingHorrorKeywords = /\b(serial killer|gore|bloody|massacre|brutal|decapitation|mutilation|torture|psychopath|disturbing|slasher|cannibal|gruesome|autopsy|dismember|visceral|terrifier|sadistic|demon|possession|exorcism|cartel)\b/i;
    if ((gids.includes(27) || gids.includes(80) || gids.includes(53) || gids.includes(99)) && disturbingHorrorKeywords.test(combinedText)) {
        r18Cache.set(key, true);
        return true;
    }

    return false;
}

async function verifyCardMetadataAsync(movie, cardEl, badgeContainerEl, countryBadgeEl) {
    if (!movie || !movie.id) return;
    const mType = movie.media_type === 'tv' ? 'tv' : 'movie';
    const key = `${mType}_${movie.id}`;

    if (r18Cache.has(key) && originCountryCache.has(key)) {
        if (r18Cache.get(key) === "BLOCKED_PORN") {
            if (cardEl) cardEl.remove();
            return;
        }
        if (r18Cache.get(key) === true && badgeContainerEl && !badgeContainerEl.querySelector('.r18-badge')) {
            badgeContainerEl.insertAdjacentHTML('afterbegin', `<span class="r18-badge">R-18</span>`);
        }
        if (countryBadgeEl) {
            countryBadgeEl.innerHTML = `<i class="fa-solid fa-location-dot" style="color:var(--secondary-glow);"></i> ${originCountryCache.get(key)}`;
        }
        return;
    }

    try {
        const append = mType === 'tv' ? 'content_ratings,keywords' : 'release_dates,keywords';
        const res = await fetch(`https://api.themoviedb.org/3/${mType}/${movie.id}?api_key=${TMDB_API_KEY}&append_to_response=${append}`);
        const d = await res.json();
        if (!d || !d.id) return;

        const companies = (d.production_companies || []).map(c => (c.name || '').toLowerCase()).join(' ');
        const kwList = (d.keywords && (d.keywords.keywords || d.keywords.results) || []).map(k => (k.name || '').toLowerCase()).join(' ');
        if (
            d.adult === true
            || companies.includes('vivamax')
            || /\b(porn|porno|erotic|erotica|softcore|pink film|sexploitation|bdsm|hentai|jav|av idol|female nudity|male nudity|full frontal nudity|explicit sex|prostitution|brothel|stripper)\b/i.test(kwList)
        ) {
            r18Cache.set(key, "BLOCKED_PORN");
            if (cardEl) cardEl.remove();
            return;
        }

        let exactCountryCode = "";
        if (Array.isArray(d.origin_country) && d.origin_country.length > 0) {
            exactCountryCode = d.origin_country[0].toUpperCase();
        } else if (Array.isArray(d.production_countries) && d.production_countries.length > 0) {
            exactCountryCode = (d.production_countries[0].iso_3166_1 || "").toUpperCase();
        }
        if (exactCountryCode) {
            const cLabel = COUNTRY_NAMES[exactCountryCode] || exactCountryCode;
            originCountryCache.set(key, cLabel);
            movie.origin_country = [exactCountryCode];
            if (countryBadgeEl) {
                countryBadgeEl.innerHTML = `<i class="fa-solid fa-location-dot" style="color:var(--secondary-glow);"></i> ${cLabel}`;
            }
        }

        let detectedR18 = isGenuineR18(d);
        if (/\b(gore|slasher|extreme violence|serial killer|massacre|torture)\b/i.test(kwList)) {
            detectedR18 = true;
        }

        if (mType === 'movie' && d.release_dates && d.release_dates.results) {
            for (const cEntry of d.release_dates.results) {
                const iso = (cEntry.iso_3166_1 || '').toUpperCase();
                if (!['US', 'PH'].includes(iso)) continue;
                for (const rd of (cEntry.release_dates || [])) {
                    const cert = (rd.certification || '').toUpperCase().trim();
                    if (['NC-17', 'X'].includes(cert)) {
                        r18Cache.set(key, "BLOCKED_PORN");
                        if (cardEl) cardEl.remove();
                        return;
                    }
                    if ((iso === 'PH' && ['R-18', 'R18'].includes(cert)) || (iso === 'US' && cert === 'R' && isGenuineR18(d))) {
                        detectedR18 = true;
                    }
                }
            }
        } else if (mType === 'tv' && d.content_ratings && d.content_ratings.results) {
            for (const cr of d.content_ratings.results) {
                const iso = (cr.iso_3166_1 || '').toUpperCase();
                if (!['US', 'PH', 'KR', 'TH'].includes(iso)) continue;
                const rating = (cr.rating || '').toUpperCase().trim();
                if (['TV-MA', 'R-18', 'R18', '19'].includes(rating)) {
                    detectedR18 = true;
                }
            }
        }

        r18Cache.set(key, detectedR18);
        movie._isR18 = detectedR18;

        if (detectedR18 && badgeContainerEl && !badgeContainerEl.querySelector('.r18-badge')) {
            badgeContainerEl.insertAdjacentHTML('afterbegin', `<span class="r18-badge">R-18</span>`);
        }
    } catch (e) {}
}

// ---------------- CLIENT-SIDE AI + TMDB SYNOPSIS PLOT ASSIST ----------------
async function clientSidePlotAssist(userQuery) {
    const guesses = [];
    try {
        const sys = `Return ONLY a JSON array of 5 objects: [{"title":"Exact Movie or TV Series Title","year":2021,"media_type":"tv"|"movie","why":"1 sentence how it matches"}]. Identify the exact movie, TV series, BL drama, GL drama, documentary, real-life sports show, or anime described by the user.`;
        const aiRes = await fetch("https://text.pollinations.ai/openai", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                model: "openai",
                messages: [
                    { role: "system", content: sys },
                    { role: "user", content: userQuery }
                ],
                temperature: 0.1
            })
        });
        if (aiRes.ok) {
            const raw = await aiRes.text();
            const m = raw.match(/\[[\s\S]*\]/);
            if (m) {
                const parsed = JSON.parse(m[0]);
                if (Array.isArray(parsed)) {
                    parsed.forEach(g => {
                        if (g && g.title) guesses.push(g);
                    });
                }
            }
        }
    } catch (e) {}
    return guesses;
}

// Light / Dark Theme Toggle
const savedTheme = localStorage.getItem('cinemind_theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);
function updateThemeIcon() {
    const t = document.documentElement.getAttribute('data-theme');
    const icon = document.getElementById('themeIcon');
    icon.className = t === 'light' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
    icon.style.color = t === 'light' ? '#7c3aed' : '#fbbf24';
}
updateThemeIcon();
document.getElementById('themeToggleBtn').onclick = () => {
    const cur = document.documentElement.getAttribute('data-theme');
    const next = cur === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('cinemind_theme', next);
    updateThemeIcon();
};

const ENDLESS_ROW_CATALOG = [
    { title: "🔥 Blockbuster Movies Trending", media: "movie", path: "/discover/movie", params: "sort_by=popularity.desc&page=1" },
    { title: "📺 Binge-Worthy TV Series & K-Dramas", media: "tv", path: "/discover/tv", params: "sort_by=popularity.desc&page=1" },
    { title: "💙 Trending Boys' Love (BL) Series & Films", media: "tv", specialCategory: "BL" },
    { title: "💖 Trending Girls' Love (GL) Series & Films", media: "tv", specialCategory: "GL" },
    { title: "⛩️ Visionary Anime Series & Films (JP / KR / CN)", media: "tv", specialCategory: "ANIME" },
    { title: "🧸 Kids, Family & Animated Adventures", media: "movie", specialCategory: "KIDS" },
    { title: "🏆 Real-Life Sports Action (FIFA, F1, WWE & Legends)", media: "tv", specialCategory: "SPORTS" },
    { title: "🕵️ True-Crime & Gripping Documentaries", media: "tv", specialCategory: "DOC" },
    { title: "🇵🇭 Hit Filipino Dramas & Movies", media: "movie", path: "/discover/movie", params: "with_origin_country=PH&sort_by=popularity.desc&page=1" },
    { title: "🇹🇭 Trending Thai Cinema & Series", media: "tv", path: "/discover/tv", params: "with_origin_country=TH&sort_by=popularity.desc&page=1" },
    { title: "🧠 Mind-Bending Sci-Fi & Portals", media: "movie", path: "/discover/movie", params: "with_genres=878&sort_by=popularity.desc&page=1" },
    { title: "🇰🇷 Hit Korean Dramas & Series", media: "tv", path: "/discover/tv", params: "with_origin_country=KR&sort_by=popularity.desc&page=1" },
    { title: "💥 High-Octane Action Thrillers", media: "movie", path: "/discover/movie", params: "with_genres=28,53&sort_by=popularity.desc&page=1" },
    { title: "💕 Heartfelt & Emotional Romances", media: "movie", path: "/discover/movie", params: "with_genres=10749&sort_by=popularity.desc&page=1" },
    { title: "👻 Spine-Chilling Supernatural Horror", media: "movie", path: "/discover/movie", params: "with_genres=27&sort_by=popularity.desc&page=1" }
];

let userGenres = JSON.parse(localStorage.getItem('cinemind_genres') || '[]');
let signupGenres = new Set(userGenres.map(String));

const genrePicker = document.getElementById('genrePicker');
const genreCountBadge = document.getElementById('genreCountBadge');

function updateGenreBadge() {
    const c = signupGenres.size;
    genreCountBadge.textContent = `${c} / 3+ selected`;
    genreCountBadge.style.color = c >= 3 ? '#10b981' : 'var(--primary-glow)';
}

function renderGenrePills() {
    genrePicker.innerHTML = '';
    Object.entries(GENRE_OPTIONS).forEach(([id, name]) => {
        const pill = document.createElement('button');
        pill.type = 'button';
        pill.className = 'filter-pill' + (signupGenres.has(String(id)) ? ' active' : '');
        pill.textContent = name;
        pill.onclick = () => {
            const sid = String(id);
            if (signupGenres.has(sid)) { signupGenres.delete(sid); pill.classList.remove('active'); }
            else { signupGenres.add(sid); pill.classList.add('active'); }
            updateGenreBadge();
        };
        genrePicker.appendChild(pill);
    });
    updateGenreBadge();
}
renderGenrePills();
renderNetflixGenreDropdown();
updateDislikedBadgeUI();

const mainContainer = document.getElementById('mainContainer');
const infiniteSentinel = document.getElementById('infiniteSentinel');
const searchInput = document.getElementById('searchInput');
const searchSubmitBtn = document.getElementById('searchSubmitBtn');
const filterPanel = document.getElementById('filterPanel');
const heroBanner = document.getElementById('heroBanner');
const navItems = document.querySelectorAll('.nav-item');

const providerDropdown = document.getElementById('providerDropdown');
const countryDropdown = document.getElementById('countryDropdown');
const regionDropdown = document.getElementById('regionDropdown');

if (regionDropdown) regionDropdown.value = selectedRegion;

providerDropdown.onchange = (e) => {
    selectedProvider = e.target.value;
    initEndlessNetflixHome();
};

countryDropdown.onchange = (e) => {
    selectedCountry = e.target.value;
    initEndlessNetflixHome();
};

regionDropdown.onchange = (e) => {
    selectedRegion = e.target.value;
    localStorage.setItem('cinemind_region', selectedRegion);
    initEndlessNetflixHome();
};

// ---------------- SLANTED RANDOM + RECENT HERO BANNER SLIDESHOW ----------------
async function initHeroBannerSlideshow() {
    const slideshowContainer = document.getElementById('heroSlideshow');
    if (!slideshowContainer) return;
    try {
        const randPage = Math.floor(Math.random() * 5) + 2;
        const [recentRes, randomRes1, randomRes2] = await Promise.all([
            fetch(`https://api.themoviedb.org/3/trending/all/week?api_key=${TMDB_API_KEY}&page=1`).then(r => r.json()).catch(() => ({ results: [] })),
            fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&sort_by=popularity.desc&page=${randPage}`).then(r => r.json()).catch(() => ({ results: [] })),
            fetch(`https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&include_adult=false&sort_by=popularity.desc&page=${randPage}`).then(r => r.json()).catch(() => ({ results: [] }))
        ]);

        const recentList = (recentRes.results || []).filter(isSafeNonPorn);
        const randomList = [...(randomRes1.results || []), ...(randomRes2.results || [])]
            .filter(isSafeNonPorn)
            .sort(() => Math.random() - 0.5);

        const combined = [...recentList, ...randomList];
        const backdrops = [];
        const posters = [];
        const seenB = new Set(), seenP = new Set();

        combined.forEach(m => {
            if (m.backdrop_path && !seenB.has(m.backdrop_path)) {
                seenB.add(m.backdrop_path);
                backdrops.push(`https://image.tmdb.org/t/p/w1280${m.backdrop_path}`);
            }
            if (m.poster_path && !seenP.has(m.poster_path)) {
                seenP.add(m.poster_path);
                posters.push(`https://image.tmdb.org/t/p/w342${m.poster_path}`);
            }
        });

        slideshowContainer.innerHTML = '';
        const slideEls = [];

        let bIdx = 0;
        for (let step = 0; step < 10; step++) {
            if (step % 2 === 0 && posters.length >= 16) {
                const wall = document.createElement('div');
                wall.className = 'hero-slide poster-wall-slide';
                const shuffledPosters = [...posters].sort(() => Math.random() - 0.5);
                for (let i = 0; i < 16; i++) {
                    const tile = document.createElement('div');
                    tile.className = 'poster-wall-tile';
                    tile.innerHTML = `<img src="${shuffledPosters[i % shuffledPosters.length]}" alt="">`;
                    wall.appendChild(tile);
                }
                slideshowContainer.appendChild(wall);
                slideEls.push(wall);
            } else if (bIdx < backdrops.length) {
                const slide = document.createElement('div');
                slide.className = 'hero-slide backdrop-slide';
                slide.style.backgroundImage = `url('${backdrops[bIdx++]}')`;
                slideshowContainer.appendChild(slide);
                slideEls.push(slide);
            }
        }

        if (!slideEls.length) return;
        slideEls[0].classList.add('active');
        let currentSlide = 0;
        setInterval(() => {
            slideEls[currentSlide].classList.remove('active');
            currentSlide = (currentSlide + 1) % slideEls.length;
            slideEls[currentSlide].classList.add('active');
        }, 4200);
    } catch (e) {}
}
initHeroBannerSlideshow();

const profileModal = document.getElementById('profileModal');
const profileDisplayName = document.getElementById('profileDisplayName');
const profileSubText = document.getElementById('profileSubText');
const welcomeName = document.getElementById('welcomeName');
const logoutBtn = document.getElementById('logoutBtn');
const chatHistory = document.getElementById('chatHistory');

function escapeHTML(str) {
    return String(str).replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
}

function saveNovaMemory() {
    sessionStorage.setItem('cinemind_nova_history', JSON.stringify(conversationHistory.slice(-20)));
    sessionStorage.setItem('cinemind_nova_movies', JSON.stringify(lastNovaMovies));
    sessionStorage.setItem('cinemind_nova_query', lastNovaQuery);
}

function renderChatHistoryInto(container) {
    if (!container) return;
    container.innerHTML = `<div class="chat-bubble ai-bubble">Hi ${escapeHTML(currentUser || 'Guest')}! 👽 I'm Nova. Ask me about Boys' Love (BL), Girls' Love (GL), real-life sports (FIFA, WWE, F1), true-crime documentaries like Jeffrey Dahmer, anime, or any movie plot!</div>`;
    conversationHistory.forEach(turn => {
        if (!turn || !turn.content) return;
        const div = document.createElement('div');
        div.className = `chat-bubble ${turn.role === 'user' ? 'user-bubble' : 'ai-bubble'}`;
        div.textContent = turn.content;
        container.appendChild(div);
    });
    container.scrollTop = container.scrollHeight;
}

window.clearNovaMemory = () => {
    conversationHistory = [];
    lastNovaMovies = [];
    lastNovaQuery = '';
    saveNovaMemory();
    renderChatHistoryInto(chatHistory);
    const enlargedHist = document.getElementById('novaEnlargedHistory');
    if (enlargedHist) renderChatHistoryInto(enlargedHist);
};

function calculateSimilarityMatch(movie, queryText = "") {
    if (movie.match) return movie.match;
    let base = 80;
    const vote = Number(movie.vote_average) || 7.2;
    base += Math.round((vote - 5) * 3.5);
    if (queryText) {
        const q = queryText.toLowerCase();
        const t = (movie.title || movie.name || "").toLowerCase();
        if (t.includes(q)) base += 6;
        const detected = detectCountryInQuery(queryText);
        if (detected && movie.genre_ids && movie.genre_ids.some(gid => detected.preferredGenres.includes(gid))) {
            base += 8;
        }
    }
    if (userGenres.length && movie.genre_ids) {
        const overlap = movie.genre_ids.filter(g => userGenres.includes(String(g)));
        if (overlap.length > 0) base += 4 * overlap.length;
    }
    return Math.max(74, Math.min(99, base));
}

async function repairSavedPosters(list) {
    return Promise.all(list.map(async (item) => {
        if (item.poster && item.poster.startsWith('http')) return item;
        if (item.poster_path) {
            item.poster = `https://image.tmdb.org/t/p/w500${item.poster_path}`;
            return item;
        }
        if (item.id) {
            const mType = item.media_type === 'tv' ? 'tv' : 'movie';
            try {
                const r = await fetch(`https://api.themoviedb.org/3/${mType}/${item.id}?api_key=${TMDB_API_KEY}`);
                const d = await r.json();
                if (d && d.poster_path) item.poster = `https://image.tmdb.org/t/p/w500${d.poster_path}`;
            } catch (e) {}
        }
        return item;
    }));
}

function updateProfileModalView() {
    const heading = document.getElementById('profileModalHeading');
    const msg = document.getElementById('authMsg');
    const loggedInCard = document.getElementById('loggedInAccountView');
    const guestInputs = document.getElementById('guestAuthInputs');
    const guestBtns = document.getElementById('guestAuthButtons');
    const loggedInBtns = document.getElementById('loggedInActionButtons');

    if (currentUser) {
        heading.innerText = "My CineMind Account";
        msg.innerText = "Your personal library and neural genre preferences are synced to your account.";
        loggedInCard.style.display = "flex";
        guestInputs.style.display = "none";
        guestBtns.style.display = "none";
        loggedInBtns.style.display = "flex";

        document.getElementById('accountAvatarInitial').innerText = currentUser.charAt(0).toUpperCase();
        document.getElementById('loggedInUsernameDisplay').innerText = `@${currentUser}`;
        document.getElementById('accWatchlistCount').innerText = watchlist.length;
        document.getElementById('accFavoritesCount').innerText = favorites.length;
        document.getElementById('accWatchedCount').innerText = watchedMovies.length;

        const gNames = userGenres.map(id => GENRE_OPTIONS[id] || ALL_GENRE_LABELS[id]).filter(Boolean);
        document.getElementById('accGenresList').innerText = gNames.length ? gNames.join(' • ') : "All Genres";
    } else {
        heading.innerText = "Welcome to CineMind Galaxy";
        msg.innerText = "Sign up or log in to sync your library, or calibrate your tastes below:";
        loggedInCard.style.display = "none";
        guestInputs.style.display = "flex";
        guestBtns.style.display = "flex";
        loggedInBtns.style.display = "none";
    }
}

async function syncCloudLibrary() {
    watchedMovies = JSON.parse(localStorage.getItem(`cinemind_watched_${currentUser || 'guest'}`) || '[]');
    notInterestedState = JSON.parse(localStorage.getItem(`cinemind_not_interested_${currentUser || 'guest'}`) || '{"ids":[],"keywords":[],"genrePairs":[],"titles":[]}');
    updateDislikedBadgeUI();

    if (!currentUser) {
        watchlist = [];
        favorites = [];
        profileDisplayName.innerText = "Guest User";
        profileSubText.innerText = userGenres.length >= 3 ? `${userGenres.length} Genres Calibrated` : "Tap to Login";
        welcomeName.innerText = "Guest";
        renderChatHistoryInto(chatHistory);
        updateProfileModalView();
        return;
    }
    profileDisplayName.innerText = currentUser;
    profileSubText.innerText = userGenres.length ? `Synced • ${userGenres.length} Genres` : "Cloud Synced";
    welcomeName.innerText = currentUser;
    renderChatHistoryInto(chatHistory);
    try {
        const res = await fetch(`${BACKEND_URL}/api/user/library?username=${encodeURIComponent(currentUser)}`);
        const data = await res.json();
        watchlist = await repairSavedPosters(data.watchlist || []);
        favorites = await repairSavedPosters(data.favorites || []);
        if (data.genres && data.genres.length >= 3 && userGenres.length === 0) {
            userGenres = data.genres.map(String);
            localStorage.setItem('cinemind_genres', JSON.stringify(userGenres));
        }
    } catch (e) {}
    updateProfileModalView();
}
syncCloudLibrary();

window.addEventListener('DOMContentLoaded', () => {
    if (!currentUser && userGenres.length < 3) {
        updateProfileModalView();
        profileModal.classList.add('active');
    }
});

document.getElementById('homeLogoBtn').onclick = () => {
    triggerTiltAnimation(mainBrandLogo);
    searchInput.value = '';
    navItems.forEach(n => n.classList.remove('active'));
    navItems[0].classList.add('active');
    currentView = 'discover';
    heroBanner.style.display = "flex";
    filterPanel.style.display = "flex";
    initEndlessNetflixHome();
};

document.getElementById('openProfile').onclick = () => {
    signupGenres = new Set(userGenres.map(String));
    renderGenrePills();
    updateProfileModalView();
    profileModal.classList.add('active');
};
document.getElementById('closeProfileModal').onclick = () => { profileModal.classList.remove('active'); };

document.getElementById('saveUserGenresBtn').onclick = () => {
    if (signupGenres.size < 3) {
        return alert("Please select at least 3 favorite genres.");
    }
    userGenres = [...signupGenres];
    localStorage.setItem('cinemind_genres', JSON.stringify(userGenres));
    if (currentUser) localStorage.setItem(`cinemind_genres_${currentUser}`, JSON.stringify(userGenres));
    updateProfileModalView();
    syncCloudLibrary();
    profileModal.classList.remove('active');
    if (currentView === 'discover') initEndlessNetflixHome();
};

document.getElementById('continueGuestBtn').onclick = () => {
    if (signupGenres.size > 0 && signupGenres.size < 3) {
        return alert("Please select at least 3 genres you like, or deselect them to continue uncalibrated.");
    }
    if (signupGenres.size >= 3) {
        userGenres = [...signupGenres];
        localStorage.setItem('cinemind_genres', JSON.stringify(userGenres));
    }
    syncCloudLibrary();
    profileModal.classList.remove('active');
    if (currentView === 'discover') initEndlessNetflixHome();
};

document.getElementById('loginBtn').onclick = async () => {
    const u = document.getElementById('authUsername').value.trim();
    const p = document.getElementById('authPassword').value.trim();
    if(!u || !p) return alert("Please enter your username and password to log in.");
    try {
        const res = await fetch(`${BACKEND_URL}/api/login`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: u, password: p})
        });
        const data = await res.json();
        if(data.success) {
            currentUser = data.username;
            localStorage.setItem('cinemind_auth_user', currentUser);
            if (signupGenres.size >= 3) userGenres = [...signupGenres];
            else if (data.genres && data.genres.length) userGenres = data.genres.map(String);
            localStorage.setItem(`cinemind_genres_${currentUser}`, JSON.stringify(userGenres));
            localStorage.setItem('cinemind_genres', JSON.stringify(userGenres));
            await syncCloudLibrary();
            profileModal.classList.remove('active');
            initEndlessNetflixHome();
        } else alert(data.message);
    } catch(e) { alert("Authentication error."); }
};

document.getElementById('signupBtn').onclick = async () => {
    const u = document.getElementById('authUsername').value.trim().toLowerCase();
    const p = document.getElementById('authPassword').value.trim();
    if(!u || p.length < 6) return alert("Please enter a username and a password (6+ characters).");
    if (signupGenres.size < 3) return alert("Please pick at least 3 favorite genres before signing up!");
    try {
        const res = await fetch(`${BACKEND_URL}/api/signup`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: u, password: p, genres: [...signupGenres]})
        });
        const data = await res.json();
        if(data.success) {
            userGenres = [...signupGenres];
            localStorage.setItem('cinemind_genres', JSON.stringify(userGenres));
            localStorage.setItem(`cinemind_genres_${u}`, JSON.stringify(userGenres));
            currentUser = u;
            localStorage.setItem('cinemind_auth_user', currentUser);
            await syncCloudLibrary();
            profileModal.classList.remove('active');
            initEndlessNetflixHome();
            alert("Account created & calibrated with your favorite genres!");
        } else alert(data.message);
    } catch(e) { alert("Signup error."); }
};

logoutBtn.onclick = () => {
    currentUser = null;
    localStorage.removeItem('cinemind_auth_user');
    userGenres = [];
    signupGenres.clear();
    localStorage.removeItem('cinemind_genres');
    document.getElementById('authUsername').value = '';
    document.getElementById('authPassword').value = '';
    renderGenrePills();
    syncCloudLibrary();
    profileModal.classList.remove('active');
    initEndlessNetflixHome();
};

function createMovieCard(movie, isAI = false, searchContext = "", rankNum = null) {
    const poster = (movie.poster && movie.poster.startsWith('http'))
        ? movie.poster
        : (movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : NO_POSTER);
    const title = movie.title || movie.name || "Untitled";
    const mType = movie.media_type || (movie.first_air_date && !movie.release_date ? 'tv' : 'movie');
    movie.media_type = mType;
    const matchPct = calculateSimilarityMatch(movie, searchContext);
    const rating = movie.vote_average ? Number(movie.vote_average).toFixed(1) : '8.2';
    const showR18 = isGenuineR18(movie);
    movie._isR18 = showR18;
    const originLabel = resolveMovieOriginCountry(movie);
    const exactGenresText = getExactGenreNames(movie);

    const r18HTML = showR18 ? `<span class="r18-badge">R-18</span>` : '';
    const badgesHTML = `
        <button type="button" class="card-not-interested-btn" title="Not Interested (Hide similar concepts)"><i class="fa-solid fa-ban"></i></button>
        <div class="badges-container">
            ${r18HTML}
            <span class="media-badge">${mType === 'tv' ? '📺 SERIES' : '🎬 MOVIE'}</span>
        </div>
        <span class="origin-country-badge"><i class="fa-solid fa-location-dot" style="color:var(--secondary-glow);"></i> ${escapeHTML(originLabel)}</span>
    `;
    const rationale = movie.rationale || (searchContext
        ? `High neural similarity to "${searchContext}".`
        : (mType === 'tv' ? `Trending ${originLabel} Series matched to your stream.` : `Curated ${originLabel} cinema via neural filtering.`));

    const card = document.createElement('div');
    card.setAttribute('data-movie-id', movie.id);
    card.setAttribute('data-concept-text', `${title} ${movie.overview || ''} ${exactGenresText}`);

    if (rankNum !== null) {
        card.className = 'movie-card top10-card';
        card.onclick = () => { fetchAndOpenModal(title, poster, rationale, movie.id, matchPct, mType, movie); };
        card.innerHTML = `
            <span class="top10-rank-num">${rankNum}</span>
            <div class="top10-inner">
                <div class="card-poster-wrap">
                    ${badgesHTML}
                    <img src="${poster}" alt="${escapeHTML(title)}" loading="lazy" decoding="async" onerror="this.onerror=null;this.src=NO_POSTER">
                </div>
                <div class="movie-info">
                    <div class="movie-title">${escapeHTML(title)}</div>
                    <div class="card-genres-tags"><i class="fa-solid fa-tags"></i> ${escapeHTML(exactGenresText)}</div>
                    <div class="card-meta-row">
                        <span class="match-score"><i class="fa-solid fa-bolt"></i> ${matchPct}%</span>
                        <span class="rating-badge"><i class="fa-solid fa-star"></i> ${rating}</span>
                    </div>
                    <div class="card-rationale-preview">${escapeHTML(rationale)}</div>
                </div>
            </div>
        `;
    } else {
        card.className = 'movie-card';
        card.onclick = () => { fetchAndOpenModal(title, poster, rationale, movie.id, matchPct, mType, movie); };
        card.innerHTML = `
            <div class="card-poster-wrap">
                ${badgesHTML}
                <img src="${poster}" alt="${escapeHTML(title)}" loading="lazy" decoding="async" onerror="this.onerror=null;this.src=NO_POSTER">
            </div>
            <div class="movie-info">
                <div class="movie-title">${escapeHTML(title)}</div>
                <div class="card-genres-tags"><i class="fa-solid fa-tags"></i> ${escapeHTML(exactGenresText)}</div>
                <div class="card-meta-row">
                    <span class="match-score"><i class="fa-solid fa-bolt"></i> ${matchPct}% Match</span>
                    <span class="rating-badge"><i class="fa-solid fa-star"></i> ${rating}</span>
                </div>
                <div class="card-rationale-preview">${escapeHTML(rationale)}</div>
            </div>
        `;
    }

    const notIntBtn = card.querySelector('.card-not-interested-btn');
    if (notIntBtn) {
        notIntBtn.onclick = (ev) => {
            ev.stopPropagation();
            markMovieNotInterested(movie, card);
        };
    }

    const bCont = card.querySelector('.badges-container');
    const cBadge = card.querySelector('.origin-country-badge');
    verifyCardMetadataAsync(movie, card, bCont, cBadge);
    return card;
}

function buildRowElement(titleHTML, movies, isAI = false, isTop10 = false) {
    const valid = [];
    for (const m of (movies || [])) {
        if (!isSafeNonPorn(m)) continue;
        if (!m.poster_path && !(m.poster && m.poster.startsWith('http'))) continue;
        const uniqueKey = `${m.media_type || 'movie'}_${m.id}`;
        if (displayedMovieIds.has(uniqueKey)) continue;
        displayedMovieIds.add(uniqueKey);
        valid.push(m);
    }
    if (!valid.length) return null;

    const sec = document.createElement('div');
    sec.className = 'row-section';
    const h3 = document.createElement('h3');
    h3.className = 'row-title';
    h3.innerHTML = titleHTML;
    sec.appendChild(h3);

    const row = document.createElement('div');
    row.className = 'movie-row';
    const slice = isTop10 ? valid.slice(0, 10) : valid;
    slice.forEach((m, idx) => {
        row.appendChild(createMovieCard(m, isAI, "", isTop10 ? idx + 1 : null));
    });
    sec.appendChild(row);
    return sec;
}

// Fetch Specialized Category Streams (BL, GL, Real-Life Sports, Documentaries, Anime, Kids & Family)
async function fetchSpecialCategoryItems(categoryKey, page = 1) {
    const results = [];
    const countryFilter = selectedCountry ? `&with_origin_country=${selectedCountry}` : "";
    const provFilter = selectedProvider ? `&with_watch_providers=${selectedProvider}&watch_region=${selectedRegion}` : "";

    // 1. Seed Page 1 with Verified Curated Hits for BL, GL, SPORTS, DOC
    if (page === 1 && CURATED_SPECIAL_TITLES[categoryKey]) {
        const curatedList = CURATED_SPECIAL_TITLES[categoryKey];
        const fetchedCurated = await Promise.all(curatedList.map(async (c) => {
            if (selectedMedia === 'movie' && c.media_type !== 'movie') return null;
            if (selectedMedia === 'tv' && c.media_type !== 'tv') return null;
            try {
                const r = await fetch(`https://api.themoviedb.org/3/search/${c.media_type}?api_key=${TMDB_API_KEY}&include_adult=false&query=${encodeURIComponent(c.title)}`).then(res => res.json());
                const hit = (r.results || []).find(x => x.poster_path);
                if (hit) {
                    hit.media_type = c.media_type;
                    hit.rationale = c.why;
                    if (categoryKey === 'BL') hit._customGenreBadge = "Boys' Love (BL)";
                    if (categoryKey === 'GL') hit._customGenreBadge = "Girls' Love (GL)";
                    if (categoryKey === 'SPORTS') hit._customGenreBadge = "Real-Life Sports";
                    if (categoryKey === 'DOC') hit._customGenreBadge = "Documentary";
                    return hit;
                }
            } catch (e) {}
            return null;
        }));
        fetchedCurated.filter(Boolean).forEach(x => results.push(x));
    }

    // 2. Discover API Queries tailored to each exact category
    try {
        if (categoryKey === "BL") {
            const originParam = selectedCountry ? `with_origin_country=${selectedCountry}` : `with_origin_country=TH|KR|JP|TW|PH`;
            const [tvRes, movRes] = await Promise.all([
                selectedMedia === 'movie' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&include_adult=false&${originParam}&with_keywords=286407|250606|158718|264386&without_genres=16&sort_by=popularity.desc&page=${page}${provFilter}`).then(r => r.json()),
                selectedMedia === 'tv' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_keywords=286407|250606|158718&without_genres=16&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json())
            ]);
            (tvRes.results || []).forEach(t => results.push({ ...t, media_type: 'tv', _customGenreBadge: "Boys' Love (BL)", rationale: "Boys' Love (BL) romance series." }));
            (movRes.results || []).forEach(m => results.push({ ...m, media_type: 'movie', _customGenreBadge: "Boys' Love (BL)", rationale: "Boys' Love (BL) cinema." }));
        } else if (categoryKey === "GL") {
            const [tvRes, movRes] = await Promise.all([
                selectedMedia === 'movie' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&include_adult=false&with_keywords=264386|9840|158718&without_genres=16&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json()),
                selectedMedia === 'tv' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_keywords=264386|9840&without_genres=16&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json())
            ]);
            (tvRes.results || []).forEach(t => results.push({ ...t, media_type: 'tv', _customGenreBadge: "Girls' Love (GL)", rationale: "Girls' Love (GL) drama series." }));
            (movRes.results || []).forEach(m => results.push({ ...m, media_type: 'movie', _customGenreBadge: "Girls' Love (GL)", rationale: "Girls' Love (GL) cinema." }));
        } else if (categoryKey === "SPORTS") {
            // Strictly Real-Life Sports (NO Animation genre 16, NO cartoons)
            const [movRes, tvRes] = await Promise.all([
                selectedMedia === 'tv' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_keywords=6075|13042|6513|1721&without_genres=16,14&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json()),
                selectedMedia === 'movie' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&include_adult=false&with_keywords=6075|13042|6513|1721&without_genres=16,10765&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json())
            ]);
            (movRes.results || []).filter(m => !isAnimatedOrCartoon(m)).forEach(m => results.push({ ...m, media_type: 'movie', _customGenreBadge: "Real-Life Sports", rationale: "Real-life sports film." }));
            (tvRes.results || []).filter(t => !isAnimatedOrCartoon(t)).forEach(t => results.push({ ...t, media_type: 'tv', _customGenreBadge: "Real-Life Sports", rationale: "Real-life sports & championship series." }));
        } else if (categoryKey === "DOC" || categoryKey === "99") {
            // Strictly Real-Life Documentaries & True-Crime Docuseries (NO Animation genre 16)
            const [tvRes, movRes] = await Promise.all([
                selectedMedia === 'movie' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&include_adult=false&with_genres=99&without_genres=16,10762&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json()),
                selectedMedia === 'tv' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_genres=99&without_genres=16,10751&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json())
            ]);
            (tvRes.results || []).filter(t => !isAnimatedOrCartoon(t)).forEach(t => results.push({ ...t, media_type: 'tv', _customGenreBadge: "Documentary", rationale: "True-life documentary series." }));
            (movRes.results || []).filter(m => !isAnimatedOrCartoon(m)).forEach(m => results.push({ ...m, media_type: 'movie', _customGenreBadge: "Documentary", rationale: "Investigative & biographical documentary." }));
        } else if (categoryKey === "ANIME") {
            // Strictly Japanese / Korean / Chinese Anime
            const originC = selectedCountry || "JP|KR|CN";
            const [tvRes, movRes] = await Promise.all([
                selectedMedia === 'movie' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&include_adult=false&with_genres=16&with_origin_country=${originC}&sort_by=popularity.desc&page=${page}${provFilter}`).then(r => r.json()),
                selectedMedia === 'tv' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_genres=16&with_origin_country=${originC}&sort_by=popularity.desc&page=${page}${provFilter}`).then(r => r.json())
            ]);
            (tvRes.results || []).forEach(t => results.push({ ...t, media_type: 'tv', _customGenreBadge: "Anime", rationale: "Hit Anime series." }));
            (movRes.results || []).forEach(m => results.push({ ...m, media_type: 'movie', _customGenreBadge: "Anime", rationale: "Feature Anime film." }));
        } else if (categoryKey === "KIDS") {
            // Kids, Family & Animated Movies (Pixar, Disney, DreamWorks, Family Adventures)
            const [movRes, tvRes] = await Promise.all([
                selectedMedia === 'tv' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_genres=10751|16&without_genres=27,53,80&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json()),
                selectedMedia === 'movie' ? { results: [] } : fetch(`https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&include_adult=false&with_genres=10762|10751&without_genres=80,9648&sort_by=popularity.desc&page=${page}${countryFilter}${provFilter}`).then(r => r.json())
            ]);
            (movRes.results || []).forEach(m => results.push({ ...m, media_type: 'movie', _customGenreBadge: "Kids & Family", rationale: "Kids, Family & Animated feature." }));
            (tvRes.results || []).forEach(t => results.push({ ...t, media_type: 'tv', _customGenreBadge: "Kids & Family", rationale: "Kids & Family series." }));
        }
    } catch (e) {}

    return results.filter(isSafeNonPorn);
}

function getActiveFilterQueryParams(mediaType = "movie") {
    let q = "&include_adult=false";
    const standardGids = [...selectedGenres].filter(g => !["BL", "GL", "ANIME", "KIDS", "SPORTS"].includes(g));
    if (standardGids.length > 0) {
        const gArr = standardGids.map(gid => mediaType === "tv" ? (MOVIE_TO_TV_GENRE[gid] || gid) : gid);
        q += `&with_genres=${[...new Set(gArr)].join(',')}`;
        if (standardGids.includes("99")) {
            q += `&without_genres=16`;
        }
    }
    if (selectedCountry) q += `&with_origin_country=${selectedCountry}`;
    if (selectedProvider) {
        q += `&with_watch_providers=${selectedProvider}&watch_region=${selectedRegion}`;
    }
    return q;
}

// ---------------- FAST ENDLESS NETFLIX ROWS ENGINE ----------------
async function appendNextNetflixRowBatch(count = 3) {
    if (isFetchingMore || streamExhausted || currentView !== 'discover' || infiniteMode !== 'rows') return;
    isFetchingMore = true;
    infiniteSentinel.style.display = "flex";
    infiniteSentinel.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Loading more galaxy titles...`;

    // Check if a Special Category Filter is active
    const specialActive = [...selectedGenres].find(g => ["BL", "GL", "ANIME", "KIDS", "SPORTS", "99"].includes(g));
    if (specialActive) {
        nextRowIndex++;
        const catKey = specialActive === "99" ? "DOC" : specialActive;
        const items = await fetchSpecialCategoryItems(catKey, nextRowIndex + 1);
        const label = GENRE_OPTIONS[specialActive] || ALL_GENRE_LABELS[specialActive];
        const rowEl = buildRowElement(`<i class="fa-solid fa-sparkles" style="color: var(--secondary-glow);"></i> ${label} Stream (Page ${nextRowIndex + 1})`, items, true);
        if (rowEl) {
            mainContainer.appendChild(rowEl);
            emptyBatchStreak = 0;
        } else {
            streamExhausted = true;
            infiniteSentinel.innerHTML = `<i class="fa-solid fa-check-circle" style="color:#10b981;"></i> ✨ You've reached the end of the ${label} stream!`;
        }
        isFetchingMore = false;
        return;
    }

    const forceTV = selectedMedia === 'tv';
    const forceMovie = selectedMedia === 'movie';

    let addedRowsCount = 0;
    for (let i = 0; i < count; i++) {
        const cycleIndex = nextRowIndex % ENDLESS_ROW_CATALOG.length;
        const pageOffset = Math.floor(nextRowIndex / ENDLESS_ROW_CATALOG.length) + 1;
        const template = ENDLESS_ROW_CATALOG[cycleIndex];
        nextRowIndex++;

        if (template.specialCategory && selectedGenres.size === 0) {
            const specItems = await fetchSpecialCategoryItems(template.specialCategory, pageOffset);
            const el = buildRowElement(`<i class="fa-solid fa-sparkles" style="color: var(--secondary-glow);"></i> ${template.title}${pageOffset > 1 ? ` (Vol. ${pageOffset})` : ''}`, specItems, true);
            if (el) {
                mainContainer.appendChild(el);
                addedRowsCount++;
            }
            continue;
        }

        const mType = forceTV ? "tv" : (forceMovie ? "movie" : (template.media || "movie"));
        const endpoint = mType === "tv" ? "/discover/tv" : "/discover/movie";
        const filterStr = getActiveFilterQueryParams(mType);

        let baseParams = selectedGenres.size > 0 || selectedCountry
            ? `sort_by=popularity.desc&page=${nextRowIndex + 1}`
            : (template.params || `sort_by=popularity.desc&page=${pageOffset}`);
        if (pageOffset > 1 && !(selectedGenres.size > 0 || selectedCountry)) {
            baseParams = baseParams.replace(/page=\d+/, `page=${pageOffset}`);
        }

        const url = `https://api.themoviedb.org/3${endpoint}?api_key=${TMDB_API_KEY}&${baseParams}${filterStr}`;
        try {
            const d = await fetch(url).then(r => r.json());
            const list = (d.results || []).map(item => ({ ...item, media_type: mType }));
            const genreNames = [...selectedGenres].map(g => GENRE_OPTIONS[g] || ALL_GENRE_LABELS[g]).filter(Boolean).join(' + ');
            const rowLabel = (selectedGenres.size > 0 || selectedCountry)
                ? `✨ ${genreNames || 'Filtered'} Stream (Page ${nextRowIndex})`
                : `${template.title}${pageOffset > 1 ? ` (Vol. ${pageOffset})` : ''}`;

            const el = buildRowElement(`<i class="fa-solid fa-sparkles" style="color: var(--secondary-glow);"></i> ${rowLabel}`, list);
            if (el) {
                mainContainer.appendChild(el);
                addedRowsCount++;
            }
        } catch (e) {}
    }

    if (addedRowsCount === 0) {
        emptyBatchStreak++;
        if (emptyBatchStreak >= 2) {
            streamExhausted = true;
            infiniteSentinel.innerHTML = `<i class="fa-solid fa-check-circle" style="color:#10b981;"></i> ✨ You've reached the end of the galaxy stream for this selection!`;
        }
    } else {
        emptyBatchStreak = 0;
    }

    isFetchingMore = false;
}

// ---------------- MASTER GALAXY HOME INITIALIZER ----------------
async function initEndlessNetflixHome() {
    if (currentView !== 'discover') return;
    infiniteMode = "rows";
    nextRowIndex = 0;
    emptyBatchStreak = 0;
    streamExhausted = false;
    displayedMovieIds.clear();
    infiniteSentinel.style.display = "flex";
    infiniteSentinel.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Synchronizing Unique Galaxy Cinema & Series Streams...`;
    mainContainer.innerHTML = '';

    // Check if user selected BL, GL, SPORTS, DOC (99), ANIME, or KIDS
    const specialActive = [...selectedGenres].find(g => ["BL", "GL", "ANIME", "KIDS", "SPORTS", "99"].includes(g));
    if (specialActive) {
        const catKey = specialActive === "99" ? "DOC" : specialActive;
        const label = GENRE_OPTIONS[specialActive] || ALL_GENRE_LABELS[specialActive];
        const [page1Items, page2Items] = await Promise.all([
            fetchSpecialCategoryItems(catKey, 1),
            fetchSpecialCategoryItems(catKey, 2)
        ]);
        mainContainer.innerHTML = '';
        const topRow = buildRowElement(`<i class="fa-solid fa-trophy" style="color:#fbbf24;"></i> 🏆 Top 10 ${label} Today`, page1Items.slice(0, 12), true, true);
        if (topRow) mainContainer.appendChild(topRow);
        const featRow = buildRowElement(`<i class="fa-solid fa-flame" style="color:var(--primary-glow);"></i> ✨ Featured ${label} Catalog`, [...page1Items.slice(10), ...page2Items], true, false);
        if (featRow) mainContainer.appendChild(featRow);
        nextRowIndex = 2;
        return;
    }

    const isSeriesTab = selectedMedia === 'tv';
    const isMovieOnly = selectedMedia === 'movie';
    const appBadge = selectedProvider ? ` on ${PROVIDER_NAMES[selectedProvider]}` : "";
    const countryBadge = selectedCountry ? ` (${COUNTRY_NAMES[selectedCountry]})` : "";
    const activeGenreLabel = selectedGenres.size > 0
        ? ` • ${[...selectedGenres].map(g => GENRE_OPTIONS[g] || ALL_GENRE_LABELS[g]).filter(Boolean).join(' + ')}`
        : "";

    const specialRows = [];

    if (watchedMovies.length > 0 && selectedGenres.size === 0 && !selectedCountry) {
        const lastWatched = watchedMovies[0];
        const lwType = lastWatched.media_type === 'tv' ? 'tv' : 'movie';
        specialRows.push({
            title: `<i class="fa-solid fa-robot" style="color: var(--primary-glow);"></i> 🤖 AI Recommended Because You Watched "${escapeHTML(lastWatched.title)}"`,
            url: `https://api.themoviedb.org/3/${lwType}/${lastWatched.id}/recommendations?api_key=${TMDB_API_KEY}&page=1`,
            mType: lwType,
            isAI: true,
            customRationale: `AI Recommended because you watched "${lastWatched.title}".`
        });
    }

    if (selectedProvider || selectedGenres.size > 0 || selectedCountry) {
        const pName = selectedProvider ? PROVIDER_NAMES[selectedProvider] : "Filtered Stream";
        if (!isSeriesTab) {
            specialRows.push({
                title: `<i class="fa-solid fa-sliders" style="color: var(--secondary-glow);"></i> 🎯 Custom Filtered Movies (${pName}${activeGenreLabel}${countryBadge})`,
                url: `https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&sort_by=popularity.desc${getActiveFilterQueryParams('movie')}&page=1`,
                mType: 'movie',
                isAI: true,
                customRationale: `Matched to your active filter selection.`
            });
        }
        if (!isMovieOnly) {
            specialRows.push({
                title: `<i class="fa-solid fa-tv" style="color: var(--primary-glow);"></i> 📺 Custom Filtered Series & Dramas (${pName}${activeGenreLabel}${countryBadge})`,
                url: `https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&sort_by=popularity.desc${getActiveFilterQueryParams('tv')}&page=1`,
                mType: 'tv',
                isAI: true,
                customRationale: `Series matched to your active filter selection.`
            });
        }
    }

    if (!isSeriesTab) {
        const top10MovieUrl = (selectedProvider || selectedCountry || selectedGenres.size > 0)
            ? `https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&sort_by=popularity.desc${getActiveFilterQueryParams('movie')}&page=2`
            : `https://api.themoviedb.org/3/trending/movie/day?api_key=${TMDB_API_KEY}`;
        specialRows.push({
            title: `<i class="fa-solid fa-trophy" style="color: #fbbf24;"></i> 🏆 Top 10 Movies Today${appBadge}${activeGenreLabel}${countryBadge}`,
            url: top10MovieUrl,
            mType: 'movie',
            isTop10: true
        });
    }
    if (!isMovieOnly) {
        const top10TVUrl = (selectedProvider || selectedCountry || selectedGenres.size > 0)
            ? `https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&sort_by=popularity.desc${getActiveFilterQueryParams('tv')}&page=2`
            : `https://api.themoviedb.org/3/trending/tv/day?api_key=${TMDB_API_KEY}`;
        specialRows.push({
            title: `<i class="fa-solid fa-crown" style="color: var(--primary-glow);"></i> 🏆 Top 10 Series & Dramas Today${appBadge}${activeGenreLabel}${countryBadge}`,
            url: top10TVUrl,
            mType: 'tv',
            isTop10: true
        });
    }

    const responses = await Promise.all(
        specialRows.map(r => fetch(r.url).then(res => res.json()).catch(() => ({ results: [] })))
    );

    mainContainer.innerHTML = '';
    responses.forEach((data, idx) => {
        const cfg = specialRows[idx];
        const items = (data.results || []).map(m => ({
            ...m,
            media_type: cfg.mType,
            rationale: cfg.customRationale || m.rationale
        }));
        const rowEl = buildRowElement(cfg.title, items, cfg.isAI, cfg.isTop10);
        if (rowEl) mainContainer.appendChild(rowEl);
    });

    await appendNextNetflixRowBatch(3);
}

// Format & Genre Pill Click Handlers
document.querySelectorAll('.filter-row').forEach(row => {
    row.querySelectorAll('.filter-pill').forEach(pill => {
        if (pill.id === 'resetDislikedBtn') return;
        pill.onclick = (e) => {
            const btn = e.currentTarget;

            if (btn.hasAttribute('data-genre')) {
                const gVal = btn.getAttribute('data-genre');
                const isSpecial = ["BL", "GL", "ANIME", "KIDS", "SPORTS", "99"].includes(gVal);
                if (!gVal) {
                    selectedGenres.clear();
                } else if (isSpecial) {
                    if (selectedGenres.has(gVal)) selectedGenres.delete(gVal);
                    else {
                        selectedGenres.clear();
                        selectedGenres.add(gVal);
                    }
                } else {
                    ["BL", "GL", "ANIME", "KIDS", "SPORTS", "99"].forEach(sp => selectedGenres.delete(sp));
                    if (selectedGenres.has(gVal)) selectedGenres.delete(gVal);
                    else selectedGenres.add(gVal);
                }
                syncGenrePillsUI();
                initEndlessNetflixHome();
                return;
            }

            if (btn.hasAttribute('data-media')) {
                row.querySelectorAll('.filter-pill[data-media]').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                selectedMedia = btn.getAttribute('data-media');
                initEndlessNetflixHome();
            }
        };
    });
});

// ---------------- ENDLESS MULTI-SEARCH & COUNTRY+GENRE AI MATCHING ENGINE ----------------
async function performSearch() {
    const query = searchInput.value.trim();
    if (currentView !== 'discover') {
        currentView = 'discover';
        navItems.forEach(n => n.classList.remove('active'));
        navItems[0].classList.add('active');
    }

    if (!query) {
        heroBanner.style.display = "flex";
        filterPanel.style.display = "flex";
        initEndlessNetflixHome();
        return;
    }

    activeSearchQuery = query;
    infiniteMode = "search";
    searchPage = 1;
    searchTotalPages = 10;
    streamExhausted = false;
    emptyBatchStreak = 0;
    displayedMovieIds.clear();

    heroBanner.style.display = "flex";
    filterPanel.style.display = "none";
    infiniteSentinel.style.display = "none";
    mainContainer.innerHTML = `<p style="color: var(--text-muted); text-align:center; padding: 40px;"><i class="fa-solid fa-spinner fa-spin"></i> Nova is analyzing "${escapeHTML(query)}"...</p>`;

    const lowerQ = query.toLowerCase();
    try {
        let initialMovies = [];
        let aiNote = "";
        let isAISearch = false;

        // Instant detection for BL, GL, Real Sports, or Documentaries in Search Bar
        if (/\b(boys love|boy's love|bl series|thai bl|korean bl)\b/i.test(lowerQ)) {
            initialMovies = await fetchSpecialCategoryItems("BL", 1);
            aiNote = "Curated Boys' Love (BL) series and films.";
            isAISearch = true;
        } else if (/\b(girls love|girl's love|gl series|thai gl|sapphic|freenbecky|lingorm)\b/i.test(lowerQ)) {
            initialMovies = await fetchSpecialCategoryItems("GL", 1);
            aiNote = "Curated Girls' Love (GL) series and films.";
            isAISearch = true;
        } else if (/\b(fifa|wwe|formula 1|real sports|sports documentary)\b/i.test(lowerQ)) {
            initialMovies = await fetchSpecialCategoryItems("SPORTS", 1);
            aiNote = "Curated real-life sports series, documentaries, and films (no cartoons/animation).";
            isAISearch = true;
        } else if (/\b(jeffrey dahmer|true crime|serial killer documentary)\b/i.test(lowerQ)) {
            initialMovies = await fetchSpecialCategoryItems("DOC", 1);
            aiNote = "Curated true-crime and investigative documentaries.";
            isAISearch = true;
        }

        const isQuestionOrPlot = query.split(/\s+/).length >= 4
            || /\?$/.test(query)
            || /\b(why|how|what|who|where|when|explain|boxing|about a|movie that|forgot|relives|infiltrates|stuck|pole|tower|trapped)\b/i.test(query);

        const countryContext = detectCountryInQuery(query);
        const queryGenres = detectGenresInQuery(query);

        if (initialMovies.length === 0 && countryContext) {
            const originCode = countryContext.code;
            const targetGenreIds = queryGenres.length > 0
                ? queryGenres
                : (userGenres.length > 0 ? userGenres.map(Number).filter(Boolean) : countryContext.preferredGenres);
            const genresPipe = targetGenreIds.join('|');
            const genreNamesText = targetGenreIds.map(id => ALL_GENRE_LABELS[id]).filter(Boolean).join(', ');

            const [cMovies1, cMovies2, cTV] = await Promise.all([
                fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_origin_country=${originCode}&with_genres=${genresPipe}&sort_by=popularity.desc&page=1`).then(r => r.json()).catch(() => ({ results: [] })),
                fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_origin_country=${originCode}&sort_by=popularity.desc&page=1`).then(r => r.json()).catch(() => ({ results: [] })),
                fetch(`https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&include_adult=false&with_origin_country=${originCode}&sort_by=popularity.desc&page=1`).then(r => r.json()).catch(() => ({ results: [] }))
            ]);

            const mappedMovies = [...(cMovies1.results || []), ...(cMovies2.results || [])].map(m => ({
                ...m,
                media_type: 'movie',
                origin_country: [originCode],
                rationale: `AI Recommended ${countryContext.label} film matched to ${genreNamesText || 'regional'} genres.`
            }));
            const mappedTV = (cTV.results || []).map(t => ({
                ...t,
                media_type: 'tv',
                origin_country: [originCode],
                rationale: `Popular ${countryContext.label} series matched to your search.`
            }));

            initialMovies = [...mappedMovies, ...mappedTV].filter(isSafeNonPorn);
            aiNote = `Curated <strong>${countryContext.label}</strong> movies & series matched to <strong>${genreNamesText || 'top regional'}</strong> genres.`;
            isAISearch = true;
        } else if (initialMovies.length === 0 && isQuestionOrPlot) {
            try {
                const clientGuesses = await clientSidePlotAssist(query);
                const res = await fetch(`${BACKEND_URL}/chat`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: query,
                        client_guesses: clientGuesses,
                        profile: { name: currentUser || 'Guest', favorite_genres: userGenres.map(id => ALL_GENRE_LABELS[id]).filter(Boolean), origin_country: selectedCountry },
                        region: selectedRegion,
                        history: conversationHistory
                    })
                });
                const data = await res.json();
                initialMovies = (data.movies || []).filter(isSafeNonPorn);
                aiNote = escapeHTML(data.reply || "");
                isAISearch = true;
            } catch (e) {}
        }

        if (initialMovies.length === 0) {
            const [r1, r2] = await Promise.all([
                fetch(`https://api.themoviedb.org/3/search/multi?api_key=${TMDB_API_KEY}&include_adult=false&query=${encodeURIComponent(query)}&page=1`).then(r => r.json()).catch(() => ({})),
                fetch(`https://api.themoviedb.org/3/search/multi?api_key=${TMDB_API_KEY}&include_adult=false&query=${encodeURIComponent(query)}&page=2`).then(r => r.json()).catch(() => ({}))
            ]);
            searchTotalPages = r1.total_pages || 1;
            searchPage = 2;
            const rawResults = [...(r1.results || []), ...(r2.results || [])].filter(m => (m.media_type === 'movie' || m.media_type === 'tv') && m.poster_path && isSafeNonPorn(m));
            initialMovies = [...initialMovies, ...rawResults];

            if (initialMovies.length > 0 && initialMovies[0].id) {
                const topHit = initialMovies[0];
                const mType = topHit.media_type === 'tv' ? 'tv' : 'movie';
                const recRes = await fetch(`https://api.themoviedb.org/3/${mType}/${topHit.id}/recommendations?api_key=${TMDB_API_KEY}&page=1`).then(r => r.json()).catch(() => ({}));
                (recRes.results || []).forEach(rm => {
                    if (rm.poster_path && isSafeNonPorn(rm)) {
                        rm.media_type = mType;
                        rm.rationale = `AI Recommended because you searched for "${topHit.title || topHit.name}".`;
                        initialMovies.push(rm);
                    }
                });
            }
        }

        const uniqueMovies = [];
        for (const m of initialMovies) {
            const key = `${m.media_type || 'movie'}_${m.id}`;
            if (!displayedMovieIds.has(key)) {
                displayedMovieIds.add(key);
                uniqueMovies.push(m);
            }
        }

        mainContainer.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <h3 class="row-title"><i class="fa-solid fa-magnifying-glass-chart" style="color: var(--secondary-glow);"></i> ${countryContext ? `${countryContext.label} Genre Matches` : `Search & AI Matches for "${escapeHTML(query)}"`}</h3>
                <button type="button" class="filter-pill" onclick="searchInput.value='';performSearch();"><i class="fa-solid fa-arrow-left"></i> Back to Galaxy Stream</button>
            </div>
        `;
        if (aiNote) {
            const p = document.createElement('div');
            p.className = 'ai-rationale-box';
            p.style.marginTop = '-14px';
            p.innerHTML = `<span class="ai-rationale-title"><i class="fa-solid fa-wand-magic-sparkles"></i> Nova AI Regional & Scene Intelligence</span><span class="ai-rationale-text" style="font-size:0.95rem; color: var(--text-main);">${aiNote}</span>`;
            mainContainer.appendChild(p);
        }

        const grid = document.createElement('div');
        grid.className = 'movie-grid';
        grid.id = 'searchResultsGrid';

        if (uniqueMovies.length > 0) {
            uniqueMovies.forEach(m => grid.appendChild(createMovieCard(m, isAISearch, query)));
            infiniteSentinel.style.display = "flex";
            infiniteSentinel.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Loading more matching titles...`;
        } else {
            grid.innerHTML = `<p style="color: var(--text-muted);">No matching titles found for "${escapeHTML(query)}".</p>`;
            streamExhausted = true;
        }
        mainContainer.appendChild(grid);
    } catch (err) {
        mainContainer.innerHTML = `<p style="color: var(--text-muted); text-align:center; padding: 40px;">Search error. Please try again.</p>`;
    }
}

async function appendMoreSearchResults() {
    if (isFetchingMore || streamExhausted || infiniteMode !== 'search') return;
    const grid = document.getElementById('searchResultsGrid');
    if (!grid) return;
    isFetchingMore = true;
    infiniteSentinel.style.display = "flex";
    searchPage++;
    try {
        let more = [];
        const countryContext = detectCountryInQuery(activeSearchQuery);
        const queryGenres = detectGenresInQuery(activeSearchQuery);
        if (countryContext) {
            const gParam = queryGenres.length ? `&with_genres=${queryGenres.join('|')}` : '';
            const r = await fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&include_adult=false&with_origin_country=${countryContext.code}${gParam}&sort_by=popularity.desc&page=${searchPage}`).then(res => res.json());
            more = (r.results || []).filter(m => m.poster_path && isSafeNonPorn(m)).map(m => ({ ...m, media_type: 'movie', origin_country: [countryContext.code] }));
        } else if (searchPage <= searchTotalPages) {
            const r = await fetch(`https://api.themoviedb.org/3/search/multi?api_key=${TMDB_API_KEY}&include_adult=false&query=${encodeURIComponent(activeSearchQuery)}&page=${searchPage}`).then(res => res.json());
            more = (r.results || []).filter(m => (m.media_type === 'movie' || m.media_type === 'tv') && m.poster_path && isSafeNonPorn(m));
        }

        let added = 0;
        more.forEach(m => {
            const key = `${m.media_type || 'movie'}_${m.id}`;
            if (!displayedMovieIds.has(key)) {
                displayedMovieIds.add(key);
                grid.appendChild(createMovieCard(m, false, activeSearchQuery));
                added++;
            }
        });

        if (added === 0) {
            streamExhausted = true;
            infiniteSentinel.innerHTML = `<i class="fa-solid fa-check-circle" style="color:#10b981;"></i> ✨ You've reached the end of the search results!`;
        }
    } catch (e) {}
    isFetchingMore = false;
}

const scrollObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !isFetchingMore && !streamExhausted && currentView === 'discover') {
        if (infiniteMode === 'rows') appendNextNetflixRowBatch(3);
        else if (infiniteMode === 'search') appendMoreSearchResults();
    }
}, { rootMargin: "900px" });
scrollObserver.observe(infiniteSentinel);

searchSubmitBtn.onclick = performSearch;
searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') performSearch(); });

// ---------------- NAVIGATION ----------------
navItems.forEach(item => {
    item.addEventListener('click', async () => {
        navItems.forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        currentView = item.getAttribute('data-view');

        if (currentView === 'discover') {
            heroBanner.style.display = "flex";
            filterPanel.style.display = "flex";
            infiniteSentinel.style.display = "flex";
            initEndlessNetflixHome();
        } else if (currentView === 'nova') {
            infiniteMode = "none";
            infiniteSentinel.style.display = "none";
            heroBanner.style.display = "none";
            filterPanel.style.display = "none";
            renderEnlargedNovaView();
        } else if (currentView === 'dataviz') {
            infiniteMode = "none";
            infiniteSentinel.style.display = "none";
            heroBanner.style.display = "none";
            filterPanel.style.display = "none";
            renderDataAnalyticsDashboard();
        } else {
            infiniteMode = "none";
            infiniteSentinel.style.display = "none";
            heroBanner.style.display = "none";
            filterPanel.style.display = "none";
            displayedMovieIds.clear();

            if (currentUser) await syncCloudLibrary();
            else watchedMovies = await repairSavedPosters(watchedMovies);

            const titles = {
                watchlist: '<i class="fa-solid fa-bookmark" style="color:var(--secondary-glow);"></i> My Saved Watchlist',
                favorites: '<i class="fa-solid fa-heart" style="color:#f43f5e;"></i> My Favorite Movies & Series',
                watched: '<i class="fa-solid fa-circle-check" style="color:#10b981;"></i> Watched History & AI Similar Picks'
            };
            mainContainer.innerHTML = `<h3 class="row-title">${titles[currentView]}</h3>`;

            if (currentView === 'watched' && watchedMovies.length > 0) {
                try {
                    const lw = watchedMovies[0];
                    const lwType = lw.media_type === 'tv' ? 'tv' : 'movie';
                    const simRes = await fetch(`https://api.themoviedb.org/3/${lwType}/${lw.id}/recommendations?api_key=${TMDB_API_KEY}&page=1`).then(r => r.json());
                    const simItems = (simRes.results || []).map(m => ({
                        ...m,
                        media_type: lwType,
                        rationale: `AI Recommended because you watched "${lw.title}".`
                    }));
                    const simRow = buildRowElement(`<i class="fa-solid fa-robot" style="color:var(--primary-glow);"></i> 🤖 AI Picks Because You Watched "${escapeHTML(lw.title)}"`, simItems, true, false);
                    if (simRow) mainContainer.appendChild(simRow);
                } catch (e) {}
            }

            const grid = document.createElement('div');
            grid.className = 'movie-grid';
            const targetArr = currentView === 'watchlist' ? watchlist : (currentView === 'favorites' ? favorites : watchedMovies);
            if (targetArr.length > 0) {
                targetArr.filter(isSafeNonPorn).forEach(movie => grid.appendChild(createMovieCard(movie)));
            } else {
                grid.innerHTML = `<p style="color: var(--text-muted); font-weight:500;">No titles saved here yet. Click any movie or series card to add it!</p>`;
            }
            mainContainer.appendChild(grid);
        }
    });
});

// ---------------- ANALYTICS HUB ----------------
async function renderDataAnalyticsDashboard() {
    let insights = {
        total_recommendations_viewed: watchedMovies.length,
        total_liked: favorites.length,
        total_watchlist: watchlist.length,
        dominant_mood: userGenres.length ? userGenres.slice(0, 3).map(id => GENRE_OPTIONS[id] || ALL_GENRE_LABELS[id]).join(' • ') : "Multi-Condition Neural Match"
    };
    if (currentUser) {
        try {
            const res = await fetch(`${BACKEND_URL}/api/user/insights?username=${encodeURIComponent(currentUser)}`);
            const d = await res.json();
            insights.total_liked = Math.max(favorites.length, d.total_liked || 0);
            insights.total_watchlist = Math.max(watchlist.length, d.total_watchlist || 0);
            insights.total_recommendations_viewed = watchedMovies.length + (d.total_recommendations_viewed || 0);
        } catch(e) {}
    }

    mainContainer.innerHTML = `
        <div class="dataviz-container" style="display:flex; flex-direction:column; gap:25px;">
            <div class="nova-banner-clean">
                <div style="display:flex; align-items:center; gap:20px;">
                    <i class="fa-solid fa-chart-line" style="font-size: 2.5rem; color: var(--secondary-glow);"></i>
                    <div>
                        <h2>CineMind Data Science & Analytics Hub</h2>
                        <p>Live metrics from user interaction telemetry, watched history, and SQLite preference models.</p>
                    </div>
                </div>
            </div>
            <div class="cascade-accordion">
                <div class="cascade-item active" id="analyticsAccordion">
                    <div class="cascade-header" onclick="document.getElementById('analyticsAccordion').classList.toggle('active')">
                        <span><i class="fa-solid fa-chart-pie" style="margin-right:10px;"></i> User Insights & Genre Popularity Distribution</span>
                        <i class="fa-solid fa-chevron-down cascade-icon"></i>
                    </div>
                    <div class="cascade-body">
                        <div class="analytics-grid-packed">
                            <div class="analytics-stat-card">
                                <h4><i class="fa-solid fa-eye"></i> Watched / Tracked</h4>
                                <p>${insights.total_recommendations_viewed}</p>
                            </div>
                            <div class="analytics-stat-card">
                                <h4><i class="fa-solid fa-heart"></i> Total Favorited</h4>
                                <p>${insights.total_liked}</p>
                            </div>
                            <div class="analytics-stat-card">
                                <h4><i class="fa-solid fa-bookmark"></i> In Watchlist</h4>
                                <p>${insights.total_watchlist}</p>
                            </div>
                            <div class="analytics-stat-card">
                                <h4><i class="fa-solid fa-brain"></i> Calibrated Taste</h4>
                                <p style="font-size: 1.02rem;">${escapeHTML(insights.dominant_mood)}</p>
                            </div>
                        </div>
                        <div class="chart-box-wrapper">
                            <canvas id="genreChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    if (analyticsChartInstance) analyticsChartInstance.destroy();
    const ctx = document.getElementById('genreChart').getContext('2d');
    analyticsChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Sci-Fi', 'Drama', 'BL / GL', 'Anime', 'Docs', 'Sports'],
            datasets: [{
                label: 'Neural Taste Weight (%)',
                data: [
                    userGenres.includes('878') ? 52 : 34,
                    userGenres.includes('18') ? 48 : 30,
                    (userGenres.includes('BL') || userGenres.includes('GL')) ? 54 : 32,
                    userGenres.includes('ANIME') ? 50 : 29,
                    userGenres.includes('99') ? 46 : 26,
                    userGenres.includes('SPORTS') ? 45 : 25
                ],
                backgroundColor: ['#00f2fe', '#d946ef', '#f43f5e', '#38bdf8', '#a855f7', '#10b981'],
                borderRadius: 10,
                maxBarThickness: 58
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, max: 60, grid: { color: 'rgba(148,163,184,0.12)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { weight: '600' } } }
            }
        }
    });
}

// ---------------- ENLARGED NOVA AI HUB ----------------
function renderEnlargedNovaView() {
    mainContainer.innerHTML = `
        <div class="nova-view-container" style="display:flex; flex-direction:column; gap:22px;">
            <div class="nova-banner-clean">
                <div style="display:flex; align-items:center; gap:20px;">
                    <img src="nova.png" alt="Nova" class="nova-avatar-animated" onclick="triggerTiltAnimation(this)" onerror="this.src='CineMind-Logo.jpg'">
                    <div>
                        <h2>Nova AI Intelligence Hub <span style="font-size:0.8rem; background:rgba(16,185,129,0.2); color:#10b981; padding:4px 10px; border-radius:12px; vertical-align:middle; margin-left:8px;">Contextual Memory Active</span></h2>
                        <p>Ask specific movie questions, BL/GL recommendations, real-life sports, true-crime docs, or describe any plot!</p>
                    </div>
                </div>
                <button type="button" class="filter-pill" onclick="clearNovaMemory()"><i class="fa-solid fa-broom"></i> Clear Memory</button>
            </div>
            <div class="nova-chat-box-large glass-panel" style="border-radius: 28px; padding: 26px; display: flex; flex-direction: column; gap: 18px; background: var(--panel-bg); border: 1px solid var(--glass-border);">
                <div class="nova-history-large" id="novaEnlargedHistory" style="height: 290px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; background: var(--chat-history-bg); padding: 20px; border-radius: 20px; border: 1px solid var(--glass-border);"></div>
                <div class="quick-chips">
                    <span class="chip" onclick="sendEnlargedPrompt('Best Thai Boys Love BL dramas')">💙 "Best Thai BL Dramas"</span>
                    <span class="chip" onclick="sendEnlargedPrompt('Top Girls Love GL series like GAP and The Secret of Us')">💖 "Top GL Series"</span>
                    <span class="chip" onclick="sendEnlargedPrompt('Documentaries like Jeffrey Dahmer')">🕵️ "Docs like Jeffrey Dahmer"</span>
                    <span class="chip" onclick="sendEnlargedPrompt('Real life sports shows like FIFA, WWE, and Formula 1')">🏆 "Real-Life Sports (FIFA/WWE)"</span>
                </div>
                <div class="nova-input-row" style="display: flex; gap: 10px;">
                    <input type="text" id="novaEnlargedInput" placeholder="Ask a movie question, country, plot, or follow-up..." autocomplete="off" style="flex: 1; background: var(--input-bg); border: 1px solid var(--glass-border); border-radius: 26px; padding: 14px 20px; outline: none; font-size: 0.95rem; color: var(--text-main);">
                    <button type="button" class="btn-action" id="novaEnlargedSendBtn"><i class="fa-solid fa-paper-plane"></i> Send</button>
                </div>
            </div>
            <h3 class="row-title" id="novaResultsTitle" style="margin-top: 10px;"><i class="fa-solid fa-sparkles" style="color: var(--secondary-glow);"></i> ${lastNovaQuery ? `Neural Matches for "${escapeHTML(lastNovaQuery)}"` : 'Neural Recommendations'}</h3>
            <div id="novaVerticalGrid" class="movie-grid"></div>
        </div>
    `;

    renderChatHistoryInto(document.getElementById('novaEnlargedHistory'));
    const vGrid = document.getElementById('novaVerticalGrid');
    if (lastNovaMovies && lastNovaMovies.length > 0) {
        lastNovaMovies.filter(isSafeNonPorn).forEach(m => vGrid.appendChild(createMovieCard(m, true, lastNovaQuery)));
    } else {
        vGrid.innerHTML = `<p style="color: var(--text-muted); font-weight:500;">Try clicking one of the prompts above or ask Nova anything!</p>`;
    }

    const inputField = document.getElementById('novaEnlargedInput');
    const sendButton = document.getElementById('novaEnlargedSendBtn');
    const executeEnlargedChat = async (promptText) => {
        const msg = promptText || inputField.value.trim();
        if (!msg) return;
        if (!promptText) inputField.value = '';
        await sendToNovaEngine(msg);
    };
    sendButton.onclick = () => executeEnlargedChat();
    inputField.addEventListener('keydown', (e) => { if (e.key === 'Enter') executeEnlargedChat(); });
    window.sendEnlargedPrompt = (p) => executeEnlargedChat(p);
}

// ---------------- MODAL DETAILS, EXACT GENRES, CAST/CHARACTERS/DIRECTOR/CREW, TRAILER & SIMILAR PICKS ----------------
async function loadModalSimilarRecommendations(id, mType, title) {
    const box = document.getElementById('modalSimilarBox');
    const strip = document.getElementById('modalSimilarStrip');
    box.style.display = 'none';
    strip.innerHTML = '';
    try {
        const r = await fetch(`https://api.themoviedb.org/3/${mType}/${id}/recommendations?api_key=${TMDB_API_KEY}&page=1`);
        const d = await r.json();
        const recs = (d.results || []).filter(x => x.poster_path && isSafeNonPorn(x)).slice(0, 8);
        if (!recs.length) return;
        box.style.display = 'flex';
        recs.forEach(sim => {
            const sTitle = sim.title || sim.name;
            const sPoster = `https://image.tmdb.org/t/p/w300${sim.poster_path}`;
            const item = document.createElement('div');
            item.className = 'modal-sim-card';
            item.onclick = () => {
                fetchAndOpenModal(sTitle, sPoster, `AI Recommended because you viewed "${title}".`, sim.id, 94, mType, sim);
            };
            item.innerHTML = `<img src="${sPoster}" alt="${escapeHTML(sTitle)}"><span>${escapeHTML(sTitle)}</span>`;
            strip.appendChild(item);
        });
    } catch (e) {}
}

function renderModalCreditsAndGenres(item, originMovie) {
    // 1. Render Exact Genres
    const exactGenresEl = document.getElementById('modalExactGenres');
    const genreList = [];
    if (originMovie && originMovie._customGenreBadge) genreList.push(originMovie._customGenreBadge);
    if (Array.isArray(item.genres)) {
        item.genres.forEach(g => {
            if (g && g.name && !genreList.includes(g.name)) genreList.push(g.name);
        });
    }
    const lang = (item.original_language || "").toLowerCase();
    if (genreList.includes("Animation") && ["ja", "ko", "zh"].includes(lang) && !genreList.includes("Anime")) {
        genreList.unshift("Anime");
    }
    if (!genreList.length) genreList.push("Drama");

    exactGenresEl.innerHTML = `<span style="font-size:0.8rem; font-weight:700; color:var(--secondary-glow); margin-right:4px;"><i class="fa-solid fa-tags"></i> Exact Genres:</span>` +
        genreList.map(g => `<span class="exact-genre-pill">${escapeHTML(g)}</span>`).join('');

    // 2. Render Director, Writers, Crew & Cast with Character Names
    const credits = item.credits || {};
    const cast = (credits.cast || []).slice(0, 12);
    const crew = credits.crew || [];

    const directors = crew.filter(c => c.job === 'Director').map(c => c.name);
    if (directors.length === 0 && Array.isArray(item.created_by) && item.created_by.length) {
        item.created_by.forEach(c => directors.push(c.name));
    }
    if (directors.length === 0) {
        crew.filter(c => c.department === 'Directing').slice(0, 2).forEach(c => directors.push(c.name));
    }

    const writers = [...new Set(crew.filter(c => ['Writer', 'Screenplay', 'Story', 'Series Composition', 'Creator'].includes(c.job) || c.department === 'Writing').map(c => c.name))].slice(0, 4);
    const producersAndCrew = [...new Set(crew.filter(c => ['Producer', 'Executive Producer', 'Original Music Composer', 'Director of Photography'].includes(c.job)).map(c => `${c.name} (${c.job})`))].slice(0, 4);

    const crewGrid = document.getElementById('modalCrewGrid');
    crewGrid.innerHTML = `
        <div class="credits-crew-item">
            <strong><i class="fa-solid fa-clapperboard"></i> Director / Creator</strong>
            <span>${escapeHTML(directors.slice(0, 3).join(', ') || 'Featured Studio Director')}</span>
        </div>
        <div class="credits-crew-item">
            <strong><i class="fa-solid fa-pen-nib"></i> Writers</strong>
            <span>${escapeHTML(writers.join(', ') || 'Original Screenplay Team')}</span>
        </div>
        <div class="credits-crew-item">
            <strong><i class="fa-solid fa-gears"></i> Producers & Key Crew</strong>
            <span>${escapeHTML(producersAndCrew.join(' • ') || 'Production Ensemble')}</span>
        </div>
    `;

    const castListEl = document.getElementById('modalCastList');
    if (cast.length > 0) {
        castListEl.innerHTML = cast.map(actor => `
            <div class="cast-chip">
                <span class="cast-actor">${escapeHTML(actor.name)}</span>
                <span class="cast-character">as ${escapeHTML(actor.character || 'Lead Role')}</span>
            </div>
        `).join('');
    } else {
        castListEl.innerHTML = `<span style="font-size:0.8rem; color:var(--text-muted);">Cast details updating for this release.</span>`;
    }
}

async function fetchAndOpenModal(title, fallbackPoster, customRationale, movieId, matchPct = 95, mediaType = 'movie', originMovie = null) {
    try {
        let item = null;
        const mType = mediaType === 'tv' ? 'tv' : 'movie';
        if (movieId) {
            const append = mType === 'tv' ? 'content_ratings,keywords,credits' : 'release_dates,keywords,credits';
            const r = await fetch(`https://api.themoviedb.org/3/${mType}/${movieId}?api_key=${TMDB_API_KEY}&append_to_response=${append}`);
            const d = await r.json();
            if (d && d.id) item = d;
        }
        if (!item) {
            const r = await fetch(`https://api.themoviedb.org/3/search/${mType}?api_key=${TMDB_API_KEY}&include_adult=false&query=${encodeURIComponent(title)}`);
            const d = await r.json();
            const firstHit = d.results && d.results[0];
            if (firstHit && firstHit.id) {
                const append = mType === 'tv' ? 'content_ratings,keywords,credits' : 'release_dates,keywords,credits';
                item = await fetch(`https://api.themoviedb.org/3/${mType}/${firstHit.id}?api_key=${TMDB_API_KEY}&append_to_response=${append}`).then(res => res.json());
            }
        }
        if (!item || !isSafeNonPorn(item)) return;

        const key = `${mType}_${item.id}`;
        let certR18 = (originMovie && originMovie._isR18 === true)
            || r18Cache.get(key) === true
            || isGenuineR18(item);

        r18Cache.set(key, certR18);
        currentMovieData = item;
        currentMovieData._isR18 = certR18;
        currentMovieData.media_type = mType;
        currentMovieData.title = item.title || item.name || title;
        currentMovieData.poster = item.poster_path
            ? `https://image.tmdb.org/t/p/w500${item.poster_path}`
            : (fallbackPoster && fallbackPoster.startsWith('http') ? fallbackPoster : NO_POSTER);
        currentMovieData.rationale = customRationale;
        currentMovieData.match = matchPct;

        const originCountryLabel = resolveMovieOriginCountry(item);
        const dateStr = item.release_date || item.first_air_date || '';
        const year = dateStr ? dateStr.split('-')[0] : 'N/A';
        const rating = item.vote_average ? Number(item.vote_average).toFixed(1) : 'NR';
        const duration = item.runtime
            ? `${item.runtime} min`
            : (item.number_of_seasons ? `${item.number_of_seasons} Season(s)` : '');

        document.getElementById('modalPosterBadges').innerHTML = `
            ${certR18 ? `<span class="r18-badge">R-18</span>` : ''}
            <span class="media-badge">${mType === 'tv' ? '📺 SERIES' : '🎬 MOVIE'}</span>
        `;

        document.getElementById('modalTitle').innerText = currentMovieData.title;
        document.getElementById('modalMeta').innerHTML = `
            ${certR18 ? `<span class="r18-badge">R-18</span>` : ''}
            <span style="color:var(--secondary-glow); font-weight:800;"><i class="fa-solid fa-bolt"></i> ${matchPct}% Neural Match</span>
            <span style="background:rgba(124,58,237,0.18); padding:3px 10px; border-radius:10px; border:1px solid var(--glass-border); color:var(--text-main);"><i class="fa-solid fa-earth-asia" style="color:var(--secondary-glow);"></i> Origin: ${escapeHTML(originCountryLabel)}</span>
            <span><i class="fa-solid fa-calendar"></i> ${year}</span>
            <span><i class="fa-solid fa-star" style="color: #fbbf24;"></i> ${rating} TMDB</span>
            ${duration ? `<span><i class="fa-regular fa-clock"></i> ${duration}</span>` : ''}
            <span id="omdbBadge"></span>
        `;
        document.getElementById('modalOverview').innerText = item.overview || "No plot description available.";
        document.getElementById('modalPoster').src = currentMovieData.poster;
        document.getElementById('modalRationale').innerText = customRationale || `Matched via CineMind neural collaborative filters for ${currentUser || 'Guest'}.`;

        // Populate Exact Genres + Cast, Characters, Director, Writers & Crew
        renderModalCreditsAndGenres(item, originMovie);

        fetch(`${BACKEND_URL}/api/omdb?title=${encodeURIComponent(currentMovieData.title)}&year=${year}`)
            .then(r => r.json())
            .then(o => {
                const b = document.getElementById('omdbBadge');
                if (b && o.imdbRating && o.imdbRating !== "N/A") {
                    b.innerHTML = `<i class="fa-brands fa-imdb" style="color:#f5c518; font-size:1.1rem;"></i> ${o.imdbRating} IMDb`;
                }
            }).catch(() => {});

        document.getElementById('modalProviders').innerHTML = `<i class="fa-solid fa-tv"></i> <span>Checking streaming apps (${selectedRegion})...</span>`;
        fetch(`https://api.themoviedb.org/3/${mType}/${currentMovieData.id}/watch/providers?api_key=${TMDB_API_KEY}`)
            .then(r => r.json())
            .then(provData => {
                const provs = provData.results && (provData.results[selectedRegion] || provData.results.US);
                const flat = provs && provs.flatrate ? provs.flatrate.map(p => p.provider_name).join(', ') : null;
                document.getElementById('modalProviders').innerHTML = `<i class="fa-solid fa-tv"></i> <span>Streaming in ${selectedRegion}: <strong>${flat || 'Available on Digital / VOD'}</strong></span>`;
            }).catch(() => {
                document.getElementById('modalProviders').innerHTML = `<i class="fa-solid fa-tv"></i> <span>Streaming on: <strong>Global VOD Catalog</strong></span>`;
            });

        document.getElementById('trailerBtn').onclick = () => { fetchAndPlayTrailer(currentMovieData.id, currentMovieData.title, mType); };
        document.getElementById('notInterestedModalBtn').onclick = () => { markMovieNotInterested(currentMovieData); };

        updateButtonStates();
        loadModalSimilarRecommendations(currentMovieData.id, mType, currentMovieData.title);
        document.getElementById('movieModal').classList.add('active');
    } catch (error) {}
}

async function fetchAndPlayTrailer(id, title, mType = 'movie') {
    try {
        const res = await fetch(`https://api.themoviedb.org/3/${mType}/${id}/videos?api_key=${TMDB_API_KEY}`);
        const data = await res.json();
        const videos = (data.results || []).filter(v => v.site === 'YouTube');
        const trailer = videos.find(v => v.type === 'Trailer' && v.official)
            || videos.find(v => v.type === 'Trailer')
            || videos[0];

        const extBtn = document.getElementById('youtubeExternalBtn');
        if (trailer && trailer.key) {
            const origin = window.location.origin.startsWith('http') ? `&origin=${encodeURIComponent(window.location.origin)}` : '';
            document.getElementById('youtubeIframe').src = `https://www.youtube-nocookie.com/embed/${trailer.key}?autoplay=1&rel=0${origin}`;
            extBtn.href = `https://www.youtube.com/watch?v=${trailer.key}`;
            document.getElementById('videoModalTitle').innerText = `${title} – Official Trailer`;
            document.getElementById('videoModal').classList.add('active');
        } else {
            window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(title + ' official trailer')}`, '_blank', 'noopener');
        }
    } catch (err) { alert("Could not load trailer."); }
}

document.getElementById('closeModal').onclick = () => document.getElementById('movieModal').classList.remove('active');
document.getElementById('closeVideoModal').onclick = () => {
    document.getElementById('youtubeIframe').src = "";
    document.getElementById('videoModal').classList.remove('active');
};

function updateButtonStates() {
    if (!currentMovieData) return;
    const inWatchlist = watchlist.some(m => Number(m.id) === Number(currentMovieData.id));
    const wBtn = document.getElementById('watchlistBtn');
    wBtn.innerHTML = inWatchlist ? `<i class="fa-solid fa-check"></i> In Watchlist` : `<i class="fa-solid fa-plus"></i> Watchlist`;
    wBtn.style.background = inWatchlist ? "#10b981" : "linear-gradient(135deg, var(--primary-glow), var(--secondary-glow))";

    const inFavs = favorites.some(m => Number(m.id) === Number(currentMovieData.id));
    const fBtn = document.getElementById('favoriteBtn');
    fBtn.innerHTML = inFavs ? `<i class="fa-solid fa-heart" style="color: #f43f5e;"></i> Favorited` : `<i class="fa-solid fa-heart"></i> Favorite`;

    const inWatched = watchedMovies.some(m => Number(m.id) === Number(currentMovieData.id));
    const watchedBtn = document.getElementById('watchedBtn');
    watchedBtn.innerHTML = inWatched ? `<i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Watched` : `<i class="fa-solid fa-eye"></i> Mark Watched`;
}

function libraryPayload(m) {
    const cleanPoster = (m.poster && m.poster.startsWith('http'))
        ? m.poster
        : (m.poster_path ? `https://image.tmdb.org/t/p/w500${m.poster_path}` : '');
    return {
        id: m.id,
        title: m.title || m.name,
        poster: cleanPoster,
        vote_average: m.vote_average || 0,
        media_type: m.media_type || 'movie',
        origin_country: m.origin_country || [],
        original_language: m.original_language || '',
        _isR18: Boolean(m._isR18),
        rationale: m.rationale || "Saved in your personal CineMind cloud library."
    };
}

document.getElementById('watchlistBtn').onclick = async () => {
    if(!currentUser) { alert("Please log in to save items to your cloud watchlist."); updateProfileModalView(); profileModal.classList.add('active'); return; }
    try {
        const res = await fetch(`${BACKEND_URL}/api/user/library/toggle`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: currentUser, type: 'watchlist', movie: libraryPayload(currentMovieData)})
        });
        const data = await res.json();
        if(data.success) {
            await syncCloudLibrary();
            updateButtonStates();
            if (currentView === 'watchlist') navItems[3].click();
        }
    } catch(e) { alert("Sync error."); }
};

document.getElementById('favoriteBtn').onclick = async () => {
    if(!currentUser) { alert("Please log in to save items to your cloud favorites."); updateProfileModalView(); profileModal.classList.add('active'); return; }
    try {
        const res = await fetch(`${BACKEND_URL}/api/user/library/toggle`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: currentUser, type: 'favorites', movie: libraryPayload(currentMovieData)})
        });
        const data = await res.json();
        if(data.success) {
            await syncCloudLibrary();
            updateButtonStates();
            if (currentView === 'favorites') navItems[4].click();
        }
    } catch(e) { alert("Sync error."); }
};

document.getElementById('watchedBtn').onclick = () => {
    if (!currentMovieData) return;
    const idx = watchedMovies.findIndex(m => Number(m.id) === Number(currentMovieData.id));
    if (idx >= 0) {
        watchedMovies.splice(idx, 1);
    } else {
        watchedMovies.unshift(libraryPayload(currentMovieData));
    }
    localStorage.setItem(`cinemind_watched_${currentUser || 'guest'}`, JSON.stringify(watchedMovies));
    updateButtonStates();
    updateProfileModalView();
    if (currentView === 'watched') navItems[5].click();
    else if (currentView === 'discover') initEndlessNetflixHome();
};

// ---------------- UNIFIED SUPER-NOVA CHAT ENGINE (WITH TILTING MOTION ON TAP) ----------------
const chatWrapper = document.getElementById('chatWrapper');
const chatToggle = document.getElementById('chatToggle');
const chatModal = document.getElementById('chatModal');
const closeChat = document.getElementById('closeChat');
const chatTooltip = document.getElementById('chatTooltip');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');

let isDraggingChat = false;
let chatDragMoved = false;
let dragStartX = 0, dragStartY = 0;
let wrapperStartLeft = 0, wrapperStartTop = 0;

function adjustChatModalPlacement() {
    const rect = chatWrapper.getBoundingClientRect();
    if (rect.left < window.innerWidth / 2) {
        chatModal.style.right = 'auto';
        chatModal.style.left = '0px';
        chatWrapper.style.alignItems = 'flex-start';
    } else {
        chatModal.style.left = 'auto';
        chatModal.style.right = '0px';
        chatWrapper.style.alignItems = 'flex-end';
    }
    if (rect.top < 420) {
        chatModal.style.bottom = 'auto';
        chatModal.style.top = '82px';
    } else {
        chatModal.style.top = 'auto';
        chatModal.style.bottom = '86px';
    }
}

function toggleNovaChatModal() {
    triggerTiltAnimation(chatToggle);
    adjustChatModalPlacement();
    chatModal.classList.toggle('active');
    chatTooltip.style.display = chatModal.classList.contains('active') ? 'none' : 'block';
    if (chatModal.classList.contains('active')) chatInput.focus();
}

chatToggle.addEventListener('pointerdown', (e) => {
    isDraggingChat = true;
    chatDragMoved = false;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    const rect = chatWrapper.getBoundingClientRect();
    wrapperStartLeft = rect.left;
    wrapperStartTop = rect.top;
    chatToggle.setPointerCapture(e.pointerId);
});

chatToggle.addEventListener('pointermove', (e) => {
    if (!isDraggingChat) return;
    const dx = e.clientX - dragStartX;
    const dy = e.clientY - dragStartY;
    if (Math.hypot(dx, dy) > 8) {
        chatDragMoved = true;
        const maxLeft = window.innerWidth - chatWrapper.offsetWidth - 10;
        const maxTop = window.innerHeight - chatWrapper.offsetHeight - 10;
        const newLeft = Math.max(10, Math.min(maxLeft, wrapperStartLeft + dx));
        const newTop = Math.max(10, Math.min(maxTop, wrapperStartTop + dy));
        chatWrapper.style.left = `${newLeft}px`;
        chatWrapper.style.top = `${newTop}px`;
        chatWrapper.style.right = 'auto';
        chatWrapper.style.bottom = 'auto';
        adjustChatModalPlacement();
    }
});

chatToggle.addEventListener('pointerup', (e) => {
    if (!isDraggingChat) return;
    isDraggingChat = false;
    chatToggle.releasePointerCapture(e.pointerId);
    if (!chatDragMoved) toggleNovaChatModal();
});

chatTooltip.onclick = () => toggleNovaChatModal();
closeChat.onclick = () => { chatModal.classList.remove('active'); chatTooltip.style.display = 'block'; };

function appendBubbleToBothChats(text, sender, isHTML = false) {
    [chatHistory, document.getElementById('novaEnlargedHistory')].forEach(box => {
        if (!box) return;
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}-bubble`;
        if (isHTML) bubble.innerHTML = text;
        else bubble.textContent = text;
        box.appendChild(bubble);
        box.scrollTop = box.scrollHeight;
    });
}

async function sendToNovaEngine(message) {
    appendBubbleToBothChats(message, 'user', false);
    appendBubbleToBothChats(`<i class="fa-solid fa-spinner fa-spin"></i> Nova is analyzing your question & scanning cinema vectors...`, 'ai', true);

    try {
        const activeFilterGenres = [...selectedGenres].map(id => GENRE_OPTIONS[id] || ALL_GENRE_LABELS[id]).filter(Boolean);
        const prefGenres = activeFilterGenres.length ? activeFilterGenres : userGenres.map(id => GENRE_OPTIONS[id] || ALL_GENRE_LABELS[id]).filter(Boolean);

        const clientGuesses = await clientSidePlotAssist(message);

        const response = await fetch(`${BACKEND_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                client_guesses: clientGuesses,
                profile: {
                    name: currentUser || 'Guest',
                    favorite_genres: prefGenres,
                    origin_country: selectedCountry,
                    watched_titles: watchedMovies.slice(0, 5).map(m => m.title),
                    disliked_titles: notInterestedState.titles || []
                },
                region: selectedRegion,
                history: conversationHistory
            })
        });
        const data = await response.json();

        [chatHistory, document.getElementById('novaEnlargedHistory')].forEach(box => {
            if (box && box.lastChild && box.lastChild.innerHTML.includes('fa-spinner')) box.lastChild.remove();
        });

        const replyText = data.reply || "Here are the best matches I found!";
        appendBubbleToBothChats(replyText, 'ai', false);

        const safeMovies = (data.movies || []).filter(isSafeNonPorn);
        const movieContextNote = safeMovies.length
            ? ` [Movies shown to user: ${safeMovies.slice(0, 5).map(m => `${m.title} (${(m.release_date || '').slice(0,4)})`).join(', ')}]`
            : '';
        conversationHistory.push({ role: "user", content: message });
        conversationHistory.push({ role: "assistant", content: replyText + movieContextNote });

        if (safeMovies.length > 0) {
            lastNovaMovies = safeMovies;
            lastNovaQuery = message;
            saveNovaMemory();

            if (currentView === 'nova') {
                const titleEl = document.getElementById('novaResultsTitle');
                const vGrid = document.getElementById('novaVerticalGrid');
                if (titleEl) titleEl.innerHTML = `<i class="fa-solid fa-sparkles" style="color: var(--secondary-glow);"></i> Neural Matches for "${escapeHTML(message)}"`;
                if (vGrid) {
                    vGrid.innerHTML = '';
                    safeMovies.forEach(movie => vGrid.appendChild(createMovieCard(movie, true, message)));
                }
            } else {
                infiniteMode = "none";
                infiniteSentinel.style.display = "none";
                heroBanner.style.display = "none";
                filterPanel.style.display = "none";
                mainContainer.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                        <h3 class="row-title"><i class="fa-solid fa-sparkles" style="color: var(--secondary-glow);"></i> Nova AI Answer & Matches for "${escapeHTML(message)}"</h3>
                        <button type="button" class="filter-pill" onclick="heroBanner.style.display='flex';filterPanel.style.display='flex';initEndlessNetflixHome();"><i class="fa-solid fa-arrow-left"></i> Back to Galaxy Stream</button>
                    </div>
                    <div class="ai-rationale-box" style="margin-top:-14px;">
                        <span class="ai-rationale-title"><i class="fa-solid fa-wand-magic-sparkles"></i> Nova AI Response</span>
                        <span class="ai-rationale-text" style="font-size:0.95rem; color:var(--text-main);">${escapeHTML(replyText)}</span>
                    </div>
                `;
                const grid = document.createElement('div');
                grid.className = 'movie-grid';
                safeMovies.forEach(movie => grid.appendChild(createMovieCard(movie, true, message)));
                mainContainer.appendChild(grid);
            }
        } else {
            saveNovaMemory();
        }
    } catch (error) {
        [chatHistory, document.getElementById('novaEnlargedHistory')].forEach(box => {
            if (box && box.lastChild && box.lastChild.innerHTML.includes('fa-spinner')) box.lastChild.remove();
        });
        appendBubbleToBothChats("Could not connect to Render server. Make sure your backend service is live.", 'ai', false);
    }
}

async function handleChat(queryText) {
    const message = queryText || chatInput.value.trim();
    if (!message) return;
    if (!queryText) chatInput.value = '';
    await sendToNovaEngine(message);
}

window.sendQuickPrompt = (prompt) => handleChat(prompt);
sendBtn.addEventListener('click', () => handleChat());
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        handleChat();
    }
});

initEndlessNetflixHome();
</script>
</body>
</html>
