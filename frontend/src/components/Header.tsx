import { AppBar, Box, Chip, Toolbar, Typography } from '@mui/material'
import { headerStyles } from '../themes/styles/header.styles'

export const Header = () => {
  return (
    <AppBar position="sticky" elevation={0} sx={headerStyles.appBar}>
      <Toolbar sx={headerStyles.toolbar}>
        <Box>
          <Typography variant="h6" component="h1" sx={headerStyles.title}>
            Baseball Stats Search
          </Typography>
          <Typography variant="body2" sx={headerStyles.subtitle}>
            Search one question at a time and view a structured result.
          </Typography>
        </Box>
        <Chip label="Search" size="small" sx={headerStyles.statusChip} />
      </Toolbar>
    </AppBar>
  )
}
