import { useState } from 'react'
import { ChatMessage } from '../types/Chat'
import axios from 'axios'
import { getApiUrl } from '../../config/config'

export const useHooks = () => {
    // const sessionId = localStorage.getItem('sessionId')
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [loading, setLoading] = useState(false)
    const [sessionId, setSessionId] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [data, setData] = useState<any>(null)
    const [parsed, setParsed] = useState<any>(null)
    const [assistantMessage, setAssistantMessage] = useState<ChatMessage | null>(null)
    const [errorMessage, setErrorMessage] = useState<ChatMessage | null>(null)

    // const [loading, setLoading] = useState(false)
    const parseMessageContent = (content: string): { text: string; data?: Array<Record<string, any>> } => {
        // Try to detect if content contains structured data
        // Look for patterns like "col1: val1, col2: val2" repeated on multiple lines
        const lines = content.split('\n').filter(line => line.trim())
        
        // Check if it looks like tabular data (multiple lines with colons)
        if (lines.length > 1 && lines.every(line => line.includes(':'))) {
          try {
            const data: Array<Record<string, any>> = []
            for (const line of lines) {
              const row: Record<string, any> = {}
              // Parse "key: value, key2: value2" format
              const pairs = line.split(',').map(p => p.trim())
              for (const pair of pairs) {
                const [key, ...valueParts] = pair.split(':').map(s => s.trim())
                if (key && valueParts.length > 0) {
                  row[key] = valueParts.join(':').trim()
                }
              }
              if (Object.keys(row).length > 0) {
                data.push(row)
              }
            }
            if (data.length > 0) {
              return { text: content, data }
            }
          } catch (e) {
            // If parsing fails, just return text
          }
        }
        
        return { text: content }
      }
    
    const sendMessage = async (input: string) => {
        if (!input.trim() || loading) return
    
        const userMessage: ChatMessage = { role: 'user', content: input }
        setMessages(prev => [...prev, userMessage])
        // setInput('')
        setLoading(true)
    
        try {
          const response = await axios.post(getApiUrl('chat/'), {
            message: userMessage.content,
            session_id: sessionId,
          })
    
          if (response.status !== 200) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }
    
          const data = response.data
          
          if (data.session_id && !sessionId) {
            setSessionId(data.session_id)
          }
    
          const parsed = parseMessageContent(data.message || 'No response received')
          const assistantMessage: ChatMessage = {
            role: 'assistant',
            content: parsed.text,
            data: parsed.data,
          }
          setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
          console.error('Error sending message:', error)
          const errorMessage: ChatMessage = {
            role: 'assistant',
            content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
          }
          setMessages(prev => [...prev, errorMessage])
        } finally {
          setLoading(false)
        }
      }
      return {
        messages,
        loading,
        sessionId,
        error,
        data,
        parsed,
        assistantMessage,
        errorMessage,
        sendMessage,
        parseMessageContent,
      }
    }
