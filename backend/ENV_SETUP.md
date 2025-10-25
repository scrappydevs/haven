# Environment Variables Setup

## Required Environment Variables

The backend optionally uses environment variables for enhanced functionality. Create a `.env` file in the `backend/` directory with the following:

### 1. Supabase (Optional)
Used for patient database. If not provided, the app uses local JSON files.

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 2. Anthropic API (Optional)
Used for AI-powered monitoring protocol recommendations. If not provided, uses keyword-based matching.

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Quick Setup

```bash
# Navigate to backend directory
cd backend

# Create .env file
cat > .env << 'EOF'
# Optional: Add your Supabase credentials
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your-anon-key

# Optional: Add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-...
EOF
```

## Running Without Environment Variables

The backend is fully functional without environment variables:
- ✅ Patient data loaded from `data/patients.json`
- ✅ Monitoring protocols use keyword matching
- ✅ All core CV features work normally

**No environment variables are required for basic functionality!**

## Notes

- The warnings you see on startup are normal if you're not using Supabase
- Missing data files (precomputed_cv.json, nct04649359.json) are optional - see scripts/ for generation

