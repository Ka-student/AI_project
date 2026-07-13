# news_project
掘金新闻实验项目

整体目录结构：
AI_project/ \n
├─ toutiao_project/    # Python FastAPI 后端项目（核心待分析文件夹）\n
├─ xwzx-news/          # Vue 前端项目\n
├─ README.md           # 项目部署说明文档\n
└─ database.sql        # MySQL数据库初始化脚本\n





运行方法：
将toutiao_project项目导入pycharm中，打开pycharm右侧的database，右击MySQL数据库，选择sql脚本 -> 运行脚本 -> databa.sql文件，在终端输入uvicorn mian:app --reload命令，运行后端。
运行cmd，cd到xwzx-news，执行npm run dev，运行前端，复制显示的网页，即可实现本地新闻项目。
