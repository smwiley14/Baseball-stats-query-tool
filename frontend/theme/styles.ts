import { createTheme, Theme } from '@mui/material/styles'

// Data-dashboard palette: cool navy-charcoal ground (not the warm neutral gray
// of a generic chat UI) with a blue/amber duotone — blue for primary actions
// and links, amber reserved for headline stat callouts and record highlights.
const bg = {
  default: '#0b0f14',
  paper: '#131a22',
  raised: '#1a232d',
}
const line = '#242e39'
const ink = {
  primary: '#e7edf3',
  secondary: '#8593a3',
}
const blue = {
  main: '#3b82f6',
  light: '#63a0ff',
  dark: '#1d5fd1',
}
const amber = {
  main: '#f5a524',
  light: '#ffbf55',
  dark: '#c9820f',
}

export const darkTheme: Theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: blue.main,
      light: blue.light,
      dark: blue.dark,
      contrastText: '#ffffff',
    },
    secondary: {
      main: amber.main,
      light: amber.light,
      dark: amber.dark,
      contrastText: '#1a1206',
    },
    background: {
      default: bg.default,
      paper: bg.paper,
    },
    text: {
      primary: ink.primary,
      secondary: ink.secondary,
    },
    divider: line,
    action: {
      hover: 'rgba(255, 255, 255, 0.045)',
      selected: 'rgba(59, 130, 246, 0.12)',
    },
  },
  typography: {
    fontFamily: '"Manrope", "Avenir Next", "IBM Plex Sans", "Segoe UI", sans-serif',
    h1: { color: ink.primary },
    h2: { color: ink.primary },
    h3: { color: ink.primary },
    h4: { color: ink.primary },
    h5: { color: ink.primary },
    h6: { color: ink.primary },
    body1: { color: ink.primary },
    body2: { color: ink.secondary },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background:
            'radial-gradient(circle at 15% 0%, rgba(59, 130, 246, 0.07) 0%, transparent 40%),' +
            'radial-gradient(circle at 85% 15%, rgba(245, 165, 36, 0.045) 0%, transparent 35%),' +
            `linear-gradient(180deg, #0d1218 0%, ${bg.default} 100%)`,
          color: ink.primary,
        },
        '#root': {
          width: '100%',
          minHeight: '100vh',
        },
        '::selection': {
          background: blue.main,
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
          backgroundColor: bg.paper,
          borderBottom: `1px solid ${line}`,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: bg.paper,
          border: `1px solid ${line}`,
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          backgroundColor: bg.paper,
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: bg.raised,
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(59, 130, 246, 0.055)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: line,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: bg.raised,
          border: `1px solid ${line}`,
          color: ink.primary,
          '&:hover': {
            backgroundColor: '#202b37',
            borderColor: '#2c3947',
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
              borderColor: line,
            },
            '&:hover fieldset': {
              borderColor: '#2c3947',
            },
            '&.Mui-focused fieldset': {
              borderColor: blue.main,
            },
          },
          '& .MuiInputBase-input': {
            color: ink.primary,
            '&::placeholder': {
              color: ink.secondary,
              opacity: 1,
            },
          },
        },
      },
    },
  },
})
