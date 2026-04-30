@echo off
chcp 65001 > nul
echo 编译 LaTeX 论文...
echo.
echo 第一次编译...
xelatex -interaction=nonstopmode paper.tex
echo.
echo 第二次编译（修复交叉引用）...
xelatex -interaction=nonstopmode paper.tex
echo.
echo 清理辅助文件...
del /Q *.aux *.log *.out *.toc 2>nul
echo.
echo 编译完成！输出文件：paper.pdf
