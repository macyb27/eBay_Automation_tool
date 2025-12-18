/**
 * 🎯 eBay Automation Dashboard - Complete Frontend
 * React + TypeScript + Tailwind CSS
 * Production-ready UI with real-time updates
 */

'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { 
  Upload, 
  Search, 
  DollarSign, 
  TrendingUp, 
  Eye, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  BarChart3,
  Settings,
  LogOut,
  Zap,
  Image as ImageIcon,
  FileText,
  Globe,
  RefreshCw,
  Download,
  Edit3,
  Share2
} from 'lucide-react'

// ================================
// Types & Interfaces
// ================================

interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
  plan: 'free' | 'pro' | 'business'
  monthly_listings_used: number
  monthly_listings_limit: number
}

interface Listing {
  id: number
  uuid: string
  product_name: string
  title: string
  status: string
  starting_price_cents: number
  views_count: number
  watchers_count: number
  created_at: string
  listed_at?: string
  sold_at?: string
}

interface JobStatus {
  job_id: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  progress: number
  current_step: string
  result?: any
  error?: string
  created_at: string
  updated_at: string
}

interface Analytics {
  total_listings_created: number
  total_listings_sold: number
  total_revenue_cents: number
  success_rate: number
  monthly_listings: number
  monthly_sales: number
  monthly_revenue_cents: number
}

// ================================
// API Service
// ================================

class ApiService {
  private baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  private token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
      ...options.headers,
    }

    const response = await fetch(url, { ...options, headers })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'API request failed')
    }
    
    return response.json()
  }

  async uploadImage(file: File, preferences: any = {}) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('user_preferences', JSON.stringify(preferences))

    const response = await fetch(`${this.baseURL}/analyze-product`, {
      method: 'POST',
      headers: {
        ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Upload failed')
    }

    return response.json()
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.request(`/job-status/${jobId}`)
  }

  async getListings(limit = 20, offset = 0): Promise<Listing[]> {
    return this.request(`/my-listings?limit=${limit}&offset=${offset}`)
  }

  async getAnalytics() {
    return this.request('/analytics/dashboard')
  }

  async getListingDetails(listingId: number) {
    return this.request(`/listing/${listingId}`)
  }

  setAuthToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }
}

const api = new ApiService()

// ================================
// Components
// ================================

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const getStatusConfig = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'ready_to_list':
      case 'listed':
        return { color: 'bg-green-100 text-green-800', icon: CheckCircle }
      case 'in_progress':
      case 'analyzing':
      case 'content_generating':
        return { color: 'bg-blue-100 text-blue-800', icon: Clock }
      case 'failed':
      case 'error':
        return { color: 'bg-red-100 text-red-800', icon: XCircle }
      case 'sold':
        return { color: 'bg-purple-100 text-purple-800', icon: DollarSign }
      default:
        return { color: 'bg-gray-100 text-gray-800', icon: AlertCircle }
    }
  }

  const { color, icon: Icon } = getStatusConfig(status)

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      <Icon className="w-3 h-3 mr-1" />
      {status.replace('_', ' ')}
    </span>
  )
}

const ProgressBar: React.FC<{ progress: number; className?: string }> = ({ 
  progress, 
  className = "" 
}) => (
  <div className={`w-full bg-gray-200 rounded-full h-2.5 ${className}`}>
    <div 
      className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
      style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
    ></div>
  </div>
)

const MetricCard: React.FC<{
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  trend?: number
  color?: string
}> = ({ title, value, subtitle, icon: Icon, trend, color = "text-blue-600" }) => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div className="flex items-center justify-between">
      <div className="flex items-center">
        <div className={`${color} bg-opacity-10 rounded-lg p-3`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
        <div className="ml-4">
          <h3 className="text-lg font-semibold text-gray-900">{value}</h3>
          <p className="text-sm text-gray-500">{title}</p>
          {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
        </div>
      </div>
      {trend !== undefined && (
        <div className={`text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend >= 0 ? '+' : ''}{trend}%
        </div>
      )}
    </div>
  </div>
)

// ================================
// Main Dashboard Component
// ================================

const EbayAutomationDashboard: React.FC = () => {
  // State Management
  const [user, setUser] = useState<User | null>(null)
  const [listings, setListings] = useState<Listing[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [currentJob, setCurrentJob] = useState<JobStatus | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'listings' | 'analytics'>('dashboard')
  const [error, setError] = useState<string>('')

  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // ================================
  // Data Fetching
  // ================================

  const fetchData = useCallback(async () => {
    try {
      const [listingsData, analyticsData] = await Promise.all([
        api.getListings(10),
        api.getAnalytics()
      ])
      
      setListings(listingsData)
      setAnalytics(analyticsData.analytics)
      
      // Mock user data (in production: get from API)
      setUser({
        id: 1,
        email: 'user@example.com',
        first_name: 'Max',
        last_name: 'Mustermann',
        plan: analyticsData.plan_info.current_plan,
        monthly_listings_used: analyticsData.plan_info.monthly_listings_used,
        monthly_listings_limit: analyticsData.plan_info.monthly_listings_limit
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    }
  }, [])

  const pollJobStatus = useCallback(async (jobId: string) => {
    try {
      const status = await api.getJobStatus(jobId)
      setCurrentJob(status)
      
      if (status.status === 'completed' || status.status === 'failed') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current)
          pollIntervalRef.current = null
        }
        
        // Refresh listings after completion
        if (status.status === 'completed') {
          setTimeout(fetchData, 1000)
        }
      }
    } catch (err) {
      console.error('Failed to poll job status:', err)
    }
  }, [fetchData])

  // ================================
  // File Upload Handling
  // ================================

  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file')
      return
    }
    
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB')
      return
    }
    
    setSelectedFile(file)
    setError('')
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setError('')

    try {
      const response = await api.uploadImage(selectedFile, {
        prioritize_speed: true,
        target_price_range: [1000, 5000] // 10-50€
      })
      
      setCurrentJob({
        job_id: response.job_id,
        status: 'pending',
        progress: 0,
        current_step: 'Initialisierung...',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })

      // Start polling for status
      pollIntervalRef.current = setInterval(() => {
        pollJobStatus(response.job_id)
      }, 2000)

      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  // Drag & Drop Handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files?.[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  // ================================
  // Effects
  // ================================

  useEffect(() => {
    // Mock authentication (in production: implement proper auth)
    api.setAuthToken('mock-jwt-token')
    fetchData()

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [fetchData])

  // ================================
  // Utility Functions
  // ================================

  const formatPrice = (cents: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR'
    }).format(cents / 100)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // ================================
  // Render Methods
  // ================================

  const renderUploadArea = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Neues Produkt analysieren
        </h2>
        <p className="text-gray-600 mb-6">
          Lade ein Produktbild hoch und lass KI eine optimale eBay-Auktion erstellen
        </p>

        <div
          className={`border-2 border-dashed rounded-lg p-8 transition-colors ${
            dragActive 
              ? 'border-blue-400 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {selectedFile ? (
            <div className="text-center">
              <ImageIcon className="mx-auto h-16 w-16 text-green-500 mb-4" />
              <p className="text-lg font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500 mb-4">
                {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
              </p>
              <div className="flex justify-center space-x-4">
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw className="animate-spin w-4 h-4 mr-2" />
                      Wird analysiert...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Analyse starten
                    </>
                  )}
                </button>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300"
                >
                  Abbrechen
                </button>
              </div>
            </div>
          ) : (
            <div>
              <Upload className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                Produktbild hochladen
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Ziehe ein Bild hierher oder klicke zum Auswählen
              </p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
              >
                Datei auswählen
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                className="hidden"
              />
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}
      </div>
    </div>
  )

  const renderJobProgress = () => {
    if (!currentJob) return null

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Verarbeitung läuft...
          </h3>
          <StatusBadge status={currentJob.status} />
        </div>
        
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{currentJob.current_step}</span>
            <span>{currentJob.progress}%</span>
          </div>
          <ProgressBar progress={currentJob.progress} />
        </div>

        {currentJob.status === 'completed' && currentJob.result && (
          <div className="border-t pt-4 mt-4">
            <h4 className="font-medium text-gray-900 mb-2">Ergebnis:</h4>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-green-800">
                ✅ Analyse abgeschlossen! Produkt: {currentJob.result.vision_analysis?.product?.name}
              </p>
              <p className="text-sm text-green-600 mt-1">
                Empfohlener Preis: {formatPrice(currentJob.result.market_insights?.price_data?.competitive_price || 0)}
              </p>
            </div>
          </div>
        )}

        {currentJob.error && (
          <div className="border-t pt-4 mt-4">
            <div className="bg-red-50 p-4 rounded-lg">
              <p className="text-red-800">❌ {currentJob.error}</p>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard
          title="Diesen Monat"
          value={user?.monthly_listings_used || 0}
          subtitle={`von ${user?.monthly_listings_limit || 10} Listings`}
          icon={FileText}
          color="text-blue-600"
        />
        <MetricCard
          title="Erfolgsrate"
          value={`${((analytics?.success_rate || 0) * 100).toFixed(1)}%`}
          subtitle="Verkaufte Listings"
          icon={TrendingUp}
          color="text-green-600"
        />
        <MetricCard
          title="Umsatz (Monat)"
          value={formatPrice(analytics?.monthly_revenue_cents || 0)}
          subtitle={`${analytics?.monthly_sales || 0} Verkäufe`}
          icon={DollarSign}
          color="text-purple-600"
        />
        <MetricCard
          title="Gesamtumsatz"
          value={formatPrice(analytics?.total_revenue_cents || 0)}
          subtitle={`${analytics?.total_listings_sold || 0} verkauft`}
          icon={BarChart3}
          color="text-orange-600"
        />
      </div>

      {/* Progress or Upload */}
      {currentJob ? renderJobProgress() : renderUploadArea()}

      {/* Recent Listings */}
      {listings.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Aktuelle Listings</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {listings.slice(0, 5).map((listing) => (
              <div key={listing.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-gray-900 truncate">
                      {listing.title}
                    </h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {listing.product_name}
                    </p>
                    <div className="flex items-center mt-2 space-x-4">
                      <span className="text-sm text-gray-500">
                        💰 {formatPrice(listing.starting_price_cents)}
                      </span>
                      <span className="text-sm text-gray-500">
                        👀 {listing.views_count}
                      </span>
                      <span className="text-sm text-gray-500">
                        ⭐ {listing.watchers_count}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <StatusBadge status={listing.status} />
                    <span className="text-xs text-gray-400">
                      {formatDate(listing.created_at)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  // ================================
  // Main Render
  // ================================

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center space-x-4">
            <div className="bg-blue-600 rounded-lg p-2">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">eBay Automation</h1>
              <p className="text-sm text-gray-500">KI-powered Listing Creation</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-xs text-gray-500 uppercase">{user?.plan} Plan</p>
            </div>
            <button className="p-2 text-gray-500 hover:text-gray-700">
              <Settings className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-500 hover:text-gray-700">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="max-w-7xl mx-auto">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
              { id: 'listings', label: 'Listings', icon: FileText },
              { id: 'analytics', label: 'Analytics', icon: TrendingUp },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`flex items-center px-3 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'dashboard' && renderDashboard()}
        {/* TODO: Implement listings and analytics tabs */}
      </div>
    </div>
  )
}

export default EbayAutomationDashboard