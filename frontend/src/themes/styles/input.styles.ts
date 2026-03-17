import { SxProps, Theme } from '@mui/material/styles'

export const inputStyles = {
  container: {
    border: '1px solid',
    borderColor: 'divider',
    backgroundColor: 'background.paper',
    width: '100%',
    borderRadius: '12px',
    padding: {
      xs: 1.1,
      sm: 1.3,
    },
    mb: 1.25,
  } as SxProps<Theme>,

  wrapper: {
    display: 'flex',
    gap: 1,
    alignItems: 'center',
    backgroundColor: 'background.default',
    border: '1px solid',
    borderColor: 'divider',
    borderRadius: '8px',
    padding: '6px 8px 6px 12px',
    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
    '&:focus-within': {
      borderColor: 'primary.main',
      boxShadow: (theme: Theme) => `0 0 0 3px ${theme.palette.primary.main}30`,
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
      color: 'text.primary',
      '&::placeholder': {
        color: 'text.secondary',
        opacity: 1,
      },
    },
  } as SxProps<Theme>,

  sendButton: {
    background: 'linear-gradient(135deg, #2f8f46 0%, #3ea85a 100%)',
    color: '#ffffff',
    width: 38,
    height: 38,
    flexShrink: 0,
    borderRadius: '6px',
    boxShadow: '0 8px 18px rgba(47, 143, 70, 0.25)',
    '&:hover': {
      background: 'linear-gradient(135deg, #2a7e3d 0%, #2f8f46 100%)',
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
    borderRadius: '8px',
    color: '#d9a2a2',
    border: '1px solid',
    borderColor: '#6b3a3a',
    backgroundColor: '#3c2a2a',
    fontWeight: 700,
    '&:hover': {
      backgroundColor: '#4a2f2f',
      borderColor: '#7a4242',
      color: '#f0b5b5',
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
