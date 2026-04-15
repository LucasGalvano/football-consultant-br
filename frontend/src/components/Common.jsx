export function Loading() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brasil-green"></div>
    </div>
  )
}

export function ErrorAlert({ message }) {
  return (
    <div className="error-alert" role="alert">
      <span className="font-bold">⚠️ Erro:</span> {message}
    </div>
  )
}

export function EmptyState({ message = 'Nenhum dado encontrado' }) {
  return (
    <div className="text-center py-8 text-gray-500">
      <p className="text-lg">{message}</p>
    </div>
  )
}
