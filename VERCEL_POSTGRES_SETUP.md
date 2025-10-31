# Setting Up Vercel Postgres (Easiest Database Option)

Vercel Postgres is the easiest database to use with Vercel. It integrates directly and requires zero configuration!

## Step 1: Create Vercel Postgres Database

1. **Go to your Vercel Dashboard**: https://vercel.com/dashboard

2. **Click on the "Storage" tab** at the top

3. **Click "Create Database"**

4. **Select "Postgres"**

5. **Configure your database:**
   - **Database Name**: `invoicing-db` (or any name you want)
   - **Region**: Choose one close to you (e.g., `Washington, D.C. (iad1)`)
   - **Plan**: Select **Free** (Hobby plan - perfect for getting started)

6. **Click "Create"**

That's it! The database is created in seconds.

---

## Step 2: Connect to Your Project

After creating the database, you'll see a connection screen:

1. **Click "Connect Project"** or go to the **"Settings"** tab of your database

2. **Select your project** from the dropdown
   - Choose: `invoicing-system` (or whatever you named it)

3. **Select environment(s)**:
   - ✅ Check **Production**
   - ✅ Check **Preview**
   - ✅ Check **Development**

4. **Click "Connect"**

**🎉 Done!** Vercel automatically sets the `DATABASE_URL` environment variable in your project.

---

## Step 3: Redeploy Your Application

Now that the database is connected:

1. Go to your **project dashboard**

2. Go to **Deployments** tab

3. Click the **"..."** menu on the latest deployment

4. Click **"Redeploy"**

5. Wait for deployment to complete (1-2 minutes)

---

## Step 4: Verify It Works

Once redeployed:

1. **Visit your app**: `https://your-app.vercel.app`

2. **Check health**: `https://your-app.vercel.app/health`
   - Should show: `{"status": "healthy", "database": "connected"}`

3. **Create an invoice** to test:
   - Click "Add Customer"
   - Fill in details
   - Add items
   - Click "Create Invoice"
   - PDF should generate!

---

## What Happens Automatically

When you connect Vercel Postgres:

✅ `DATABASE_URL` environment variable is set automatically
✅ Database tables are created on first run (via `init_db()`)
✅ Connection pooling is handled by Vercel
✅ SSL is enabled by default
✅ Backups are automatic (on paid plans)

---

## Viewing Your Database

To see your data:

1. Go to **Storage** → Click your database

2. Click **"Data"** tab

3. You'll see three tables:
   - `invoices` - Your invoice headers
   - `customers` - Customer information
   - `items` - Line items for each customer

4. Click **"Query"** tab to run SQL queries

Example query to see all invoices:
```sql
SELECT * FROM invoices ORDER BY creation_date DESC;
```

---

## Database Limits (Free Tier)

The **Hobby plan** includes:
- ✅ 256 MB storage
- ✅ 60 hours of compute per month
- ✅ Perfect for small to medium invoice apps
- ✅ Can handle thousands of invoices

Need more? Upgrade to Pro plan anytime.

---

## Troubleshooting

### Issue: "DATABASE_URL environment variable is not set"

**Solution:**
1. Make sure you clicked "Connect Project" in the database settings
2. Redeploy your application
3. Check Project Settings → Environment Variables to verify `DATABASE_URL` exists

### Issue: Database connection failed

**Solution:**
1. Check the database is in the same region as your deployment
2. Verify the database is running (go to Storage → your database)
3. Check Function Logs for detailed errors

### Issue: Tables not created

**Solution:**
The tables are created automatically on first run. Just visit your app URL and they'll be created. Check Function Logs to see initialization messages.

---

## Alternative: Manual Connection String

If you prefer to see the connection string:

1. Go to **Storage** → Your database → **Settings**

2. Under **Connection String**, click **Show**

3. Copy the connection string (looks like):
   ```
   postgres://default:xxxxx@ep-xxxx-xxxx.us-east-1.postgres.vercel-storage.com:5432/verceldb
   ```

4. Go to **Project Settings** → **Environment Variables**

5. If not already set, add:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the connection string
   - **Environments**: Check all three

---

## Cost

**Free Tier (Hobby):**
- $0/month
- 256 MB storage
- 60 compute hours/month
- Perfect for development and small apps

**Pro Tier:**
- $20/month
- 512 MB storage
- Unlimited compute
- Daily backups
- Point-in-time recovery

---

## Summary: 3 Simple Steps

1. **Create Vercel Postgres** in Storage tab → Click "Postgres" → Create
2. **Connect to your project** → Select your app → Click "Connect"
3. **Redeploy** → Go to Deployments → Redeploy

**Total time: ~2 minutes** ⚡

Your invoice system will work immediately with zero code changes!

---

## Your Code is Already Ready!

Your app.py already has:
```python
DATABASE_URL = os.environ.get('DATABASE_URL')
```

This automatically picks up Vercel Postgres! No changes needed. 🎉
