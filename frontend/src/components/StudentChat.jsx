import { useState, useRef, useEffect } from 'react'
import './StudentChat.css'

const API_URL = 'http://localhost:8000'

function StudentChat() {
  const [studentProfile, setStudentProfile] = useState(null)
  const [showProfileSetup, setShowProfileSetup] = useState(true)
  const [profileForm, setProfileForm] = useState({
    student_id: '',
    name: '',
    grade: '',
    preferred_name: ''
  })
  
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [thinkingMessage, setThinkingMessage] = useState('')
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, thinkingMessage])

  const handleProfileSubmit = async (e) => {
    e.preventDefault()
    
    try {
      const response = await fetch(`${API_URL}/students`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_id: profileForm.student_id,
          name: profileForm.name,
          grade: profileForm.grade || null,
          preferred_name: profileForm.preferred_name || null,
          communication_style: 'casual'
        })
      })

      if (response.ok) {
        const profile = await response.json()
        setStudentProfile(profile)
        setShowProfileSetup(false)
        
        // Add welcome message
        setMessages([{
          role: 'assistant',
          content: `Hi ${profile.preferred_name || profile.name}! ${
            profile.total_conversations > 0 
              ? "It's good to see you again. How have you been?" 
              : "I'm Connor. I'm here to listen without judgment. How are you feeling right now?"
          }`,
          timestamp: new Date()
        }])
      }
    } catch (error) {
      console.error('Failed to create profile:', error)
      alert('Failed to create profile. Please try again.')
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()

    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }])

    setLoading(true)
    setThinkingMessage("Connor is connecting...")

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
          student_id: profileForm.student_id  // Include student ID
        })
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';
      let riskLevel = null;
      let isCrisis = false;

      // Create a placeholder message for the assistant
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true
      }]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'thinking') {
                setThinkingMessage(data.message);
              } else if (data.type === 'token') {
                setThinkingMessage('');
                assistantMessage += data.content;

                // Update the last message
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMsg = newMessages[newMessages.length - 1];
                  lastMsg.content = assistantMessage;
                  return newMessages;
                });
              } else if (data.type === 'done') {
                riskLevel = data.risk_level;
                isCrisis = data.is_crisis;
              } else if (data.type === 'error') {
                console.error("Stream error:", data.message);
              }
            } catch (e) {
              console.error("Error parsing stream:", e);
            }
          }
        }
      }

      // Finalize message
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        lastMsg.isStreaming = false;
        lastMsg.risk_level = riskLevel;
        lastMsg.is_crisis = isCrisis;
        return newMessages;
      });

    } catch (error) {
      console.error('Error sending message:', error)
      setThinkingMessage('');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm having trouble connecting right now. Please try again or reach out to a counselor directly.",
        timestamp: new Date(),
        error: true
      }])
    } finally {
      setLoading(false)
      setThinkingMessage('')
    }
  }

  if (showProfileSetup) {
    return (
      <div className="profile-setup">
        <div className="setup-container">
          <h1>Welcome to PsyFlo</h1>
          <p className="setup-intro">
            Let's get to know you a bit. This helps Connor provide better support.
          </p>
          
          <form onSubmit={handleProfileSubmit} className="profile-form">
            <div className="form-group">
              <label htmlFor="student_id">Student ID *</label>
              <input
                id="student_id"
                type="text"
                value={profileForm.student_id}
                onChange={(e) => setProfileForm({...profileForm, student_id: e.target.value})}
                placeholder="e.g., S12345"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <input
                id="name"
                type="text"
                value={profileForm.name}
                onChange={(e) => setProfileForm({...profileForm, name: e.target.value})}
                placeholder="e.g., Alex Johnson"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="preferred_name">Preferred Name (optional)</label>
              <input
                id="preferred_name"
                type="text"
                value={profileForm.preferred_name}
                onChange={(e) => setProfileForm({...profileForm, preferred_name: e.target.value})}
                placeholder="What should Connor call you?"
              />
            </div>

            <div className="form-group">
              <label htmlFor="grade">Grade (optional)</label>
              <select
                id="grade"
                value={profileForm.grade}
                onChange={(e) => setProfileForm({...profileForm, grade: e.target.value})}
              >
                <option value="">Select grade...</option>
                <option value="9">9th Grade</option>
                <option value="10">10th Grade</option>
                <option value="11">11th Grade</option>
                <option value="12">12th Grade</option>
              </select>
            </div>

            <button type="submit" className="submit-btn">
              Start Chatting
            </button>
          </form>

          <div className="privacy-notice">
            <p><strong>🔒 Your Privacy Matters</strong></p>
            <p>
              Conversations are confidential. We only notify school counselors 
              if a serious safety risk is detected.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="student-chat">
      <div className="chat-container">
        <div className="chat-header">
          <div className="student-info-bar">
            <span className="student-name">
              {studentProfile?.preferred_name || studentProfile?.name}
            </span>
            <button 
              className="change-profile-btn"
              onClick={() => setShowProfileSetup(true)}
            >
              Change Profile
            </button>
          </div>
        </div>

        <div className="messages">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`message ${msg.role} ${msg.is_crisis ? 'crisis' : ''} ${msg.error ? 'error' : ''}`}
            >
              <div className="message-content">
                {msg.content}
                {msg.isStreaming && <span className="cursor">|</span>}
              </div>
              <div className="message-time">
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}

          {loading && thinkingMessage && (
            <div className="thinking-indicator-wrapper">
              <div className="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p className="thinking-text">{thinkingMessage}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form className="input-form" onSubmit={sendMessage}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message here..."
            disabled={loading}
            autoFocus
          />
          <button type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>

      <div className="help-sidebar">
        <h3>Support Resources</h3>
        <p className="sidebar-intro">You are not alone. Help is available 24/7.</p>
        <div className="crisis-resources">
          <div className="resource">
            <span className="icon">📞</span>
            <div>
              <strong>988</strong>
              <p>Suicide & Crisis Lifeline</p>
            </div>
          </div>
          <div className="resource">
            <span className="icon">💬</span>
            <div>
              <strong>Text HOME to 741741</strong>
              <p>Crisis Text Line</p>
            </div>
          </div>
        </div>

        <div className="privacy-note">
          <p><strong>Your Privacy Matters</strong></p>
          <p>Conversations are private and anonymous. We only notify school counselors if a serious safety risk is detected.</p>
        </div>
      </div>
    </div>
  )
}

export default StudentChat
