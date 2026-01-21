import { render, screen } from '@testing-library/react'
import Navigation from '../components/Navigation'

describe('Navigation', () => {
  it('renderiza o nome Frete.ai', () => {
    render(<Navigation />)
    expect(screen.getByText('Frete.ai')).toBeInTheDocument()
  })
})
