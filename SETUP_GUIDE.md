# 🚀 eBay Automation Tool - Setup Guide
## Von 0 auf Production-Ready in 15 Minuten! ⚡

### 🎯 QUICK START (Development)

```bash
# 1. Repository klonen
git clone <your-repo-url>
cd ebay_automation_tool

# 2. Environment Setup
cp .env.example .env
# -> Trage deine API Keys ein!

# 3. Mit Docker starten (empfohlen!)
docker-compose up --build

# ✅ Fertig! 
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
```

### 🔑 BENÖTIGTE API KEYS

Erstelle eine `.env` Datei im Root-Verzeichnis:

```bash
# 🤖 AI SERVICES
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-claude-key

# 🛒 EBAY API (Sandbox für Development)
EBAY_APP_ID=your-app-id
EBAY_CERT_ID=your-cert-id  
EBAY_DEV_ID=your-dev-id
EBAY_TOKEN=your-user-token
EBAY_SANDBOX=true

# 🔒 SECURITY
JWT_SECRET=your-super-secret-jwt-key
ENCRYPTION_KEY=your-32-char-encryption-key

# 📊 MONITORING (Optional)
SENTRY_DSN=your-sentry-dsn
```

### 📋 API KEYS BESCHAFFEN

#### 🤖 OpenAI API
1. Gehe zu https://platform.openai.com/api-keys
2. Erstelle einen neuen API Key
3. **Wichtig:** Mindestens $5 Guthaben aufladen für GPT-4V

#### 🤖 Anthropic Claude (Optional)
1. Registriere dich bei https://console.anthropic.com/
2. Erstelle einen API Key
3. Als Fallback für OpenAI

#### 🛒 eBay Developer Account
1. Registriere dich bei https://developer.ebay.com/
2. Erstelle eine neue App im Developer Portal
3. Notiere dir: App ID, Cert ID, Dev ID
4. Generiere ein User Token für Sandbox Tests

### 🐳 ENTWICKLUNG MIT DOCKER (Empfohlen!)

```bash
# Alles auf einmal starten
docker-compose up --build

# Nur Backend
docker-compose up api postgres redis

# Mit Monitoring 
docker-compose --profile monitoring up

# Produktions-Setup
docker-compose --profile production up
```

### 💻 NATIVE ENTWICKLUNG (Ohne Docker)

```bash
# Backend Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# PostgreSQL + Redis starten (lokal installiert)
brew install postgresql redis  # macOS
sudo systemctl start postgresql redis  # Linux

# Frontend Setup  
cd frontend
npm install
npm run dev

# Backend starten
uvicorn main:app --reload
```

### 🗄️ DATENBANK SETUP

```bash
# Automatisch mit Docker
docker-compose up postgres

# Oder manuell:
createdb ebay_automation
psql ebay_automation < init.sql
```

### 🧪 TESTING

```bash
# Backend Tests
pytest
pytest --cov=. --cov-report=html  # Mit Coverage

# Frontend Tests
cd frontend
npm run test
npm run test:watch  # Watch mode
```

### 📦 DEPLOYMENT

#### 🚀 Vercel + Railway (Empfohlen)

```bash
# Frontend auf Vercel
npm i -g vercel
vercel --prod

# Backend auf Railway
# Verbinde GitHub Repo mit Railway
# Environment Variables in Railway Dashboard setzen
```

#### 🐳 Docker Production

```bash
# Production Build
docker build --target production -t ebay-automation .

# Mit docker-compose
docker-compose --profile production up -d
```

#### ☁️ Cloud Provider (AWS/GCP/Azure)

```bash
# Container Registry Push
docker tag ebay-automation your-registry/ebay-automation:latest
docker push your-registry/ebay-automation:latest

# Kubernetes Deployment
kubectl apply -f k8s/
```

### 📊 MONITORING & DEBUGGING

```bash
# Logs anzeigen
docker-compose logs -f api

# Metriken (mit Prometheus)
docker-compose --profile monitoring up
# -> http://localhost:9090 (Prometheus)
# -> http://localhost:3001 (Grafana, admin/admin)

# Performance Monitoring
# -> Sentry für Error Tracking
# -> Posthog für User Analytics
```

### 🔧 DEVELOPMENT TIPPS

#### ⚡ Performance Optimierungen
- Redis Caching für API Responses aktivieren
- PostgreSQL Connection Pooling nutzen  
- Async/Await für alle I/O Operations
- Image Compression vor Upload

#### 🛠️ Code Quality
```bash
# Formatter & Linter
black .
isort .
ruff check .
mypy .
```

#### 🧪 API Testing
```bash
# Swagger UI (Auto-generiert)
http://localhost:8000/docs

# Curl Examples
curl -X POST "http://localhost:8000/analyze-product" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_product.jpg"
```

### 🚨 TROUBLESHOOTING

#### ❌ "Docker not found"
```bash
# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

#### ❌ "Port bereits belegt"
```bash
# Ports ändern in docker-compose.yml
# oder andere Services stoppen
sudo lsof -i :8000
sudo kill -9 <PID>
```

#### ❌ "API Key Fehler"
- Prüfe `.env` Datei Syntax (keine Leerzeichen!)
- Validiere API Keys auf entsprechenden Plattformen
- Prüfe API Limits/Guthaben

#### ❌ "Database Connection Error"
```bash
# PostgreSQL Status prüfen
docker-compose logs postgres

# Connection String prüfen
echo $DATABASE_URL
```

### 🎯 NÄCHSTE SCHRITTE

1. **MVP testen** → Ein Produktfoto hochladen und Auktion generieren
2. **eBay Integration** → Echte API Calls implementieren
3. **Performance tuning** → Caching und Optimierungen
4. **Security** → Rate Limiting, Input Validation
5. **Monitoring** → Logging, Metrics, Alerting
6. **Scaling** → Load Balancer, Multiple Instances

### 📞 SUPPORT

- 🐛 **Issues:** GitHub Issues erstellen
- 💬 **Diskussion:** GitHub Discussions
- 📧 **Direkte Hilfe:** Einfach fragen! 😉

---

## 🔥 BONUS: Performance Benchmarks

**Ziel-Performance:**
- 📸 **Bildanalyse:** < 2s
- 📊 **Marktforschung:** < 3s  
- ✍️ **Content-Generation:** < 5s
- 🚀 **Gesamt-Pipeline:** < 10s

**Skalierung:**
- 🔄 **Concurrent Users:** 100+
- 📦 **Listings/Tag:** 1000+
- 💾 **Storage:** Unlimited (Cloud)

**Das wird ein Game-Changer! 🚀**