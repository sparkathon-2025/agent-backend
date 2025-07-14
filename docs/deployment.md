# Render Deployment Guide

## Prerequisites

1. GitHub repository with your code
2. Render account
3. MongoDB Atlas account (or use Render's managed database)

## Deployment Steps

### 1. Connect Repository
- Go to Render dashboard
- Click "New +" → "Web Service"
- Connect your GitHub repository

### 2. Configure Service
- **Name**: `voice-agent-backend`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements-dev.txt`
- **Start Command**: `python main.py`

### 3. Environment Variables
Add these in Render service settings:

```bash
MONGODB_URL=your-mongodb-connection-string
DATABASE_NAME=voice_agent
OPENAI_API_KEY=your-openai-key
DEEPGRAM_API_KEY=your-deepgram-key
ENVIRONMENT=production
```

### 4. Database Setup
Option A: Use MongoDB Atlas
- Create cluster on MongoDB Atlas
- Get connection string
- Add to MONGODB_URL environment variable

Option B: Use Render's managed database
- Add PostgreSQL database (if switching from MongoDB)
- Connection details auto-configured

### 5. Deploy
- Click "Create Web Service"
- Render will automatically build and deploy

## Health Checks

The service includes a health check endpoint:
- `GET /health` - Returns service status

## Troubleshooting

### Build Issues
- Check that requirements-dev.txt is up to date
- Verify Python version compatibility

### Runtime Issues
- Check logs in Render dashboard
- Verify environment variables are set
- Test database connectivity

### Performance
- Monitor resource usage
- Consider upgrading plan for ML workloads
- Enable auto-scaling if needed

## Production Considerations

1. **Security**: Update CORS origins for your domain
2. **Monitoring**: Set up logging and alerts
3. **Scaling**: Configure auto-scaling based on traffic
4. **Backups**: Ensure database backups are configured
