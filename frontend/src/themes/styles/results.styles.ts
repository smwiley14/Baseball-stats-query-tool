import { SxProps, Theme } from '@mui/material/styles'

// Shared tones for the StatMuse-style results view.
const METRIC_BLUE = '#1d4ed8'
const HEADER_BG = '#0f151d'
const ROW_BORDER = '#1e2732'

export const resultsStyles = {
  // --- hero answer banner ---------------------------------------------------
  heroBanner: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    gap: { xs: 1.5, sm: 2.5 },
    borderRadius: '14px',
    background: 'linear-gradient(135deg, #1e40af 0%, #2563eb 55%, #1d4ed8 100%)',
    p: { xs: 2, sm: 2.5 },
    mb: 1.5,
    boxShadow: '0 12px 34px rgba(37, 99, 235, 0.28)',
  } as SxProps<Theme>,

  heroText: {
    flex: 1,
    pr: 4,
    color: '#ffffff',
    fontWeight: 800,
    lineHeight: 1.28,
    letterSpacing: '-0.01em',
    fontSize: { xs: '1.08rem', sm: '1.35rem' },
  } as SxProps<Theme>,

  heroShare: {
    position: 'absolute',
    top: 12,
    right: 12,
    color: '#ffffff',
    backgroundColor: 'rgba(255,255,255,0.16)',
    '&:hover': { backgroundColor: 'rgba(255,255,255,0.3)' },
  } as SxProps<Theme>,

  interpretedAs: {
    color: 'text.secondary',
    fontSize: '0.82rem',
    fontWeight: 500,
    mb: 1.5,
    px: 0.5,
  } as SxProps<Theme>,

  // --- table ----------------------------------------------------------------
  tableContainer: {
    width: '100%',
    overflowX: 'auto',
    borderRadius: '12px',
    border: '1px solid',
    borderColor: 'divider',
    backgroundColor: 'background.paper',
    '&::-webkit-scrollbar': { height: '8px' },
    '&::-webkit-scrollbar-track': { background: 'transparent' },
    '&::-webkit-scrollbar-thumb': { background: '#2c3947', borderRadius: '4px' },
  } as SxProps<Theme>,

  table: {
    width: '100%',
    borderCollapse: 'separate',
    borderSpacing: 0,
  } as SxProps<Theme>,

  tableHeadRow: {} as SxProps<Theme>,

  rankHeaderCell: {
    width: 30,
    backgroundColor: HEADER_BG,
    borderBottom: `1px solid ${ROW_BORDER}`,
    p: 0,
  } as SxProps<Theme>,

  headerCell: {
    py: 1,
    px: 1.5,
    fontWeight: 800,
    fontSize: '0.7rem',
    letterSpacing: '0.04em',
    whiteSpace: 'nowrap',
    color: 'text.secondary',
    backgroundColor: HEADER_BG,
    borderBottom: `1px solid ${ROW_BORDER}`,
    textAlign: 'left',
    cursor: 'default',
  } as SxProps<Theme>,

  headerCellNumeric: {
    textAlign: 'right',
  } as SxProps<Theme>,

  headerCellLabel: {
    position: 'sticky',
    left: 0,
    zIndex: 2,
    backgroundColor: HEADER_BG,
  } as SxProps<Theme>,

  headerCellPrimary: {
    color: '#ffffff',
    backgroundColor: METRIC_BLUE,
    textAlign: 'right',
    borderBottom: `1px solid ${METRIC_BLUE}`,
  } as SxProps<Theme>,

  bodyRow: {
    '&:nth-of-type(even) td': { backgroundColor: 'rgba(255,255,255,0.018)' },
    '&:hover td': { backgroundColor: 'rgba(59,130,246,0.07)' },
  } as SxProps<Theme>,

  rankCell: {
    width: 30,
    px: 0,
    textAlign: 'center',
    color: 'text.secondary',
    fontSize: '0.82rem',
    fontVariantNumeric: 'tabular-nums',
    borderBottom: `1px solid ${ROW_BORDER}`,
  } as SxProps<Theme>,

  nameCell: {
    position: 'sticky',
    left: 0,
    zIndex: 1,
    py: 0.85,
    px: 1.5,
    borderBottom: `1px solid ${ROW_BORDER}`,
    backgroundColor: 'background.paper',
  } as SxProps<Theme>,

  nameInner: {
    display: 'flex',
    alignItems: 'center',
    gap: 1.1,
  } as SxProps<Theme>,

  nameText: {
    fontWeight: 700,
    fontSize: '0.95rem',
    color: 'primary.light',
    whiteSpace: 'nowrap',
  } as SxProps<Theme>,

  dataCell: {
    py: 0.85,
    px: 1.5,
    fontSize: '0.92rem',
    color: 'text.primary',
    whiteSpace: 'nowrap',
    borderBottom: `1px solid ${ROW_BORDER}`,
  } as SxProps<Theme>,

  dataCellNumeric: {
    textAlign: 'right',
    fontVariantNumeric: 'tabular-nums',
    fontFeatureSettings: '"tnum"',
  } as SxProps<Theme>,

  dataCellPrimary: {
    textAlign: 'right',
    fontWeight: 800,
    color: '#ffffff',
    backgroundColor: `${METRIC_BLUE} !important`,
    borderBottom: `1px solid ${METRIC_BLUE}`,
  } as SxProps<Theme>,

  metaText: {
    display: 'block',
    mt: 1,
    px: 0.5,
    color: 'text.secondary',
    fontWeight: 600,
    fontSize: '0.76rem',
  } as SxProps<Theme>,

  // --- fallbacks / summary / supplemental -----------------------------------
  resultsCard: {
    backgroundColor: 'background.paper',
    borderRadius: '12px',
    padding: { xs: 2, sm: 2.5 },
    border: '1px solid',
    borderColor: 'divider',
  } as SxProps<Theme>,

  summaryText: {
    color: 'text.primary',
    lineHeight: 1.6,
    fontSize: '0.96rem',
    whiteSpace: 'pre-wrap',
  } as SxProps<Theme>,

  supplementalSection: {
    mt: 2,
  } as SxProps<Theme>,

  supplementalButton: {
    borderRadius: '8px',
    textTransform: 'none',
    fontWeight: 600,
    borderColor: 'primary.dark',
    color: 'primary.light',
    '&:hover': {
      borderColor: 'primary.main',
      backgroundColor: 'rgba(59,130,246,0.12)',
    },
  } as SxProps<Theme>,

  supplementalTableWrapper: {
    mt: 1.5,
  } as SxProps<Theme>,

  loadingContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
    py: 3,
    px: 0.5,
    opacity: 0.9,
  } as SxProps<Theme>,

  loadingText: {
    fontSize: '0.9rem',
    color: 'text.secondary',
    fontWeight: 600,
  } as SxProps<Theme>,

  emptyState: {
    textAlign: 'center',
    padding: 4,
    color: 'text.secondary',
  } as SxProps<Theme>,
}
