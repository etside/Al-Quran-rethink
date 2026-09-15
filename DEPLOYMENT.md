# Miraz — Deployment Guide

## Vercel Deployment (Recommended)

### Option 1: Frontend + Backend as Separate Projects (Recommended)

#### Backend Deployment

1. **Create a new Vercel project for the backend:**
   ```bash
   cd backend
   vercel --prod
   ```

2. **Set environment variables in Vercel dashboard:**
   - `ALLOWED_ORIGINS`: Your frontend domain (e.g., `https://miraz.vercel.app`)
   - `MIRAZ_DB`: Leave empty (uses default path)

3. **Note the backend URL** (e.g., `https://miraz-api.vercel.app`)

#### Frontend Deployment

1. **Create a new Vercel project for the frontend:**
   ```bash
   cd frontend
   vercel --prod
   ```

2. **Set environment variables in Vercel dashboard:**
   - `VITE_API_BASE`: Your backend URL (e.g., `https://miraz-api.vercel.app`)

3. **Update backend CORS:**
   - Go to backend project settings
   - Update `ALLOWED_ORIGINS` to include your frontend URL

### Option 2: Monorepo with Vercel

For a single Vercel project with both frontend and backend:

1. **Root `vercel.json`:**
   ```json
   {
     "builds": [
       { "src": "backend/api/index.py", "use": "@vercel/python" },
       { "src": "frontend/package.json", "use": "@vercel/static-build", "config": { "distDir": "dist" } }
     ],
     "routes": [
       { "src": "/api/(.*)", "dest": "/backend/api/index.py" },
       { "src": "/(.*)", "dest": "/frontend/$1" }
     ]
   }
   ```

2. **Set environment variables:**
   - `VITE_API_BASE`: Leave empty (uses relative `/api` path)
   - `ALLOWED_ORIGINS`: `*` or your domain

## Local Development

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Import Quran data (if not already done)
python scripts/import_quran.py

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and will proxy API requests to `http://localhost:8000`.

## Environment Variables

### Frontend (Vite)

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE` | Backend API base URL | `""` (empty, uses `/api` prefix) |

### Backend (FastAPI)

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `*` |
| `MIRAZ_DB` | Path to SQLite database | `../miraz.db` |

## Custom Domain Setup

### Adding a Custom Domain to Vercel

1. Go to your Vercel project settings
2. Navigate to "Domains"
3. Add your custom domain
4. Follow Vercel's DNS configuration instructions

### DNS Configuration

For a subdomain (e.g., `miraz.yourdomain.com`):
- Add a CNAME record pointing to `cname.vercel-dns.com`

For apex domain (e.g., `yourdomain.com`):
- Add an A record pointing to `76.76.21.21`

## Production Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend deployed with correct `VITE_API_BASE`
- [ ] CORS configured with specific origins (not `*`)
- [ ] Custom domains configured
- [ ] SSL certificates active
- [ ] Error monitoring set up (optional)
- [ ] Analytics added (optional)

## Troubleshooting

### CORS Errors
- Ensure `ALLOWED_ORIGINS` includes your frontend domain
- Check that the backend is accessible from the frontend

### API Connection Issues
- Verify `VITE_API_BASE` is set correctly
- Check browser network tab for 404 or 500 errors
- Ensure backend is running and healthy

### Database Issues
- Verify `miraz.db` exists in the backend directory
- Check file permissions
- Run `python scripts/import_quran.py` if data is missing

## Monitoring

### Health Check
- Backend: `GET /health` returns `{"ok": true, "service": "miraz-api"}`
- Frontend: Check Vercel deployment logs

### Logs
- Vercel Dashboard → Project → Deployments → Select deployment → Logs
- Or use Vercel CLI: `vercel logs <deployment-url>`

## Performance Optimization

### Frontend
- Enable Vercel's Edge Network (automatic)
- Use image optimization for any images
- Enable compression (automatic on Vercel)

### Backend
- Consider using Vercel's Edge Functions for read-only endpoints
- For high traffic, consider upgrading to a hosted database (Turso/Neon)

## Security

### Production Recommendations
1. **CORS**: Set specific origins, not `*`
2. **Rate Limiting**: Consider adding rate limiting for public APIs
3. **Input Validation**: Already handled by FastAPI
4. **Database**: For Phase 2, use hosted database with proper access controls

### Environment Variables
- Never commit `.env` files
- Use Vercel's environment variable encryption
- Rotate secrets regularly

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Vercel deployment logs
3. Check GitHub issues (if applicable)
