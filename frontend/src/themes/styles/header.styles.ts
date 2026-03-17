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
    py: 1.5,
    px: {
      xs: 1.8,
      sm: 2.2,
    },
  } as SxProps<Theme>,

  title: {
    fontWeight: 800,
    fontSize: {
      xs: '1.02rem',
      sm: '1.14rem',
    },
    letterSpacing: '-0.01em',
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
    borderRadius: '8px',
    color: '#ffffff',
    border: '1px solid',
    borderColor: 'primary.dark',
    backgroundColor: 'primary.main',
    '& .MuiChip-label': {
      px: 1.1,
    },
  } as SxProps<Theme>,
}
