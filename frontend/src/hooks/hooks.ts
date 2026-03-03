import { useRef, useState } from 'react'
import { ChatMessage, SupplementalData } from '../types/Chat'
import axios from 'axios'
import { getApiUrl } from '../../config/config'

export const useHooks = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [loading, setLoading] = useState(false)
    const [sessionId, setSessionId] = useState<string | null>(null)
    const abortControllerRef = useRef<AbortController | null>(null)
    const sessionIdRef = useRef<string | null>(null)

    const parseMessageContent = (content: string): { text: string; data?: Array<Record<string, any>> } => {
        const lines = content.split('\n').filter(line => line.trim())
        
        if (lines.length > 1 && lines.every(line => line.includes(':'))) {
          try {
            const data: Array<Record<string, any>> = []
            for (const line of lines) {
              const row: Record<string, any> = {}
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
          }
        }
        
        return { text: content }
      }
    
    const sendMessage = async (input: string) => {
        if (!input.trim() || loading) return
        const activeSessionId = sessionId ?? crypto.randomUUID()
        if (!sessionId) {
          setSessionId(activeSessionId)
        }
        sessionIdRef.current = activeSessionId
    
        const userMessage: ChatMessage = { role: 'user', content: input }
        setMessages(prev => [...prev, userMessage])
        const controller = new AbortController()
        abortControllerRef.current = controller
        setLoading(true)
    
        try {
          const response = await axios.post(getApiUrl('chat/'), {
            message: userMessage.content,
            session_id: activeSessionId,
          }, {
            signal: controller.signal,
          })
    
          if (response.status !== 200) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }
    
          const data = response.data as {
            message?: string
            session_id?: string
            table_data?: Array<Record<string, unknown>>
            summary?: string
            metadata?: Record<string, unknown>
            supplemental_data?: SupplementalData
          }
          
          if (data.session_id && !sessionId) {
            setSessionId(data.session_id)
            sessionIdRef.current = data.session_id
          }
    
          // Use API's table_data and summary when present; otherwise fall back to parsing message
          const content = data.summary ?? data.message ?? 'No response received'
          const tableData = data.table_data && Array.isArray(data.table_data) && data.table_data.length > 0
            ? data.table_data as Array<Record<string, any>>
            : undefined
          const parsed = tableData ? { text: content, data: tableData } : parseMessageContent(content)
          
          const assistantMessage: ChatMessage = {
            role: 'assistant',
            content: parsed.text,
            data: parsed.data ?? tableData ,
            supplemental_data: data.supplemental_data,
          }
          console.log('assistantMessage', assistantMessage)
          setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
          if (axios.isAxiosError(error) && error.code === 'ERR_CANCELED') {
            return
          }
          console.error('Error sending message:', error)
          const errorMessage: ChatMessage = {
            role: 'assistant',
            content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
          }
          setMessages(prev => [...prev, errorMessage])
        } finally {
          abortControllerRef.current = null
          setLoading(false)
        }
    }

    const cancelQuery = async () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      abortControllerRef.current = null
      setLoading(false)
      const activeSessionId = sessionIdRef.current
      if (!activeSessionId) {
        return
      }
      try {
        await axios.post(getApiUrl('chat/cancel/'), { session_id: activeSessionId })
      } catch (error) {
        console.error('Error cancelling query:', error)
      }
    }

    return {
        messages,
        loading,
        sessionId,
        sendMessage,
        cancelQuery,
        parseMessageContent,
    }
}
