import { SxProps, Theme } from '@mui/material/styles'

export const resultsStyles = {
  container: {
    flex: 1,
    overflowY: 'auto',
    width: '100%',
    padding: 3,
    backgroundColor: 'background.default',
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
  } as SxProps<Theme>,

  resultsCard: {
    backgroundColor: 'background.paper',
    borderRadius: '18px',
    padding: {
      xs: 2,
      sm: 2.5,
    },
    boxShadow: '0 10px 30px rgba(17, 24, 39, 0.06)',
    border: '1px solid',
    borderColor: 'divider',
  } as SxProps<Theme>,

  queryCard: {
    mb: 1.5,
    borderRadius: '16px',
    border: '1px solid',
    borderColor: '#c9d7fb',
    backgroundColor: '#f5f8ff',
    py: 1.25,
    px: 1.5,
    color: 'text.primary',
    fontWeight: 600,
    boxShadow: '0 3px 10px rgba(17, 24, 39, 0.04)',
  } as SxProps<Theme>,

  queryTitle: {
    color: '#4f5f80',
    fontSize: '0.72rem',
    letterSpacing: '0.08em',
    fontWeight: 700,
  } as SxProps<Theme>,

  queryDivider: {
    my: 0.6,
    borderColor: '#dde6fb',
  } as SxProps<Theme>,

  tableContainer: {
    width: '100%',
    overflowX: 'auto',
    mb: 2,
    borderRadius: '12px',
    border: '1px solid',
    borderColor: 'divider',
  } as SxProps<Theme>,

  table: {
    minWidth: 650,
    fontSize: '0.89rem',
  } as SxProps<Theme>,

  tableHead: {
    backgroundColor: 'background.default',
  } as SxProps<Theme>,

  tableHeaderCell: {
    fontWeight: 600,
    whiteSpace: 'nowrap',
    color: 'text.primary',
    backgroundColor: 'background.default',
    borderBottom: '2px solid',
    borderColor: 'divider',
  } as SxProps<Theme>,

  tableCell: {
    color: 'text.primary',
    borderBottom: '1px solid',
    borderColor: 'divider',
  } as SxProps<Theme>,

  tableRow: {
    '&:nth-of-type(even)': {
      backgroundColor: '#fbfcff',
    },
    '&:hover': {
      backgroundColor: 'action.hover',
    },
    '&:last-child td': {
      borderBottom: 0,
    },
  } as SxProps<Theme>,

  summaryContainer: {
    mt: 1.8,
    pt: 1.6,
    borderTop: '1px solid',
    borderColor: 'divider',
  } as SxProps<Theme>,

  summaryTitle: {
    fontWeight: 600,
    mb: 1,
    color: 'text.primary',
    fontSize: '0.875rem',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  } as SxProps<Theme>,

  summaryText: {
    color: 'text.primary',
    lineHeight: 1.65,
    fontSize: '0.96rem',
    whiteSpace: 'pre-wrap',
  } as SxProps<Theme>,

  metaRow: {
    mt: 0.4,
    mb: 0.1,
  } as SxProps<Theme>,

  metaText: {
    color: 'text.secondary',
    fontWeight: 600,
  } as SxProps<Theme>,

  supplementalSection: {
    mt: 2,
    pt: 2,
    borderTop: '1px solid',
    borderColor: 'divider',
  } as SxProps<Theme>,

  supplementalButton: {
    borderRadius: '999px',
    textTransform: 'none',
    fontWeight: 600,
    borderColor: '#bfd0ff',
    color: 'primary.main',
    '&:hover': {
      borderColor: 'primary.main',
      backgroundColor: 'rgba(15, 98, 254, 0.04)',
    },
  } as SxProps<Theme>,

  supplementalTableWrapper: {
    mt: 1.5,
  } as SxProps<Theme>,

  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 1,
    padding: 3,
    opacity: 0.9,
  } as SxProps<Theme>,

  loadingText: {
    fontSize: '0.86rem',
    color: 'text.secondary',
    fontWeight: 600,
  } as SxProps<Theme>,

  emptyState: {
    textAlign: 'center',
    padding: 4,
    color: 'text.secondary',
  } as SxProps<Theme>,
}
