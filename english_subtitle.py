import streamlit as st
import streamlit.components.v1 as components
from youtube_transcript_api import YouTubeTranscriptApi
import json

st.set_page_config(layout="wide")
st.title("英文字幕學習工具")

# 用 markdown 顯示帶有 HTML 顏色與粗體的文字
st.markdown('請輸入 YouTube 影片 ID (例如網址中粗體部分: https://www.youtube.com/watch?v=<span style="color:brown; font-weight:bold;">OPf0YbXqDm0</span>)', unsafe_allow_html=True)

# text_input 的標籤（第一個參數）設為空字串 "" 或使用 label_visibility 隱藏
video_id = st.text_input("", "OPf0YbXqDm0", label_visibility="collapsed").strip()


if video_id:
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=["en"])

        subtitles = []
        for i, item in enumerate(transcript):
            subtitles.append({
                "index": i,
                "start": float(item.start),
                "duration": float(item.duration),
                "text": item.text
            })

        subtitles_json = json.dumps(subtitles, ensure_ascii=False)

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    margin: 0;
                    font-family: Arial, sans-serif;
                    color: #222;
                }}

                .container {{
                    display: flex;
                    gap: 20px;
                    height: 620px;
                }}

                .left {{
                    flex: 1.35;
                }}

                .right {{
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }}

                .search-input {{
                    width: 100%;
                    box-sizing: border-box;
                    padding: 10px 12px;
                    font-size: 15px;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    margin-bottom: 10px;
                }}

                .subtitle-panel {{
                    flex: 1;
                    overflow-y: auto;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 12px;
                    background: #fafafa;
                    scroll-behavior: smooth;
                }}

                .subtitle {{
                    padding: 10px;
                    margin-bottom: 8px;
                    border-radius: 8px;
                    cursor: pointer;
                    line-height: 1.5;
                    transition: background-color 0.15s ease;
                }}

                .subtitle:hover {{
                    background: #f0f0f0;
                }}

                .subtitle.active {{
                    background: #ffe9a8;
                    border-left: 4px solid #e0a800;
                    padding-left: 8px;
                }}

                .time {{
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 4px;
                }}

                .text {{
                    font-size: 16px;
                    white-space: pre-wrap;
                    word-break: break-word;
                }}

                .hidden {{
                    display: none;
                }}

                #player {{
                    width: 100%;
                    height: 420px;
                    background: #000;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="left">
                    <div id="player"></div>
                </div>

                <div class="right">
                    <input id="searchInput" class="search-input" type="text" placeholder="搜尋單字，例如 actually">
                    <div id="subtitlePanel" class="subtitle-panel"></div>
                </div>
            </div>

            <script>
                const subtitles = {subtitles_json};
                const subtitlePanel = document.getElementById("subtitlePanel");
                const searchInput = document.getElementById("searchInput");

                let player = null;
                let activeIndex = -1;
                let subtitleMap = {{}};

                function formatTime(sec) {{
                    sec = Math.floor(sec);
                    const m = Math.floor(sec / 60);
                    const s = sec % 60;
                    return m + ":" + String(s).padStart(2, "0");
                }}

                function renderSubtitles(filterText = "") {{
                    subtitlePanel.innerHTML = "";
                    subtitleMap = {{}};

                    const keyword = filterText.trim().toLowerCase();

                    subtitles.forEach(item => {{
                        const matched = item.text.toLowerCase().includes(keyword);
                        if (keyword && !matched) return;

                        const row = document.createElement("div");
                        row.className = "subtitle";
                        row.setAttribute("data-index", item.index);

                        row.innerHTML = `
                            <div class="time">${{formatTime(item.start)}}</div>
                            <div class="text"></div>
                        `;
                        row.querySelector(".text").textContent = item.text;

                        row.addEventListener("click", function() {{
                            if (player && typeof player.seekTo === "function") {{
                                player.seekTo(item.start, true);
                                player.playVideo();
                                setActiveSubtitle(item.index, true);
                            }}
                        }});

                        subtitlePanel.appendChild(row);
                        subtitleMap[item.index] = row;
                    }});

                    if (activeIndex !== -1 && subtitleMap[activeIndex]) {{
                        subtitleMap[activeIndex].classList.add("active");
                    }}
                }}

                function setActiveSubtitle(index, scrollIntoView) {{
                    if (activeIndex !== -1 && subtitleMap[activeIndex]) {{
                        subtitleMap[activeIndex].classList.remove("active");
                    }}

                    activeIndex = index;

                    if (subtitleMap[activeIndex]) {{
                        subtitleMap[activeIndex].classList.add("active");

                        if (scrollIntoView) {{
                            subtitleMap[activeIndex].scrollIntoView({{
                                behavior: "smooth",
                                block: "center"
                            }});
                        }}
                    }}
                }}

                function findCurrentSubtitleIndex(currentTime) {{
                    for (let i = 0; i < subtitles.length; i++) {{
                        const start = subtitles[i].start;
                        let end = start + subtitles[i].duration;

                        if (i < subtitles.length - 1) {{
                            end = subtitles[i + 1].start;
                        }}

                        if (currentTime >= start && currentTime < end) {{
                            return subtitles[i].index;
                        }}
                    }}
                    return -1;
                }}

                searchInput.addEventListener("input", function() {{
                    renderSubtitles(this.value);
                }});

                renderSubtitles();

                // 明確掛到 window，避免 YouTube API 找不到
                window.onYouTubeIframeAPIReady = function() {{
                    player = new YT.Player("player", {{
                        height: "420",
                        width: "100%",
                        videoId: "{video_id}",
                        playerVars: {{
                            playsinline: 1,
                            rel: 0
                        }},
                        events: {{
                            onReady: function() {{
                                // 播放器準備好後，開始每 300ms 檢查目前時間
                                setInterval(function() {{
                                    if (!player || typeof player.getCurrentTime !== "function") return;

                                    const currentTime = player.getCurrentTime();
                                    const idx = findCurrentSubtitleIndex(currentTime);

                                    if (idx !== -1 && idx !== activeIndex) {{
                                        setActiveSubtitle(idx, false);
                                    }}
                                }}, 300);
                            }}
                        }}
                    }});
                }};

                // 載入 YouTube IFrame API
                const tag = document.createElement("script");
                tag.src = "https://www.youtube.com/iframe_api";
                document.head.appendChild(tag);
            </script>
        </body>
        </html>
        """

        components.html(html_code, height=650)

    except Exception as e:
        st.error(f"無法取得字幕：{e}")
