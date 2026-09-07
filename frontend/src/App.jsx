import React, { useState } from 'react';
import './App.css';
import Dashboard from './Dashboard';

function App() {
  const [currentView, setCurrentView] = useState('landing');

  if (currentView === 'dashboard') {
    return <Dashboard onBackToHome={() => setCurrentView('landing')} />;
  }

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="logo">
          <span className="logo-accent">■</span> FinchQL
        </div>
        <div className="nav-links">
          <a href="#features">Architecture</a>
          <a href="#advantages">Advantages</a>
          <a href="https://github.com/farizest/enterprise-data-analyst-agent" target="_blank" rel="noreferrer">
            GitHub
          </a>
        </div>
      </nav>

      <header className="hero">
        <div className="badge">Production-Grade AI Data Analyst</div>
        <h1 className="hero-title">
          Talk to your database <br />
          <span className="highlight">with AI Agents.</span>
        </h1>
        <p className="hero-subtitle">
          FinchQL translates complex business questions into precise PostgreSQL queries. 
          Featuring memory, deterministic accuracy, and an enterprise interactive dashboard.
        </p>

        <div className="cta-wrapper">
          <button onClick={() => setCurrentView('dashboard')} className="btn-cta">
            Launch App
          </button>
        </div>
      </header>

      <section id="features" className="features-section">
        <h2 className="section-title">Built for Enterprise, faster than ever!</h2>
        <p className="section-subtitle">A robust agentic workflow ensuring zero hallucination on metrics.</p>
        
        <div className="features-grid">
          <div className="feature-card">
            <h3>Database Schema</h3>
            <p>Powered by a fully localized <strong>PostgreSQL</strong> instance of the complex <strong>AdventureWorks</strong> enterprise database, handling multi-table joins and realistic business constraints.</p>
          </div>
          <div className="feature-card">
            <h3>Agentic Architecture</h3>
            <p>Orchestrated via <strong>LangGraph</strong>. Features a Human-in-the-Loop (HITL) gate for ambiguous queries, memory state management, and strict SQL safety validation.</p>
          </div>
          <div className="feature-card">
            <h3>Modern Tech Stack</h3>
            <p>Built with <strong>Python</strong>, <strong>React/Vite</strong> for full-stack presentation, and powered by the <strong>Google Gemini API</strong>.</p>
          </div>
          <div className="feature-card">
            <h3>Deterministic Accuracy</h3>
            <p>Evaluated against a custom Golden Set using pure row-tuple execution matching. Numbers are calculated by the SQL engine, never guessed by the LLM.</p>
          </div>
        </div>
      </section>

      <section id="advantages" className="advantages-section">
        <h2 className="section-title">Project Advantages</h2>
        <p className="section-subtitle">Why this architecture stands out to engineering teams.</p>
        
        <div className="features-grid">
          <div className="feature-card highlight-card">
            <h3>Maximized Employability</h3>
            <p>Demonstrates industrial software engineering standards required for AI Data Engineering roles, moving beyond basic tutorials to a production-ready application [cite: Imagine you are a project mentor helping a beginner Fresh AI Data Science BTECH graduate to do this project and a get job as soon as possible using this project .So you have mentor me simple way.].</p>
          </div>
          <div className="feature-card highlight-card">
            <h3>Zero Data Hallucination</h3>
            <p>By enforcing a deterministic stats engine, the LLM only narrates the final numbers; it never calculates them, ensuring 100% mathematical accuracy [cite: Imagine you are a project mentor helping a beginner Fresh AI Data Science BTECH graduate to do this project and a get job as soon as possible using this project .So you have mentor me simple way.].</p>
          </div>
          <div className="feature-card highlight-card">
            <h3>Contextual Memory</h3>
            <p>Conversational memory allows the agent to process deep follow-up questions, preventing crashes when users ask to slice data dynamically [cite: Imagine you are a project mentor helping a beginner Fresh AI Data Science BTECH graduate to do this project and a get job as soon as possible using this project .So you have mentor me simple way.].</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default App;