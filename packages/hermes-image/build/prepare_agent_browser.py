#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, *, path: Path) -> str:
    if old not in text:
        raise RuntimeError(f"failed to locate patch marker in {path}: {old[:80]!r}")
    return text.replace(old, new, 1)


def patch_interaction(root: Path) -> None:
    path = root / "cli" / "src" / "native" / "interaction.rs"
    text = path.read_text(encoding="utf-8")
    if "GHOSTSHIP_HUMANIZED_AGENT_BROWSER" in text:
        return

    text = replace_once(
        text,
        "use std::collections::HashMap;\n",
        "use std::{collections::HashMap, time::{SystemTime, UNIX_EPOCH}};\n",
        path=path,
    )
    text = replace_once(
        text,
        """    client
        .send_command_typed::<_, Value>(
            "Input.dispatchMouseEvent",
            &DispatchMouseEventParams {
                event_type: "mouseMoved".to_string(),
                x,
                y,
                button: None,
                buttons: None,
                click_count: None,
                delta_x: None,
                delta_y: None,
                modifiers: None,
            },
            Some(&effective_session_id),
        )
        .await?;
    Ok(())
}
""",
        """    ghostship_human_mouse_move(client, &effective_session_id, x, y).await?;
    Ok(())
}
""",
        path=path,
    )
    text = replace_once(
        text,
        """    // Insert text (keyboard input dispatched at page level, use parent session_id)
    client
        .send_command_typed::<_, Value>(
            "Input.insertText",
            &InsertTextParams {
                text: value.to_string(),
            },
            Some(session_id),
        )
        .await?;

    Ok(())
}
""",
        """    // Type per character so form fill has CloakBrowser-like human timing.
    ghostship_human_type_text(client, session_id, value, None).await?;

    Ok(())
}
""",
        path=path,
    )
    text = replace_once(
        text,
        "    let delay = delay_ms.unwrap_or(0);\n\n    for ch in text.chars() {\n",
        "    for ch in text.chars() {\n",
        path=path,
    )
    text = replace_once(
        text,
        """        } else {
            // VS Code/Electron webviews reject repeated dispatchKeyEvent calls
            // carrying printable `text`. Insert printable characters directly
            // and reserve key events for controls like Enter and Tab.
            client
                .send_command_typed::<_, Value>(
                    "Input.insertText",
                    &InsertTextParams {
                        text: ch.to_string(),
                    },
                    Some(session_id),
                )
                .await?;
        }

        if delay > 0 {
            tokio::time::sleep(tokio::time::Duration::from_millis(delay)).await;
        }
    }

    Ok(())
}
""",
        """        } else if ghostship_shift_symbol_info(ch).is_some() {
            ghostship_type_shift_symbol(client, session_id, ch).await?;
        } else {
            // VS Code/Electron webviews reject repeated dispatchKeyEvent calls
            // carrying printable `text`. Insert printable characters directly
            // and reserve key events for controls like Enter and Tab.
            client
                .send_command_typed::<_, Value>(
                    "Input.insertText",
                    &InsertTextParams {
                        text: ch.to_string(),
                    },
                    Some(session_id),
                )
                .await?;
        }

        ghostship_typing_pause(delay_ms).await;
    }

    Ok(())
}
""",
        path=path,
    )
    text = replace_once(
        text,
        """    if let Some(sel) = selector_or_ref {
        let (object_id, effective_session_id) =
            resolve_element_object_id(client, session_id, ref_map, sel, iframe_sessions).await?;
        let js = "function(dx, dy) { this.scrollBy(dx, dy); }".to_string();
        client
            .send_command_typed::<_, Value>(
                "Runtime.callFunctionOn",
                &CallFunctionOnParams {
                    function_declaration: js,
                    object_id: Some(object_id),
                    arguments: Some(vec![
                        CallArgument {
                            value: Some(serde_json::json!(delta_x)),
                            object_id: None,
                        },
                        CallArgument {
                            value: Some(serde_json::json!(delta_y)),
                            object_id: None,
                        },
                    ]),
                    return_by_value: Some(true),
                    await_promise: Some(false),
                },
                Some(&effective_session_id),
            )
            .await?;
    } else {
        let js = format!("window.scrollBy({}, {})", delta_x, delta_y);
        client
            .send_command_typed::<_, Value>(
                "Runtime.evaluate",
                &EvaluateParams {
                    expression: js,
                    return_by_value: Some(true),
                    await_promise: Some(false),
                },
                Some(session_id),
            )
            .await?;
    }
    Ok(())
}
""",
        """    if let Some(sel) = selector_or_ref {
        let (object_id, effective_session_id) =
            resolve_element_object_id(client, session_id, ref_map, sel, iframe_sessions).await?;
        ghostship_human_element_scroll(client, &effective_session_id, &object_id, delta_x, delta_y).await?;
    } else {
        ghostship_human_wheel(client, session_id, delta_x, delta_y).await?;
    }
    Ok(())
}
""",
        path=path,
    )
    text = replace_once(
        text,
        """async fn dispatch_click(
    client: &CdpClient,
    session_id: &str,
    x: f64,
    y: f64,
    button: &str,
    click_count: i32,
) -> Result<(), String> {
    // Move
    client
        .send_command_typed::<_, Value>(
            "Input.dispatchMouseEvent",
            &DispatchMouseEventParams {
                event_type: "mouseMoved".to_string(),
                x,
                y,
                button: None,
                buttons: None,
                click_count: None,
                delta_x: None,
                delta_y: None,
                modifiers: None,
            },
            Some(session_id),
        )
        .await?;
""",
        """const GHOSTSHIP_HUMANIZED_AGENT_BROWSER: &str = "ghostship-humanized-agent-browser-v1";

fn ghostship_humanize_enabled() -> bool {
    std::env::var("GHOSTSHIP_AGENT_BROWSER_HUMANIZE")
        .map(|value| !matches!(value.trim().to_ascii_lowercase().as_str(), "0" | "false" | "off" | "no"))
        .unwrap_or(true)
}

fn ghostship_seed() -> u64 {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos() as u64)
        .unwrap_or(0);
    let mut x = nanos ^ 0x9E37_79B9_7F4A_7C15;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    x.wrapping_mul(0x2545_F491_4F6C_DD1D)
}

fn ghostship_rand_unit() -> f64 {
    (ghostship_seed() as f64) / (u64::MAX as f64)
}

fn ghostship_rand(min: f64, max: f64) -> f64 {
    min + (max - min) * ghostship_rand_unit()
}

fn ghostship_rand_u64(min: u64, max: u64) -> u64 {
    if max <= min {
        return min;
    }
    min + ((ghostship_rand_unit() * ((max - min + 1) as f64)).floor() as u64).min(max - min)
}

async fn ghostship_sleep_range(min_ms: u64, max_ms: u64) {
    tokio::time::sleep(tokio::time::Duration::from_millis(ghostship_rand_u64(min_ms, max_ms))).await;
}

fn ghostship_ease_in_out(t: f64) -> f64 {
    if t < 0.5 {
        4.0 * t * t * t
    } else {
        1.0 - (-2.0 * t + 2.0).powi(3) / 2.0
    }
}

fn ghostship_bezier(p0: (f64, f64), p1: (f64, f64), p2: (f64, f64), p3: (f64, f64), t: f64) -> (f64, f64) {
    let u = 1.0 - t;
    let uu = u * u;
    let uuu = uu * u;
    let tt = t * t;
    let ttt = tt * t;
    (
        uuu * p0.0 + 3.0 * uu * t * p1.0 + 3.0 * u * tt * p2.0 + ttt * p3.0,
        uuu * p0.1 + 3.0 * uu * t * p1.1 + 3.0 * u * tt * p2.1 + ttt * p3.1,
    )
}

async fn ghostship_mouse_event(
    client: &CdpClient,
    session_id: &str,
    event_type: &str,
    x: f64,
    y: f64,
    button: Option<String>,
    buttons: Option<i32>,
    click_count: Option<i32>,
    delta_x: Option<f64>,
    delta_y: Option<f64>,
) -> Result<(), String> {
    client
        .send_command_typed::<_, Value>(
            "Input.dispatchMouseEvent",
            &DispatchMouseEventParams {
                event_type: event_type.to_string(),
                x,
                y,
                button,
                buttons,
                click_count,
                delta_x,
                delta_y,
                modifiers: None,
            },
            Some(session_id),
        )
        .await?;
    Ok(())
}

async fn ghostship_human_mouse_move(
    client: &CdpClient,
    session_id: &str,
    target_x: f64,
    target_y: f64,
) -> Result<(), String> {
    if !ghostship_humanize_enabled() {
        return ghostship_mouse_event(client, session_id, "mouseMoved", target_x, target_y, None, None, None, None, None).await;
    }

    let start_x = (target_x + ghostship_rand(-120.0, 120.0)).max(0.0);
    let start_y = (target_y + ghostship_rand(-80.0, 80.0)).max(0.0);
    let dx = target_x - start_x;
    let dy = target_y - start_y;
    let dist = (dx * dx + dy * dy).sqrt();
    let steps = ((dist / 28.0).round() as i32).clamp(10, 42);
    let perp = if dist > 0.0 { (-dy / dist, dx / dist) } else { (0.0, 0.0) };
    let cp1 = (
        start_x + dx * 0.25 + perp.0 * ghostship_rand(-0.25 * dist, 0.25 * dist),
        start_y + dy * 0.25 + perp.1 * ghostship_rand(-0.25 * dist, 0.25 * dist),
    );
    let cp2 = (
        start_x + dx * 0.75 + perp.0 * ghostship_rand(-0.25 * dist, 0.25 * dist),
        start_y + dy * 0.75 + perp.1 * ghostship_rand(-0.25 * dist, 0.25 * dist),
    );

    for i in 0..=steps {
        let progress = i as f64 / steps as f64;
        let eased = ghostship_ease_in_out(progress);
        let (mut x, mut y) = ghostship_bezier((start_x, start_y), cp1, cp2, (target_x, target_y), eased);
        let wobble = (std::f64::consts::PI * progress).sin() * 2.2;
        x += ghostship_rand(-wobble, wobble);
        y += ghostship_rand(-wobble, wobble);
        ghostship_mouse_event(client, session_id, "mouseMoved", x.round(), y.round(), None, None, None, None, None).await?;
        if i < steps {
            ghostship_sleep_range(5, 22).await;
        }
    }
    if ghostship_rand_unit() < 0.25 {
        ghostship_mouse_event(
            client,
            session_id,
            "mouseMoved",
            (target_x + ghostship_rand(-3.0, 3.0)).round(),
            (target_y + ghostship_rand(-3.0, 3.0)).round(),
            None,
            None,
            None,
            None,
            None,
        ).await?;
        ghostship_sleep_range(25, 70).await;
    }
    Ok(())
}

async fn ghostship_typing_pause(delay_ms: Option<u64>) {
    if !ghostship_humanize_enabled() {
        if let Some(delay) = delay_ms {
            if delay > 0 {
                tokio::time::sleep(tokio::time::Duration::from_millis(delay)).await;
            }
        }
        return;
    }
    if let Some(delay) = delay_ms {
        tokio::time::sleep(tokio::time::Duration::from_millis(delay)).await;
    } else if ghostship_rand_unit() < 0.08 {
        ghostship_sleep_range(220, 620).await;
    } else {
        ghostship_sleep_range(45, 165).await;
    }
}

async fn ghostship_human_type_text(
    client: &CdpClient,
    session_id: &str,
    text: &str,
    delay_ms: Option<u64>,
) -> Result<(), String> {
    type_text_into_active_context(client, session_id, text, delay_ms).await
}

fn ghostship_shift_symbol_info(ch: char) -> Option<(&'static str, i32)> {
    match ch {
        '!' => Some(("Digit1", 49)),
        '@' => Some(("Digit2", 50)),
        '#' => Some(("Digit3", 51)),
        '$' => Some(("Digit4", 52)),
        '%' => Some(("Digit5", 53)),
        '^' => Some(("Digit6", 54)),
        '&' => Some(("Digit7", 55)),
        '*' => Some(("Digit8", 56)),
        '(' => Some(("Digit9", 57)),
        ')' => Some(("Digit0", 48)),
        '_' => Some(("Minus", 189)),
        '+' => Some(("Equal", 187)),
        '{' => Some(("BracketLeft", 219)),
        '}' => Some(("BracketRight", 221)),
        '|' => Some(("Backslash", 220)),
        ':' => Some(("Semicolon", 186)),
        '"' => Some(("Quote", 222)),
        '<' => Some(("Comma", 188)),
        '>' => Some(("Period", 190)),
        '?' => Some(("Slash", 191)),
        '~' => Some(("Backquote", 192)),
        _ => None,
    }
}

async fn ghostship_type_shift_symbol(client: &CdpClient, session_id: &str, ch: char) -> Result<(), String> {
    let Some((code, key_code)) = ghostship_shift_symbol_info(ch) else {
        return Ok(());
    };
    let key = ch.to_string();
    client
        .send_command_typed::<_, Value>(
            "Input.dispatchKeyEvent",
            &DispatchKeyEventParams {
                event_type: "keyDown".to_string(),
                key: Some("Shift".to_string()),
                code: Some("ShiftLeft".to_string()),
                text: None,
                unmodified_text: None,
                windows_virtual_key_code: Some(16),
                native_virtual_key_code: Some(16),
                modifiers: Some(8),
            },
            Some(session_id),
        )
        .await?;
    ghostship_sleep_range(20, 70).await;
    client
        .send_command_typed::<_, Value>(
            "Input.dispatchKeyEvent",
            &DispatchKeyEventParams {
                event_type: "keyDown".to_string(),
                key: Some(key.clone()),
                code: Some(code.to_string()),
                text: Some(key.clone()),
                unmodified_text: Some(key.clone()),
                windows_virtual_key_code: Some(key_code),
                native_virtual_key_code: Some(key_code),
                modifiers: Some(8),
            },
            Some(session_id),
        )
        .await?;
    ghostship_sleep_range(25, 95).await;
    client
        .send_command_typed::<_, Value>(
            "Input.dispatchKeyEvent",
            &DispatchKeyEventParams {
                event_type: "keyUp".to_string(),
                key: Some(key),
                code: Some(code.to_string()),
                text: None,
                unmodified_text: None,
                windows_virtual_key_code: Some(key_code),
                native_virtual_key_code: Some(key_code),
                modifiers: Some(8),
            },
            Some(session_id),
        )
        .await?;
    ghostship_sleep_range(15, 55).await;
    client
        .send_command_typed::<_, Value>(
            "Input.dispatchKeyEvent",
            &DispatchKeyEventParams {
                event_type: "keyUp".to_string(),
                key: Some("Shift".to_string()),
                code: Some("ShiftLeft".to_string()),
                text: None,
                unmodified_text: None,
                windows_virtual_key_code: Some(16),
                native_virtual_key_code: Some(16),
                modifiers: None,
            },
            Some(session_id),
        )
        .await?;
    Ok(())
}

async fn ghostship_human_wheel(
    client: &CdpClient,
    session_id: &str,
    delta_x: f64,
    delta_y: f64,
) -> Result<(), String> {
    if !ghostship_humanize_enabled() {
        return ghostship_mouse_event(client, session_id, "mouseWheel", 400.0, 300.0, None, None, None, Some(delta_x), Some(delta_y)).await;
    }
    let total = delta_y.abs().max(delta_x.abs()).max(1.0);
    let steps = ((total / 90.0).ceil() as i32).clamp(3, 18);
    for i in 0..steps {
        let phase = i as f64 / steps as f64;
        let multiplier = if phase < 0.25 || phase > 0.75 { ghostship_rand(0.55, 0.9) } else { ghostship_rand(0.9, 1.25) };
        let chunk_x = delta_x / steps as f64 * multiplier;
        let chunk_y = delta_y / steps as f64 * multiplier;
        ghostship_mouse_event(client, session_id, "mouseWheel", 400.0, 300.0, None, None, None, Some(chunk_x), Some(chunk_y)).await?;
        ghostship_sleep_range(12, 55).await;
    }
    Ok(())
}

async fn ghostship_human_element_scroll(
    client: &CdpClient,
    session_id: &str,
    object_id: &str,
    delta_x: f64,
    delta_y: f64,
) -> Result<(), String> {
    let steps = if ghostship_humanize_enabled() { ((delta_y.abs().max(delta_x.abs()) / 100.0).ceil() as i32).clamp(3, 16) } else { 1 };
    let js = "function(dx, dy) { this.scrollBy(dx, dy); }".to_string();
    for _ in 0..steps {
        client
            .send_command_typed::<_, Value>(
                "Runtime.callFunctionOn",
                &CallFunctionOnParams {
                    function_declaration: js.clone(),
                    object_id: Some(object_id.to_string()),
                    arguments: Some(vec![
                        CallArgument {
                            value: Some(serde_json::json!(delta_x / steps as f64)),
                            object_id: None,
                        },
                        CallArgument {
                            value: Some(serde_json::json!(delta_y / steps as f64)),
                            object_id: None,
                        },
                    ]),
                    return_by_value: Some(true),
                    await_promise: Some(false),
                },
                Some(session_id),
            )
            .await?;
        if steps > 1 {
            ghostship_sleep_range(14, 58).await;
        }
    }
    Ok(())
}

async fn dispatch_click(
    client: &CdpClient,
    session_id: &str,
    x: f64,
    y: f64,
    button: &str,
    click_count: i32,
) -> Result<(), String> {
    let target_x = if ghostship_humanize_enabled() { (x + ghostship_rand(-4.0, 4.0)).max(0.0) } else { x };
    let target_y = if ghostship_humanize_enabled() { (y + ghostship_rand(-3.0, 3.0)).max(0.0) } else { y };
    ghostship_human_mouse_move(client, session_id, target_x, target_y).await?;
""",
        path=path,
    )
    text = replace_once(
        text,
        """            Some(session_id),
        )
        .await?;

    // Release
""",
        """            Some(session_id),
        )
        .await?;

    if ghostship_humanize_enabled() {
        ghostship_sleep_range(45, 145).await;
    }

    // Release
""",
        path=path,
    )
    text = replace_once(
        text,
        """                event_type: "mousePressed".to_string(),
                x,
                y,
                button: Some(button.to_string()),
""",
        """                event_type: "mousePressed".to_string(),
                x: target_x,
                y: target_y,
                button: Some(button.to_string()),
""",
        path=path,
    )
    text = replace_once(
        text,
        """                event_type: "mouseReleased".to_string(),
                x,
                y,
                button: Some(button.to_string()),
""",
        """                event_type: "mouseReleased".to_string(),
                x: target_x,
                y: target_y,
                button: Some(button.to_string()),
""",
        path=path,
    )

    for marker in (
        "GHOSTSHIP_HUMANIZED_AGENT_BROWSER",
        "ghostship_human_mouse_move",
        "ghostship_human_wheel",
        "ghostship_type_shift_symbol",
        "ghostship_human_type_text",
    ):
        if marker not in text:
            raise RuntimeError(f"missing agent-browser humanize marker: {marker}")

    path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_agent_browser.py /path/to/agent-browser")
    root = Path(sys.argv[1]).resolve()
    patch_interaction(root)


if __name__ == "__main__":
    main()
