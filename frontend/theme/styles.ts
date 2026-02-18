import { createTheme, Theme } from '@mui/material/styles'

export const darkTheme: Theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#19c37d', // Keep the green for consistency
      light: '#4dd4a0',
      dark: '#138f5e',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ab68ff', // Keep the purple for consistency
      light: '#c495ff',
      dark: '#8a4fd9',
      contrastText: '#ffffff',
    },
    background: {
      default: '#1a1a1f', // Very dark gray/charcoal
      paper: '#25252d', // Slightly lighter for cards/containers
    },
    text: {
      primary: '#e5e5e6', // Light gray for primary text
      secondary: '#9ca3af', // Medium gray for secondary text
    },
    divider: '#2d2d35', // Subtle divider color
    action: {
      hover: 'rgba(255, 255, 255, 0.08)', // Subtle hover effect
      selected: 'rgba(255, 255, 255, 0.12)',
    },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif',
    h1: {
      color: '#e5e5e6',
    },
    h2: {
      color: '#e5e5e6',
    },
    h3: {
      color: '#e5e5e6',
    },
    h4: {
      color: '#e5e5e6',
    },
    h5: {
      color: '#e5e5e6',
    },
    h6: {
      color: '#e5e5e6',
    },
    body1: {
      color: '#e5e5e6',
    },
    body2: {
      color: '#9ca3af',
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#25252d',
          borderBottom: '1px solid #2d2d35',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#25252d',
          border: '1px solid #2d2d35',
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#1a1a1f',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: '#2d2d35',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: '#25252d',
          border: '1px solid #2d2d35',
          color: '#e5e5e6',
          '&:hover': {
            backgroundColor: '#2d2d35',
            borderColor: '#3d3d45',
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
              borderColor: '#2d2d35',
            },
            '&:hover fieldset': {
              borderColor: '#3d3d45',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#19c37d',
            },
          },
          '& .MuiInputBase-input': {
            color: '#e5e5e6',
            '&::placeholder': {
              color: '#9ca3af',
              opacity: 1,
            },
          },
        },
      },
    },
  },
})
