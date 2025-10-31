# Deploying to Vercel with PostgreSQL

This guide will walk you through deploying your Invoicing System to Vercel with PostgreSQL.

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. Vercel CLI installed: `npm install -g vercel`
3. A PostgreSQL database (options below)

## Step 1: Set Up PostgreSQL Database

You have several options for PostgreSQL hosting:

### Option A: Vercel Postgres (Recommended)
1. Go to your Vercel dashboard
2. Navigate to the Storage tab
3. Create a new Postgres database
4. Copy the `DATABASE_URL` connection string (it will look like: `postgres://user:password@host:port/database`)

### Option B: Neon (Free tier available)
1. Sign up at https://neon.tech
2. Create a new project
3. Copy the connection string from the dashboard

### Option C: Supabase (Free tier available)
1. Sign up at https://supabase.com
2. Create a new project
3. Go to Settings > Database and copy the connection string (use the pooler connection string for best performance)

### Option D: Railway (Free tier available)
1. Sign up at https://railway.app
2. Create a new PostgreSQL database
3. Copy the connection string from the database settings

## Step 2: Deploy to Vercel

### Using Vercel CLI (Recommended)

1. Login to Vercel:
   ```bash
   vercel login
   ```

2. Navigate to your project directory:
   ```bash
   cd /home/user/Invoicing_System_2
   ```

3. Deploy:
   ```bash
   vercel
   ```

4. Follow the prompts:
   - Set up and deploy? Y
   - Which scope? Select your account
   - Link to existing project? N (for first deployment)
   - What's your project's name? invoicing-system (or your preferred name)
   - In which directory is your code located? ./

5. Add the DATABASE_URL environment variable:
   ```bash
   vercel env add DATABASE_URL
   ```
   - When prompted, select "Production, Preview, and Development"
   - Paste your PostgreSQL connection string
   - If the URL starts with `postgres://`, it will be automatically converted to `postgresql://` by the app

6. Redeploy with the environment variable:
   ```bash
   vercel --prod
   ```

### Using Vercel Dashboard

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)

2. Go to https://vercel.com/dashboard

3. Click "Add New Project"

4. Import your Git repository

5. Configure your project:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: (leave empty)
   - Output Directory: (leave empty)

6. Add Environment Variables:
   - Click "Environment Variables"
   - Add `DATABASE_URL` with your PostgreSQL connection string
   - Make sure it's available for Production, Preview, and Development

7. Click "Deploy"

## Step 3: Verify Deployment

1. Once deployed, Vercel will provide you with a URL (e.g., `https://your-project.vercel.app`)

2. Visit the URL to see your application

3. The database tables will be automatically created on first run thanks to the `init_db()` function

4. Test the application by creating an invoice

## Troubleshooting

### Database Connection Issues

If you see database connection errors:

1. Verify your DATABASE_URL is correct:
   ```bash
   vercel env ls
   ```

2. Check if the URL starts with `postgresql://` (not `postgres://`)
   - The app automatically converts it, but some providers require the correct protocol

3. Ensure your database allows connections from Vercel's IP addresses
   - Most cloud providers (Neon, Supabase, Railway) allow this by default
   - For custom databases, you may need to whitelist Vercel's IPs

### Build Failures

If the build fails:

1. Check the build logs in Vercel dashboard

2. Common issues:
   - Missing dependencies: Make sure all packages are in requirements.txt
   - Lambda size too large: The current config allows up to 15MB

### SSL Certificate Errors

If you see SSL errors:

1. Update your DATABASE_URL to include `?sslmode=require` at the end:
   ```
   postgresql://user:password@host:port/database?sslmode=require
   ```

2. Redeploy:
   ```bash
   vercel --prod
   ```

## Environment Variables

The application requires the following environment variable:

- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql://username:password@host:port/database`
  - Example: `postgresql://user:pass@db.example.com:5432/mydb`

## Updating Your Application

To update your deployed application:

1. Make your changes locally

2. Commit and push to your Git repository (if using Git integration)

3. Or run:
   ```bash
   vercel --prod
   ```

Vercel will automatically redeploy your application.

## Additional Configuration

### Custom Domain

1. Go to your project in Vercel dashboard
2. Click "Settings" > "Domains"
3. Add your custom domain
4. Follow the DNS configuration instructions

### Environment Variables for Different Environments

You can set different DATABASE_URL values for:
- Production: Your main database
- Preview: A staging database (optional)
- Development: Your local database (optional)

## Support

- Vercel Documentation: https://vercel.com/docs
- Vercel Postgres: https://vercel.com/docs/storage/vercel-postgres
- Flask on Vercel: https://vercel.com/docs/frameworks/flask

## Notes

- The application uses Flask with PostgreSQL
- Database tables are automatically created on startup
- Static files are served from the `/static` directory
- The app uses psycopg2-binary for PostgreSQL connectivity
- Serverless functions have a maximum execution time (check Vercel plan limits)
