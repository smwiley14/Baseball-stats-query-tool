import { TextField, IconButton, Box, Typography, Button } from '@mui/material'
import { Search } from '@mui/icons-material'
import { inputStyles } from '../themes/styles/input.styles'

interface InputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onCancel: () => void
  loading?: boolean
}

export const Input = ({ value, onChange, onSend, onCancel, loading = false }: InputProps) => {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (value.trim() && !loading) {
        onSend()
      }
    }
  }

  return (
    <Box sx={inputStyles.container}>
      <Box sx={inputStyles.wrapper}>
        <TextField
          value={value}
          onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Search baseball stats..."
          disabled={loading}
          variant="outlined"
          sx={inputStyles.textField}
        />
        <IconButton
          onClick={onSend}
          disabled={loading || !value.trim()}
          aria-label="Run search"
          sx={inputStyles.sendButton}
        >
          <Search sx={{ fontSize: 20 }} />
        </IconButton>
      </Box>
      <Box sx={inputStyles.footer}>
        <Typography variant="caption" sx={inputStyles.footerHint}>
          Press Enter to run search.
        </Typography>
        {loading && (
          <Box sx={inputStyles.cancelRow}>
            <Button onClick={onCancel} size="small" sx={inputStyles.cancelButton}>
              Cancel
            </Button>
          </Box>
        )}
        <Typography variant="caption" sx={inputStyles.footerText}>
          Results may contain approximation or incomplete data.
        </Typography>
      </Box>
    </Box>
  )
}
