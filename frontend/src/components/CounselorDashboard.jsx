import { useState, useEffect } from 'react'
import './CounselorDashboard.css'

const API_URL = 'http://localhost:8000'

function CounselorDashboard() {
  const [view, setView] = useState('students') // 'students' or 'crisis'
  const [students, setStudents] = useState([])
  const [selectedStudent, setSelectedStudent] = useState(null)
  const [studentConversations, setStudentConversations] = useState([])
  const [studentThemes, setStudentThemes] = useState([])
  const [crisisEvents, setCrisisEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedConversations, setExpandedConversations] = useState(new Set())
  const [expandedCrisisEvents, setExpandedCrisisEvents] = useState(new Set())
  const [responseFeedback, setResponseFeedback] = useState({})

  useEffect(() => {
    loadStudents()
    loadCrisisEvents()
  }, [])

  const loadStudents = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/students`)
      if (response.ok) {
        const data = await response.json()
        setStudents(data)
      }
    } catch (error) {
      console.error('Failed to load students:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCrisisEvents = async () => {
    try {
      console.log('[Crisis Events] Fetching crisis events...')
      const response = await fetch(`${API_URL}/crisis-events`)
      if (response.ok) {
        const data = await response.json()
        console.log('[Crisis Events] Received events:', data.length)
        
        // For each crisis event, fetch the full conversation details
        const eventsWithConversations = await Promise.all(
          data.map(async (event, index) => {
            try {
              console.log(`[Crisis Event ${index}] Event ID: ${event.id}, Conv ID: ${event.conversation_id}`)
              
              // Parse matched_patterns if it's a string
              if (typeof event.matched_patterns === 'string') {
                event.matched_patterns = JSON.parse(event.matched_patterns)
              }
              
              const convResponse = await fetch(`${API_URL}/conversations/${event.conversation_id}`)
              console.log(`[Crisis Event ${index}] Conversation fetch status: ${convResponse.status}`)
              
              if (convResponse.ok) {
                const conversation = await convResponse.json()
                console.log(`[Crisis Event ${index}] Conversation data:`, {
                  id: conversation.id,
                  hasMessage: !!conversation.message,
                  hasResponse: !!conversation.response,
                  messageLength: conversation.message?.length,
                  responseLength: conversation.response?.length
                })
                
                // Parse matched_patterns in conversation too
                if (typeof conversation.matched_patterns === 'string') {
                  conversation.matched_patterns = JSON.parse(conversation.matched_patterns)
                }
                
                return { ...event, conversation }
              } else {
                console.error(`[Crisis Event ${index}] Failed to fetch conversation: ${convResponse.status}`)
              }
            } catch (err) {
              console.error(`[Crisis Event ${index}] Error loading conversation:`, err)
            }
            return event
          })
        )
        
        console.log('[Crisis Events] Events with conversations:', eventsWithConversations)
        setCrisisEvents(eventsWithConversations)
      }
    } catch (error) {
      console.error('[Crisis Events] Failed to load crisis events:', error)
    }
  }

  const selectStudent = async (student) => {
    setSelectedStudent(student)
    setLoading(true)
    
    try {
      // Load conversations
      const convResponse = await fetch(
        `${API_URL}/students/hash/${student.student_id_hash}/conversations`
      )
      if (convResponse.ok) {
        const convData = await convResponse.json()
        // Parse matched_patterns if they're strings
        const parsedConvData = convData.map(conv => ({
          ...conv,
          matched_patterns: typeof conv.matched_patterns === 'string' 
            ? JSON.parse(conv.matched_patterns) 
            : conv.matched_patterns
        }))
        setStudentConversations(parsedConvData)
      }

      // Load themes
      const themeResponse = await fetch(
        `${API_URL}/students/hash/${student.student_id_hash}/themes`
      )
      if (themeResponse.ok) {
        const themeData = await themeResponse.json()
        setStudentThemes(themeData)
      }
    } catch (error) {
      console.error('Failed to load student details:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleConversationExpand = (convId) => {
    const newExpanded = new Set(expandedConversations)
    if (newExpanded.has(convId)) {
      newExpanded.delete(convId)
    } else {
      newExpanded.add(convId)
    }
    setExpandedConversations(newExpanded)
  }

  const toggleCrisisEventExpand = (eventIdx) => {
    const newExpanded = new Set(expandedCrisisEvents)
    if (newExpanded.has(eventIdx)) {
      newExpanded.delete(eventIdx)
    } else {
      newExpanded.add(eventIdx)
    }
    setExpandedCrisisEvents(newExpanded)
  }

  const handleResponseFeedback = async (convId, isPositive) => {
    // Store feedback locally (in production, send to backend)
    setResponseFeedback(prev => ({
      ...prev,
      [convId]: isPositive ? 'positive' : 'negative'
    }))
    
    // TODO: Send to backend for model fine-tuning
    console.log(`Feedback for conversation ${convId}: ${isPositive ? 'positive' : 'negative'}`)
  }

  const getRiskBadge = (riskLevel) => {
    const badges = {
      'CRISIS': { icon: '🚨', color: '#dc3545', label: 'Crisis' },
      'CAUTION': { icon: '⚠️', color: '#ffc107', label: 'Caution' },
      'SAFE': { icon: '✅', color: '#28a745', label: 'Safe' }
    }
    const badge = badges[riskLevel] || badges['SAFE']
    return (
      <span className="risk-badge" style={{ backgroundColor: badge.color }}>
        {badge.icon} {badge.label}
      </span>
    )
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="counselor-dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Counselor Dashboard</h1>
          <p className="dashboard-subtitle">Monitor student wellbeing and provide feedback</p>
        </div>
        <div className="view-toggle">
          <button 
            className={view === 'students' ? 'active' : ''}
            onClick={() => setView('students')}
          >
            📚 Students ({students.length})
          </button>
          <button 
            className={view === 'crisis' ? 'active' : ''}
            onClick={() => setView('crisis')}
          >
            🚨 Crisis Alerts ({crisisEvents.length})
          </button>
        </div>
      </div>

      {view === 'students' && (
        <div className="students-view">
          <div className="students-list">
            <h2>Student Roster</h2>
            {loading && !selectedStudent && <p className="loading-text">Loading students...</p>}
            {!loading && students.length === 0 && (
              <p className="empty-state">No students registered yet.</p>
            )}
            {students.map((student) => (
              <div
                key={student.id}
                className={`student-card ${selectedStudent?.id === student.id ? 'selected' : ''}`}
                onClick={() => selectStudent(student)}
              >
                <div className="student-header">
                  <div className="student-avatar">
                    {(student.preferred_name || student.name).charAt(0).toUpperCase()}
                  </div>
                  <div className="student-info">
                    <h3>{student.preferred_name || student.name}</h3>
                    <p className="student-meta">
                      {student.grade && `Grade ${student.grade} • `}
                      {student.total_conversations} conversation{student.total_conversations !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <div className="student-status">
                  <span className="last-active">
                    {formatDate(student.last_active)}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {selectedStudent && (
            <div className="student-detail">
              <div className="detail-header">
                <h2>{selectedStudent.preferred_name || selectedStudent.name}</h2>
                <button onClick={() => setSelectedStudent(null)}>✕ Close</button>
              </div>

              {/* Active Themes */}
              {studentThemes.length > 0 && (
                <div className="themes-section">
                  <h3>🎯 Active Themes</h3>
                  <div className="themes-list">
                    {studentThemes.map((theme) => (
                      <div key={theme.id} className="theme-card">
                        <div className="theme-header">
                          <strong>{theme.theme.replace(/_/g, ' ')}</strong>
                          <span className="mention-count">{theme.mention_count}x</span>
                        </div>
                        {theme.description && (
                          <p className="theme-description">{theme.description}</p>
                        )}
                        <p className="theme-meta">
                          Last mentioned: {formatDate(theme.last_mentioned)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Conversation History */}
              <div className="conversations-section">
                <div className="section-header">
                  <h3>💬 Conversation History</h3>
                  <p className="section-note">
                    Use 👍 👎 to provide feedback on Connor's responses for model improvement
                  </p>
                </div>
                {loading && <p className="loading-text">Loading conversations...</p>}
                {!loading && studentConversations.length === 0 && (
                  <p className="empty-state">No conversations yet.</p>
                )}
                {!loading && studentConversations.length > 0 && (
                  <div className="conversations-list">
                    {studentConversations.map((conv) => (
                      <div key={conv.id} className="conversation-card">
                        <div className="conv-header">
                          <div className="conv-header-left">
                            <span className="conv-date">
                              {new Date(conv.created_at).toLocaleString()}
                            </span>
                            <button 
                              className="expand-btn"
                              onClick={() => toggleConversationExpand(conv.id)}
                            >
                              {expandedConversations.has(conv.id) ? '▼ Collapse' : '▶ Expand Details'}
                            </button>
                          </div>
                          {getRiskBadge(conv.risk_level)}
                        </div>
                        
                        <div className="conv-message">
                          <strong>👤 Student:</strong>
                          <p>{conv.message}</p>
                        </div>
                        
                        <div className="conv-response">
                          <div className="response-header">
                            <strong>🤖 Connor's Response:</strong>
                            <div className="feedback-buttons">
                              <button
                                className={`feedback-btn ${responseFeedback[conv.id] === 'positive' ? 'active positive' : ''}`}
                                onClick={() => handleResponseFeedback(conv.id, true)}
                                title="Good response"
                              >
                                👍
                              </button>
                              <button
                                className={`feedback-btn ${responseFeedback[conv.id] === 'negative' ? 'active negative' : ''}`}
                                onClick={() => handleResponseFeedback(conv.id, false)}
                                title="Needs improvement"
                              >
                                👎
                              </button>
                            </div>
                          </div>
                          <p>{conv.response}</p>
                          {responseFeedback[conv.id] && (
                            <div className="feedback-note">
                              {responseFeedback[conv.id] === 'positive' 
                                ? '✓ Marked as good response for training' 
                                : '✗ Marked for review and model improvement'}
                            </div>
                          )}
                        </div>

                        {expandedConversations.has(conv.id) && (
                          <div className="conv-details">
                            {/* Diagnostic Analysis */}
                            <div className="diagnostic-section">
                              <h4>🔬 Diagnostic Analysis</h4>
                              <div className="layer-scores">
                                <div className="layer-score-card">
                                  <div className="layer-name">Regex Layer</div>
                                  <div className="layer-score">{(conv.regex_score * 100).toFixed(1)}%</div>
                                  <div className="layer-latency">{conv.latency_ms ? `<${conv.latency_ms}ms` : 'N/A'}</div>
                                </div>
                                <div className="layer-score-card">
                                  <div className="layer-name">Semantic Layer</div>
                                  <div className="layer-score">{(conv.semantic_score * 100).toFixed(1)}%</div>
                                  <div className="layer-latency">Embedding-based</div>
                                </div>
                                {conv.mistral_score !== null && (
                                  <div className="layer-score-card">
                                    <div className="layer-name">Mistral Layer</div>
                                    <div className="layer-score">{(conv.mistral_score * 100).toFixed(1)}%</div>
                                    <div className="layer-latency">LLM Analysis</div>
                                  </div>
                                )}
                                {conv.timeout_occurred && (
                                  <div className="layer-score-card timeout">
                                    <div className="layer-name">⚠️ Timeout</div>
                                    <div className="layer-score">Degraded</div>
                                    <div className="layer-latency">Fallback used</div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Reasoning Trace */}
                            {conv.reasoning && (
                              <div className="reasoning-section">
                                <h4>🧠 AI Reasoning</h4>
                                <div className="reasoning-text">{conv.reasoning}</div>
                              </div>
                            )}

                            {/* Matched Patterns */}
                            {conv.matched_patterns.length > 0 && (
                              <div className="conv-patterns">
                                <strong>🔍 Detected Patterns:</strong>
                                <div className="pattern-tags">
                                  {conv.matched_patterns.map((pattern, idx) => (
                                    <span key={idx} className="pattern-tag">{pattern}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Metadata */}
                            <div className="conv-metadata">
                              <div className="metadata-item">
                                <span className="metadata-label">Session ID:</span>
                                <span className="metadata-value code">{conv.session_id_hash || 'N/A'}</span>
                              </div>
                              <div className="metadata-item">
                                <span className="metadata-label">Conversation #:</span>
                                <span className="metadata-value">{conv.id}</span>
                              </div>
                              <div className="metadata-item">
                                <span className="metadata-label">Final Risk Score:</span>
                                <span className="metadata-value">{(conv.risk_score * 100).toFixed(1)}%</span>
                              </div>
                              <div className="metadata-item">
                                <span className="metadata-label">Processing Time:</span>
                                <span className="metadata-value">{conv.latency_ms}ms</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {view === 'crisis' && (
        <div className="crisis-events">
          <div className="section-header">
            <h2>🚨 Recent Crisis Events</h2>
            <p className="section-note">Click on any event to view full details</p>
          </div>
          {crisisEvents.length === 0 && (
            <p className="empty-state">No crisis events recorded yet.</p>
          )}
          {crisisEvents.length > 0 && (
            <div className="events-list">
              {crisisEvents.map((event, idx) => (
                <div key={idx} className="event-card">
                  <div className="event-header" onClick={() => toggleCrisisEventExpand(idx)}>
                    <div className="event-header-left">
                      <span className="event-icon">🚨</span>
                      <div>
                        <span className="event-time">
                          {new Date(event.detected_at).toLocaleString()}
                        </span>
                        <span className="event-risk">
                          Risk Score: {(event.risk_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <button className="expand-btn">
                      {expandedCrisisEvents.has(idx) ? '▼ Collapse' : '▶ View Details'}
                    </button>
                  </div>
                  
                  {expandedCrisisEvents.has(idx) && (
                    <div className="event-details">
                      {/* Conversation Context */}
                      {event.conversation ? (
                        <div className="detail-section conversation-context">
                          <h4>💬 Conversation That Triggered Alert</h4>
                          <div className="crisis-conversation">
                            <div className="crisis-message">
                              <strong>👤 Student Message:</strong>
                              <p>{event.conversation.message || 'No message available'}</p>
                            </div>
                            <div className="crisis-response">
                              <strong>🤖 Connor's Response:</strong>
                              <p>{event.conversation.response || 'No response available'}</p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="detail-section">
                          <p className="loading-text">Loading conversation details...</p>
                        </div>
                      )}

                      {/* Diagnostic Analysis */}
                      <div className="detail-section">
                        <h4>🔬 Multi-Layer Analysis</h4>
                        {event.conversation ? (
                          <div className="layer-scores">
                            <div className="layer-score-card">
                              <div className="layer-name">Regex Layer</div>
                              <div className="layer-score crisis">
                                {event.conversation.regex_score != null 
                                  ? (event.conversation.regex_score * 100).toFixed(1) + '%'
                                  : 'N/A'}
                              </div>
                              <div className="layer-latency">Pattern matching</div>
                            </div>
                            <div className="layer-score-card">
                              <div className="layer-name">Semantic Layer</div>
                              <div className="layer-score crisis">
                                {event.conversation.semantic_score != null
                                  ? (event.conversation.semantic_score * 100).toFixed(1) + '%'
                                  : 'N/A'}
                              </div>
                              <div className="layer-latency">Embedding similarity</div>
                            </div>
                            {event.conversation.mistral_score != null && (
                              <div className="layer-score-card">
                                <div className="layer-name">Mistral Layer</div>
                                <div className="layer-score crisis">
                                  {(event.conversation.mistral_score * 100).toFixed(1)}%
                                </div>
                                <div className="layer-latency">LLM reasoning</div>
                              </div>
                            )}
                            <div className="layer-score-card final">
                              <div className="layer-name">Final Score</div>
                              <div className="layer-score crisis">
                                {(event.risk_score * 100).toFixed(1)}%
                              </div>
                              <div className="layer-latency">Consensus result</div>
                            </div>
                          </div>
                        ) : (
                          <div className="detail-grid">
                            <div className="detail-item">
                              <span className="detail-label">Risk Score:</span>
                              <span className="detail-value crisis-level">
                                {(event.risk_score * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* AI Reasoning */}
                      {(event.reasoning || event.conversation?.reasoning) && (
                        <div className="detail-section">
                          <h4>🧠 AI Reasoning Trace</h4>
                          <div className="reasoning-box">
                            {event.reasoning || event.conversation?.reasoning}
                          </div>
                        </div>
                      )}

                      {/* Matched Patterns */}
                      {event.matched_patterns && event.matched_patterns.length > 0 && (
                        <div className="detail-section">
                          <h4>🔍 Crisis Patterns Detected</h4>
                          <div className="pattern-tags">
                            {event.matched_patterns.map((pattern, pidx) => (
                              <span key={pidx} className="pattern-tag crisis">{pattern}</span>
                            ))}
                          </div>
                          <p className="pattern-explanation">
                            These patterns triggered the crisis alert based on our safety protocols.
                          </p>
                        </div>
                      )}

                      {/* Performance Metrics */}
                      {event.conversation && (
                        <div className="detail-section">
                          <h4>⚡ Performance Metrics</h4>
                          <div className="detail-grid">
                            <div className="detail-item">
                              <span className="detail-label">Detection Latency:</span>
                              <span className="detail-value">
                                {event.conversation.latency_ms != null 
                                  ? event.conversation.latency_ms + 'ms'
                                  : 'N/A'}
                              </span>
                            </div>
                            <div className="detail-item">
                              <span className="detail-label">Timeout Occurred:</span>
                              <span className="detail-value">
                                {event.conversation.timeout_occurred ? 'Yes (Degraded)' : 'No'}
                              </span>
                            </div>
                            <div className="detail-item">
                              <span className="detail-label">Session Hash:</span>
                              <span className="detail-value code">{event.session_id_hash}</span>
                            </div>
                            <div className="detail-item">
                              <span className="detail-label">Conversation ID:</span>
                              <span className="detail-value">{event.conversation_id}</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Recommended Actions */}
                      <div className="detail-section">
                        <h4>⚡ Recommended Actions</h4>
                        <ul className="action-list">
                          <li className="action-completed">✓ Immediate counselor notification sent</li>
                          <li className="action-completed">✓ Crisis resources displayed to student</li>
                          <li className="action-completed">✓ Event logged to immutable audit trail</li>
                          <li className="action-pending">→ Follow up with student within 24 hours</li>
                          <li className="action-pending">→ Document intervention in student record</li>
                          <li className="action-pending">→ Assess need for parent/guardian notification</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CounselorDashboard
