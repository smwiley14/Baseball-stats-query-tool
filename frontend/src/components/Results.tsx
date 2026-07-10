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

// A column is treated as numeric only if every non-empty value in it parses
// as a number — used to right-align + tabular-num those columns like a real
// stats table, without misclassifying things like "162" game IDs vs prose.
const isNumericValue = (value: any): boolean => {
  if (value === null || value === undefined || value === '') return false
  if (typeof value === 'number') return true
  if (typeof value !== 'string') return false
  return /^-?\d[\d,]*\.?\d*$/.test(value.trim())
}

const getNumericColumns = (data: Array<Record<string, any>>, columns: string[]): Set<string> => {
  const numeric = new Set<string>()
  for (const col of columns) {
    const values = data.map((row) => row[col]).filter((v) => v !== null && v !== undefined && v !== '')
    if (values.length > 0 && values.every(isNumericValue)) {
      numeric.add(col)
    }
  }
  return numeric
}

// Display formatter for cell values. Baseball stats are at most 3 decimals
// (AVG/OBP/SLG/OPS = .3f, ERA/WHIP = .2-.3f), but raw SQL sometimes returns
// long repeating floats (e.g. innings as 538.6666666666667). Round any
// non-integer numeric to 3 decimals and trim trailing zeros; leave integers,
// non-numeric strings (names, dates), and years untouched.
const formatCellValue = (value: any): any => {
  if (value === null || value === undefined || value === '') return ''
  if (!isNumericValue(value)) return value
  const str = String(value)
  // No decimal point -> leave untouched (years, counts, all-digit ids) so we
  // never strip leading zeros from an identifier.
  if (!str.includes('.')) return value
  const num = Number(str.replace(/,/g, ''))
  if (!Number.isFinite(num)) return value
  // 536.0000000000 -> "536"; 538.6666667 -> "538.667"; 0.2470 -> "0.247".
  if (Number.isInteger(num)) return String(num)
  return parseFloat(num.toFixed(3)).toString()
}

const renderTable = (data: Array<Record<string, any>>) => {
  if (!data || data.length === 0) return null

  const columns = Object.keys(data[0])
  const numericColumns = getNumericColumns(data, columns)

  return (
    <TableContainer component={Paper} sx={resultsStyles.tableContainer} elevation={0}>
      <Table sx={resultsStyles.table}>
        <TableHead sx={resultsStyles.tableHead}>
          <TableRow>
            {columns.map((col) => (
              <TableCell
                key={col}
                sx={[
                  resultsStyles.tableHeaderCell,
                  numericColumns.has(col) ? resultsStyles.tableHeaderCellNumeric : {},
                ]}
              >
                {col}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row, idx) => (
            <TableRow key={idx} sx={resultsStyles.tableRow}>
              {columns.map((col) => (
                <TableCell
                  key={col}
                  sx={[
                    resultsStyles.tableCell,
                    numericColumns.has(col) ? resultsStyles.tableCellNumeric : {},
                  ]}
                >
                  {formatCellValue(row[col])}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

// A single row with one label column and exactly one numeric column reads as
// a "leader" answer (e.g. Player Name + Career HR) — worth a big scoreboard-
// style number instead of a one-row table. Anything wider/taller falls back
// to the regular table so we're not guessing at data we don't understand.
const renderHeadlineOrTable = (data: Array<Record<string, any>>) => {
  const columns = Object.keys(data[0])
  const numericColumns = getNumericColumns(data, columns)
  const labelColumns = columns.filter((col) => !numericColumns.has(col))

  if (data.length === 1 && numericColumns.size === 1 && labelColumns.length === 1) {
    const valueCol = [...numericColumns][0]
    const labelCol = labelColumns[0]
    return (
      <Box sx={resultsStyles.headlineCard}>
        <Typography sx={resultsStyles.headlineValue}>{formatCellValue(data[0][valueCol])}</Typography>
        <Box sx={resultsStyles.headlineMeta}>
          <Typography sx={resultsStyles.headlineLabel}>{valueCol}</Typography>
          <Typography sx={resultsStyles.headlineEntity}>{data[0][labelCol]}</Typography>
        </Box>
      </Box>
    )
  }

  return renderTable(data)
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
        {renderHeadlineOrTable(message.data!)}
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
