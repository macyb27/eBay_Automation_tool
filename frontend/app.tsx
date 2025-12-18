"""
🎨 Next.js 14 Frontend - eBay Automation Tool
Blazing fast React App mit TypeScript und Tailwind
"""

'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { toast, Toaster } from 'react-hot-toast'

interface JobStatus {
  job_id: string
  status: 'analyzing' | 'researching' | 'generating' | 'ready' | 'published' | 'error'
  progress: number
  result?: any
  error?: string
}

export default function EbayAutomationApp() {
  const [currentJob, setCurrentJob] = useState<JobStatus | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isPolling, setIsPolling] = useState(false)

  // 📸 FILE UPLOAD LOGIC
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setIsUploading(true)
    
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/analyze-product', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()
      
      if (response.ok) {
        toast.success('🚀 Analyse gestartet!')
        setCurrentJob({ 
          job_id: result.job_id, 
          status: 'analyzing', 
          progress: 0 
        })
        setIsPolling(true)
      } else {
        toast.error('❌ Upload fehlgeschlagen')
      }
    } catch (error) {
      toast.error('❌ Fehler beim Upload')
      console.error(error)
    } finally {
      setIsUploading(false)
    }
  }, [])

  // 🔄 STATUS POLLING
  useEffect(() => {
    if (!isPolling || !currentJob?.job_id) return

    const pollStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/status/${currentJob.job_id}`)
        const status: JobStatus = await response.json()
        
        setCurrentJob(status)
        
        if (status.status === 'ready') {
          setIsPolling(false)
          toast.success('✅ Auktion ist bereit!')
        } else if (status.status === 'error') {
          setIsPolling(false)
          toast.error(`❌ Fehler: ${status.error}`)
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }

    const interval = setInterval(pollStatus, 2000) // Poll every 2s
    return () => clearInterval(interval)
  }, [isPolling, currentJob?.job_id])

  // 🚀 PUBLISH TO EBAY
  const publishToEbay = async () => {
    if (!currentJob?.job_id) return

    try {
      toast.loading('📤 Veröffentliche auf eBay...')
      
      const response = await fetch(`http://localhost:8000/publish-listing/${currentJob.job_id}`, {
        method: 'POST'
      })
      
      const result = await response.json()
      
      if (result.success) {
        toast.success('🎉 Erfolgreich auf eBay veröffentlicht!')
        setCurrentJob(prev => ({ ...prev!, status: 'published', result }))
      } else {
        toast.error(`❌ Veröffentlichung fehlgeschlagen: ${result.error}`)
      }
    } catch (error) {
      toast.error('❌ Fehler bei der Veröffentlichung')
      console.error(error)
    }
  }

  // 👀 PREVIEW LISTING  
  const openPreview = () => {
    if (currentJob?.job_id) {
      window.open(`http://localhost:8000/preview/${currentJob.job_id}`, '_blank')
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp']
    },
    maxFiles: 1,
    disabled: isUploading || isPolling
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        
        {/* 🎯 HEADER */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🎯 eBay Automation Tool
          </h1>
          <p className="text-gray-600 text-lg">
            Foto hochladen → KI analysiert → Auktion erstellt → Profit! 🚀
          </p>
        </motion.div>

        {/* 📸 UPLOAD ZONE */}
        {!currentJob && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
                transition-all duration-300 bg-white shadow-lg
                ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}
                ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input {...getInputProps()} />
              
              <div className="text-6xl mb-4">📸</div>
              
              {isUploading ? (
                <div className="space-y-4">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                  <p className="text-gray-600">Analysiere Bild...</p>
                </div>
              ) : isDragActive ? (
                <p className="text-xl text-blue-600 font-semibold">
                  📦 Lass das Bild hier fallen!
                </p>
              ) : (
                <div>
                  <p className="text-xl text-gray-700 mb-2">
                    Produktfoto hier hochladen
                  </p>
                  <p className="text-gray-500">
                    Drag & Drop oder klicken zum Auswählen
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* 📊 PROGRESS SECTION */}
        <AnimatePresence>
          {currentJob && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-xl shadow-lg p-8 mb-6"
            >
              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-semibold">
                    {getStatusText(currentJob.status)}
                  </h3>
                  <span className="text-sm text-gray-600">
                    {currentJob.progress}%
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <motion.div
                    className="bg-blue-500 h-3 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${currentJob.progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>

              {/* Results Preview */}
              {currentJob.result && (
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-800">📱 Produktinfo:</h4>
                    <div className="bg-gray-50 p-4 rounded-lg text-sm">
                      <p><strong>Marke:</strong> {currentJob.result.product?.brand}</p>
                      <p><strong>Modell:</strong> {currentJob.result.product?.model}</p>
                      <p><strong>Zustand:</strong> {currentJob.result.product?.condition}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-800">💰 Preisstrategie:</h4>
                    <div className="bg-gray-50 p-4 rounded-lg text-sm">
                      <p><strong>Startpreis:</strong> {currentJob.result.listing?.starting_price}€</p>
                      <p><strong>Sofort-Kauf:</strong> {currentJob.result.listing?.buy_it_now_price}€</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              {currentJob.status === 'ready' && (
                <div className="flex gap-4 mt-6">
                  <button
                    onClick={openPreview}
                    className="flex-1 bg-gray-600 text-white py-3 px-6 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    👀 Vorschau anzeigen
                  </button>
                  
                  <button
                    onClick={publishToEbay}
                    className="flex-1 bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 transition-colors font-semibold"
                  >
                    🚀 Auf eBay veröffentlichen
                  </button>
                </div>
              )}

              {/* Success State */}
              {currentJob.status === 'published' && currentJob.result?.ebay_url && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-800 font-semibold mb-2">
                    🎉 Erfolgreich veröffentlicht!
                  </p>
                  <a 
                    href={currentJob.result.ebay_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    → Auktion auf eBay anzeigen
                  </a>
                </div>
              )}

              {/* Reset Button */}
              <button
                onClick={() => setCurrentJob(null)}
                className="mt-4 text-gray-600 hover:text-gray-800 text-sm underline"
              >
                🔄 Neue Auktion erstellen
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 💡 FEATURES */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="grid md:grid-cols-3 gap-6 mt-12"
        >
          {features.map((feature, index) => (
            <div key={index} className="bg-white p-6 rounded-xl shadow-lg text-center">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-sm">{feature.description}</p>
            </div>
          ))}
        </motion.div>
      </div>

      <Toaster position="top-right" />
    </div>
  )
}

// 📝 HELPER FUNCTIONS
function getStatusText(status: string): string {
  const statusMap = {
    analyzing: '🔍 Analysiere Produkt...',
    researching: '📊 Recherchiere Marktpreise...',
    generating: '✍️ Erstelle Auktionstext...',
    ready: '✅ Auktion bereit!',
    published: '🎉 Veröffentlicht!',
    error: '❌ Fehler aufgetreten'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const features = [
  {
    icon: '🤖',
    title: 'KI-Powered',
    description: 'Automatische Produkterkennung und Marktanalyse'
  },
  {
    icon: '⚡',
    title: 'Blitzschnell',
    description: 'Von Foto zu fertiger Auktion in unter 60 Sekunden'
  },
  {
    icon: '💰',
    title: 'Optimal Pricing',
    description: 'Datenbasierte Preisempfehlungen für maximalen Profit'
  }
]