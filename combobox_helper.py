import tkinter as tk


def set_combobox_values(combo, values):
    """Set combobox values and keep a full immutable source list for filtering."""
    full_values = list(values)
    combo._full_values_cache = full_values
    combo["values"] = full_values


def bind_searchable_combobox(combo):
    """Enable ERP-like search + autocomplete for ttk.Combobox."""
    try:
        if combo.cget("state") == "readonly":
            combo.configure(state="normal")
    except Exception:
        pass

    def _get_full_values():
        return list(getattr(combo, "_full_values_cache", []))

    def _match_values(query):
        text = (query or "").strip().lower()
        full = _get_full_values()
        if not text:
            return full

        prefix_matches = [item for item in full if item.lower().startswith(text)]
        contains_matches = [item for item in full if text in item.lower() and item not in prefix_matches]
        return prefix_matches + contains_matches

    def _on_key_release(event):
        if event.keysym in {"Up", "Down", "Left", "Right", "Return", "Escape", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"}:
            return

        current_text = combo.get()
        typed = current_text.strip()
        matches = _match_values(typed)
        combo["values"] = matches

        if not typed or not matches:
            return

        first = matches[0]
        if event.keysym not in {"BackSpace", "Delete"} and first.lower().startswith(typed.lower()):
            combo.delete(0, tk.END)
            combo.insert(0, first)
            combo.selection_range(len(typed), tk.END)
            combo.icursor(len(typed))

        # Make filtered results visible immediately while typing.
        if combo.focus_get() is combo:
            combo.event_generate("<Down>")

    def _on_focus_out(_event=None):
        full = _get_full_values()
        combo["values"] = full
        text = combo.get().strip()
        if not text:
            return

        if text in full:
            return

        matches = _match_values(text)
        combo.set(matches[0] if matches else "")

    combo.bind("<KeyRelease>", _on_key_release)
    combo.bind("<FocusOut>", _on_focus_out)
    combo.bind("<<ComboboxSelected>>", _on_focus_out)
