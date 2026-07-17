import { useEffect, useMemo, useRef, useState } from 'react'
import { ChatMessage } from '../types/Chat'
import { Box, Button, CircularProgress, IconButton, Tooltip, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Card, Paper } from '@mui/material'
import type { SxProps, Theme } from '@mui/material/styles'
import { IosShare } from '@mui/icons-material'
import { resultsStyles } from '../themes/styles/results.styles'
import { barStyles } from '../themes/styles/bar.styles'
import { WelcomeScreen } from './WelcomeScreen'

interface ResultsProps {
  messages: ChatMessage[]
  loading?: boolean
  onExampleClick?: (query: string) => void
}

// --- value helpers -------------------------------------------------------

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
    if (values.length > 0 && values.every(isNumericValue)) numeric.add(col)
  }
  return numeric
}

const isSeasonColumn = (col: string) => /\b(season|year|yr)\b/i.test(col)
// AVG/OBP/SLG/OPS: shown to 3 decimals with no leading zero (.362, 1.422).
const isBattingRate = (col: string) => /average|percentage|\bops\b|\bobp\b|\bslg\b|\bavg\b/i.test(col)

// Baseball-style value formatting:
//  - counting stats get thousands separators (1,793)
//  - years never do (2020)
//  - AVG/OBP/SLG/OPS show 3 decimals, leading zero dropped (.362), values >= 1 kept (1.422)
//  - other rates (ERA/WHIP/K9) keep their leading digit (0.866, 3.02)
const formatStat = (value: any, col: string): string => {
  if (value === null || value === undefined || value === '') return ''
  if (!isNumericValue(value)) return String(value)
  const num = Number(String(value).replace(/,/g, ''))
  if (!Number.isFinite(num)) return String(value)
  if (isSeasonColumn(col)) return String(Math.trunc(num))
  if (Number.isInteger(num)) return num.toLocaleString('en-US')
  if (isBattingRate(col)) {
    let s = num.toFixed(3)
    if (num >= 0 && num < 1) s = s.replace(/^0/, '')
    else if (num > -1 && num < 0) s = s.replace(/^-0/, '-')
    return s
  }
  return parseFloat(num.toFixed(3)).toString()
}

// Standard stat abbreviations for column headers. Full name shown on hover.
const ABBREV: Record<string, string> = {
  'team name': 'TEAM', team: 'TEAM', season: 'SZN',
  'games played': 'G', games: 'G',
  'plate appearances': 'PA', 'at bats': 'AB', runs: 'R', hits: 'H',
  singles: '1B', doubles: '2B', triples: '3B', 'home runs': 'HR',
  rbis: 'RBI', rbi: 'RBI', walks: 'BB', strikeouts: 'SO', 'stolen bases': 'SB',
  'caught stealing': 'CS', 'hit by pitch': 'HBP', 'total bases': 'TB',
  'batting average': 'AVG', 'on base percentage': 'OBP', 'slugging percentage': 'SLG', ops: 'OPS',
  'innings pitched': 'IP', wins: 'W', losses: 'L', saves: 'SV',
  'walks allowed': 'BB', 'hits allowed': 'H', 'earned runs': 'ER', era: 'ERA', whip: 'WHIP',
  'k per 9': 'K/9', 'bb per 9': 'BB/9', 'home runs allowed': 'HR',
  'game date': 'DATE', opponent: 'OPP',
  'career hr': 'HR', 'career ab': 'AB', 'career h': 'H', 'career rbi': 'RBI',
  'career r': 'R', 'career sb': 'SB', 'career avg': 'AVG', 'career obp': 'OBP', 'career slg': 'SLG',
}
const abbrev = (col: string) => ABBREV[col.toLowerCase()] ?? col

// --- avatar (initials in a colored circle, deterministic per name) --------

const initials = (name: any): string => {
  const words = String(name ?? '').trim().split(/\s+/).filter(Boolean)
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase()
  return String(name ?? '?').slice(0, 2).toUpperCase()
}
const avatarHue = (name: any): number => {
  let h = 0
  for (const ch of String(name ?? '')) h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
}
const Avatar = ({ name, size = 30 }: { name: any; size?: number }) => (
  <Box
    sx={{
      width: size, height: size, minWidth: size, borderRadius: '50%',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontWeight: 800, fontSize: size * 0.36, letterSpacing: '0.01em', color: '#fff',
      background: `linear-gradient(150deg, hsl(${avatarHue(name)},48%,46%), hsl(${(avatarHue(name) + 24) % 360},48%,34%))`,
      boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.12)',
    }}
  >
    {initials(name)}
  </Box>
)

// --- table ----------------------------------------------------------------

const renderTable = (
  data: Array<Record<string, any>>,
  opts: { primaryMetric?: string; withRankAndAvatar?: boolean } = {},
) => {
  if (!data || data.length === 0) return null

  const original = Object.keys(data[0])
  const numericColumns = getNumericColumns(data, original)
  const labelCol = original.find((c) => !numericColumns.has(c)) // entity name, if any
  const primary = opts.primaryMetric && original.includes(opts.primaryMetric) && opts.primaryMetric !== labelCol
    ? opts.primaryMetric
    : undefined
  const showEntity = Boolean(opts.withRankAndAvatar && labelCol)

  // Column order: name, [primary metric], then the rest in original order.
  const rest = original.filter((c) => c !== labelCol && c !== primary)
  const columns = [
    ...(labelCol ? [labelCol] : []),
    ...(primary ? [primary] : []),
    ...rest,
  ]

  return (
    <TableContainer component={Paper} sx={resultsStyles.tableContainer} elevation={0}>
      <Table sx={resultsStyles.table} size="small">
        <TableHead>
          <TableRow sx={resultsStyles.tableHeadRow}>
            {showEntity && <TableCell sx={resultsStyles.rankHeaderCell} />}
            {columns.map((col) => {
              const isNum = col !== labelCol && numericColumns.has(col)
              const isPrimary = col === primary
              return (
                <Tooltip key={col} title={col} arrow disableInteractive>
                  <TableCell
                    sx={[
                      resultsStyles.headerCell,
                      isNum && resultsStyles.headerCellNumeric,
                      col === labelCol && resultsStyles.headerCellLabel,
                      isPrimary && resultsStyles.headerCellPrimary,
                    ] as SxProps<Theme>}
                  >
                    {col === labelCol ? 'NAME' : abbrev(col)}
                  </TableCell>
                </Tooltip>
              )
            })}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row, idx) => (
            <TableRow key={idx} sx={resultsStyles.bodyRow}>
              {showEntity && (
                <TableCell sx={resultsStyles.rankCell}>{idx + 1}</TableCell>
              )}
              {columns.map((col) => {
                const isNum = numericColumns.has(col)
                const isPrimary = col === primary
                if (col === labelCol) {
                  return (
                    <TableCell key={col} sx={resultsStyles.nameCell}>
                      <Box sx={resultsStyles.nameInner}>
                        {showEntity && <Avatar name={row[col]} />}
                        <Typography component="span" sx={resultsStyles.nameText}>{row[col]}</Typography>
                      </Box>
                    </TableCell>
                  )
                }
                return (
                  <TableCell
                    key={col}
                    sx={[
                      resultsStyles.dataCell,
                      isNum && resultsStyles.dataCellNumeric,
                      isPrimary && resultsStyles.dataCellPrimary,
                    ] as SxProps<Theme>}
                  >
                    {formatStat(row[col], col)}
                  </TableCell>
                )
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

// --- hero answer banner ---------------------------------------------------

const HeroBanner = ({ summary, entity }: { summary: string; entity?: any }) => {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(summary)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch { /* clipboard unavailable */ }
  }
  return (
    <Box sx={resultsStyles.heroBanner}>
      {entity !== undefined && entity !== null && entity !== '' && (
        <Avatar name={entity} size={64} />
      )}
      <Typography sx={resultsStyles.heroText}>{summary}</Typography>
      <Tooltip title={copied ? 'Copied' : 'Copy answer'} arrow>
        <IconButton onClick={copy} size="small" sx={resultsStyles.heroShare} aria-label="Copy answer">
          <IosShare sx={{ fontSize: 18 }} />
        </IconButton>
      </Tooltip>
    </Box>
  )
}

const getSupplementalRows = (message: ChatMessage): Array<Record<string, any>> => {
  const supplementalData = message.supplemental_data?.data
  if (!Array.isArray(supplementalData) || supplementalData.length === 0) return []
  return supplementalData as Array<Record<string, any>>
}

const firstLabelValue = (data?: Array<Record<string, any>>): any => {
  if (!data || data.length === 0) return undefined
  const cols = Object.keys(data[0])
  const numeric = getNumericColumns(data, cols)
  const labelCol = cols.find((c) => !numeric.has(c))
  return labelCol ? data[0][labelCol] : undefined
}

const renderBody = (message: ChatMessage, showSupplemental: boolean, onToggleSupplemental: () => void) => {
  const hasData = message.data && message.data.length > 0
  const hasSupplemental = Boolean(message.supplemental_data)
  const supplementalRows = getSupplementalRows(message)

  return (
    <>
      {hasData && renderTable(message.data!, { primaryMetric: message.primaryMetric, withRankAndAvatar: true })}
      {hasData && (
        <Typography variant="caption" sx={resultsStyles.metaText}>
          {message.data!.length} {message.data!.length === 1 ? 'row' : 'rows'}
        </Typography>
      )}

      {!hasData && message.content && (
        <Card sx={resultsStyles.resultsCard}>
          <Typography variant="body2" sx={resultsStyles.summaryText}>{message.content}</Typography>
        </Card>
      )}

      {hasSupplemental && (
        <Box sx={resultsStyles.supplementalSection}>
          <Button onClick={onToggleSupplemental} variant="outlined" size="small" sx={resultsStyles.supplementalButton}>
            {showSupplemental ? 'Hide game log' : 'Show game log'}
          </Button>
          {showSupplemental && supplementalRows.length > 0 && (
            <Box sx={resultsStyles.supplementalTableWrapper}>{renderTable(supplementalRows)}</Box>
          )}
          {showSupplemental && supplementalRows.length === 0 && (
            <Typography variant="body2" sx={resultsStyles.summaryText}>
              {message.supplemental_data?.description || message.supplemental_data?.error || 'No additional data available.'}
            </Typography>
          )}
        </Box>
      )}
    </>
  )
}

export const Results = ({ messages, loading = false, onExampleClick }: ResultsProps) => {
  const resultsEndRef = useRef<HTMLDivElement>(null)
  const [showSupplemental, setShowSupplemental] = useState(false)

  const latestResult = messages.filter((m) => m.role === 'assistant').slice(-1)[0]
  const latestUserPrompt = messages.filter((m) => m.role === 'user').slice(-1)[0]
  const latestAssistantIndex = useMemo(
    () => messages.map((m, idx) => ({ m, idx })).filter((x) => x.m.role === 'assistant').slice(-1)[0]?.idx ?? -1,
    [messages],
  )

  useEffect(() => {
    resultsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => { setShowSupplemental(false) }, [latestAssistantIndex])

  if (messages.length === 0 && onExampleClick) {
    return (
      <Box sx={barStyles.messagesContainer}>
        <WelcomeScreen onExampleClick={onExampleClick} />
      </Box>
    )
  }

  const heroEntity = firstLabelValue(latestResult?.data)

  return (
    <Box sx={barStyles.messagesContainer}>
      <Box>
        {loading ? (
          <>
            {latestUserPrompt && (
              <Typography sx={resultsStyles.interpretedAs}>{latestUserPrompt.content}</Typography>
            )}
            <Box sx={resultsStyles.loadingContainer}>
              <CircularProgress size={18} />
              <Typography sx={resultsStyles.loadingText}>Running search…</Typography>
            </Box>
          </>
        ) : latestResult ? (
          <>
            {latestResult.content && <HeroBanner summary={latestResult.content} entity={heroEntity} />}
            {latestUserPrompt && (
              <Typography sx={resultsStyles.interpretedAs}>
                Searched: {latestUserPrompt.content}
              </Typography>
            )}
            {renderBody(latestResult, showSupplemental, () => setShowSupplemental((p) => !p))}
          </>
        ) : null}
        <div ref={resultsEndRef} />
      </Box>
    </Box>
  )
}
