import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { UserProvider } from './context/UserContext';
import { ChatBotProvider } from './context/ChatBotContext';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
      <UserProvider>
          <ChatBotProvider>
              <App />
          </ChatBotProvider>
      </UserProvider>
  </StrictMode>,
)
