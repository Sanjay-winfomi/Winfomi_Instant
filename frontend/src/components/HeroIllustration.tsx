import "./HeroIllustration.css";

export default function HeroIllustration() {
  return (
    <div className="hero-illustration" aria-hidden="true">
      <div className="hero-pedestal" />
      <div className="hero-panel hero-panel--back" />
      <div className="hero-panel hero-panel--mid" />
      <div className="hero-panel hero-panel--front" />
      <span className="hero-sparkle hero-sparkle--1">✦</span>
      <span className="hero-sparkle hero-sparkle--2">✦</span>
      <span className="hero-sparkle hero-sparkle--3">✦</span>
      <div className="hero-glow" />
    </div>
  );
}
