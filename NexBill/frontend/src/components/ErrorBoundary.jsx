import { Component } from 'react'
import Button from './Button'
import EmptyState from './EmptyState'

export default class ErrorBoundary extends Component {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    if (!this.state.failed) return this.props.children
    return (
      <EmptyState title="Something went wrong" message="Reload the page to try again."
        action={<Button onClick={() => window.location.reload()}>Reload</Button>} />
    )
  }
}
