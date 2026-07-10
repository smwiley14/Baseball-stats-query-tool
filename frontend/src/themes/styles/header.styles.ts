import { SxProps, Theme } from '@mui/material/styles'

export const headerStyles = {
  appBar: {
    position: 'sticky',
    top: 0,
    zIndex: 10,
    backgroundColor: 'background.paper',
    color: 'text.primary',
    border: '1px solid',
    borderColor: 'divider',
    borderBottom: '1px solid',
    borderTopLeftRadius: '12px',
    borderTopRightRadius: '12px',
    boxShadow: '0 6px 16px rgba(0, 0, 0, 0.28)',
  } as SxProps<Theme>,

  toolbar: {
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 1,
    py: 1.4,
    px: {
      xs: 1.8,
      sm: 2.2,
    },
  } as SxProps<Theme>,

  brandRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 1.1,
  } as SxProps<Theme>,

  mark: {
    width: 34,
    height: 34,
    borderRadius: '9px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    background: 'linear-gradient(135deg, #2563eb 0%, #f5a524 130%)',
    color: '#0b0f14',
    fontWeight: 800,
    fontSize: '0.95rem',
    letterSpacing: '-0.02em',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
  } as SxProps<Theme>,

  titleGroup: {
    display: 'flex',
    flexDirection: 'column',
    lineHeight: 1.15,
  } as SxProps<Theme>,

  title: {
    fontWeight: 800,
    fontSize: {
      xs: '1.0rem',
      sm: '1.1rem',
    },
    letterSpacing: '-0.01em',
    lineHeight: 1.2,
  } as SxProps<Theme>,

  eyebrow: {
    color: 'text.secondary',
    fontSize: '0.66rem',
    fontWeight: 700,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
  } as SxProps<Theme>,

  subtitle: {
    color: 'text.secondary',
    fontSize: {
      xs: '0.8rem',
      sm: '0.88rem',
    },
  } as SxProps<Theme>,

  statusChip: {
    fontWeight: 700,
    fontSize: '0.7rem',
    borderRadius: '999px',
    color: '#8fd99a',
    border: '1px solid',
    borderColor: 'rgba(74, 222, 128, 0.35)',
    backgroundColor: 'rgba(74, 222, 128, 0.09)',
    '& .MuiChip-label': {
      px: 1.2,
    },
  } as SxProps<Theme>,

  statusDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    backgroundColor: '#4ade80',
    display: 'inline-block',
    mr: 0.75,
    boxShadow: '0 0 0 3px rgba(74, 222, 128, 0.18)',
  } as SxProps<Theme>,
}
