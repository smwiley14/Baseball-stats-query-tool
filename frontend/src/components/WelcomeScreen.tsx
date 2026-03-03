import { Box, Typography, Stack, Button } from '@mui/material'
import { barStyles } from '../themes/styles/bar.styles'

interface WelcomeScreenProps {
  onExampleClick: (query: string) => void
}

const exampleQueries = [
  "Who leads MLB all-time in home runs?",
  "Top 10 qualified OPS seasons all-time",
  "Which pitchers had the most strikeouts in 2020?",
  "How many home runs did each team hit in 2020?",
]

export const WelcomeScreen = ({ onExampleClick }: WelcomeScreenProps) => {
  return (
    <Box sx={barStyles.welcomeScreen}>
      <Typography variant="overline" sx={barStyles.welcomeEyebrow}>
        Explore
      </Typography>
      <Typography variant="h5" component="h2" sx={barStyles.welcomeTitle}>
        Search baseball stats in plain English
      </Typography>
      <Typography variant="body1" sx={barStyles.welcomeSubtitle}>
        Try a starter query or type your own below.
      </Typography>
      <Stack spacing={1} sx={barStyles.exampleQueries}>
        {exampleQueries.map((query) => (
          <Button
            key={query}
            onClick={() => onExampleClick(query)}
            sx={barStyles.exampleQuery}
          >
            {query}
          </Button>
        ))}
      </Stack>
    </Box>
  )
}
