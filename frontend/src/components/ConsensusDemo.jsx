import React, { useState, useEffect } from 'react';
import './ConsensusDemo.css';

const ConsensusDemo = () => {
  const [message, setMessage] = useState('');
  const [sessionId] = useState(() => {
    // Persistent session ID - stored in localStorage
    const stored = localStorage.getItem('beacon_demo_session');
    if (stored) return stored;
    const newId = 'demo-session-' + Date.now();
    localStorage.setItem('beacon_demo_session', newId);
    return newId;
  });
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [liveScores, setLiveScores] = useState({
    regex: null,
    semantic: null,
    mistral: null
  });
  const [consensusVerdict, setConsensusVerdict] = useState(null);
  const [result, setResult] = useState(() => {
    // Restore last result from localStorage
    const stored = localStorage.getItem('beacon_last_result');
    return stored ? JSON.parse(stored) : null;
  });
  const [history, setHistory] = useState(() => {
    // Restore history from localStorage
    const stored = localStorage.getItem('psyflo_history');
    return stored ? JSON.parse(stored) : [];
  });
  const [streamingResponse, setStreamingResponse] = useState('');

  // Save result to localStorage whenever it changes
  useEffect(() => {
    if (result) {
      localStorage.setItem('psyflo_last_result', JSON.stringify(result));
    }
  }, [result]);

  // Save history to localStorage whenever it changes
  useEffect(() => {
    if (history.length > 0) {
      localStorage.setItem('psyflo_history', JSON.stringify(history));
    }
  }, [history]);

  const exampleMessages = [
    { label: '🚨 Crisis', text: 'I want to kill myself', category: 'crisis' },
    { label: '🚨 Crisis with Plan', text: "I'm going to end my life tonight", category: 'crisis' },
    { label: '⚠️ Caution', text: 'I feel hopeless and worthless', category: 'caution' },
    { label: '⚠️ Depression', text: "I can't sleep and nothing matters anymore", category: 'caution' },
    { label: '✅ Hyperbole', text: 'This homework is killing me', category: 'safe' },
    { label: '✅ Stress', text: "I'm stressed about exams", category: 'safe' },
  ];

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    setLoading(true);
    setAnalyzing(true);
    setStreamingResponse('');
    setResult(null);
    setLiveScores({ regex: null, semantic: null, mistral: null });
    setConsensusVerdict(null);

    try {
      // Use streaming endpoint for real-time risk assessment
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          skip_response: true  // Skip response generation for demo (scoring only)
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullResponse = '';
      let conversationId = null;
      let riskLevel = null;
      let isCrisis = false;
      let finalScores = { regex: null, semantic: null, mistral: null };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'risk_analysis_start') {
              setAnalyzing(true);
            } else if (data.type === 'risk_score') {
              // Update live scores as they come in
              setLiveScores(prev => ({
                ...prev,
                [data.layer]: {
                  score: data.score,
                  latency_ms: data.latency_ms,
                  patterns: data.patterns || [],
                  timeout: data.timeout || false
                }
              }));
              finalScores[data.layer] = {
                score: data.score,
                latency_ms: data.latency_ms,
                patterns: data.patterns || [],
                timeout: data.timeout || false
              };
            } else if (data.type === 'consensus_verdict') {
              setConsensusVerdict({
                risk_level: data.risk_level,
                final_score: data.final_score,
                is_crisis: data.is_crisis,
                total_latency_ms: data.total_latency_ms
              });
              riskLevel = data.risk_level;
              isCrisis = data.is_crisis;
              setAnalyzing(false);
            } else if (data.type === 'crisis_alert') {
              // Show crisis alert banner
              console.log('CRISIS ALERT:', data.message);
            } else if (data.type === 'token') {
              fullResponse += data.content;
              setStreamingResponse(fullResponse);
            } else if (data.type === 'done') {
              conversationId = data.conversation_id;
              riskLevel = data.risk_level;
              isCrisis = data.is_crisis;
            } else if (data.type === 'error') {
              throw new Error(data.message);
            }
          }
        }
      }

      // Build final result - USE consensusVerdict.final_score directly
      const resultData = {
        message: text,
        response: fullResponse,
        riskLevel: riskLevel,
        isCrisis: isCrisis,
        conversationId: conversationId,
        details: {
          // CRITICAL: Use consensusVerdict.final_score directly, not from reasoning string
          risk_score: consensusVerdict?.final_score || 0,
          regex_score: finalScores.regex?.score || 0,
          semantic_score: finalScores.semantic?.score || 0,
          mistral_score: finalScores.mistral?.score,
          matched_patterns: [
            ...(finalScores.regex?.patterns || []),
            ...(finalScores.semantic?.patterns || []),
            ...(finalScores.mistral?.patterns || [])
          ],
          latency_ms: consensusVerdict?.total_latency_ms || 0,
          timeout_occurred: finalScores.mistral?.timeout || false,
          reasoning: `Risk Level: ${riskLevel}\nConsensus Score: ${(consensusVerdict?.final_score * 100).toFixed(1)}%\n\nLayer Scores:\n  Regex: ${(finalScores.regex?.score * 100).toFixed(1)}%\n  Semantic: ${(finalScores.semantic?.score * 100).toFixed(1)}%\n  Mistral: ${finalScores.mistral?.score ? (finalScores.mistral.score * 100).toFixed(1) + '%' : 'TIMEOUT'}`,
          created_at: new Date().toISOString()
        },
      };

      setResult(resultData);

      setHistory([...history, {
        message: text,
        riskLevel: riskLevel,
        isCrisis: isCrisis,
        timestamp: new Date().toLocaleTimeString(),
      }]);

      setMessage('');
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to send message. Make sure the backend is running on http://localhost:8000');
    } finally {
      setLoading(false);
      setAnalyzing(false);
      setStreamingResponse('');
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'CRISIS': return '#dc3545';
      case 'CAUTION': return '#ffc107';
      case 'SAFE': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getRiskIcon = (level) => {
    switch (level) {
      case 'CRISIS': return '🚨';
      case 'CAUTION': return '⚠️';
      case 'SAFE': return '✅';
      default: return '❓';
    }
  };

  return (
    <div className="consensus-demo">
      <div className="demo-header">
        <h1>🧠 PsyFlo Consensus Demo</h1>
        <p>Watch the 3-way consensus in action: Regex + Semantic + Mistral</p>
      </div>

      <div className="demo-container">
        {/* Left Panel - Input & Examples */}
        <div className="input-panel">
          <div className="message-input-section">
            <h3>Test Message</h3>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type a message to analyze..."
              rows="4"
              disabled={loading}
            />
            <button
              onClick={() => sendMessage(message)}
              disabled={loading || !message.trim()}
              className="send-button"
            >
              {loading ? 'Analyzing...' : 'Analyze Message'}
            </button>
          </div>

          <div className="examples-section">
            <h3>Quick Examples</h3>
            <div className="example-buttons">
              {exampleMessages.map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessage(example.text)}
                  disabled={loading}
                  className={`example-button ${example.category}`}
                >
                  {example.label}
                  <span className="example-text">{example.text}</span>
                </button>
              ))}
            </div>
          </div>

          {/* History */}
          {history.length > 0 && (
            <div className="history-section">
              <h3>Analysis History</h3>
              <div className="history-list">
                {history.map((item, idx) => (
                  <div key={idx} className="history-item">
                    <span className="history-icon">{getRiskIcon(item.riskLevel)}</span>
                    <span className="history-message">{item.message.substring(0, 40)}...</span>
                    <span className="history-time">{item.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Results */}
        <div className="results-panel">
          {!result && !loading && (
            <div className="empty-state">
              <h2>👈 Send a message to see the consensus in action</h2>
              <p>The system will analyze it using three strategies and show you how they vote.</p>
            </div>
          )}

          {loading && (
            <div className="loading-state">
              {analyzing ? (
                <>
                  <div className="live-analysis">
                    <h3>🔍 Real-Time Risk Assessment</h3>
                    <p className="analysis-subtitle">Detecting crisis markers as message is analyzed...</p>
                    
                    {/* Live Score Cards */}
                    <div className="live-scores">
                      {/* Regex Layer */}
                      <div className={`live-score-card ${liveScores.regex ? 'complete' : 'pending'}`}>
                        <div className="score-header">
                          <span className="score-icon">🔍</span>
                          <span className="score-name">Regex</span>
                        </div>
                        {liveScores.regex ? (
                          <>
                            <div className="score-value" style={{ 
                              color: liveScores.regex.score > 0.85 ? '#dc3545' : 
                                     liveScores.regex.score > 0.6 ? '#ffc107' : '#28a745' 
                            }}>
                              {(liveScores.regex.score * 100).toFixed(1)}%
                            </div>
                            <div className="score-latency">{liveScores.regex.latency_ms}ms</div>
                            {liveScores.regex.patterns.length > 0 && (
                              <div className="score-patterns">
                                {liveScores.regex.patterns.slice(0, 2).map((p, i) => (
                                  <span key={i} className="pattern-badge">{p}</span>
                                ))}
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="score-pending">
                            <div className="spinner"></div>
                            <span>Analyzing...</span>
                          </div>
                        )}
                      </div>

                      {/* Semantic Layer */}
                      <div className={`live-score-card ${liveScores.semantic ? 'complete' : 'pending'}`}>
                        <div className="score-header">
                          <span className="score-icon">🧬</span>
                          <span className="score-name">Semantic</span>
                        </div>
                        {liveScores.semantic ? (
                          <>
                            <div className="score-value" style={{ 
                              color: liveScores.semantic.score > 0.85 ? '#dc3545' : 
                                     liveScores.semantic.score > 0.6 ? '#ffc107' : '#28a745' 
                            }}>
                              {(liveScores.semantic.score * 100).toFixed(1)}%
                            </div>
                            <div className="score-latency">{liveScores.semantic.latency_ms}ms</div>
                          </>
                        ) : (
                          <div className="score-pending">
                            <div className="spinner"></div>
                            <span>Analyzing...</span>
                          </div>
                        )}
                      </div>

                      {/* Mistral Layer */}
                      <div className={`live-score-card ${liveScores.mistral ? 'complete' : 'pending'}`}>
                        <div className="score-header">
                          <span className="score-icon">🤖</span>
                          <span className="score-name">Mistral</span>
                        </div>
                        {liveScores.mistral ? (
                          liveScores.mistral.timeout ? (
                            <div className="score-timeout">
                              <span>⏱️ Timeout</span>
                              <div className="timeout-note">Graceful degradation</div>
                            </div>
                          ) : (
                            <>
                              <div className="score-value" style={{ 
                                color: liveScores.mistral.score > 0.85 ? '#dc3545' : 
                                       liveScores.mistral.score > 0.6 ? '#ffc107' : '#28a745' 
                              }}>
                                {(liveScores.mistral.score * 100).toFixed(1)}%
                              </div>
                              <div className="score-latency">{liveScores.mistral.latency_ms}ms</div>
                            </>
                          )
                        ) : (
                          <div className="score-pending">
                            <div className="spinner"></div>
                            <span>Analyzing...</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Consensus Verdict */}
                    {consensusVerdict && (
                      <div className="consensus-verdict-live" style={{ 
                        borderColor: consensusVerdict.risk_level === 'CRISIS' ? '#dc3545' : 
                                    consensusVerdict.risk_level === 'CAUTION' ? '#ffc107' : '#28a745' 
                      }}>
                        <div className="verdict-icon">
                          {consensusVerdict.risk_level === 'CRISIS' ? '🚨' : 
                           consensusVerdict.risk_level === 'CAUTION' ? '⚠️' : '✅'}
                        </div>
                        <div className="verdict-content">
                          <div className="verdict-level">{consensusVerdict.risk_level}</div>
                          <div className="verdict-score">
                            Consensus: {(consensusVerdict.final_score * 100).toFixed(1)}%
                          </div>
                          <div className="verdict-latency">
                            Total: {consensusVerdict.total_latency_ms}ms
                          </div>
                        </div>
                        {consensusVerdict.is_crisis && (
                          <div className="crisis-badge-live">
                            ⚠️ COUNSELOR NOTIFIED
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <div className="typing-indicator">
                    <div className="typing-text">{streamingResponse}</div>
                    <span className="cursor">|</span>
                  </div>
                </>
              )}
            </div>
          )}

          {result && (
            <div className="result-display">
              {/* Message Being Analyzed */}
              <div className="analyzed-message">
                <h3>Message Analyzed</h3>
                <div className="message-box">{result.message}</div>
              </div>

              {/* Final Verdict */}
              <div className="final-verdict" style={{ borderColor: getRiskColor(result.riskLevel) }}>
                <div className="verdict-header">
                  <span className="verdict-icon">{getRiskIcon(result.riskLevel)}</span>
                  <h2>Final Risk Level: {result.riskLevel}</h2>
                </div>
                <div className="verdict-score">
                  <div className="score-label">Consensus Score</div>
                  <div className="score-value" style={{ color: getRiskColor(result.riskLevel) }}>
                    {(result.details.risk_score * 100).toFixed(1)}%
                  </div>
                </div>
                {result.isCrisis && (
                  <div className="crisis-badge">⚠️ CRISIS PROTOCOL ACTIVATED</div>
                )}
              </div>

              {/* Component Scores */}
              <div className="component-scores">
                <h3>Component Analysis</h3>
                
                {/* Regex Strategy */}
                <div className="component-card regex">
                  <div className="component-header">
                    <span className="component-icon">🔍</span>
                    <h4>Regex Detection</h4>
                    <span className="component-weight">Weight: 40%</span>
                  </div>
                  <div className="component-score">
                    <div className="score-bar">
                      <div 
                        className="score-fill regex-fill" 
                        style={{ width: `${result.details.regex_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="score-text">{(result.details.regex_score * 100).toFixed(1)}%</span>
                  </div>
                  {result.details.matched_patterns && result.details.matched_patterns.length > 0 && (
                    <div className="matched-patterns">
                      <strong>Matched Patterns:</strong>
                      <div className="pattern-tags">
                        {result.details.matched_patterns.map((pattern, idx) => (
                          <span key={idx} className="pattern-tag">{pattern}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Semantic Strategy */}
                <div className="component-card semantic">
                  <div className="component-header">
                    <span className="component-icon">🧬</span>
                    <h4>Semantic Analysis</h4>
                    <span className="component-weight">Weight: 20%</span>
                  </div>
                  <div className="component-score">
                    <div className="score-bar">
                      <div 
                        className="score-fill semantic-fill" 
                        style={{ width: `${result.details.semantic_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="score-text">{(result.details.semantic_score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="component-description">
                    Embedding similarity to known crisis patterns
                  </div>
                </div>

                {/* Mistral Strategy */}
                <div className="component-card mistral">
                  <div className="component-header">
                    <span className="component-icon">🤖</span>
                    <h4>Mistral Reasoner</h4>
                    <span className="component-weight">Weight: 30%</span>
                  </div>
                  <div className="component-score">
                    <div className="score-bar">
                      <div 
                        className="score-fill mistral-fill" 
                        style={{ width: `${(result.details.mistral_score || 0) * 100}%` }}
                      ></div>
                    </div>
                    <span className="score-text">
                      {result.details.mistral_score 
                        ? `${(result.details.mistral_score * 100).toFixed(1)}%`
                        : 'Timeout'}
                    </span>
                  </div>
                  {result.details.timeout_occurred && (
                    <div className="timeout-notice">
                      ⏱️ Analysis timed out (graceful degradation)
                    </div>
                  )}
                </div>
              </div>

              {/* Reasoning Trace */}
              <div className="reasoning-section">
                <h3>Reasoning Trace</h3>
                <div className="reasoning-box">
                  {result.details.reasoning}
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="metrics-section">
                <h3>Performance Metrics</h3>
                <div className="metrics-grid">
                  <div className="metric-item">
                    <span className="metric-label">Total Latency</span>
                    <span className="metric-value">{result.details.latency_ms}ms</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Conversation ID</span>
                    <span className="metric-value">#{result.conversationId}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Timestamp</span>
                    <span className="metric-value">{new Date(result.details.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>

              {/* System Response */}
              <div className="response-section">
                <h3>System Response to Student</h3>
                <div className="response-box">
                  {result.response}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConsensusDemo;
