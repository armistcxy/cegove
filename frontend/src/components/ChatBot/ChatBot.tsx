import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useNavigate } from 'react-router-dom';
import { useChatBot, ChatMessage, QuickReplyChip } from '../../context/ChatBotContext';
import { useUser } from '../../context/UserContext';
import styles from './ChatBot.module.css';

// Quick Reply Chips Component
const QuickReplyChips: React.FC<{
    chips: QuickReplyChip[];
    onChipClick: (chip: QuickReplyChip) => void;
    disabled?: boolean;
}> = ({ chips, onChipClick, disabled }) => {
    if (!chips || chips.length === 0) return null;

    const getChipIcon = (type: string) => {
        switch (type) {
            case 'movie': return '🎬';
            case 'showtime': return '🕐';
            case 'seat': return '🪑';
            case 'cinema': return '🏢';
            case 'action': return '▶️';
            case 'link': return '🔗';
            default: return '';
        }
    };

    return (
        <div className={styles.chipsContainer}>
            {chips.map((chip, index) => (
                <button
                    key={index}
                    className={`${styles.chip} ${styles[`chip${chip.type.charAt(0).toUpperCase() + chip.type.slice(1)}`]}`}
                    onClick={() => onChipClick(chip)}
                    disabled={disabled}
                >
                    {getChipIcon(chip.type)} {chip.label}
                </button>
            ))}
        </div>
    );
};

const ChatBot: React.FC = () => {
    const navigate = useNavigate();
    const {
        messages,
        isOpen,
        isLoading,
        setIsOpen,
        sendMessage,
        loadHistory,
        clearSession
    } = useChatBot();
    const { userProfile, isLoggedIn } = useUser();

    const [inputValue, setInputValue] = useState('');
    const [showTimestamps, setShowTimestamps] = useState(false);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const [wasLoggedIn, setWasLoggedIn] = useState(isLoggedIn);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    // Clear chat when user logs out
    useEffect(() => {
        if (wasLoggedIn && !isLoggedIn) {
            clearSession();
        }
        setWasLoggedIn(isLoggedIn);
    }, [isLoggedIn, wasLoggedIn, clearSession]);

    // Get user ID
    const getUserId = (): string => {
        if (isLoggedIn && userProfile?.id) {
            return String(userProfile.id);
        }
        let guestId = localStorage.getItem('chatbot-guest-id');
        if (!guestId) {
            guestId = `guest-${Date.now()}`;
            localStorage.setItem('chatbot-guest-id', guestId);
        }
        return guestId;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        await sendMessage(inputValue.trim(), getUserId());
        setInputValue('');
    };

    const handleChipClick = async (chip: QuickReplyChip) => {
        if (isLoading) return;

        // Handle link type - open in new tab
        if (chip.type === 'link' && chip.url) {
            window.open(chip.url, '_blank');
            return;
        }

        // Handle movie type - navigate + continue chat
        if (chip.type === 'movie' && chip.id) {
            // Navigate to movie detail page
            navigate(`/MovieDetail/${chip.id}`);
            // Also send context to bot to show showtimes
            await sendMessage(`I want to see showtimes for ${chip.label}`, getUserId(), chip);
            return;
        }

        // Handle showtime type - navigate to seat selection
        if (chip.type === 'showtime' && chip.id) {
            // Navigate to booking page with showtime ID
            navigate(`/booking/${chip.id}`);
            return;
        }

        // Handle cinema type - navigate + continue chat
        if (chip.type === 'cinema' && chip.id) {
            navigate(`/CinemaDetails/${chip.id}`);
            await sendMessage(`Show me movies at ${chip.label}`, getUserId(), chip);
            return;
        }

        // For other chips, just send to bot with context
        await sendMessage(chip.label, getUserId(), chip);
    };

    const handleLoadHistory = async () => {
        setIsLoadingHistory(true);
        try {
            await loadHistory();
        } finally {
            setIsLoadingHistory(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const toggleChat = () => {
        setIsOpen(!isOpen);
    };

    const handleClearChat = () => {
        if (window.confirm('Are you sure you want to clear the chat history?')) {
            clearSession();
        }
    };

    // Check if this is the last assistant message (for showing chips)
    const isLastAssistantMessage = (index: number): boolean => {
        for (let i = messages.length - 1; i >= 0; i--) {
            if (messages[i].role === 'assistant') {
                return i === index;
            }
        }
        return false;
    };

    return (
        <div className={styles.chatbotContainer}>
            {/* Chat Window */}
            <div className={`${styles.chatWindow} ${isOpen ? styles.open : ''}`}>
                {/* Header */}
                <div className={styles.header}>
                    <div className={styles.headerLeft}>
                        <div className={styles.botAvatar}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                                <circle cx="8" cy="14" r="1"/>
                                <circle cx="16" cy="14" r="1"/>
                            </svg>
                        </div>
                        <div>
                            <h3 className={styles.headerTitle}>Cegove Assistant</h3>
                            <span className={styles.headerStatus}>
                                {isLoading ? 'Typing...' : 'Online'}
                            </span>
                        </div>
                    </div>
                    <div className={styles.headerActions}>
                        {isLoggedIn && (
                            <button
                                className={styles.headerBtn}
                                onClick={handleLoadHistory}
                                disabled={isLoadingHistory}
                                title="Load chat history"
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                                    <path d="M3 3v5h5"/>
                                    <path d="M12 7v5l4 2"/>
                                </svg>
                            </button>
                        )}
                        {isLoggedIn && (
                            <button
                                className={`${styles.headerBtn} ${showTimestamps ? styles.headerBtnActive : ''}`}
                                onClick={() => setShowTimestamps(!showTimestamps)}
                                title="Toggle timestamps"
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <polyline points="12 6 12 12 16 14"/>
                                </svg>
                            </button>
                        )}
                        <button
                            className={styles.headerBtn}
                            onClick={handleClearChat}
                            title="Clear chat"
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                        <button
                            className={styles.closeBtn}
                            onClick={toggleChat}
                            title="Close chat"
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Messages Area */}
                <div className={styles.messagesContainer}>
                    {messages.length === 0 ? (
                        <div className={styles.welcomeMessage}>
                            <div className={styles.welcomeIcon}>
                                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                    <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                                    <circle cx="8" cy="14" r="1"/>
                                    <circle cx="16" cy="14" r="1"/>
                                </svg>
                            </div>
                            <h4>Welcome to Cegove Assistant!</h4>
                            <p>I can help you find movies, book tickets, and navigate our website. How can I assist you today?</p>
                        </div>
                    ) : (
                        messages.map((msg: ChatMessage, index: number) => (
                            <div
                                key={index}
                                className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.botMessage}`}
                            >
                                <div className={styles.messageContent}>
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                                {/* Render chips only for the last assistant message */}
                                {msg.role === 'assistant' && isLastAssistantMessage(index) && msg.metadata?.chips && (
                                    <QuickReplyChips
                                        chips={msg.metadata.chips}
                                        onChipClick={handleChipClick}
                                        disabled={isLoading}
                                    />
                                )}
                                {showTimestamps && isLoggedIn && (
                                    <div className={styles.messageTime}>
                                        {formatTime(msg.timestamp)}
                                        {msg.agent && <span className={styles.agentTag}>{msg.agent}</span>}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                    {isLoading && (
                        <div className={`${styles.message} ${styles.botMessage}`}>
                            <div className={styles.typingIndicator}>
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <form className={styles.inputArea} onSubmit={handleSubmit}>
                    <input
                        ref={inputRef}
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your message..."
                        className={styles.input}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className={styles.sendBtn}
                        disabled={!inputValue.trim() || isLoading}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="22" y1="2" x2="11" y2="13"/>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                        </svg>
                    </button>
                </form>
            </div>

            {/* Floating Button */}
            <button
                className={`${styles.floatingBtn} ${isOpen ? styles.hidden : ''}`}
                onClick={toggleChat}
                aria-label="Open chat"
            >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                {messages.length > 0 && (
                    <span className={styles.badge}>{messages.length}</span>
                )}
            </button>
        </div>
    );
};

export default ChatBot;
