import { createTheme, Theme } from '@mui/material/styles'

export const darkTheme: Theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0f62fe',
      light: '#4f87ff',
      dark: '#0043ce',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#3a3f4b',
      light: '#636a79',
      dark: '#232833',
      contrastText: '#f7f9fc',
    },
    background: {
      default: '#f2f6ff',
      paper: '#ffffff',
    },
    text: {
      primary: '#131722',
      secondary: '#5d6472',
    },
    divider: '#d4ddee',
    action: {
      hover: 'rgba(15, 98, 254, 0.06)',
      selected: 'rgba(15, 98, 254, 0.12)',
    },
  },
  typography: {
    fontFamily: '"Manrope", "Avenir Next", "IBM Plex Sans", "Segoe UI", sans-serif',
    h1: { color: '#131722' },
    h2: { color: '#131722' },
    h3: { color: '#131722' },
    h4: { color: '#131722' },
    h5: { color: '#131722' },
    h6: { color: '#131722' },
    body1: { color: '#131722' },
    body2: { color: '#5d6472' },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #d8deea',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          border: '1px solid #d8deea',
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#f4f7ff',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(15, 98, 254, 0.03)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: '#d8deea',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          border: '1px solid #d8deea',
          color: '#131722',
          '&:hover': {
            backgroundColor: '#f6f9ff',
            borderColor: '#bfd0ff',
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
              borderColor: '#d8deea',
            },
            '&:hover fieldset': {
              borderColor: '#bfd0ff',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#0f62fe',
            },
          },
          '& .MuiInputBase-input': {
            color: '#131722',
            '&::placeholder': {
              color: '#5d6472',
              opacity: 1,
            },
          },
        },
      },
    },
  },
})
