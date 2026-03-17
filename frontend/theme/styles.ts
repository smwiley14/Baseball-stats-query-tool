import { createTheme, Theme } from '@mui/material/styles'

export const darkTheme: Theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2f8f46',
      light: '#4aa15d',
      dark: '#1f6a34',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#3a3a3a',
      light: '#4a4a4a',
      dark: '#2a2a2a',
      contrastText: '#e8e8e8',
    },
    background: {
      default: '#2b2b2a',
      paper: '#343433',
    },
    text: {
      primary: '#e8e8e8',
      secondary: '#b5b5b5',
    },
    divider: '#3e3e3e',
    action: {
      hover: 'rgba(255, 255, 255, 0.05)',
      selected: 'rgba(255, 255, 255, 0.08)',
    },
  },
  typography: {
    fontFamily: '"Manrope", "Avenir Next", "IBM Plex Sans", "Segoe UI", sans-serif',
    h1: { color: '#e8e8e8' },
    h2: { color: '#e8e8e8' },
    h3: { color: '#e8e8e8' },
    h4: { color: '#e8e8e8' },
    h5: { color: '#e8e8e8' },
    h6: { color: '#e8e8e8' },
    body1: { color: '#e8e8e8' },
    body2: { color: '#b5b5b5' },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background:
            'radial-gradient(circle at 20% 10%, rgba(255, 255, 255, 0.05) 0%, transparent 45%),' +
            'radial-gradient(circle at 80% 0%, rgba(255, 255, 255, 0.04) 0%, transparent 40%),' +
            'linear-gradient(180deg, #2d2d2c 0%, #262625 100%)',
          color: '#e8e8e8',
        },
        '#root': {
          width: '100%',
          minHeight: '100vh',
        },
        '::selection': {
          background: '#2f8f46',
          color: '#ffffff',
        },
        '*': {
          boxSizing: 'border-box',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#343433',
          borderBottom: '1px solid #3e3e3e',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#343433',
          border: '1px solid #3e3e3e',
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          backgroundColor: '#343433',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#303030',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.04)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: '#3e3e3e',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: '#343433',
          border: '1px solid #3e3e3e',
          color: '#e8e8e8',
          '&:hover': {
            backgroundColor: '#3b3b3b',
            borderColor: '#4a4a4a',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: 'transparent',
            '& fieldset': {
              borderColor: '#3e3e3e',
            },
            '&:hover fieldset': {
              borderColor: '#4a4a4a',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#2f8f46',
            },
          },
          '& .MuiInputBase-input': {
            color: '#e8e8e8',
            '&::placeholder': {
              color: '#b5b5b5',
              opacity: 1,
            },
          },
        },
      },
    },
  },
})
