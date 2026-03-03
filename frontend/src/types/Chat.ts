export interface SupplementalData {
    status?: string
    type?: string
    description?: string
    sql_query?: string
    row_count?: number
    error?: string
    data?: Array<Record<string, unknown>>
}

export interface ChatMessage {
    role: 'user' | 'assistant'
    content: string
    data?: Array<Record<string, any>> // Optional structured data for tables
    supplemental_data?: SupplementalData
}
