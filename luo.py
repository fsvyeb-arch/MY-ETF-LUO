with bot_c2.expander("⚙️ 標的管理 (庫存與資料備份)", expanded=True):
    st.markdown("#### ➕ 新增庫存標的")
    st.text_input("輸入代碼 (不需手打 .TW)", key="add_sym_bot", on_change=auto_fill_etf_name)
    st.text_input("自定義名稱", key="add_name_bot")
    a1, a2 = st.columns(2)
    a1.number_input("張數", step=1.0, key="add_h_bot")
    a2.number_input("均價", step=0.1, key="add_c_bot")
    st.button("確認新增", key="btn_add_bot", use_container_width=True, on_click=add_new_etf_bot)

    if st.session_state.my_data['etfs']:
        st.write("---")
        st.markdown("#### 📝 修改與刪除")
        for i, item in enumerate(st.session_state.my_data['etfs']):
            with st.expander(f"📍 {item['name']}"):
                e1, e2 = st.columns(2)
                e1.number_input("張數", value=float(item['holdings']), step=1.0, key=f"edit_h_{i}", on_change=save_edits)
                e2.number_input("均價", value=float(item['cost']), step=0.1, key=f"edit_c_{i}", on_change=save_edits)
                st.button(f"🗑️ 刪除", key=f"del_{i}", on_click=delete_etf, args=(i,), use_container_width=True)
        st.button("💾 儲存上方修改", use_container_width=True, type="secondary", on_click=save_edits)
    
    st.write("---")
    st.markdown("#### 🛡️ 資料庫備份與還原 (改 Code 前必備)")
    
    # 1. 提供下載目前的 settings.json
    json_string = json.dumps(st.session_state.my_data, ensure_ascii=False, indent=4)
    st.download_button(
        label="📥 下載完整資料庫備份 (settings.json)",
        data=json_string,
        file_name="settings.json",
        mime="application/json",
        use_container_width=True,
        type="primary"
    )
    
    # 2. 上傳還原 settings.json
    uploaded_file = st.file_uploader("📂 如果資料遺失，請在此上傳備份檔還原", type="json")
    if uploaded_file is not None:
        if st.button("🚨 確認覆蓋並還原資料", use_container_width=True):
            try:
                restored_data = json.load(uploaded_file)
                st.session_state.my_data = restored_data
                save_to_json(restored_data)
                st.success("✅ 資料庫已成功還原！正在重新載入...")
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"還原失敗，檔案格式可能錯誤：{e}")
