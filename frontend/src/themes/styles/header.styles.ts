import { SxProps, Theme } from '@mui/material/styles'

export const headerStyles = {
  appBar: {
    position: 'sticky',
    top: 0,
    zIndex: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.88)',
    backdropFilter: 'blur(10px)',
    color: 'text.primary',
    border: '1px solid',
    borderColor: 'divider',
    borderBottom: '1px solid',
    borderTopLeftRadius: '20px',
    borderTopRightRadius: '20px',
    boxShadow: 'none',
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
    borderRadius: '999px',
    color: '#0d4fd1',
    border: '1px solid #bfd0ff',
    backgroundColor: '#eef4ff',
    '& .MuiChip-label': {
      px: 1.1,
    },
  } as SxProps<Theme>,
}
