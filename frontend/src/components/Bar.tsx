import { Container } from '@mui/material'
import { barStyles } from '../themes/styles/bar.styles'

interface BarProps {
  children: React.ReactNode
}

export const Bar = ({ children }: BarProps) => {
  return (
    <Container maxWidth={false} sx={barStyles.container}>
      {children}
    </Container>
  )
}
