<template>
  <div class="realistic-train-background">
    <!-- SVG Filters for Textures -->
    <svg width="0" height="0" style="position:absolute">
      <filter id="noise">
        <feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="3" stitchTiles="stitch"/>
        <feColorMatrix type="saturate" values="0"/>
        <feComponentTransfer>
          <feFuncA type="linear" slope="0.1"/>
        </feComponentTransfer>
      </filter>
      <defs>
        <linearGradient id="duneGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#E6C288" />
          <stop offset="100%" stop-color="#D4A373" />
        </linearGradient>
        <linearGradient id="duneShadow" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="rgba(0,0,0,0.1)" />
          <stop offset="100%" stop-color="rgba(0,0,0,0)" />
        </linearGradient>
      </defs>
    </svg>

    <!-- Sky Layer -->
    <div class="layer sky">
      <div class="stars"></div>
    </div>

    <!-- Celestial Bodies (Sun & Moon) -->
    <div class="celestial-system">
      <div class="sun-wrapper">
        <div class="sun"></div>
        <div class="sun-halo"></div>
      </div>
      <div class="moon-wrapper">
        <div class="moon">
          <div class="crater c1"></div>
          <div class="crater c2"></div>
          <div class="crater c3"></div>
        </div>
        <div class="moon-halo"></div>
      </div>
    </div>

    <!-- Heat Haze -->
    <div class="heat-haze"></div>

    <!-- Far Dunes (Parallax Speed: Slow) -->
    <div class="layer far-dunes"></div>

    <!-- Mid Dunes (Parallax Speed: Medium) -->
    <div class="layer mid-dunes"></div>

    <!-- Ground/Track Layer -->
    <div class="layer ground">
      <div class="track-bed"></div>
      <div class="track"></div>
    </div>

    <!-- Train Layer -->
    <div class="layer train-layer">
      <div class="train-shadow"></div>
      <div class="train-container">
        <!-- Industrial Locomotive -->
        <div class="train-car locomotive">
          <div class="cabin">
            <div class="roof"></div>
            <div class="window"></div>
          </div>
          <div class="engine-block">
            <div class="vents"></div>
            <div class="handrail"></div>
            <div class="headlight"></div>
            <div class="headlight-beam"></div>
          </div>
          <div class="hazard-stripes"></div>
          <div class="chassis"></div>
          <div class="wheels">
            <div class="wheel big">
              <div class="rim"></div>
              <div class="spokes"></div>
            </div>
            <div class="wheel big">
              <div class="rim"></div>
              <div class="spokes"></div>
            </div>
            <div class="wheel big">
              <div class="rim"></div>
              <div class="spokes"></div>
            </div>
          </div>
        </div>

        <!-- Hopper Wagons with Stones -->
        <div class="train-car wagon hopper-wagon" v-for="n in 6" :key="'h'+n">
          <div class="stone-pile"></div>
          <div class="hopper-body">
            <div class="inner-shadow"></div>
            <div class="ribs"></div>
            <div class="ladder"></div>
          </div>
          <div class="chassis"></div>
          <div class="wheels">
            <div class="wheel">
              <div class="rim"></div>
              <div class="spokes"></div>
            </div>
            <div class="wheel">
              <div class="rim"></div>
              <div class="spokes"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Foreground Layer (Parallax Speed: Fast) -->
    <div class="layer foreground">
      <div class="desert-shrub" v-for="n in 4" :key="'s'+n" :style="{ left: (n * 25) + '%' }"></div>
      <div class="rock" v-for="n in 3" :key="'r'+n" :style="{ left: (n * 30 + 15) + '%' }"></div>
    </div>

    <!-- Day/Night Overlay -->
    <div class="day-night-overlay"></div>
  </div>
</template>

<script>
export default {
  name: 'RealisticTrainBackground'
}
</script>

<style scoped>
.realistic-train-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
  pointer-events: none;
  background-color: #87CEEB;
}

.layer {
  position: absolute;
  width: 100%;
  height: 100%;
}

/* Sky: Day/Night Cycle */
.sky {
  background: linear-gradient(to bottom, #4FC3F7 0%, #E0F7FA 50%, #FFCCBC 80%, #FFAB91 100%);
  animation: skyCycle 60s linear infinite;
}

.stars {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 3px),
    radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 2px),
    radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 3px);
  background-size: 550px 550px, 350px 350px, 250px 250px;
  background-position: 0 0, 40px 60px, 130px 270px;
  opacity: 0;
  animation: starFade 60s linear infinite;
}

.celestial-system {
  position: absolute;
  bottom: -50vh; /* Center of rotation below screen */
  left: 50%;
  width: 100vw; /* Wide enough orbit */
  height: 100vw;
  transform: translateX(-50%);
  animation: celestialRotate 60s linear infinite;
  /* z-index removed to respect DOM order (behind dunes) */
}

.sun-wrapper {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100px;
  height: 100px;
}

.sun {
  position: absolute;
  width: 60px;
  height: 60px;
  background: radial-gradient(circle at 30% 30%, #FFFDE7 0%, #FDD835 100%);
  border-radius: 50%;
  box-shadow: 0 0 50px rgba(253, 216, 53, 0.8);
  top: 20px;
  left: 20px;
}

.sun-halo {
  position: absolute;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse 4s ease-in-out infinite;
}

.moon-wrapper {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translate(-50%, 50%) rotate(180deg); /* Opposite to sun */
  width: 80px;
  height: 80px;
}

.moon {
  position: absolute;
  width: 60px;
  height: 60px;
  background: radial-gradient(circle at 30% 30%, #E0E0E0 0%, #BDBDBD 100%);
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
  top: 10px;
  left: 10px;
  overflow: hidden;
}

.moon .crater {
  position: absolute;
  background: rgba(0,0,0,0.1);
  border-radius: 50%;
  box-shadow: inset 1px 1px 2px rgba(0,0,0,0.2);
}

.moon .c1 { top: 20%; left: 20%; width: 15px; height: 15px; }
.moon .c2 { top: 60%; left: 50%; width: 10px; height: 10px; }
.moon .c3 { top: 30%; left: 60%; width: 8px; height: 8px; }

.moon-halo {
  position: absolute;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 60%);
  border-radius: 50%;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 0.8; }
}

@keyframes skyCycle {
  0% { background: linear-gradient(to bottom, #0D47A1 0%, #000000 100%); } /* Night */
  10% { background: linear-gradient(to bottom, #1565C0 0%, #4527A0 100%); } /* Dawn */
  20% { background: linear-gradient(to bottom, #FF8A65 0%, #FFD54F 100%); } /* Sunrise */
  30% { background: linear-gradient(to bottom, #4FC3F7 0%, #E0F7FA 100%); } /* Day */
  70% { background: linear-gradient(to bottom, #4FC3F7 0%, #E0F7FA 100%); } /* Day */
  80% { background: linear-gradient(to bottom, #FF7043 0%, #8E24AA 100%); } /* Sunset */
  90% { background: linear-gradient(to bottom, #1565C0 0%, #4527A0 100%); } /* Dusk */
  100% { background: linear-gradient(to bottom, #0D47A1 0%, #000000 100%); } /* Night */
}

@keyframes celestialRotate {
  0% { transform: translateX(-50%) rotate(180deg); }
  100% { transform: translateX(-50%) rotate(540deg); }
}

@keyframes starFade {
  0%, 10% { opacity: 1; }
  20%, 80% { opacity: 0; }
  90%, 100% { opacity: 1; }
}

.day-night-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 10, 40, 0.7);
  pointer-events: none;
  z-index: 10;
  animation: dimming 60s linear infinite;
}

@keyframes dimming {
  0%, 10% { opacity: 0.8; } /* Night */
  20% { opacity: 0.4; } /* Sunrise */
  30%, 70% { opacity: 0; } /* Day */
  80% { opacity: 0.4; } /* Sunset */
  90%, 100% { opacity: 0.8; } /* Night */
}

/* Headlight */
.headlight {
  position: absolute;
  top: 25px; /* Adjusted position on nose */
  right: -2px;
  width: 8px;
  height: 8px;
  background: #FFF;
  border-radius: 50%;
  box-shadow: 0 0 5px #FFF;
  z-index: 5;
  opacity: 0;
  animation: lightOn 60s linear infinite;
}

.headlight-beam {
  position: absolute;
  top: 14px;
  left: 100%;
  width: 150px;
  height: 30px;
  background: linear-gradient(to right, rgba(255, 255, 200, 0.6) 0%, transparent 100%);
  transform-origin: left center;
  transform: rotate(15deg); /* Angle down slightly */
  clip-path: polygon(0 40%, 100% 0, 100% 100%, 0 60%);
  pointer-events: none;
  opacity: 0;
  animation: lightOn 60s linear infinite;
}

/* Window Glow */
.locomotive .window {
  /* Existing styles will be inherited, adding animation */
  animation: windowGlow 60s linear infinite;
}

@keyframes lightOn {
  0%, 15% { opacity: 1; }
  25%, 75% { opacity: 0; }
  85%, 100% { opacity: 1; }
}

@keyframes windowGlow {
  0%, 15% { background: #FFEB3B; box-shadow: 0 0 10px #FFEB3B; }
  25%, 75% { background: linear-gradient(135deg, #90A4AE 0%, #607D8B 100%); box-shadow: inset 1px 1px 2px rgba(0,0,0,0.5); }
  85%, 100% { background: #FFEB3B; box-shadow: 0 0 10px #FFEB3B; }
}

/* Heat Haze Overlay */
.heat-haze {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 30%;
  background: linear-gradient(to top, rgba(255,255,255,0.1), transparent);
  filter: url(#noise);
  opacity: 0.3;
  pointer-events: none;
}

/* Far Dunes */
.far-dunes {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 300' preserveAspectRatio='none'%3E%3Cpath d='M0,300 L0,150 C150,150 200,80 400,120 C600,160 700,100 900,140 C1100,180 1150,150 1200,180 L1200,300 Z' fill='url(%23duneGradient)' opacity='0.8'/%3E%3C/svg%3E");
  background-repeat: repeat-x;
  background-size: 100% 50%;
  background-position: bottom;
  animation: moveBackground 80s linear infinite;
  bottom: 80px;
  height: 60%;
  filter: brightness(0.9);
}

/* Mid Dunes */
.mid-dunes {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 200' preserveAspectRatio='none'%3E%3Cdefs%3E%3ClinearGradient id='g1' x1='0%25' y1='0%25' x2='0%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%23E6C288'/%3E%3Cstop offset='100%25' stop-color='%23D4A373'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath d='M0,200 L0,100 C200,80 300,150 500,120 C700,90 800,140 1000,110 C1100,95 1150,120 1200,100 L1200,200 Z' fill='url(%23g1)'/%3E%3C/svg%3E");
  background-repeat: repeat-x;
  background-size: 60% 40%;
  background-position: bottom;
  animation: moveBackground 40s linear infinite;
  bottom: 40px;
  height: 50%;
  filter: drop-shadow(0 -5px 15px rgba(0,0,0,0.1));
}

/* Ground/Track */
.ground {
  bottom: 0;
  height: 15%;
  background: linear-gradient(to bottom, #E6C288 0%, #D4A373 100%);
}

.track-bed {
  position: absolute;
  top: 0;
  width: 100%;
  height: 20px;
  background: 
    linear-gradient(to bottom, rgba(0,0,0,0.2), transparent),
    repeating-linear-gradient(90deg, transparent 0, transparent 2px, rgba(0,0,0,0.05) 2px, rgba(0,0,0,0.05) 4px); /* Gravel texture */
}

.track {
  position: absolute;
  top: 0;
  width: 100%;
  height: 15px;
  /* Ties with perspective (simulated by gradient) */
  background: 
    repeating-linear-gradient(90deg, #3E2723 0, #3E2723 12px, transparent 12px, transparent 24px),
    linear-gradient(to bottom, rgba(0,0,0,0.3), transparent);
  border-top: 4px solid #5D6D7E; /* Rail */
  border-bottom: 4px solid #5D6D7E;
  box-shadow: 0 5px 10px rgba(0,0,0,0.3); /* Track shadow */
}

/* Train Animation */
.train-layer {
  bottom: 15%;
  height: 120px;
  perspective: 1000px;
}

.train-shadow {
  position: absolute;
  bottom: 5px;
  left: 0;
  width: 100%;
  height: 10px;
  background: radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0.4) 0%, transparent 70%);
  transform: scaleX(1.5);
  animation: trainMove 25s linear infinite;
}

.train-container {
  display: flex;
  position: absolute;
  bottom: 12px;
  left: 100%;
  animation: trainMove 25s linear infinite;
  filter: drop-shadow(5px 5px 10px rgba(0,0,0,0.4)); /* Overall train shadow */
}

@keyframes trainMove {
  from { transform: translateX(0); }
  to { transform: translateX(-400%); }
}

@keyframes moveBackground {
  from { background-position-x: 0; }
  to { background-position-x: 100%; }
}

/* Train Cars */
.train-car {
  position: relative;
  margin-right: 4px;
  transform-style: preserve-3d;
}

/* Industrial Locomotive */
.locomotive {
  width: 170px;
  height: 75px;
  display: flex;
  flex-direction: column;
}

.locomotive .cabin {
  position: absolute;
  top: -25px;
  right: 15px;
  width: 55px;
  height: 40px;
  background: linear-gradient(135deg, #455A64 0%, #263238 100%);
  border: 1px solid #263238;
  border-radius: 2px;
  z-index: 2;
  box-shadow: -2px 2px 5px rgba(0,0,0,0.3);
}

.locomotive .roof {
  position: absolute;
  top: -3px;
  left: -2px;
  width: 110%;
  height: 5px;
  background: #263238;
  border-radius: 2px;
}

.locomotive .window {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 25px;
  height: 18px;
  background: linear-gradient(135deg, #90A4AE 0%, #607D8B 100%);
  border: 1px solid #263238;
  box-shadow: inset 1px 1px 2px rgba(0,0,0,0.5);
}

.locomotive .engine-block {
  width: 100%;
  height: 100%;
  position: relative;
  background: linear-gradient(to bottom, #37474F 0%, #263238 100%);
  border-right: 8px solid #F9A825; /* Yellow nose */
  border-radius: 4px;
}

.locomotive .vents {
  position: absolute;
  top: 10px;
  left: 15px;
  width: 70px;
  height: 35px;
  background: repeating-linear-gradient(90deg, #101518 0, #101518 4px, #37474F 4px, #37474F 8px);
  box-shadow: inset 1px 1px 3px rgba(0,0,0,0.5);
  border: 1px solid #101518;
}

.locomotive .handrail {
  position: absolute;
  top: 5px;
  left: 5px;
  width: 90%;
  height: 5px;
  border-top: 2px solid #CFD8DC;
  border-left: 2px solid #CFD8DC;
  border-right: 2px solid #CFD8DC;
  height: 50px;
  pointer-events: none;
}

.locomotive .hazard-stripes {
  position: absolute;
  bottom: 15px; /* Above chassis */
  left: 0;
  width: 100%;
  height: 12px;
  background: repeating-linear-gradient(45deg, #F9A825 0, #F9A825 10px, #212121 10px, #212121 20px);
  box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.locomotive .chassis {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 15px;
  background: #101518;
  border-radius: 0 0 4px 4px;
}

/* Hopper Wagons */
.hopper-wagon {
  width: 120px;
  height: 55px;
  margin-top: 20px;
  position: relative;
}

.hopper-body {
  width: 100%;
  height: 100%;
  background: linear-gradient(to bottom, #6D4C41 0%, #4E342E 100%); /* Rusty Brown */
  clip-path: polygon(0 0, 100% 0, 90% 100%, 10% 100%);
  position: relative;
}

.hopper-body .inner-shadow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(to right, rgba(0,0,0,0.3), transparent 20%, transparent 80%, rgba(0,0,0,0.3));
  pointer-events: none;
}

.hopper-body .ribs {
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(90deg, transparent 0, transparent 25px, rgba(0,0,0,0.4) 25px, rgba(0,0,0,0.4) 28px);
}

.hopper-body .ladder {
  position: absolute;
  right: 5px;
  top: 5px;
  width: 10px;
  height: 40px;
  border: 1px solid rgba(255,255,255,0.2);
  background: repeating-linear-gradient(to bottom, transparent 0, transparent 5px, rgba(255,255,255,0.2) 5px, rgba(255,255,255,0.2) 6px);
}

.wagon .chassis {
  position: absolute;
  bottom: -5px;
  left: 10%;
  width: 80%;
  height: 8px;
  background: #212121;
}

/* Stone Pile */
.stone-pile {
  position: absolute;
  top: -18px;
  left: 5px;
  width: 110px;
  height: 25px;
  background: #9E9E9E;
  border-radius: 50% 50% 0 0;
  /* Complex gradient for 3D stones */
  background-image: 
    radial-gradient(circle at 20% 50%, #757575 5px, transparent 6px),
    radial-gradient(circle at 40% 30%, #616161 6px, transparent 7px),
    radial-gradient(circle at 60% 60%, #757575 5px, transparent 6px),
    radial-gradient(circle at 80% 40%, #616161 7px, transparent 8px),
    linear-gradient(to bottom, transparent, rgba(0,0,0,0.2));
  filter: drop-shadow(0 2px 3px rgba(0,0,0,0.4));
}

/* Wheels 3D */
.wheels {
  position: absolute;
  bottom: -14px;
  width: 100%;
  display: flex;
  justify-content: space-around;
  padding: 0 10px;
  z-index: 5;
}

.wheel {
  width: 20px;
  height: 20px;
  background: conic-gradient(from 0deg, #424242, #616161, #424242);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  position: relative;
  box-shadow: 1px 1px 3px rgba(0,0,0,0.5);
}

.wheel .rim {
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  border: 2px solid #BDBDBD; /* Shiny rim */
  border-radius: 50%;
}

.wheel .spokes {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 2px;
  background: #9E9E9E;
  transform: translate(-50%, -50%);
}

.wheel .spokes::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  background: #9E9E9E;
  transform: translate(-50%, -50%) rotate(90deg);
}

.locomotive .wheel.big {
  width: 26px;
  height: 26px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(-360deg); }
}

/* Foreground */
.foreground {
  bottom: 0;
  height: 100%;
  pointer-events: none;
}

.desert-shrub {
  position: absolute;
  bottom: 12%;
  width: 35px;
  height: 25px;
  background: radial-gradient(circle at 30% 30%, #A1887F 0%, #5D4037 100%);
  border-radius: 40% 40% 0 0;
  opacity: 0.9;
  box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
  animation: moveForeground 6s linear infinite;
}

.rock {
  position: absolute;
  bottom: 10%;
  width: 25px;
  height: 18px;
  background: linear-gradient(135deg, #8D6E63 0%, #5D4037 100%);
  border-radius: 5px 10px 2px 2px;
  box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
  animation: moveForeground 6s linear infinite;
}

@keyframes moveForeground {
  from { transform: translateX(-100vw); }
  to { transform: translateX(100vw); }
}

</style>
