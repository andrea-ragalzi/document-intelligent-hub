import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AlertMessage } from '../../components/AlertMessage'
import type { AlertState } from '../../lib/types'

describe('AlertMessage', () => {
    it('should not render when alert is null', () => {
        const { container } = render(
            <AlertMessage alert={null} />
        )

        expect(container.firstChild).toBeNull()
    })

    it('should render success alert with correct styles', () => {
        const alert: AlertState = {
            message: 'Operation successful!',
            type: 'success',
        }

        render(<AlertMessage alert={alert} />)

        expect(screen.getByText('Operation successful!')).toBeInTheDocument()
        const container = screen.getByText('Operation successful!').closest('div')
        expect(container).toHaveClass('bg-green-50')
    })

    it('should render error alert with correct styles', () => {
        const alert: AlertState = {
            message: 'Something went wrong',
            type: 'error',
        }

        render(<AlertMessage alert={alert} />)

        expect(screen.getByText('Something went wrong')).toBeInTheDocument()
        const container = screen.getByText('Something went wrong').closest('div')
        expect(container).toHaveClass('bg-red-50')
    })

    it('should render info alert with correct styles', () => {
        const alert: AlertState = {
            message: 'Please note this information',
            type: 'info',
        }

        render(<AlertMessage alert={alert} />)

        expect(screen.getByText('Please note this information')).toBeInTheDocument()
        const container = screen.getByText('Please note this information').closest('div')
        expect(container).toHaveClass('bg-blue-50')
    })

    it('should render icon for each alert type', () => {
        const successAlert: AlertState = { message: 'Success', type: 'success' }
        const { rerender, container } = render(<AlertMessage alert={successAlert} />)

        expect(screen.getByText('Success')).toBeInTheDocument()
        expect(container.querySelector('svg')).toBeInTheDocument()

        const errorAlert: AlertState = { message: 'Error', type: 'error' }
        rerender(<AlertMessage alert={errorAlert} />)

        expect(screen.getByText('Error')).toBeInTheDocument()
        expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('should not render when alert message is empty', () => {
        const alert: AlertState = {
            message: '',
            type: 'info',
        }

        const { container } = render(<AlertMessage alert={alert} />)

        expect(container.firstChild).toBeNull()
    })

    it('should apply dark mode classes', () => {
        const alert: AlertState = {
            message: 'Dark mode test',
            type: 'success',
        }

        render(<AlertMessage alert={alert} />)

        const container = screen.getByText('Dark mode test').closest('div')
        expect(container).toHaveClass('dark:bg-green-900/20')
    })
})
