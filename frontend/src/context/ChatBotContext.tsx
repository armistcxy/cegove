import React, { createContext, useContext, useState, useCallback } from 'react';

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    agent?: string;
}

interface ChatBotContextType {
    sessionId: string | null;
    messages: ChatMessage[];
    isOpen: boolean;
    isLoading: boolean;
    setIsOpen: (open: boolean) => void;
    sendMessage: (message: string, userId: string) => Promise<void>;
    loadHistory: () => Promise<void>;
    clearSession: () => Promise<void>;
}

const ChatBotContext = createContext<ChatBotContextType | undefined>(undefined);

const CHATBOT_API_URL = 'https://chatbot.cegove.cloud/api/v1';

export const ChatBotProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [sessionId, setSessionId] = useState<string | null>(() =>
        localStorage.getItem('chatbot-session-id')
    );
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const loadHistory = useCallback(async () => {
        if (!sessionId) return;

        const token = localStorage.getItem('access-token');

        try {
            const headers: HeadersInit = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${CHATBOT_API_URL}/chat/${sessionId}/history`, {
                headers
            });

            if (response.ok) {
                const data = await response.json();
                if (data.history && Array.isArray(data.history)) {
                    setMessages(data.history.map((msg: any) => ({
                        role: msg.role,
                        content: msg.content,
                        timestamp: msg.timestamp,
                        agent: msg.agent
                    })));
                }
            } else if (response.status === 401) {
                // Session expired or unauthorized - clear old session
                localStorage.removeItem('chatbot-session-id');
                setSessionId(null);
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }, [sessionId]);

    const sendMessage = async (message: string, userId: string) => {
        setIsLoading(true);

        const userMessage: ChatMessage = {
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMessage]);

        try {
            const response = await fetch(`${CHATBOT_API_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    message: message,
                    session_id: sessionId || undefined
                })
            });

            if (response.ok) {
                const data = await response.json();

                if (data.session_id && data.session_id !== sessionId) {
                    setSessionId(data.session_id);
                    localStorage.setItem('chatbot-session-id', data.session_id);
                }

                const assistantMessage: ChatMessage = {
                    role: 'assistant',
                    content: data.message,
                    timestamp: data.timestamp,
                    agent: data.agent
                };
                setMessages(prev => [...prev, assistantMessage]);
            } else {
                const errorMessage: ChatMessage = {
                    role: 'assistant',
                    content: 'Sorry, I encountered an error. Please try again.',
                    timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: 'Sorry, I could not connect to the server. Please try again later.',
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const clearSession = async () => {
        if (sessionId) {
            try {
                await fetch(`${CHATBOT_API_URL}/chat/${sessionId}`, {
                    method: 'DELETE'
                });
            } catch (error) {
                console.error('Error clearing session:', error);
            }
        }

        localStorage.removeItem('chatbot-session-id');
        setSessionId(null);
        setMessages([]);
    };

    return (
        <ChatBotContext.Provider value={{
            sessionId,
            messages,
            isOpen,
            isLoading,
            setIsOpen,
            sendMessage,
            loadHistory,
            clearSession
        }}>
            {children}
        </ChatBotContext.Provider>
    );
};

export const useChatBot = () => {
    const context = useContext(ChatBotContext);
    if (!context) {
        throw new Error('useChatBot must be used within ChatBotProvider');
    }
    return context;
};
