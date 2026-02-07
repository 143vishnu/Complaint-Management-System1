cd "C:\Users\Admin\Desktop\Complaint Management System1"

# Clean up any stuck merge state
if (Test-Path ".git\MERGE_HEAD") {
    Remove-Item ".git\MERGE_HEAD" -Force
}
if (Test-Path ".git\MERGE_MSG") {
    Remove-Item ".git\MERGE_MSG" -Force
}

# Reset to clean state
git reset --mixed HEAD

# Add and commit changes
git add .
git commit -m "Add Vercel deployment config and fix 404 errors"

# Push to GitHub
git push origin main

Write-Host "✅ Successfully pushed to GitHub!"
