-- Keep Omarchy's screensaver and lock timers paused while a game is fullscreen.
-- Add this to ~/.config/hypr/hyprland.lua after the user modules are loaded.
o.window(".*", { idle_inhibit = "fullscreen" })
