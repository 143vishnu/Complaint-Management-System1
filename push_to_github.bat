@echo off
cd /d "C:\Users\Admin\Desktop\Complaint Management System1"

echo Cleaning merge state...
del /F /Q .git\MERGE_HEAD 2>nul
del /F /Q .git\MERGE_MSG 2>nul

echo Adding files...
git add .

echo Committing changes...
git commit -m "Add Vercel deployment config and fix 404 errors"

echo Pushing to GitHub...
git push origin main

echo.
echo ✅ Successfully updated GitHub!
pause
