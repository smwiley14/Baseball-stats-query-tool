import { useState, useRef, useEffect } from 'react'
import { useHooks } from './hooks/hooks'
import { ChatMessage } from './types/Chat'
import {
  Container,
  Typography,
  TextField,
  Box,
  Avatar,
  Card,
  CardContent,
  IconButton,
  AppBar,
  Toolbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stack,
} from '@mui/material'
import { Send } from '@mui/icons-material'
import { styled } from '@mui/material/styles'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { darkTheme } from '../theme/styles'

const StyledContainer = styled(Container)(({ theme }: { theme: any }) => ({
  height: '100vh',
  display: 'flex',
  flexDirection: 'column',
  padding: 0,
  maxWidth: '800px !important',
  backgroundColor: theme.palette.background.paper,
  boxShadow: '0 0 0 1px rgba(255, 255, 255, 0.05)',
}))

const StyledAppBar = styled(AppBar)(({ theme }: { theme: any }) => ({
  position: 'sticky',
  top: 0,
  zIndex: 10,
  backgroundColor: theme.palette.background.paper,
  color: theme.palette.text.primary,
  boxShadow: '0 1px 0 0 rgba(255, 255, 255, 0.05)',
}))

const MessagesContainer = styled(Box)(({ theme }: { theme: any }) => ({
  flex: 1,
  overflowY: 'auto',
  padding: theme.spacing(2, 0),
  backgroundColor: theme.palette.background.default,
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: 'transparent',
  },
  '&::-webkit-scrollbar-thumb': {
    background: '#d1d1d7',
    borderRadius: '4px',
    '&:hover': {
      background: '#9ca3af',
    },
  },
}))

const MessageWrapper = styled(Box)<{ isUser?: boolean }>(({ theme, isUser }: { theme: any; isUser?: boolean }) => ({
  display: 'flex',
  gap: theme.spacing(1),
  alignItems: 'flex-start',
  maxWidth: '100%',
  flexDirection: isUser ? 'row-reverse' : 'row',
  marginBottom: theme.spacing(2),
  padding: theme.spacing(0, 2),
}))

const MessageBubble = styled(Card)<{ isUser?: boolean }>(({ theme, isUser }: { theme: any; isUser?: boolean }) => ({
  maxWidth: '85%',
  padding: theme.spacing(1, 1.25),
  borderRadius: theme.spacing(1),
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.background.paper,
  color: isUser ? '#ffffff' : theme.palette.text.primary,
  border: `1px solid ${isUser ? theme.palette.primary.main : theme.palette.divider}`,
  boxShadow: isUser ? '0 2px 4px rgba(25, 195, 125, 0.2)' : '0 1px 2px rgba(0, 0, 0, 0.2)',
}))

const StyledAvatar = styled(Avatar)<{ isUser?: boolean }>(({ theme, isUser }: { theme: any; isUser?: boolean }) => ({
  width: 32,
  height: 32,
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.secondary.main,
  flexShrink: 0,
  fontSize: '1.25rem',
}))

const InputContainer = styled(Box)(({ theme }: { theme: any }) => ({
  borderTop: `1px solid ${theme.palette.divider}`,
  backgroundColor: theme.palette.background.paper,
  padding: theme.spacing(2),
}))

const InputWrapper = styled(Box)(({ theme }: { theme: any }) => ({
  display: 'flex',
  gap: theme.spacing(1),
  alignItems: 'flex-end',
  backgroundColor: theme.palette.background.paper,
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.spacing(3),
  padding: theme.spacing(1, 1.5),
  transition: 'border-color 0.2s',
  '&:focus-within': {
    borderColor: theme.palette.primary.main,
    boxShadow: `0 0 0 3px ${theme.palette.primary.main}30`,
  },
}))

const StyledTextField = styled(TextField)(({ theme }: { theme: any }) => ({
  flex: 1,
  '& .MuiInputBase-root': {
    border: 'none',
    fontSize: '0.9375rem',
    maxHeight: '200px',
    overflowY: 'auto',
    '& fieldset': {
      border: 'none',
    },
    '&:hover fieldset': {
      border: 'none',
    },
    '&.Mui-focused fieldset': {
      border: 'none',
    },
  },
  '& .MuiInputBase-input': {
    padding: theme.spacing(0.5, 0),
    resize: 'none',
    lineHeight: 1.5,
  },
}))

const SendButton = styled(IconButton)(({ theme }: { theme: any }) => ({
  backgroundColor: theme.palette.primary.main,
  color: '#ffffff',
  width: 32,
  height: 32,
  flexShrink: 0,
  '&:hover': {
    backgroundColor: '#16a870',
  },
  '&:disabled': {
    opacity: 0.5,
  },
}))

const WelcomeScreen = styled(Box)(({ theme }: { theme: any }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(4, 2),
  textAlign: 'center',
  minHeight: '100%',
}))

const ExampleQuery = styled(Chip)(({ theme }: { theme: any }) => ({
  padding: theme.spacing(1.5, 1),
  backgroundColor: theme.palette.background.paper,
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.spacing(1),
  cursor: 'pointer',
  transition: 'all 0.2s',
  textAlign: 'left',
  fontSize: '0.9375rem',
  color: theme.palette.text.primary,
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
    borderColor: theme.palette.divider,
  },
}))

const TypingIndicator = styled(Box)(({ theme }: { theme: any }) => ({
  display: 'flex',
  gap: theme.spacing(0.5),
  padding: theme.spacing(1, 0),
  '& span': {
    width: 8,
    height: 8,
    borderRadius: '50%',
    backgroundColor: theme.palette.text.secondary,
    animation: 'typing 1.4s infinite',
    '&:nth-of-type(2)': {
      animationDelay: '0.2s',
    },
    '&:nth-of-type(3)': {
      animationDelay: '0.4s',
    },
  },
  '@keyframes typing': {
    '0%, 60%, 100%': {
      transform: 'translateY(0)',
      opacity: 0.7,
    },
    '30%': {
      transform: 'translateY(-10px)',
      opacity: 1,
    },
  },
}))

function App() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { sendMessage, messages, loading } = useHooks()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() && !loading) {
        sendMessage(input)
        setInput('')
      }
    }
  }

  const handleSend = () => {
    if (input.trim() && !loading) {
      sendMessage(input)
      setInput('')
    }
  }

  const renderMessageContent = (message: ChatMessage) => {
    if (message.data && message.data.length > 0) {
      const columns = Object.keys(message.data[0])
      
      return (
        <TableContainer component={Box} sx={{ margin: (theme) => theme.spacing(-1, -1.25), padding: (theme) => theme.spacing(1, 1.25) }}>
          <Table size="small" sx={{ fontSize: '0.875rem' }}>
            <TableHead>
              <TableRow>
                {columns.map((col) => (
                  <TableCell key={col} sx={{ fontWeight: 600, whiteSpace: 'nowrap', color: 'text.primary' }}>
                    {col}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {message.data.map((row, idx) => (
                <TableRow 
                  key={idx}
                >
                  {columns.map((col) => (
                    <TableCell key={col} sx={{ color: 'text.primary' }}>{row[col] ?? ''}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
    
    const lines = message.content.split('\n')
    return (
      <Box sx={{ lineHeight: 1.6, fontSize: '0.9375rem' }}>
        {lines.map((line, idx) => (
          <Typography key={idx} variant="body2" sx={{ margin: '0.25rem 0', whiteSpace: 'pre-wrap' }}>
            {line || '\u00A0'}
          </Typography>
        ))}
      </Box>
    )
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <StyledContainer maxWidth={false}>
        <StyledAppBar position="sticky" elevation={0}>
          <Toolbar sx={{ justifyContent: 'center', flexDirection: 'column', py: 1.5 }}>
            <Typography variant="h6" component="h1" sx={{ fontWeight: 600, fontSize: '1.25rem' }}>
              ⚾ Baseball Stats Assistant
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.875rem' }}>
              Ask questions about baseball statistics
            </Typography>
          </Toolbar>
        </StyledAppBar>

        <MessagesContainer>
          {messages.length === 0 ? (
            <WelcomeScreen>
              <Typography variant="h2" sx={{ fontSize: '4rem', mb: 2 }}>
                ⚾
              </Typography>
              <Typography variant="h5" component="h2" sx={{ fontWeight: 600, mb: 1 }}>
                Welcome to Baseball Stats Assistant
              </Typography>
              <Typography variant="body1" sx={{ color: 'text.secondary', mb: 3 }}>
                Ask me anything about baseball statistics!
              </Typography>
              <Stack spacing={1} sx={{ width: '100%', maxWidth: 500 }}>
                <ExampleQuery
                  label="Who has the most home runs of all time?"
                  onClick={() => setInput("Who has the most home runs of all time?")}
                  clickable
                />
                <ExampleQuery
                  label="Show me the top 10 batting averages"
                  onClick={() => setInput("Show me the top 10 batting averages")}
                  clickable
                />
                <ExampleQuery
                  label="Who had the most strikeouts in 2020?"
                  onClick={() => setInput("Who had the most strikeouts in 2020?")}
                  clickable
                />
              </Stack>
            </WelcomeScreen>
          ) : (
            <Box>
              {messages.map((msg, idx) => (
                <MessageWrapper key={idx} isUser={msg.role === 'user'}>
                  <StyledAvatar isUser={msg.role === 'user'}>
                    {msg.role === 'user' ? '👤' : '⚾'}
                  </StyledAvatar>
                  <MessageBubble isUser={msg.role === 'user'}>
                    <CardContent sx={{ p: '0 !important', '&:last-child': { pb: 0 } }}>
                      {renderMessageContent(msg)}
                    </CardContent>
                  </MessageBubble>
                </MessageWrapper>
              ))}
              {loading && (
                <MessageWrapper>
                  <StyledAvatar>⚾</StyledAvatar>
                  <MessageBubble>
                    <CardContent sx={{ p: '0 !important', '&:last-child': { pb: 0 } }}>
                      <TypingIndicator>
                        <Box component="span" />
                        <Box component="span" />
                        <Box component="span" />
                      </TypingIndicator>
                    </CardContent>
                  </MessageBubble>
                </MessageWrapper>
              )}
              <div ref={messagesEndRef} />
            </Box>
          )}
        </MessagesContainer>

        <InputContainer>
          <InputWrapper>
            <StyledTextField
              multiline
              maxRows={8}
              value={input}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask a question about baseball statistics..."
              disabled={loading}
              variant="outlined"
            />
            <SendButton
              onClick={handleSend}
              disabled={loading || !input.trim()}
              aria-label="Send message"
            >
              <Send sx={{ fontSize: 20 }} />
            </SendButton>
          </InputWrapper>
          <Box sx={{ mt: 1, textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.75rem' }}>
              Baseball Stats Assistant can make mistakes. Check important stats.
            </Typography>
          </Box>
        </InputContainer>
      </StyledContainer>
    </ThemeProvider>
  )
}

export default App
