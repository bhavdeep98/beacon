# Student Chat Interface - Summary

## Overview
The Student Chat is a React-based conversational interface where students interact with Connor, an AI mental health support agent. It features real-time streaming responses, profile management, and integrated crisis resources.

## Key Features

### 1. Profile Setup
- **First-time onboarding**: Students create profiles with ID, name, grade, and preferred name
- **Returning users**: System recognizes previous conversations and personalizes greeting
- **Privacy notice**: Clear communication about confidentiality and when counselors are notified

### 2. Real-Time Streaming Chat
- **SSE (Server-Sent Events)**: Responses stream word-by-word for natural typing effect
- **Thinking indicators**: Shows "Connor is connecting..." and animated dots during processing
- **Risk assessment**: Receives real-time risk scores from consensus layers (regex, semantic, Mistral)
- **Crisis detection**: Immediate visual feedback if crisis is detected

### 3. Message Flow
```
Student types message
    ↓
POST /chat/stream
    ↓
Backend runs consensus analysis (<50ms for fast path)
    ↓
Stream thinking status → risk scores → consensus verdict
    ↓
If crisis: Show alert immediately
    ↓
Generate response (up to 2 minutes with Mistral)
    ↓
Stream response word-by-word
    ↓
Save to database + index in RAG
```

### 4. Crisis Resources Sidebar
Always visible panel with:
- **988 Suicide & Crisis Lifeline** (phone)
- **Crisis Text Line** (text HOME to 741741)
- Privacy reminder about when counselors are notified

### 5. Visual Design
- **Clean, minimal interface**: Reduces cognitive load
- **Message bubbles**: Student (right) vs Connor (left)
- **Crisis highlighting**: Red border on crisis-level messages
- **Timestamps**: Shows when each message was sent
- **Streaming cursor**: Blinking cursor during response generation

## Technical Implementation

### State Management
- `studentProfile`: Current student data
- `messages`: Array of conversation messages
- `loading`: Controls send button and input
- `thinkingMessage`: Dynamic status updates during processing
- `sessionId`: Unique identifier for conversation continuity

### API Integration
- **POST /students**: Create/update student profile
- **POST /chat/stream**: Stream chat responses with real-time risk assessment
- Handles SSE parsing for multi-stage updates (thinking, risk_score, token, done)

### User Experience
- **Auto-scroll**: Messages automatically scroll to bottom
- **Disabled states**: Input disabled during processing
- **Error handling**: Graceful fallback messages if connection fails
- **Profile switching**: Can change profile mid-session

## Safety Features
- **Zero PII in logs**: Student IDs hashed before transmission
- **Crisis override**: If crisis detected, resources shown immediately
- **Always-available help**: Crisis resources visible at all times
- **Transparent notifications**: Students know when counselors are alerted

## Performance
- **Fast initial response**: Consensus scoring <50ms for routine messages
- **Progressive disclosure**: Risk assessment completes before response generation
- **Smooth streaming**: 40-60ms delay between words for natural feel
- **Responsive UI**: No blocking operations, async throughout
