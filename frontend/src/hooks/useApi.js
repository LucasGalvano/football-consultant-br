import { useState, useEffect, useRef } from 'react'

export function useApi(apiCall, dependencies = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Serializa as dependências para comparação estável
  const depsKey = JSON.stringify(dependencies)
  const depsKeyRef = useRef(depsKey)

  useEffect(() => {
    depsKeyRef.current = depsKey

    let mounted = true

    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await apiCall()
        if (mounted) {
          setData(response.data)
        }
      } catch (err) {
        if (mounted) {
          setError(err.response?.data?.detail || err.message || 'Erro ao carregar dados')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    fetchData()

    return () => {
      mounted = false
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [depsKey])

  return { data, loading, error }
}