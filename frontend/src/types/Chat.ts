export interface ChatMessage {
    role: 'user' | 'assistant'
    content: string
    data?: Array<Record<string, any>> // Optional structured data for tables
}