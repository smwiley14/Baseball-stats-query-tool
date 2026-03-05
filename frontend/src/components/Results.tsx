import { useEffect, useMemo, useRef, useState } from 'react'
import { ChatMessage } from '../types/Chat'
import { Box, Button, CircularProgress, Divider, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Card, Paper } from '@mui/material'
import { resultsStyles } from '../themes/styles/results.styles'
import { barStyles } from '../themes/styles/bar.styles'
import { WelcomeScreen } from './WelcomeScreen'

interface ResultsProps {
  messages: ChatMessage[]
  loading?: boolean
  onExampleClick?: (query: string) => void
}

const renderTable = (data: Array<Record<string, any>>) => {
  if (!data || data.length === 0) return null

  const columns = Object.keys(data[0])

  return (
    <TableContainer component={Paper} sx={resultsStyles.tableContainer} elevation={0}>
      <Table sx={resultsStyles.table}>
        <TableHead sx={resultsStyles.tableHead}>
          <TableRow>
            {columns.map((col) => (
              <TableCell key={col} sx={resultsStyles.tableHeaderCell}>
                {col}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row, idx) => (
            <TableRow key={idx} sx={resultsStyles.tableRow}>
              {columns.map((col) => (
                <TableCell key={col} sx={resultsStyles.tableCell}>
                  {row[col] ?? ''}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

const getSupplementalRows = (message: ChatMessage): Array<Record<string, any>> => {
  const supplementalData = message.supplemental_data?.data
  if (!Array.isArray(supplementalData) || supplementalData.length === 0) {
    return []
  }
  return supplementalData as Array<Record<string, any>>
}

const renderResults = (message: ChatMessage, showSupplemental: boolean, onToggleSupplemental: () => void) => {
  const hasData = message.data && message.data.length > 0
  const hasContent = message.content && message.content.trim()
  const hasSupplemental = Boolean(message.supplemental_data)
  const supplementalRows = getSupplementalRows(message)
  const hasSupplementalRows = supplementalRows.length > 0

  if (hasData) {
    return (
      <Card sx={resultsStyles.resultsCard}>
        {renderTable(message.data!)}
        <Box sx={resultsStyles.metaRow}>
          <Typography variant="caption" sx={resultsStyles.metaText}>
            {message.data?.length ?? 0} rows returned
          </Typography>
        </Box>
        {hasContent && (
          <Box sx={resultsStyles.summaryContainer}>
            <Typography variant="overline" sx={resultsStyles.summaryTitle}>
              Summary
            </Typography>
            <Typography variant="body2" sx={resultsStyles.summaryText}>
              {message.content}
            </Typography>
          </Box>
        )}
        {hasSupplemental && (
          <Box sx={resultsStyles.supplementalSection}>
            <Button
              onClick={onToggleSupplemental}
              variant="outlined"
              size="small"
              sx={resultsStyles.supplementalButton}
            >
              {showSupplemental ? 'Hide additional data' : 'Show additional data'}
            </Button>
            {showSupplemental && hasSupplementalRows && (
              <Box sx={resultsStyles.supplementalTableWrapper}>
                <Typography variant="overline" sx={resultsStyles.summaryTitle}>
                  Additional Data
                </Typography>
                {renderTable(supplementalRows)}
              </Box>
            )}
            {showSupplemental && !hasSupplementalRows && (
              <Typography variant="body2" sx={resultsStyles.summaryText}>
                {message.supplemental_data?.description || message.supplemental_data?.error || 'No additional data available.'}
              </Typography>
            )}
          </Box>
        )}
      </Card>
    )
  }

  if (hasContent) {
    return (
      <Card sx={resultsStyles.resultsCard}>
        <Typography variant="body2" sx={resultsStyles.summaryText}>
          {message.content}
        </Typography>
        {hasSupplemental && (
          <Box sx={resultsStyles.supplementalSection}>
            <Button
              onClick={onToggleSupplemental}
              variant="outlined"
              size="small"
              sx={resultsStyles.supplementalButton}
            >
              {showSupplemental ? 'Hide additional data' : 'Show additional data'}
            </Button>
            {showSupplemental && hasSupplementalRows && (
              <Box sx={resultsStyles.supplementalTableWrapper}>
                <Typography variant="overline" sx={resultsStyles.summaryTitle}>
                  Additional Data
                </Typography>
                {renderTable(supplementalRows)}
              </Box>
            )}
            {showSupplemental && !hasSupplementalRows && (
              <Typography variant="body2" sx={resultsStyles.summaryText}>
                {message.supplemental_data?.description || message.supplemental_data?.error || 'No additional data available.'}
              </Typography>
            )}
          </Box>
        )}
      </Card>
    )
  }

  return (
    <Card sx={resultsStyles.resultsCard}>
      <Typography variant="body2" sx={resultsStyles.emptyState}>
        No results to display
      </Typography>
    </Card>
  )
}

export const Results = ({ messages, loading = false, onExampleClick }: ResultsProps) => {
  const resultsEndRef = useRef<HTMLDivElement>(null)
  const [showSupplemental, setShowSupplemental] = useState(false)

  const latestResult = messages
    .filter(msg => msg.role === 'assistant')
    .slice(-1)[0]
  const latestUserPrompt = messages
    .filter(msg => msg.role === 'user')
    .slice(-1)[0]
  const latestAssistantIndex = useMemo(
    () => messages.map((msg, idx) => ({ msg, idx })).filter(item => item.msg.role === 'assistant').slice(-1)[0]?.idx ?? -1,
    [messages]
  )

  useEffect(() => {
    if (resultsEndRef.current) {
      resultsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading])

  useEffect(() => {
    setShowSupplemental(false)
  }, [latestAssistantIndex])

  return (
    <Box sx={barStyles.messagesContainer}>
      {messages.length === 0 && onExampleClick ? (
        <WelcomeScreen onExampleClick={onExampleClick} />
      ) : (
        <Box>
          {latestUserPrompt && (
            <Box sx={resultsStyles.queryCard}>
              <Typography variant="overline" sx={resultsStyles.queryTitle}>
                Results For
              </Typography>
              <Divider sx={resultsStyles.queryDivider} />
              {latestUserPrompt.content}
            </Box>
          )}
          {latestResult && renderResults(latestResult, showSupplemental, () => setShowSupplemental(prev => !prev))}
          {loading && (
            <Box sx={resultsStyles.loadingContainer}>
              <CircularProgress size={18} />
              <Typography sx={resultsStyles.loadingText}>Running search...</Typography>
            </Box>
          )}
          <div ref={resultsEndRef} />
        </Box>
      )}
    </Box>
  )
}
