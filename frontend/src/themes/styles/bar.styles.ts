import { SxProps, Theme } from '@mui/material/styles'

export const barStyles = {
  container: {
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    padding: {
      xs: 1.5,
      md: 2.5,
    },
    maxWidth: '1080px !important',
    backgroundColor: 'transparent',
  } as SxProps<Theme>,

  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    width: '100%',
    px: {
      xs: 1,
      sm: 2.5,
    },
    py: 2,
    backgroundColor: 'background.paper',
    borderLeft: '1px solid',
    borderRight: '1px solid',
    borderBottom: '1px solid',
    borderBottomLeftRadius: '12px',
    borderBottomRightRadius: '12px',
    borderColor: 'divider',
    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)',
    '&::-webkit-scrollbar': {
      width: '8px',
    },
    '&::-webkit-scrollbar-track': {
      background: 'transparent',
    },
    '&::-webkit-scrollbar-thumb': {
      background: '#4a4a4a',
      borderRadius: '4px',
      '&:hover': {
        background: '#5a5a5a',
      },
    },
  } as SxProps<Theme>,

  welcomeScreen: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    justifyContent: 'center',
    padding: {
      xs: 1.8,
      sm: 2.8,
    },
    textAlign: 'left',
    minHeight: '100%',
  } as SxProps<Theme>,

  welcomeEyebrow: {
    color: 'text.secondary',
    letterSpacing: '0.08em',
    fontWeight: 700,
    mb: 0.4,
  } as SxProps<Theme>,

  welcomeTitle: {
    fontWeight: 800,
    mb: 0.8,
    letterSpacing: '-0.01em',
    maxWidth: 630,
  } as SxProps<Theme>,

  welcomeSubtitle: {
    color: 'text.secondary',
    mb: 2,
    maxWidth: 620,
  } as SxProps<Theme>,

  exampleQueries: {
    width: '100%',
    maxWidth: 700,
    display: 'grid',
    gridTemplateColumns: {
      xs: '1fr',
      md: '1fr 1fr',
    },
    gap: 1,
  } as SxProps<Theme>,

  exampleQuery: {
    justifyContent: 'flex-start',
    textTransform: 'none',
    py: 1.2,
    px: 1.3,
    backgroundColor: 'background.paper',
    border: '1px solid',
    borderColor: 'divider',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    textAlign: 'left',
    fontSize: '0.9375rem',
    color: 'text.primary',
    fontWeight: 600,
    lineHeight: 1.4,
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.22)',
    '&:hover': {
      backgroundColor: 'action.hover',
      borderColor: 'primary.dark',
      transform: 'translateY(-1px)',
    },
  } as SxProps<Theme>,
}
