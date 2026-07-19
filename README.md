# EverytimeCleaner
에브리타임(Everytime) 내가 쓴 글 및 댓글 자동 삭제 프로그램 (GUI 지원)

# 🧹 Everytime Cleaner (에브리타임 클리너)

에브리타임에 작성한 내 글과 댓글을 자동으로 삭제해 주는 GUI 기반 데스크톱 애플리케이션입니다.

## 📌 필수 요구사항
*   Google Chrome 브라우저: 이 프로그램은 크롬 브라우저를 기반으로 작동하므로 반드시 설치되어 있어야 합니다.
*   PC에서만 사용이 가능합니다!
## 🚀 사용 방법
1.  프로그램 실행: 복잡한 명령어 입력 없이 `dist` 폴더에 생성된 `EverytimeCleaner.exe` 파일을 더블 클릭하여 실행합니다.
2.  설정 조작 (선택): 좌측 패널에서 동작 사이의 '최소 지연' 및 '최대 지연' 시간(초)을 설정합니다.
3.  작업 시작: '▶ 삭제 시작' 버튼을 누릅니다.
4.  로그인 및 인증: 브라우저 창이 열리면 5분 이내에 에브리타임 아이디/비밀번호를 입력하고 2단계 인증을 마쳐야 합니다.
5.  자동 삭제: 로그인이 완료되면 프로그램이 '내가 쓴 글' 및 '내가 쓴 댓글' 메뉴를 자동으로 탐색하며 삭제 작업을 진행합니다.

## 💡 주요 기능
*   직관적인 GUI: 작업 진행률(Progress Bar), 성공/실패 통계, 프로그램 실행 로그를 실시간으로 확인할 수 있습니다.
*   안전한 딜레이 기능: 봇 탐지로 인한 차단을 방지하기 위해 무작위 지연 시간(Random Delay)을 적용하여 안전하게 작동합니다.
*   헤드리스(Headless) 모드: 브라우저 창을 띄우지 않고 백그라운드에서 조용히 실행할 수 있습니다.
    *   주의: 첫 실행 시에는 에브리타임 로그인을 직접 해야 하므로 이 옵션을 꺼두어야 합니다.
*   안전한 중지 및 로그 저장: 언제든지 '■ 중지' 버튼을 눌러 안전하게 작업을 멈출 수 있으며, 작업이 끝난 후 전체 로그 내역을 `.txt` 파일로 저장할 수 있습니다.

---

# 🧹 Everytime Cleaner

A GUI-based desktop application that automatically deletes your posts and comments on the Everytime platform.

## 📌 Requirements
*   Google Chrome Browser: This application requires Google Chrome to be installed on your system.
*   Available only on PC!
## 🚀 How to Use
1.  Run the App: No command-line knowledge is required. Simply double-click the `EverytimeCleaner.exe` file located in your `dist` folder.
2.  Configure Settings (Optional): Set the 'Minimum Delay' and 'Maximum Delay' (in seconds) on the left panel.
3.  Start Deletion: Click the '▶ 삭제 시작' (Start) button.
4.  Login & Authentication: Once the browser opens, you have 5 minutes to manually log in and complete the 2-factor authentication.
5.  Automatic Cleanup: After a successful login, the cleaner will automatically navigate through your written posts and comments to delete them.

## 💡 Key Features
*   Intuitive GUI: Monitor the progress bar, success/failure statistics, and real-time execution logs directly from the dashboard.
*   Safe Delay Mechanism: Applies randomized delays between clicks and navigations to prevent your account from being flagged or blocked.
*   Headless Mode: Run the browser invisibly in the background. 
    *   Note: You must uncheck this option if you need to log in manually for the first time.
*   Safe Stop & Export Logs: You can safely halt the process at any time using the '■ 중지' (Stop) button and save your execution history as a `.txt` file.
