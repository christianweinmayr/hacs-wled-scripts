# How to Deploy This to GitHub and HACS

## Step 1: Create GitHub Repository

1. Go to https://github.com and sign in
2. Click the "+" icon → "New repository"
3. Name it: `hacs-wled-scripts` (or any name you prefer)
4. Description: "WLED effect scripts for Home Assistant"
5. Make it Public
6. Do NOT initialize with README (we already have one)
7. Click "Create repository"

## Step 2: Upload Files to GitHub

### Option A: Using GitHub Web Interface (Easiest)

1. In your new repository, click "uploading an existing file"
2. Drag and drop all files from the `hacs-wled-scripts` folder
3. Commit changes

### Option B: Using Git Command Line

```bash
cd ~/Downloads/wledscript/hacs-wled-scripts

# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - WLED fade effect script"

# Add your GitHub repository as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/hacs-wled-scripts.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Add to HACS

### On Your Home Assistant:

1. Open Home Assistant
2. Go to **HACS** → **Integrations**
3. Click the **⋮** (three dots menu) in the top right
4. Select **Custom repositories**
5. Add your repository:
   - **Repository**: `https://github.com/YOUR_USERNAME/hacs-wled-scripts`
   - **Category**: Select `Integration` or `Python Script`
6. Click **Add**
7. Close the dialog
8. Click **+ Explore & Download Repositories**
9. Search for "WLED Effect Scripts"
10. Click it and then **Download**
11. Restart Home Assistant

## Step 4: Configure

1. Navigate to `/config/pyscript/wled_fade_effect.py`
2. Edit the configuration variables at the top (WLED_IP, coordinates, etc.)
3. Add the helper and automation from `examples/configuration.yaml` to your `configuration.yaml`
4. Restart Home Assistant or reload automations
5. Add a dashboard card from `examples/dashboard.yaml`

## Step 5: Use It!

Toggle the `input_boolean.wled_fade_effect` from your dashboard to start/stop the effect.

## Updating the Script

When you make changes:

```bash
cd ~/Downloads/wledscript/hacs-wled-scripts
git add .
git commit -m "Description of changes"
git push
```

Then in Home Assistant HACS, you can update the integration to get the latest version.

## Troubleshooting

### Repository not showing in HACS
- Make sure the repository is Public on GitHub
- Verify `hacs.json` exists in the repository root
- Check HACS logs: Settings → System → Logs → Filter by "hacs"

### Pyscript not loaded
- Ensure Pyscript integration is installed via HACS
- Check Configuration → Integrations → Pyscript
- Verify pyscript folder exists: `/config/pyscript/`
- Check logs for pyscript errors

### Script not starting
- Check Home Assistant logs: Settings → System → Logs
- Verify WLED IP is correct and reachable
- Test WLED connection: `http://YOUR_WLED_IP/json/info`
