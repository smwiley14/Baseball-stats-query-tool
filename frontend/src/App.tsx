import { useState } from 'react'
import { useHooks } from './hooks/hooks'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { darkTheme } from '../theme/styles'
import { Bar } from './components/Bar'
import { Header } from './components/Header'
import { Results } from './components/Results'
import { Input } from './components/Input'

function App() {
  const [input, setInput] = useState('')
  const { sendMessage, cancelQuery, messages, loading } = useHooks()

  const handleSend = () => {
    if (input.trim() && !loading) {
      sendMessage(input)
      setInput('')
    }
  }

  const handleExampleClick = (query: string) => {
    setInput(query)
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Bar>
        <Header />
        <Input 
          value={input}
          onChange={setInput}
          onSend={handleSend}
          onCancel={cancelQuery}
          loading={loading}
        />
        <Results 
          messages={messages} 
          loading={loading}
          onExampleClick={handleExampleClick}
        />
      </Bar>
    </ThemeProvider>
  )
}

export default App
