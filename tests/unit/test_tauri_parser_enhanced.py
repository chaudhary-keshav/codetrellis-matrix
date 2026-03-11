"""
Tests for EnhancedTauriParser — Tauri desktop framework analysis.

Part of CodeTrellis v5.4 Rust Framework Support.
Tests: command extraction, state management, events, plugins,
windows, menus, config, version detection, self-selection.
"""

import pytest
from codetrellis.tauri_parser_enhanced import EnhancedTauriParser, TauriParseResult


@pytest.fixture
def parser():
    return EnhancedTauriParser()


# ═══════════════════════════════════════════════════════════════════
# Self-Selection Tests
# ═══════════════════════════════════════════════════════════════════

class TestTauriSelfSelection:

    def test_returns_empty_for_non_tauri_file(self, parser):
        code = '''
use std::io;
fn main() {}
'''
        result = parser.parse(code, "main.rs")
        assert result.commands == []
        assert result.detected_frameworks == []

    def test_detects_tauri_import(self, parser):
        code = '''
use tauri::{command, State};
'''
        result = parser.parse(code, "main.rs")
        assert "tauri" in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Command Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestTauriCommandExtraction:

    def test_extract_basic_commands(self, parser):
        code = '''
use tauri::command;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

#[tauri::command]
async fn fetch_data(state: State<'_, AppState>) -> Result<Vec<Item>, String> {
    Ok(state.db.get_items().await.map_err(|e| e.to_string())?)
}
'''
        result = parser.parse(code, "commands.rs")
        assert len(result.commands) >= 2
        names = [c.name for c in result.commands]
        assert "greet" in names
        assert "fetch_data" in names

    def test_extract_command_with_state(self, parser):
        code = '''
use tauri::{command, State};

#[tauri::command]
fn get_count(counter: State<'_, Counter>) -> u32 {
    counter.0.load(Ordering::Relaxed)
}
'''
        result = parser.parse(code, "commands.rs")
        assert len(result.commands) >= 1

    def test_extract_generate_handler(self, parser):
        code = '''
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            greet,
            fetch_data,
            save_item,
            delete_item,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
'''
        result = parser.parse(code, "main.rs")
        assert len(result.commands) >= 1


# ═══════════════════════════════════════════════════════════════════
# State Tests
# ═══════════════════════════════════════════════════════════════════

class TestTauriState:

    def test_extract_managed_state(self, parser):
        code = '''
use tauri::{command, Manager, State};

struct AppState {
    db: Database,
}

#[tauri::command]
fn get_data(state: State<'_, AppState>) -> String {
    "ok".into()
}

fn main() {
    tauri::Builder::default()
        .manage(AppState { db: Database::new() })
        .run(tauri::generate_context!())
        .unwrap();
}
'''
        result = parser.parse(code, "main.rs")
        assert len(result.state) >= 1


# ═══════════════════════════════════════════════════════════════════
# Event Tests
# ═══════════════════════════════════════════════════════════════════

class TestTauriEvents:

    def test_extract_emit_events(self, parser):
        code = '''
use tauri::Manager;

fn setup(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    app.emit_all("app-started", Payload { message: "ready" })?;
    Ok(())
}
'''
        result = parser.parse(code, "setup.rs")
        assert len(result.events) >= 1

    def test_extract_listen_events(self, parser):
        code = '''
use tauri::Manager;

fn setup(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    app.listen_global("ui-event", |event| {
        println!("got event: {:?}", event.payload());
    });
    Ok(())
}
'''
        result = parser.parse(code, "setup.rs")
        assert len(result.events) >= 1


# ═══════════════════════════════════════════════════════════════════
# Plugin Tests
# ═══════════════════════════════════════════════════════════════════

class TestTauriPlugins:

    def test_extract_plugin_registration(self, parser):
        code = '''
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_sql::Builder::default().build())
        .run(tauri::generate_context!())
        .unwrap();
}
'''
        result = parser.parse(code, "main.rs")
        assert len(result.plugins) >= 2

    def test_extract_custom_plugin(self, parser):
        code = '''
use tauri::plugin;

let my_plugin = plugin::Builder::new("my-plugin")
    .invoke_handler(tauri::generate_handler![custom_cmd])
    .build();

tauri::Builder::default()
    .plugin(my_plugin);
'''
        result = parser.parse(code, "main.rs")
        assert len(result.plugins) >= 1


# ═══════════════════════════════════════════════════════════════════
# Window Tests
# ═══════════════════════════════════════════════════════════════════

class TestTauriWindows:

    def test_extract_window_creation(self, parser):
        code = '''
use tauri::{Manager, WindowBuilder, WindowUrl};

fn setup(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    WindowBuilder::new(app, "settings", WindowUrl::App("settings.html".into()))
        .title("Settings")
        .inner_size(800.0, 600.0)
        .build()?;
    Ok(())
}
'''
        result = parser.parse(code, "setup.rs")
        assert len(result.windows) >= 1


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestTauriVersionDetection:

    def test_detect_tauri_ecosystem(self, parser):
        code = '''
use tauri::{command, State, Manager};
use tauri_plugin_store;
'''
        result = parser.parse(code, "main.rs")
        assert "tauri" in result.detected_frameworks

    def test_detect_v2_patterns(self, parser):
        code = '''
use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::default().build())
        .run(tauri::generate_context!())
        .unwrap();
}
'''
        result = parser.parse(code, "main.rs")
        assert result.tauri_version != "" or result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestTauriIntegration:

    def test_full_tauri_app(self, parser):
        """Test parsing a complete Tauri application entry point."""
        code = '''
use tauri::{command, Manager, State};

struct AppState {
    count: std::sync::atomic::AtomicU32,
}

#[tauri::command]
fn increment(state: State<'_, AppState>) -> u32 {
    state.count.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
}

#[tauri::command]
fn get_count(state: State<'_, AppState>) -> u32 {
    state.count.load(std::sync::atomic::Ordering::Relaxed)
}

fn main() {
    tauri::Builder::default()
        .manage(AppState { count: std::sync::atomic::AtomicU32::new(0) })
        .invoke_handler(tauri::generate_handler![increment, get_count])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
'''
        result = parser.parse(code, "main.rs")
        assert "tauri" in result.detected_frameworks
        assert len(result.commands) >= 2
        assert len(result.state) >= 1
