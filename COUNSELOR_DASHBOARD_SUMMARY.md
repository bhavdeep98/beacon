# Counselor Dashboard - Summary

## Overview
The Counselor Dashboard is a React-based monitoring interface for school counselors to track student wellbeing, review conversations, and respond to crisis alerts. It provides full transparency into AI decision-making with explainable risk assessments.

## Key Features

### 1. Dual View System
- **Students View**: Roster of all students with conversation history
- **Crisis Alerts View**: Real-time feed of crisis events requiring immediate attention

### 2. Student Roster
- **Student cards**: Show name, grade, conversation count, last active time
- **Quick selection**: Click to view detailed student profile
- **Activity tracking**: Visual indicators for recent activity
- **Avatar initials**: Color-coded student identifiers

### 3. Student Detail Panel

#### Active Themes
- **Ongoing topics**: Tracks recurring themes (academic_stress, family_issues, etc.)
- **Mention count**: Shows frequency of each theme
- **Last mentioned**: Timestamp of most recent discussion
- **Description**: Context about the theme

#### Conversation History
- **Full transcript**: Student message + Connor's response
- **Risk badges**: Visual indicators (🚨 Crisis, ⚠️ Caution, ✅ Safe)
- **Timestamps**: When each conversation occurred
- **Expandable details**: Click to see full diagnostic analysis

#### Response Feedback System
- **👍 👎 buttons**: Counselors rate Connor's responses
- **Training data**: Feedback used for model improvement
- **Visual confirmation**: Shows when feedback is recorded

### 4. Diagnostic Analysis (Expanded View)

#### Multi-Layer Scores
Shows individual layer contributions:
- **Regex Layer**: Pattern matching score + latency
- **Semantic Layer**: Embedding similarity score
- **Mistral Layer**: Clinical reasoning score (if available)
- **Timeout indicator**: Shows if Mistral layer timed out

#### AI Reasoning Trace
- **Step-by-step explanation**: How AI reached its conclusion
- **Clinical markers**: PHQ-9, GAD-7, C-SSRS indicators detected
- **Evidence quotes**: Specific phrases that triggered detection

#### Matched Patterns
- **Crisis categories**: Tags showing detected patterns (suicidal_ideation, self_harm, etc.)
- **Multi-layer detection**: Shows which layers detected which patterns

#### Performance Metrics
- **Processing time**: Total latency in milliseconds
- **Session hash**: Anonymized session identifier
- **Conversation ID**: Database reference
- **Final risk score**: Consensus score as percentage

### 5. Crisis Events View

#### Real-Time Alert Feed
- **Chronological list**: Most recent crises first
- **Risk score**: Consensus score that triggered alert
- **Timestamp**: When crisis was detected
- **Expandable cards**: Click to see full details

#### Crisis Event Details
- **Conversation context**: Full student message + Connor's response
- **Multi-layer analysis**: All three layer scores with visual cards
- **AI reasoning**: Complete reasoning trace
- **Detected patterns**: All crisis markers identified
- **Performance metrics**: Latency, timeout status, session info

#### Recommended Actions Checklist
- ✓ **Completed**: Automatic actions (notification sent, resources shown, audit logged)
- → **Pending**: Manual follow-up tasks (24hr check-in, parent notification, documentation)

## Technical Implementation

### State Management
- `view`: Toggle between 'students' and 'crisis' views
- `students`: Array of all student profiles
- `selectedStudent`: Currently viewed student detail
- `studentConversations`: Conversation history for selected student
- `studentThemes`: Active themes for selected student
- `crisisEvents`: Array of crisis alerts with full conversation data
- `expandedConversations`: Set of expanded conversation IDs
- `expandedCrisisEvents`: Set of expanded crisis event indices
- `responseFeedback`: Map of conversation ID → feedback (positive/negative)

### API Integration
- **GET /students**: Load student roster
- **GET /students/hash/{id}/conversations**: Load student conversation history
- **GET /students/hash/{id}/themes**: Load active themes
- **GET /crisis-events**: Load crisis alert feed
- **GET /conversations/{id}**: Load full conversation details for crisis events

### Data Processing
- **JSON parsing**: Handles matched_patterns as both string and array
- **Date formatting**: Relative timestamps (5m ago, 2h ago, 3d ago)
- **Risk badges**: Color-coded visual indicators
- **Nested data loading**: Fetches conversation details for each crisis event

## Safety & Compliance Features

### Explainability (Tenet #9)
- **Full transparency**: Every AI decision is traceable
- **Layer-by-layer breakdown**: Shows how each detection method contributed
- **Reasoning traces**: Natural language explanation of decisions
- **Evidence-based**: Quotes and patterns that triggered alerts

### Audit Trail (Tenet #2)
- **Immutable records**: All conversations and crisis events logged
- **Session tracking**: Hashed identifiers for privacy
- **Timestamp precision**: Exact time of detection
- **Performance metrics**: Latency and timeout tracking

### Privacy (Tenet #2)
- **Zero PII in logs**: All identifiers hashed
- **Hashed session IDs**: Displayed as truncated hashes
- **Anonymized display**: Student names shown but IDs protected
- **Secure access**: Counselor-only interface

### Human-in-the-Loop (Tenet #12)
- **Counselor review**: All crisis events require human acknowledgment
- **Response feedback**: Counselors improve AI through ratings
- **Manual override**: Counselors can escalate or de-escalate
- **Action checklist**: Clear follow-up tasks for counselors

## User Experience

### Visual Hierarchy
- **Color coding**: Red (crisis), yellow (caution), green (safe)
- **Progressive disclosure**: Summary → expand for details
- **Clear sections**: Organized by themes, conversations, metrics
- **Responsive layout**: Adapts to different screen sizes

### Performance
- **Lazy loading**: Conversations loaded on-demand
- **Efficient updates**: Only re-fetches changed data
- **Smooth animations**: Expand/collapse transitions
- **Fast filtering**: Client-side search and sort

### Accessibility
- **Semantic HTML**: Proper heading hierarchy
- **ARIA labels**: Screen reader support
- **Keyboard navigation**: Tab through interface
- **High contrast**: Clear visual distinctions

## Monitoring Capabilities

### Student Wellbeing Tracking
- **Conversation frequency**: How often student engages
- **Theme evolution**: What topics are recurring
- **Risk trends**: Pattern of risk scores over time
- **Engagement metrics**: Response quality and depth

### System Performance
- **Detection latency**: How fast consensus scoring runs
- **Timeout frequency**: When Mistral layer fails
- **Layer accuracy**: Which layers are most reliable
- **False positive rate**: Feedback on incorrect alerts

### Model Improvement
- **Response ratings**: Counselor feedback on quality
- **Pattern validation**: Confirm detected patterns are accurate
- **Threshold tuning**: Adjust based on false positive/negative rates
- **Training data**: Collect examples for fine-tuning
