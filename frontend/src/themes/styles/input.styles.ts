import { SxProps, Theme } from '@mui/material/styles'

export const inputStyles = {
  container: {
    border: '1px solid',
    borderColor: 'divider',
    backgroundColor: 'rgba(255, 255, 255, 0.88)',
    width: '100%',
    borderRadius: '16px',
    padding: {
      xs: 1.1,
      sm: 1.3,
    },
    backdropFilter: 'blur(10px)',
    mb: 1.25,
  } as SxProps<Theme>,

  wrapper: {
    display: 'flex',
    gap: 1,
    alignItems: 'center',
    backgroundColor: '#f7faff',
    border: '1px solid',
    borderColor: 'divider',
    borderRadius: '20px',
    padding: '6px 8px 6px 12px',
    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
    '&:focus-within': {
      borderColor: 'primary.main',
      boxShadow: (theme: Theme) => `0 0 0 3px ${theme.palette.primary.main}20`,
    },
  } as SxProps<Theme>,

  textField: {
    flex: 1,
    '& .MuiInputBase-root': {
      border: 'none',
      fontSize: '0.98rem',
      '& fieldset': {
        border: 'none',
      },
      '&:hover fieldset': {
        border: 'none',
      },
      '&.Mui-focused fieldset': {
        border: 'none',
      },
    },
    '& .MuiInputBase-input': {
      padding: '8px 0',
      lineHeight: 1.4,
    },
  } as SxProps<Theme>,

  sendButton: {
    background: 'linear-gradient(135deg, #0f62fe 0%, #1b7bff 100%)',
    color: '#ffffff',
    width: 38,
    height: 38,
    flexShrink: 0,
    boxShadow: '0 8px 18px rgba(15, 98, 254, 0.25)',
    '&:hover': {
      background: 'linear-gradient(135deg, #0d57e2 0%, #0f62fe 100%)',
    },
    '&:disabled': {
      opacity: 0.55,
      boxShadow: 'none',
    },
  } as SxProps<Theme>,

  footer: {
    mt: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 1,
    px: 0.6,
  } as SxProps<Theme>,

  cancelRow: {
    display: 'flex',
    justifyContent: 'flex-end',
  } as SxProps<Theme>,

  cancelButton: {
    textTransform: 'none',
    minWidth: 'auto',
    px: 1.3,
    py: 0.3,
    borderRadius: '999px',
    color: '#8b2a2a',
    border: '1px solid',
    borderColor: '#f2c1c1',
    backgroundColor: '#fff8f8',
    fontWeight: 700,
    '&:hover': {
      backgroundColor: '#ffecec',
      borderColor: '#e7a8a8',
      color: '#7f2020',
    },
  } as SxProps<Theme>,

  footerHint: {
    color: 'text.secondary',
    fontSize: '0.74rem',
    fontWeight: 600,
  } as SxProps<Theme>,

  footerText: {
    color: 'text.secondary',
    fontSize: '0.74rem',
  } as SxProps<Theme>,
}
