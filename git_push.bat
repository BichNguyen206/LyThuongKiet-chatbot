@echo off
set /p MSG="Cập nhật code: sửa và xóa một số file "
git add .
git commit -m "%MSG%"
git push
pause
