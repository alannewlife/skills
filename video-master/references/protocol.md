# 项目与确认协议

CLI 位于此 Skill 的 `scripts/video_master.py`。下方 `SKILL_DIR` 是当前 Skill 的绝对路径；`PROJECT` 是用户的视频项目绝对路径。不要覆盖已有目录。调用示例：

```bash
python3 "$SKILL_DIR/scripts/video_master.py" init "$PROJECT" --story /absolute/path/story.md
python3 "$SKILL_DIR/scripts/video_master.py" serve "$PROJECT" --port 0
python3 "$SKILL_DIR/scripts/video_master.py" status "$PROJECT"
python3 "$SKILL_DIR/scripts/video_master.py" wait "$PROJECT" style --timeout 50
python3 "$SKILL_DIR/scripts/video_master.py" wait "$PROJECT" styleframe --after-revision 3 --timeout 50
python3 "$SKILL_DIR/scripts/video_master.py" wait "$PROJECT" restoration --after-revision 10 --timeout 50
```

`init` 会原样归档 UTF-8 故事，复制公司默认 Logo 到项目；`--logo /path/logo.png` 可换成自己的素材。页面启动后打印实际 URL，监听 `127.0.0.1`，自动打开浏览器；如需避免打开浏览器，添加 `--no-browser`。服务持续运行时可在另一个命令读取状态。`wait` 至多等 50 秒，退出码 2 表示仍在等待；保持对话运行并再次等待，不得解释为确认。传入展示版本的 `--after-revision` 后，用户保存修改意见也会立即返回状态；应检查是草稿意见还是确认，再决定重做或进入下一阶段。页面本身不会唤醒已经结束的 Codex 对话；若对话停止，用户需在聊天中恢复。服务重启后仍读取项目文件。

等待命令运行时会短暂写入仅含阶段和时间的心跳文件，页面显示“自动等待已连接”；进程结束后心跳失效。它证明有等待程序运行，不保证已结束的 Codex 对话会被重新唤醒。Agent 在每个确认关口保持等待进程运行，50 秒超时立即以最新 revision 再次等待；用户提交后先读取状态，再制作对应的下一阶段或按意见修改。等待和制作期间不要结束当前 Codex 任务，直到用户明确停止、完成交付或发生确实无法处理的故障。

项目 `source/story.md` 是原故事，`assets/` 是图像及品牌，`audio/` 是旁白，`video/` 是样片及工程，`output/` 是交付物，`project.json` 是唯一状态文件。媒体路径必须是项目目录内相对路径。项目状态使用单调递增的 revision，用户按钮确认时写历史快照和依赖文件校验值；旧浏览器提交会被拒绝。已确认阶段返回修改时，后续变为 stale；下一阶段必须由 Codex 依据最新输入重新检查并用 `propose` 发布，才能再次确认。内容不变时仍可经检查重新发布，不能跳过检查。已确认文件被外部修改时会阻止后续确认，回到受影响阶段重新确认。

Codex 在当前阶段准备好真实资源后，以文件形式发布对象（不得调用用户确认 API）：

开始制作或重做图片、视频前，先用 `propose` 将当前阶段的 `processing` 设为 `true`，页面才会在对应媒体框显示九宫格制作状态并禁止确认。分镜仅修改指定幕时，同时写入 `processing_scene_ids`（稳定场景 ID 数组）；整组制作则省略或置空该数组。完成后发布新媒体并设 `processing: false`、清空 `processing_scene_ids`；失败或暂停时也要及时清除状态并向用户说明，不能让加载动画冒充仍在制作。所有更新都读取最新 revision，保留尚未处理的用户意见。

```bash
python3 "$SKILL_DIR/scripts/video_master.py" propose "$PROJECT" styleframe --json /absolute/path/frame-proposal.json
python3 "$SKILL_DIR/scripts/video_master.py" propose "$PROJECT" storyboard --json /absolute/path/storyboard-proposal.json
python3 "$SKILL_DIR/scripts/video_master.py" propose "$PROJECT" sample --json /absolute/path/sample-proposal.json
python3 "$SKILL_DIR/scripts/video_master.py" propose "$PROJECT" restoration --json /absolute/path/restoration-proposal.json
python3 "$SKILL_DIR/scripts/video_master.py" propose "$PROJECT" final --json /absolute/path/final-proposal.json
```

修改分镜时先读取最新状态，以场景稳定 ID 定位用户意见，只更新对应场景并保留其他编辑；发布时带上 `--expected-revision <读取时的版本>`。若用户在制作期间又更新了项目，命令会拒绝覆盖：重新读取并核对意见是否变化，再决定合并或重新制作，不得清空未经处理的意见。

Schema 2 样片与逐幕还原提案（图、视频及 `asset` 均须是项目内真实文件）：

```json
{"image":"assets/styleframe-v1.png", "notes":""}
```

```json
{"scenes":[{"id":"scene-001","title":"开场","narration":"对应故事的旁白。","description":"画面与动作说明。","image":"assets/scene-001-v1.png","notes":"","source_excerpt":"对应原文"}],"notes":""}
```

```json
{"video":"video/sample-v1.mp4","comparison_scene_id":"scene-001","comparison_frame":"review/sample-frame-v1.png","comparison_time":8.2,"asset_plan":[{"name":"人物与桌面","method":"drawn","source":"已确认分镜的员工与桌面","asset":"assets/employee.png"},{"name":"关系线","method":"code","source":"按分镜线条样式与连接方向绘制"}],"deviation":"","notes":""}
```

`comparison_frame` 必须是该视频在 `comparison_time` 的实际编码帧；场景 ID 必须属于已确认分镜。分工 `method` 为 `drawn`（绘画）、`code`（代码）、`existing`（已有素材）或 `group`（整体保留），`asset` 可选。`deviation` 必须明确填写：无差异用空字符串；有无法消除的差异时具体说明。Agent 不得设置 `deviation_accepted`，只有用户可在页面勾选。

```json
{"review_video_required":true,"comparisons":[{"scene_id":"scene-001","video":"video/scene-001-v1.mp4","frame":"review/scene-001-overview-v1.png","asset_plan":[{"name":"人物与桌面","method":"drawn","source":"已确认分镜的员工与桌面"},{"name":"关系线","method":"code","source":"按分镜线条样式与连接方向绘制"}],"deviation":"","notes":""}],"notes":""}
```

`comparisons` 必须覆盖全部已确认场景且 ID 唯一；新项目的 `review_video_required` 为 true，每幕必须提供项目内实际编码的 `video` 和从该视频提取的 `frame`。页面右侧播放带声音的片段，用户在此审核运镜、入场、连线与旁白，最终视频由确认后的片段整合。已有 schema 2 项目保持原要求；用户明确要求片段审核时，在返回逐幕阶段后通过 `propose` 设置 `review_video_required: true`，并重新发布各幕。视频、截图和素材均绑定确认版本，文件变化须重新审核。有差异要写出，只有用户可逐幕勾选接受。场景卡片的“修改实施”写入 `requested_scene_ids`，整体按钮写入 `overall_requested`；每次只处理明确提交的请求，使用最新 revision 合并其余未提交草稿。处理失败或暂停时清除 `processing` 并说明原因。

```json
{"video":"output/final-v1.mp4", "notes":""}
```

可修改旁白、画面说明、顺序及删除幕；新增幕或重画由 Codex 根据意见准备并重新发布。编辑后的当前内容才是后续依据。页面中的修改意见会阻止确认，必须由 Codex 处理并清空已处理意见；若有不能满足的要求，向用户说明，不要悄悄清空。

新项目使用 schema 2：样片之后进入 `restoration`，确认后才进入 `final`。历史 schema 1 项目继续使用原有五阶段与确认记录，不自动迁移或凭空赋予还原确认。用户明确希望在既有项目启用新流程时，先读取最新 revision 并说明：文件和历史记录保留；若原项目已到样片或之后，将回到样片并要求补充对照、重新确认，后续确认变为待复核，不会自动重新生成视频。用户已确认后才执行 `python3 "$SKILL_DIR/scripts/video_master.py" upgrade "$PROJECT" --expected-revision <最新版本>`。若仍在前面的阶段，保留当前位置，后续按新流程推进。

每张分镜卡片的“修改实施”将该场景 ID 加入 `requested_scene_ids`；页面会同时保存其他卡片的当前草稿，但尚未点击提交的意见不应自动生成。整体意见区的“修改实施”设置 `overall_requested`。处理后只清除已完成的请求 ID 和相应意见，保留其他场景的已提交请求、未提交草稿和旁白改动；多个请求逐个处理。其他阶段的“修改实施”提交该阶段意见，不代替“确认并继续”。

**聊天降级：**页面无法使用或用户要求仅聊天时，逐项展示和讨论同一阶段内容；仅在用户在聊天中明确确认当前阶段、内容和版本后，由 Codex 使用 `python3 scripts/chat_confirm.py PROJECT STAGE REVISION` 记录；不得将 Agent 的判断视为用户确认。脚本与页面采用同样的校验、版本与历史机制，`history` 记录标记为聊天确认。用户没有明确确认时不能调用。
对列出的差异，只有用户明确逐项接受后才可增加 `--accept-deviation`（样片）或逐幕重复 `--accept-scene 场景ID`（还原）；一般的“确认”不自动解释为接受未指出的差异。

页面右上角“配音设置”用于安全配置 MiMo。Mac 和 Windows 使用各自系统凭证存储，其他系统支持进程环境变量。使用 `python` 替代 `python3`（如 Windows 仅有 `python`）时命令等价。不要在聊天中索取或输出 API Key。
