'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePathname } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTaggedContextStore } from '@/stores/taggedContextStore';
import { ToolUseIndicator, FollowUpQuestions, ExportButton, CopyButton } from './ChatEnhancements';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
  toolCalls?: number;
  timestamp?: string;
}

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export default function AIChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [showSessions, setShowSessions] = useState(false);
  const [panelSize, setPanelSize] = useState({ width: 550, height: 900 });
  const [isResizing, setIsResizing] = useState(false);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [autocompleteItems, setAutocompleteItems] = useState<any[]>([]);
  const [autocompleteType, setAutocompleteType] = useState<'patient' | 'room' | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [showToolIndicator, setShowToolIndicator] = useState(false);
  const [toolCallCount, setToolCallCount] = useState(0);
  const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([]);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const pathname = usePathname();
  
  // Tagged context store
  const { contextItems, addItem, removeItem, clearAll, popTaggedContext } = useTaggedContextStore();

  // Update time every minute for footer
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute
    return () => clearInterval(timer);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowSessions(false);
      }
    };

    if (showSessions) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showSessions]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + Shift + H to toggle chat
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'h') {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      // Escape to close chat when open
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Initialize voice recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  // Generate follow-up questions based on actual conversation context
  const generateFollowUpQuestions = (userQuery: string, response: string) => {
    const questions: string[] = [];
    const queryLower = userQuery.toLowerCase();
    const responseLower = response.toLowerCase();
    
    // Check recent conversation history for better context
    const recentMessages = messages.slice(-3); // Last 3 messages
    const conversationContext = recentMessages.map(m => m.content.toLowerCase()).join(' ');
    
    // After successful operations - show verification options
    if (responseLower.includes('✅')) {
      // After patient removed
      if (responseLower.includes('removed')) {
        const roomMatch = response.match(/Room \d+/i);
        if (roomMatch) {
          questions.push(`Verify ${roomMatch[0]} is empty`);
        }
        if (!conversationContext.includes('occupancy')) {
          questions.push('Check all room status');
        }
        return questions.slice(0, 2);
      }
      
      // After transfer
      if (responseLower.includes('transferred')) {
        const toRoomMatch = response.match(/to\s+(Room \d+|`Room \d+`)/i);
        if (toRoomMatch) {
          const roomNum = toRoomMatch[1].replace(/`/g, '');
          questions.push(`Confirm patient arrived in ${roomNum}`);
        }
        return questions.slice(0, 1);
      }
      
      // After assignment
      if (responseLower.includes('assigned')) {
        questions.push('Show remaining available rooms');
        return questions.slice(0, 1);
      }
    }
    
    // Room is empty response
    if (responseLower.includes('empty') || responseLower.includes('no patient')) {
      questions.push('Show which rooms are occupied');
      return questions.slice(0, 1);
    }
    
    // Confirmation requests - different options
    if (responseLower.includes('confirm')) {
      questions.push('Cancel operation');
      questions.push('Show current state first');
      return questions;
    }
    
    // Patient location query result
    if (queryLower.includes('where') && responseLower.includes('room')) {
      const patientMatch = userQuery.match(/(P-\d+|\w+ \w+)/i);
      if (patientMatch) {
        questions.push('Get full patient details');
      }
      return questions.slice(0, 1);
    }
    
    // Multi-room query
    if (queryLower.includes('all rooms') || queryLower.includes('who\'s in')) {
      if (!conversationContext.includes('available')) {
        questions.push('List only available rooms');
      }
      if (!conversationContext.includes('statistics')) {
        questions.push('Hospital statistics');
      }
      return questions.slice(0, 2);
    }
    
    // Alert queries
    if (queryLower.includes('alert')) {
      if (responseLower.includes('active')) {
        questions.push('Show alert details');
      } else {
        questions.push('Active alerts');
      }
      return questions.slice(0, 1);
    }
    
    // Protocol queries
    if (responseLower.includes('protocol') || responseLower.includes('monitoring')) {
      return []; // No follow-ups for protocols
    }
    
    // If no specific context, show page-relevant options
    if (pathname?.includes('floorplan')) {
      return ['Current room status'];
    } else if (pathname?.includes('dashboard')) {
      return ['Hospital overview'];
    }
    
    return []; // No follow-ups if nothing relevant
  };

  // Get smart context based on current page
  const getSmartContext = () => {
    const suggestions: string[] = [];
    
    if (pathname?.includes('floorplan')) {
      suggestions.push('Show room occupancy');
      suggestions.push('List available rooms');
    } else if (pathname?.includes('dashboard')) {
      suggestions.push('Hospital statistics');
      suggestions.push('Active alerts summary');
    } else if (pathname?.includes('stream')) {
      suggestions.push('Patient monitoring status');
      suggestions.push('Critical alerts');
    }
    
    return suggestions;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText]);

  // Fetch all sessions
  const fetchSessions = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ai/sessions?user_id=default_user`);
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  // Load session from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('haven_chat_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
      // TODO: Load message history from session
    }
    // Fetch available sessions
    fetchSessions();
    
    // Load saved panel size
    const savedSize = localStorage.getItem('haven_chat_panel_size');
    if (savedSize) {
      try {
        setPanelSize(JSON.parse(savedSize));
      } catch (e) {
        // Ignore invalid saved size
      }
    }
  }, []);

  // Resize handlers
  const startResize = (e: React.MouseEvent, direction: 'left' | 'corner') => {
    e.preventDefault();
    setIsResizing(true);

    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = panelSize.width;
    const startHeight = panelSize.height;

    const handleMouseMove = (e: MouseEvent) => {
      if (direction === 'left' || direction === 'corner') {
        const newWidth = Math.max(350, Math.min(800, startWidth + (startX - e.clientX)));
        setPanelSize(prev => ({ ...prev, width: newWidth }));
      }
      if (direction === 'corner') {
        const newHeight = Math.max(400, Math.min(900, startHeight + (startY - e.clientY)));
        setPanelSize(prev => ({ ...prev, height: newHeight }));
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      // Save panel size
      localStorage.setItem('haven_chat_panel_size', JSON.stringify(panelSize));
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Start a completely new session
  const startNewSession = () => {
    setMessages([]);
    setSessionId(null);
    setSessionTitle(null);
    setStreamingText('');
    setIsStreaming(false);
    localStorage.removeItem('haven_chat_session_id');
    setShowSessions(false);
  };

  // Switch to an existing session
  const loadSession = async (session: ChatSession) => {
    try {
      setIsLoading(true);
      setSessionId(session.id);
      setSessionTitle(session.title);
      localStorage.setItem('haven_chat_session_id', session.id);
      setShowSessions(false);
      
      // Fetch message history for this session
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ai/sessions/${session.id}`);
      const data = await response.json();
      
      if (data.messages) {
        // Convert backend message format to frontend format
        const loadedMessages: Message[] = data.messages.map((msg: any) => ({
          role: msg.role,
          content: msg.content,
          isStreaming: false
        }));
        setMessages(loadedMessages);
      }
    } catch (error) {
      console.error('Error loading session:', error);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Simulate streaming effect (Perplexity-style)
  const streamText = async (text: string) => {
    setIsStreaming(true);
    setStreamingText('');
    
    // Add empty assistant message placeholder
    const placeholderMsg: Message = { 
      role: 'assistant', 
      content: '',
      isStreaming: true 
    };
    setMessages(prev => [...prev, placeholderMsg]);
    
    // Stream text word by word for smooth effect
    const words = text.split(' ');
    let currentText = '';
    
    for (let i = 0; i < words.length; i++) {
      currentText += (i > 0 ? ' ' : '') + words[i];
      setStreamingText(currentText);
      
      // Update the last message with streamed content
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: currentText,
          isStreaming: true
        };
        return updated;
      });
      
      // Delay between words (faster = more smooth, slower = more readable)
      await new Promise(resolve => setTimeout(resolve, 30));
    }
    
    // Mark streaming as complete
    setMessages(prev => {
      const updated = [...prev];
      updated[updated.length - 1] = {
        role: 'assistant',
        content: text,
        isStreaming: false
      };
      return updated;
    });
    
    setIsStreaming(false);
    setStreamingText('');
  };

  const handleSendMessage = async () => {
    if (input.trim() === '' || isLoading || isStreaming) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Build chat state with contextual information including tagged items
      const taggedContext = popTaggedContext();
      const chatState = {
        current_page: pathname || '/',
        user_name: 'Clinical Staff', // TODO: Get from auth
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        // Add page-specific context
        ...(pathname?.includes('floorplan') && { context_type: 'floor_plan' }),
        ...(pathname?.includes('dashboard') && { context_type: 'dashboard' }),
        ...(pathname?.includes('stream') && { context_type: 'patient_stream' }),
        // Add tagged context if available
        ...(taggedContext && { tagged_context: taggedContext }),
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
          user_id: 'default_user',
          chat_state: chatState,
        }),
      });

      const data = await response.json();
      
      // Save session ID and title for future messages
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem('haven_chat_session_id', data.session_id);
      }
      if (data.session_title) {
        setSessionTitle(data.session_title);
      }
      
      // Show tool use indicator if tools were called
      if (data.tool_calls && data.tool_calls > 0) {
        setShowToolIndicator(true);
        setToolCallCount(data.tool_calls);
        await new Promise(resolve => setTimeout(resolve, 1000));
        setShowToolIndicator(false);
      }
      
      setIsLoading(false);
      
      // Stream the response text with animation
      const responseText = data.response || 'Sorry, I encountered an error.';
      await streamText(responseText);
      
      // Invalidate cache if AI made changes to database
      if (data.invalidate_cache || data.tool_calls > 0) {
        console.log('🔄 AI made changes - invalidating cache');
        console.log('   Tool calls:', data.tool_calls);
        console.log('   Cache keys:', data.cache_keys || ['rooms', 'patients']);
        
        // Dispatch multiple times to ensure it's caught
        for (let i = 0; i < 3; i++) {
          window.dispatchEvent(new CustomEvent('haven-invalidate-cache', {
            detail: { keys: data.cache_keys || ['rooms', 'patients'], timestamp: Date.now() }
          }));
        }
        
        console.log('   ✅ Cache invalidation events dispatched');
      }
      
      // Generate follow-up questions
      const followUps = generateFollowUpQuestions(userMessage.content, responseText);
      setFollowUpQuestions(followUps);
      
      // Refresh sessions list
      fetchSessions();
      
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      setFollowUpQuestions(['Try again', 'Hospital statistics', 'Room status']);
      await streamText('Sorry, I\'m having trouble connecting. Please try again.');
    }
  };

  const handleSuggestionClick = async (prompt: string) => {
    // Auto-send the message like GPT
    setInput('');
    
    const userMessage: Message = { role: 'user', content: prompt };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Build chat state with contextual information including tagged items
      const taggedContext = popTaggedContext();
      const chatState = {
        current_page: pathname || '/',
        user_name: 'Clinical Staff',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        // Add page-specific context
        ...(pathname?.includes('floorplan') && { context_type: 'floor_plan' }),
        ...(pathname?.includes('dashboard') && { context_type: 'dashboard' }),
        ...(pathname?.includes('stream') && { context_type: 'patient_stream' }),
        // Add tagged context if available
        ...(taggedContext && { tagged_context: taggedContext }),
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: prompt,
          session_id: sessionId,
          user_id: 'default_user',
          chat_state: chatState,
        }),
      });

      const data = await response.json();
      
      // Save session ID and title for future messages
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem('haven_chat_session_id', data.session_id);
      }
      if (data.session_title) {
        setSessionTitle(data.session_title);
      }
      
      // Show tool use indicator if tools were called
      if (data.tool_calls && data.tool_calls > 0) {
        setShowToolIndicator(true);
        setToolCallCount(data.tool_calls);
        await new Promise(resolve => setTimeout(resolve, 1000));
        setShowToolIndicator(false);
      }
      
      setIsLoading(false);
      
      // Stream the response text with animation
      const responseText = data.response || 'Sorry, I encountered an error.';
      await streamText(responseText);
      
      // Generate follow-up questions
      const followUps = generateFollowUpQuestions(userMessage.content, responseText);
      setFollowUpQuestions(followUps);
      
      // Refresh sessions list
      fetchSessions();
      
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      setFollowUpQuestions(['Try again', 'Hospital statistics', 'Room status']);
      await streamText('Sorry, I\'m having trouble connecting. Please try again.');
    }
  };

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Voice recognition not supported in this browser');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Fetch autocomplete suggestions based on @ mention
  const fetchAutocompleteData = async (query: string, type: 'patient' | 'room') => {
    try {
      if (type === 'patient') {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients?search=${query}`);
        const data = await response.json();
        setAutocompleteItems(data.patients || []);
      } else if (type === 'room') {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/rooms`);
        const data = await response.json();
        const filtered = (data.rooms || []).filter((r: any) => 
          r.room_name.toLowerCase().includes(query.toLowerCase())
        );
        setAutocompleteItems(filtered);
      }
    } catch (error) {
      console.error('Error fetching autocomplete data:', error);
      setAutocompleteItems([]);
    }
  };

  // Handle input change with @ detection
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInput(value);

    // Check for @ mentions
    const lastWord = value.split(' ').pop() || '';
    if (lastWord.startsWith('@')) {
      const query = lastWord.substring(1);
      
      // Determine type based on context or keywords
      if (query.toLowerCase().includes('room') || query.toLowerCase().startsWith('r')) {
        setAutocompleteType('room');
        fetchAutocompleteData(query, 'room');
        setShowAutocomplete(true);
      } else {
        setAutocompleteType('patient');
        fetchAutocompleteData(query, 'patient');
        setShowAutocomplete(true);
      }
    } else {
      setShowAutocomplete(false);
    }
  };

  // Select item from autocomplete
  const selectAutocompleteItem = (item: any) => {
    // Add to tagged context
    if (autocompleteType === 'patient') {
      addItem({
        id: item.id,
        name: item.name,
        type: 'patient',
        metadata: { patient_id: item.patient_id, condition: item.condition }
      });
    } else if (autocompleteType === 'room') {
      addItem({
        id: item.room_id,
        name: item.room_name,
        type: 'room',
        metadata: { room_type: item.room_type }
      });
    }

    // Remove @ mention from input
    const words = input.split(' ');
    words.pop(); // Remove last word (the @ mention)
    setInput(words.join(' ') + ' ');
    setShowAutocomplete(false);
  };

  return (
    <>
      <AnimatePresence>
        {isOpen ? (
          // Expanded Panel
          <motion.div
            ref={panelRef}
            initial={{ scale: 0.95, opacity: 0, originX: 1, originY: 1 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ 
              duration: 0.2,
              ease: [0.16, 1, 0.3, 1] // Notion's easing curve
            }}
            className="fixed bottom-6 right-6 z-50 bg-white border border-neutral-200 shadow-2xl flex flex-col"
            style={{ 
              width: `${panelSize.width}px`,
              height: `${panelSize.height}px`,
              borderRadius: '12px',
              transformOrigin: 'bottom right',
              cursor: isResizing ? 'grabbing' : 'default',
              userSelect: isResizing ? 'none' : 'auto'
            }}
          >
            {/* Resize Handles */}
            <div 
              className="absolute left-0 top-0 bottom-0 w-1 cursor-ew-resize hover:bg-primary-700 transition-colors"
              onMouseDown={(e) => startResize(e, 'left')}
              style={{ zIndex: 60 }}
            />
            <div 
              className="absolute left-0 top-0 w-4 h-4 cursor-nwse-resize"
              onMouseDown={(e) => startResize(e, 'corner')}
              style={{ zIndex: 61 }}
            />
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                {/* Session Dropdown Selector */}
                <div className="relative flex-1">
                  <button
                    onClick={() => setShowSessions(!showSessions)}
                    className="flex items-center gap-2 hover:bg-neutral-50 transition-colors px-2 py-1 rounded max-w-full"
                  >
                    <p className="text-sm font-light text-neutral-950 truncate">
                      {sessionTitle && messages.length > 0 ? sessionTitle : 'New Chat'}
                    </p>
                    <svg className="w-4 h-4 text-neutral-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {/* Export Button */}
                {messages.length > 0 && (
                  <ExportButton messages={messages} sessionTitle={sessionTitle} />
                )}
                {/* New Chat Button */}
                {!isLoading && !isStreaming && (
                  <button
                    onClick={startNewSession}
                    className="text-neutral-400 hover:text-neutral-950 transition-colors"
                    title="Start new conversation"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                    </svg>
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-neutral-400 hover:text-neutral-950 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Sessions Dropdown */}
            {showSessions && (
              <motion.div 
                ref={dropdownRef}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.15 }}
                className="absolute top-16 left-4 right-4 bg-white border border-neutral-200 shadow-xl rounded-lg overflow-hidden z-50 max-h-80"
              >
                <div className="p-3 border-b border-neutral-200 bg-neutral-50">
                  <p className="text-[10px] font-medium text-neutral-600 uppercase tracking-wider">
                    Recent Conversations
                  </p>
                </div>
                <div className="overflow-y-auto max-h-64">
                  {sessions.length === 0 ? (
                    <div className="p-4 text-center">
                      <p className="text-xs font-light text-neutral-400 mb-2">No previous conversations</p>
                    </div>
                  ) : (
                    sessions.map((session) => (
                      <button
                        key={session.id}
                        onClick={() => loadSession(session)}
                        className={`w-full text-left px-4 py-2.5 border-b border-neutral-100 last:border-b-0 hover:bg-neutral-50 transition-colors ${
                          sessionId === session.id ? 'bg-primary-50 border-l-2 border-primary-700' : ''
                        }`}
                      >
                        <p className="text-sm font-light text-neutral-950 mb-1 truncate">
                          {session.title}
                        </p>
                        <p className="text-[10px] font-light text-neutral-400">
                          {new Date(session.updated_at).toLocaleDateString()} • {new Date(session.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </button>
                    ))
                  )}
                </div>
              </motion.div>
            )}

            {/* Messages Area */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="flex-1 overflow-y-auto p-4 space-y-4"
            >
                {messages.length === 0 ? (
                  <>
                    {/* Welcome Message - Minimal */}
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: 0.1 }}
                    >
                      <p className="text-sm font-light text-neutral-600 mb-4">
                        Ask about patients, rooms, protocols, or alerts.
                      </p>

                      {/* Quick Actions - Minimal */}
                      <div className="space-y-1.5">
                        {getSmartContext().length > 0 ? (
                          // Show smart context if on specific page
                          getSmartContext().map((prompt, i) => (
                            <motion.button
                              key={i}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ duration: 0.3, delay: 0.2 + (i * 0.08) }}
                              onClick={() => handleSuggestionClick(prompt)}
                              className="w-full text-left px-3 py-2 text-sm font-light text-neutral-700 bg-white hover:bg-neutral-50 border border-neutral-200 transition-all"
                              style={{ borderRadius: '6px' }}
                            >
                              {prompt}
                            </motion.button>
                          ))
                        ) : (
                          // Default suggestions
                          ['Room status', 'Active alerts', 'Hospital statistics'].map((prompt, i) => (
                            <motion.button
                              key={i}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ duration: 0.3, delay: 0.2 + (i * 0.08) }}
                              onClick={() => handleSuggestionClick(prompt)}
                              className="w-full text-left px-3 py-2 text-sm font-light text-neutral-700 bg-white hover:bg-neutral-50 border border-neutral-200 transition-all"
                              style={{ borderRadius: '6px' }}
                            >
                              {prompt}
                            </motion.button>
                          ))
                        )}
                      </div>

                      {/* Subtle hint */}
                      <motion.p 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.4, delay: 0.5 }}
                        className="text-xs text-neutral-400 mt-4 pt-3 border-t border-neutral-100"
                      >
                        Type <code className="bg-neutral-100 px-1 py-0.5 rounded text-primary-700 text-[11px]">@</code> to reference patients or rooms
                      </motion.p>
                    </motion.div>
                </>
              ) : (
                <>
                  {/* Chat Messages */}
                  {messages.map((msg, idx) => (
                    <motion.div 
                      key={idx} 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, ease: 'easeOut' }}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[75%] px-4 py-3 text-sm font-light leading-relaxed ${
                          msg.role === 'user'
                            ? 'bg-primary-700 text-white'
                            : 'bg-neutral-100 text-neutral-950'
                        }`}
                        style={{ 
                          borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                          wordBreak: 'break-word',
                          lineHeight: '1.6'
                        }}
                      >
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed whitespace-pre-wrap">{children}</p>,
                              strong: ({ children }) => <strong className="font-bold text-neutral-950">{children}</strong>,
                              em: ({ children }) => <em className="italic text-neutral-700">{children}</em>,
                              ul: ({ children }) => <ul className="my-3 space-y-2 list-disc list-inside">{children}</ul>,
                              ol: ({ children }) => <ol className="my-3 space-y-2 list-decimal list-inside">{children}</ol>,
                              li: ({ children }) => <li className="leading-relaxed text-sm">{children}</li>,
                              code: ({ children }) => <code className="bg-yellow-100 text-neutral-950 px-1.5 py-0.5 rounded text-xs font-medium">{children}</code>,
                              pre: ({ children }) => (
                                <div className="relative group my-3">
                                  <pre className="bg-neutral-200 p-3 rounded text-xs font-mono overflow-x-auto border border-neutral-300">
                                    {children}
                                  </pre>
                                  <CopyButton text={String(children)} />
                                </div>
                              ),
                              h1: ({ children }) => <h1 className="text-base font-bold text-neutral-950 mb-2 mt-1">{children}</h1>,
                              h2: ({ children }) => <h2 className="text-sm font-bold text-neutral-950 mb-2 mt-1">{children}</h2>,
                              h3: ({ children }) => <h3 className="text-sm font-semibold text-neutral-950 mb-1.5 mt-1">{children}</h3>,
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                        {msg.isStreaming && (
                          <span className="inline-block w-1.5 h-3.5 bg-primary-700 ml-0.5 animate-pulse" />
                        )}
                      </div>
                    </motion.div>
                  ))}
                  
                  {/* Tool Use Indicator */}
                  {showToolIndicator && <ToolUseIndicator toolCount={toolCallCount} />}
                  
                  {/* Loading indicator */}
                  {isLoading && !isStreaming && !showToolIndicator && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="flex justify-start"
                    >
                      <div className="bg-neutral-100 px-4 py-3 text-sm font-light text-neutral-600" style={{ borderRadius: '12px 12px 12px 2px' }}>
                        <div className="flex gap-1">
                          <span className="animate-bounce">●</span>
                          <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>●</span>
                          <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>●</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                  
                  {/* Follow-up Questions */}
                  {!isLoading && !isStreaming && messages.length > 0 && followUpQuestions.length > 0 && (
                    <FollowUpQuestions 
                      questions={followUpQuestions} 
                      onSelect={(q) => {
                        setFollowUpQuestions([]);
                        handleSuggestionClick(q);
                      }} 
                    />
                  )}
                  
                  <div ref={messagesEndRef} />
                </>
              )}
            </motion.div>

            {/* Input Area */}
            <div>
                <div className="border-t border-neutral-200 p-4">
                  {/* Tagged Context Chips */}
                  {contextItems.length > 0 && (
                    <div className="mb-2 flex flex-wrap gap-1">
                      {contextItems.map((item) => (
                        <div
                          key={item.id}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-primary-100 text-primary-700 text-xs rounded"
                        >
                          <span>{item.name}</span>
                          <button
                            onClick={() => removeItem(item.id)}
                            className="hover:text-primary-900"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Autocomplete Dropdown */}
                  {showAutocomplete && autocompleteItems.length > 0 && (
                    <div className="mb-2 bg-white border border-neutral-200 rounded shadow-lg max-h-40 overflow-y-auto">
                      {autocompleteItems.map((item, idx) => (
                        <button
                          key={idx}
                          onClick={() => selectAutocompleteItem(item)}
                          className="w-full text-left px-3 py-2 hover:bg-neutral-50 text-xs font-light text-neutral-950"
                        >
                          {autocompleteType === 'patient' ? item.name : item.room_name}
                          {autocompleteType === 'patient' && item.patient_id && (
                            <span className="text-neutral-400 ml-2">({item.patient_id})</span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={handleInputChange}
                      onKeyPress={handleKeyPress}
                      placeholder={isLoading ? "Thinking..." : isStreaming ? "Responding..." : isListening ? "Listening..." : "Ask me anything... (@ to tag)"}
                      disabled={isLoading || isStreaming}
                      className="flex-1 px-3 py-2 text-sm font-light text-neutral-950 placeholder:text-neutral-400 border border-neutral-200 focus:outline-none focus:border-primary-700 transition-colors disabled:opacity-50 disabled:bg-neutral-50"
                      style={{ borderRadius: '6px' }}
                    />
                    {/* Voice Input Button */}
                    {recognitionRef.current && (
                      <button
                        onClick={toggleVoiceInput}
                        disabled={isLoading || isStreaming}
                        className={`px-3 py-2 border text-sm font-light transition-colors disabled:opacity-50 ${
                          isListening 
                            ? 'bg-red-50 border-red-500 text-red-700' 
                            : 'border-neutral-200 text-neutral-600 hover:text-neutral-950 hover:border-neutral-400'
                        }`}
                        style={{ borderRadius: '6px' }}
                        title="Voice input"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                        </svg>
                      </button>
                    )}
                    <button
                      onClick={handleSendMessage}
                      disabled={isLoading || isStreaming || input.trim() === ''}
                      className="px-4 py-2 bg-primary-700 text-white text-sm font-light hover:bg-primary-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ borderRadius: '6px' }}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>
                
              {/* Location Footer */}
              <div className="px-4 py-3 border-t border-neutral-200 bg-neutral-50">
                <div className="flex items-center justify-between text-xs font-light text-neutral-500">
                  <span className="uppercase tracking-wider flex items-center gap-2">
                    {pathname?.includes('floorplan') ? (
                      <><span className="text-sm">🗺️</span><span>Floor Plan</span></>
                    ) : pathname?.includes('dashboard') ? (
                      <><span className="text-sm">📊</span><span>Dashboard</span></>
                    ) : pathname?.includes('stream') ? (
                      <><span className="text-sm">📹</span><span>Patient Stream</span></>
                    ) : (
                      <><span className="text-sm">🏥</span><span>Haven</span></>
                    )}
                  </span>
                  <span className="text-neutral-400 font-mono text-[10px]" title="Keyboard shortcut: ⌘⇧H">
                    {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • ⌘⇧H
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          // Floating Button
          <div className="fixed bottom-6 right-6 z-50 group">
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              onClick={() => setIsOpen(true)}
              className="w-14 h-14 bg-primary-700 hover:bg-primary-800 text-white shadow-lg hover:shadow-xl transition-all flex items-center justify-center"
              style={{ borderRadius: '50%' }}
              title="Hi, it's Haven AI"
            >
            {/* Medical AI Icon - Heartbeat with gentle curves */}
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {/* Heart shape */}
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" 
                    fill="currentColor" 
                    opacity="0.9"
              />
              {/* Heartbeat pulse line */}
              <path 
                d="M7 12 L9 12 L10 9 L12 15 L14 12 L17 12" 
                stroke="white" 
                strokeWidth="2"
                fill="none"
              />
            </svg>
            </motion.button>
            
            {/* Tooltip - Notion style */}
            <div className="absolute bottom-full right-0 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
              <div className="bg-neutral-900 text-white text-xs font-light px-3 py-1.5 rounded whitespace-nowrap">
                Hi, it's Haven AI
              </div>
            </div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

