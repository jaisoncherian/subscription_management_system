import Modal from './Modal'
import Button from './Button'

export default function ConfirmDialog({ open, title, message, confirmLabel = 'Confirm', danger = false, loading = false, onConfirm, onCancel }) {
  return (
    <Modal open={open} onClose={onCancel} title={title}
      footer={<>
        <Button variant="secondary" onClick={onCancel}>Back</Button>
        <Button variant={danger ? 'danger-solid' : 'primary'} loading={loading} onClick={onConfirm}>{confirmLabel}</Button>
      </>}>
      <p className="pb-2 text-sm leading-relaxed text-slate-600">{message}</p>
    </Modal>
  )
}
