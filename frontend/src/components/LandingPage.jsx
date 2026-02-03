import React, { useEffect } from 'react';
import './LandingPage.css';

const LandingPage = ({ onNavigate }) => {

  useEffect(() => {
    // Reveal animations on scroll could be added here
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="landing-container">
      {/* Hero Section */}
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">Speak Freely. Heal Safely.</h1>
          <p className="hero-subtitle">
            Experience the next generation of mental health support. 24/7 access to Connor, your AI companion, backed by clinical safety protocols.
          </p>
          <div className="cta-group">
            <button className="cta-button primary" onClick={() => onNavigate('demo')}>
              Start Chatting
            </button>
            <button className="cta-button secondary" onClick={() => document.querySelector('.features-section').scrollIntoView({ behavior: 'smooth' })}>
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* Value Props */}
      <section className="value-props-section">
        <h2 className="section-title">Why Choose PsyFlo?</h2>
        <div className="props-grid">
          <div className="prop-card">
            <div className="prop-icon">💬</div>
            <h3 className="prop-title">Always Available</h3>
            <p className="prop-desc">
              <strong>24/7 Support:</strong> Life doesn't stop at 5 PM. Connor is ready to listen whenever you need to talk—3 AM anxiety or Sunday scaries included.
            </p>
          </div>
          <div className="prop-card">
            <div className="prop-icon">🧠</div>
            <h3 className="prop-title">Clinically Grounded</h3>
            <p className="prop-desc">
              <strong>Safety First:</strong> Built on established clinical frameworks (CBT, DBT principles). We prioritize your well-being with real-time risk monitoring.
            </p>
          </div>
          <div className="prop-card">
            <div className="prop-icon">🔒</div>
            <h3 className="prop-title">Private by Design</h3>
            <p className="prop-desc">
              <strong>Zero-Trust Privacy:</strong> Your data is anonymized before it even touches our servers. We adhere to strict FERPA & COPPA guidelines to keep your secrets yours.
            </p>
          </div>
          <div className="prop-card">
            <div className="prop-icon">⚡</div>
            <h3 className="prop-title">Empathic AI</h3>
            <p className="prop-desc">
              <strong>Human-Like Connection:</strong> Connor uses advanced "Empathic Latency" to process and reflect on your feelings, providing responses that feel genuine, not robotic.
            </p>
          </div>
        </div>
      </section>

      {/* The MOAT / Features */}
      <section className="features-section">
        <h2 className="section-title">The PsyFlo Advantage</h2>

        <div className="feature-row">
          <div className="feature-text">
            <h3>Parallel Consensus Model</h3>
            <p>
              Unlike standard chatbots, PsyFlo separates conversation from safety. A dedicated "Safety Service" and "Clinical Reasoner" analyze every message in real-time, independent of the LLM.
            </p>
            <p><strong>Result:</strong> Zero-latency crisis detection, even if the LLM hallucinates. (See HLD Sec 4.1)</p>
          </div>
          <div className="feature-visual">
            {/* Abstract visual of parallel lines merging */}
            <div style={{ color: '#5E5CE6', fontSize: '2rem' }}>Safety || LLM || Observer</div>
          </div>
        </div>

        <div className="feature-row reverse">
          <div className="feature-text">
            <h3>Privacy by Design</h3>
            <p>
              Student data is processed at the edge and anonymized before analysis. We use a Zero-Trust architecture where PII is never exposed to the AI model.
            </p>
            <p><strong>Retention:</strong> Aggressive lifecycle policies (Glacier/Purge) ensure data is only kept as long as clinically necessary.</p>
          </div>
          <div className="feature-visual">
            <div style={{ color: '#32D74B', fontSize: '2rem' }}>🔒 AES-256 Encrypted</div>
          </div>
        </div>
      </section>

      {/* How It Works / Architecture */}
      <section className="how-it-works-section">
        <h2 className="section-title">System Architecture</h2>
        <div className="architecture-diagram">
          <div className="arch-block">Student Input</div>
          <div className="arch-arrow">⬇️</div>
          <div className="arch-block" style={{ border: '1px solid #5E5CE6' }}>Orchestrator</div>
          <div className="arch-arrow">➡️</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div className="arch-block">Safety Service</div>
            <div className="arch-block">Mistral Reasoner</div>
            <div className="arch-block">LLM Agent</div>
          </div>
          <div className="arch-arrow">⬅️</div>
          <div className="arch-block" style={{ border: '1px solid #FFD60A' }}>Consensus Score</div>
        </div>
      </section>

      {/* Compliance */}
      <section className="compliance-section">
        <h2>Enterprise Grade Compliance</h2>
        <div className="compliance-badges">
          <div className="badge">FERPA Compliant</div>
          <div className="badge">COPPA Compliant</div>
          <div className="badge">HIPAA Ready</div>
          <div className="badge">SOC 2 (Target)</div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="footer-links">
          <a href="#">High Level Design</a>
          <a href="#">Low Level Design</a>
          <a href="#">Contact Sales</a>
        </div>
        <p style={{ marginTop: '20px' }}>&copy; 2026 PsyFlo Inc. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
