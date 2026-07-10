import { AppBar, Box, Chip, Toolbar, Typography } from '@mui/material'
import { headerStyles } from '../themes/styles/header.styles'

export const Header = () => {
  return (
    <AppBar position="sticky" elevation={0} sx={headerStyles.appBar}>
      <Toolbar sx={headerStyles.toolbar}>
        <Box sx={headerStyles.brandRow}>
          <Box sx={headerStyles.mark}>BB</Box>
          <Box sx={headerStyles.titleGroup}>
            <Typography sx={headerStyles.eyebrow}>MLB Data</Typography>
            <Typography variant="h6" component="h1" sx={headerStyles.title}>
              Baseball Stats Search
            </Typography>
          </Box>
        </Box>
        <Chip
          label={<><Box component="span" sx={headerStyles.statusDot} />Live query engine</>}
          size="small"
          sx={headerStyles.statusChip}
        />
      </Toolbar>
    </AppBar>
  )
}
